from urllib.parse import urljoin
import scrapy
from scrapy import Request
from scrapy.selector import Selector
from scrapy.http import TextResponse
from news_scraper.utils.utils import *
from news_scraper.metadata import METADATA_URLS, INVALID_URL_WORDS, SITEMAP_NAMESPACES
import gzip

class SitemapParser:
    def __init__(self, from_date):     
        self.from_date = from_date


    def parse_sitemap(self, response, domain=None):
        """
        Procesa un sitemap para extraer URLs de noticias.
        """
        # Procesar sitemaps anidados
        yield from self._process_nested_sitemaps(response, domain)

        # Verificar que el archivo tenga noticias recientes
        if not self._has_recent_news(response):
            return

        # Extraer datos de cada tag <url>
        yield from self._extract_url_data(response, domain)


    def _process_nested_sitemaps(self, response, domain=None):
        """
        Procesa los sitemaps anidados dentro de un sitemap.
        """
        if isinstance(response, Selector):
            # Si es un selector, usar sus métodos directamente
            sitemap_selectors = response.xpath('//ns:sitemap', namespaces=SITEMAP_NAMESPACES)
        elif isinstance(response, TextResponse):
            # Si es una TextResponse, acceder a su selector
            sitemap_selectors = response.selector.xpath('//ns:sitemap', namespaces=SITEMAP_NAMESPACES)
        else:
            print(f"La respuesta no es un TextResponse ni un Selector. {type(response)}")
            return

        for sitemap in sitemap_selectors:
            sitemap_loc = sitemap.xpath('./ns:loc/text()', namespaces=SITEMAP_NAMESPACES).get()

            # Omitir sitemaps antiguos
            last_mod = sitemap.xpath('./ns:lastmod/text()', namespaces=SITEMAP_NAMESPACES).get()
            if last_mod:
                lastmod = normalize_date(last_mod)
                if lastmod < self.from_date:
                    continue

            # Algunas sitemaps no contiene la url completa, agregar base_url
            if not is_full_url(sitemap_loc):
                sitemap_loc = urljoin(domain, sitemap_loc)

            # Verificar que la url es un archivo xml
            file_extension = get_url_extension(sitemap_loc)

            if file_extension.lower() != '.gz' and is_valid_sitemap_url(sitemap_loc, INVALID_URL_WORDS):
                #print(f'Se encontró otro xml dentro del archivo actual: {sitemap_loc}') # varias salidas
                if sitemap_loc:
                    # Explorar recursivamente otros archivos xml
                    yield scrapy.Request(sitemap_loc, callback=lambda response: self.parse_sitemap(response, domain) )
            elif file_extension.lower() == '.gz'  and is_valid_sitemap_url(sitemap_loc, INVALID_URL_WORDS):
                print(f"Se encontró archivo comprimido {sitemap_loc}")
                yield scrapy.Request(sitemap_loc, callback=lambda response: self.parse_sitemap_gz(response, domain) )


    def parse_sitemap_gz(self, response, domain=None):
        compressed_file = response.body
        decompressed_file = gzip.decompress(compressed_file).decode("utf-8")
        selector = Selector(text=decompressed_file, type="xml")
        yield from self.parse_sitemap(selector, domain)


    def _has_recent_news(self, response):
        if isinstance(response, Selector):
            # Si es un selector, usar sus métodos directamente
            selector_list = response.xpath('//ns:url', namespaces=SITEMAP_NAMESPACES)
        elif isinstance(response, TextResponse):
            # Si es una TextResponse, acceder a su selector
            selector_list = response.selector.xpath('//ns:url', namespaces=SITEMAP_NAMESPACES)
        else:
            print(f"La respuesta no es un TextResponse ni un Selector. {type(response)}")
            return

        if len(selector_list) < 1:
            return False

        start_index = 0 if len(selector_list) == 1 else 1
        first_publication_date = self._get_publication_date(selector_list[start_index])
        last_publication_date = self._get_publication_date(selector_list[-1])

        if not first_publication_date or not last_publication_date:
            return False

        return not (first_publication_date < self.from_date and last_publication_date < self.from_date)


    def _extract_url_data(self, response, domain):
        """
        Extrae datos de cada tag <url> en el sitemap.
        """
        for url in response.xpath('//ns:url', namespaces=SITEMAP_NAMESPACES):
            loc = url.xpath('./ns:loc/text()', namespaces=SITEMAP_NAMESPACES).get()
            titulo = url.xpath('./news:news/news:title/text()', namespaces=SITEMAP_NAMESPACES).get() or ""
            fecha_publicacion = self._get_publication_date(url, normalize=False)
            fecha_publicacion_norm = normalize_date(fecha_publicacion) if fecha_publicacion else None #fecha normalizada para comparar
            fuente = self._get_source(url, domain)

            if loc and is_full_url(loc) and fecha_publicacion and fecha_publicacion_norm >= self.from_date:
                yield {
                    'fuente': fuente,
                    'url': loc,
                    'titulo': titulo,
                    'fecha_publicacion': fecha_publicacion,
                }


    def _get_publication_date(self, selector, normalize=True):
        """
        Obtiene la fecha de publicación de un selector.
        """
        fecha = selector.xpath('./news:news/news:publication_date/text()', namespaces=SITEMAP_NAMESPACES).get()
        if not fecha:
            fecha = selector.xpath('./ns:lastmod/text()', namespaces=SITEMAP_NAMESPACES).get()

        if not fecha:
            return None

        return normalize_date(fecha) if normalize else fecha


    def _get_source(self, selector, domain):
        """
        Obtiene la fuente de la noticia.
        """
        fuente = selector.xpath('./news:news/news:publication/news:name/text()', namespaces=SITEMAP_NAMESPACES).get()
        if domain:
            domain_base = get_base_url(domain)
            if domain_base in METADATA_URLS:
                fuente = METADATA_URLS[domain_base]['nombre']
        return fuente or ""
