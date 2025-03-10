import scrapy
from newspaper import build, Config, Article
import requests
from urllib.parse import urljoin, urlparse
import os
import time
import re
from datetime import datetime
import gzip
from scrapy.selector import Selector
import dateutil
from config_urls import METADATA_URLS


class NewsUrlExtractorSpider(scrapy.Spider):
    name = 'news_extractor'

    def __init__(self, date="2025-01-01", *args, **kwargs):
        super(NewsUrlExtractorSpider, self).__init__(*args, **kwargs)
        self.from_date = datetime.strptime(date, '%Y-%m-%d').date()
        self.invalid_url_words = {'section', 'tag', 'template',
                                  'category', 'author', 'page-sitemap'
                                  'categories', 'video', 'image', 'temas',
								                  'live', 'microsite', 'focus', 'blog',
                                  'ocio', 'cine', 'board', 'character',
                                  'galeria', 'categoria', 'ficha', 'firmante',
                                  'secciones', 'hemeroteca', 'landing',
                                  'sorteo', 'elecciones', 'autor', 'hilos', 'cartelera'}
        self.metadata_urls = METADATA_URLS

    #metadata_urls = {
    #    'https://fernandezrozas.com/': {'nombre': 'Blog de José Carlos Fernández Rozas'},
    #}

    custom_settings = {
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        #'DOWNLOAD_DELAY': 2,   # Agregar delay 0.5 segundos entre requests
        #'RETRY_TIMES': 5       #
    }

    # Para extracción de xmls
    namespaces = {
        'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',  # Default namespace
        'news': 'http://www.google.com/schemas/sitemap-news/0.9'
    }

    def get_base_url(self, url):
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}/"

    def normalize_date(self, date_string):
        try:
            # Conviertir la cadena de fechas en un objeto datetime
            parsed_date = dateutil.parser.parse(date_string)
            # Formatea el objeto datetime como 'YYYY-MM-DD'
            #return parsed_date.strftime('%Y-%m-%d')
            return parsed_date.date()
        except (ValueError, TypeError):
            #raise ValueError(f"Formato de fecha inválido: '{date_string}'")
            print(f"Formato de fecha inválido: '{date_string}'")
            return None

    def is_valid_xml_url(self, sitemap_url):
        for invalid_word in self.invalid_url_words:
            if invalid_word in sitemap_url:
                return False

        pattern = r'\b(1[0-9]{3}|20[0-1][0-9]|202[0-4])\b' # Matches 1000-1999, 2000-2019, and 2020-2024
        match_url = re.search(pattern, sitemap_url)
        if match_url:
            return False
        else:
            return True

    def start_requests(self):
        for url in self.metadata_urls:
            #yield scrapy.Request(url=url, callback=self.parse, errback=lambda failure: self.handle_error(failure, url))
            yield scrapy.Request(url=url, callback=self.parse)


    def handle_error(self, failure, domain=None):
        if failure and failure.value and failure.value.response:
            print(f"Request fallida: {failure.value.response.status} para {failure.request.url}")
        else:
            print(f"Request fallida para {failure.request.url}")
        print(f"Accediendo a enlaces con librería Newspaper...")
        if domain is None:
            domain = failure.request.url
        yield from self.get_news_urls(domain)


    def parse(self, response):
        robots_url = urljoin(response.url, "/robots.txt")
        print(f'Robots URL: {robots_url}')
        self.valid_robots = False
        yield scrapy.Request(robots_url, callback=self.parse_robots,
                             meta={'domain': response.url},
                             errback=lambda failure: self.handle_error(failure, response.url))#self.get_base_url(response.url)))


    def is_full_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.scheme) and bool(parsed.netloc)


    def parse_robots(self, response):
        if response.status != 200:
            print(f"Error al acceder a la url: {response.status}.")
            return
        self.valid_robots = True

        domain = response.meta['domain']
        domain_base = self.get_base_url(domain)

        current_sitemap_urls = set() #[]

        # Extraer urls de sitemaps de robots.txt
        for line in response.text.splitlines():
            if line.lower().startswith('sitemap:'):
                sitemap_url = line.split(':', 1)[1].strip()
                parsed_url = urlparse(sitemap_url)
                file_path = parsed_url.path
                file_name, file_extension = os.path.splitext(file_path)
                if self.is_valid_xml_url(sitemap_url):
                    current_sitemap_urls.add(sitemap_url)

        if len(current_sitemap_urls) > 0:
            print(f"Se encontraron los siguientes enlaces xml: {current_sitemap_urls}")

            for enum, sitemap_url in enumerate(current_sitemap_urls):
                print(f"Accediendo al siguiente enlace... {sitemap_url}")
                #yield scrapy.Request(sitemap_url, callback=self.parse_sitemap)  # Llamada recursiva
                if enum == 0:
                    yield scrapy.Request(sitemap_url,
                                         callback=lambda response: self.parse_sitemap(response, domain),
                                         errback=lambda failure: self.handle_error(failure, domain) )
                else:
                    yield scrapy.Request(sitemap_url, callback=lambda response: self.parse_sitemap(response, domain) )

        elif domain_base in self.metadata_urls and 'sitemap' in self.metadata_urls[domain_base]:
            print("No se encontraron enlaces xml en robots.txt.", end=" ")
            sitemap_names = self.metadata_urls[domain_base]['sitemap']
            if isinstance(sitemap_names, list):
                for sitemap_name in sitemap_names:
                    sitemap_url = urljoin(domain_base, sitemap_name)
                    print(f"Accediendo al siguiente enlace especificado... {sitemap_url}")
                    yield scrapy.Request(sitemap_url, callback=lambda response: self.parse_sitemap(response, domain_base) )
            else:
                sitemap_url = urljoin(domain_base, sitemap_names)
                print(f"Accediendo al siguiente enlace especificado... {sitemap_url}")
                #yield scrapy.Request(sitemap_url, callback=self.parse_sitemap)
                yield scrapy.Request(sitemap_url,
                                     callback=lambda response: self.parse_sitemap(response, domain_base),
                                     errback=lambda failure: self.handle_error(failure, domain) )
        else:
            print("No se encontraron enlaces xml. Accediendo a enlaces con librería Newspaper...")
            # Si no se encuentra ningún mapa del sitio,
            # utilizar Newspaper4k para obtener las URL de los artículos de noticias
            yield from self.get_news_urls(domain)


    def parse_sitemap(self, response, domain=None):

        # Sitemaps anidados. Tag <sitemap>
        for sitemap in response.xpath('//ns:sitemap', namespaces=self.namespaces):
            sitemap_loc = sitemap.xpath('./ns:loc/text()', namespaces=self.namespaces).get()

            # Omitir sitemaps antiguos
            last_mod = sitemap.xpath('./ns:lastmod/text()', namespaces=self.namespaces).get()
            if last_mod:
                lastmod = self.normalize_date(last_mod)
                if lastmod < self.from_date:
                    continue
            #else:
            #    continue

            # Algunas sitemaps no contiene la url completa, agregar base_url
            if not self.is_full_url(sitemap_loc):
                sitemap_loc = urljoin(domain, sitemap_loc)


            # Verificar que la url es un archivo xml
            parsed_url = urlparse(sitemap_loc)
            file_path = parsed_url.path
            file_name, file_extension = os.path.splitext(file_path)


            if file_extension.lower() != '.gz' and self.is_valid_xml_url(sitemap_loc):#'section' not in sitemap_loc:
                #print(f'Se encontró otro xml dentro del archivo actual: {sitemap_loc}') ## lots of outputs
                if sitemap_loc:
                    #yield scrapy.Request(sitemap_loc, callback=self.parse_sitemap)  # Llamada recursiva
                    yield scrapy.Request(sitemap_loc, callback=lambda response: self.parse_sitemap(response, domain) )
            elif file_extension.lower() == '.gz'  and self.is_valid_xml_url(sitemap_loc):#'section' not in sitemap_loc:
                print(f"Se encontró archivo comprimido {sitemap_loc}")
                #yield scrapy.Request(sitemap_loc, callback=self.parse_sitemap_gz)
                yield scrapy.Request(sitemap_loc, callback=lambda response: self.parse_sitemap_gz(response, domain) )



        # Verificar que el archivo tenga noticias recientes
        selector_list = response.xpath('//ns:url', namespaces=self.namespaces)
        if len(selector_list) > 1:
            first_publication_date = selector_list[1].xpath('./news:news/news:publication_date/text()', namespaces=self.namespaces).get()
            if first_publication_date is None:
                first_publication_date = selector_list[1].xpath('./ns:lastmod/text()', namespaces=self.namespaces).get()

            last_publication_date = selector_list[-1].xpath('./news:news/news:publication_date/text()', namespaces=self.namespaces).get()
            if last_publication_date is None:
                last_publication_date = selector_list[-1].xpath('./ns:lastmod/text()', namespaces=self.namespaces).get()

            if first_publication_date and last_publication_date:
                first_publication_date = self.normalize_date(first_publication_date)
                last_publication_date = self.normalize_date(last_publication_date)
                if first_publication_date < self.from_date and last_publication_date < self.from_date:
                    return # No cumple con las fechas requeridas
            else:
                return # No se tienen fechas

        # Extraer datos de cada tag <url>
        for url in selector_list:
            loc = url.xpath('./ns:loc/text()', namespaces=self.namespaces).get()
            title = url.xpath('./news:news/news:title/text()', namespaces=self.namespaces).get()
            publication_date = url.xpath('./news:news/news:publication_date/text()', namespaces=self.namespaces).get()
            fuente = url.xpath('./news:news/news:publication/news:name/text()', namespaces=self.namespaces).get()

            if loc is None or not self.is_full_url(loc):
                break

            title = "" if title is None else title

            if publication_date is None:
                publication_date = url.xpath('./ns:lastmod/text()', namespaces=self.namespaces).get()

            if publication_date is not None:
                publication_date_comp = self.normalize_date(publication_date)
                if publication_date_comp < self.from_date:
                    continue
            else:
                continue


            if domain is not None:
                domain_base = self.get_base_url(domain)
                if domain_base in self.metadata_urls:
                    fuente = self.metadata_urls[domain_base]['nombre']

            yield {
                'fuente': fuente,
                'url': loc,
                'titulo': title,
                'fecha_publicacion': publication_date,
            }


    def parse_sitemap_gz(self, response, domain=None):
        compressed_file = response.body
        decompressed_file = gzip.decompress(compressed_file).decode("utf-8")
        selector = Selector(text=decompressed_file, type="xml")
        yield from self.parse_sitemap(selector, domain)


    def get_news_urls(self, domain):

        config = Config()
        config.request_timeout = 5
        config.language= 'es'
        config.thread_timeout_seconds = 5
        config.memoize_articles = False
        config.fetch_images = False
        config.follow_meta_refresh = True
        config.number_threads = 4
        config.browser_user_agent = self.custom_settings['USER_AGENT']
        config.headers = {
            "User-Agent": self.custom_settings['USER_AGENT'],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        try:
            print(f'Extrayendo noticias con librería Newspaper para url: {domain}')
            start_time = time.time()
            paper = build(domain, config=config)
            print(f"--- {(time.time() - start_time):.2f}s segundos ---")
            articulos_urls = set(paper.article_urls())
            print(f'Se encontraron {len(articulos_urls)} enlaces de noticias.')

            # Obtener fuente
            if domain is not None:
                domain_base = self.get_base_url(domain)
                #print(domain_base, ' ', domain_base in self.metadata_urls)
                if domain_base in self.metadata_urls:
                    fuente = self.metadata_urls[domain_base]['nombre']
                else:
                    found_match = re.search(r"www\.(.*?)\.(.+)", domain)
                    fuente = ''
                    if found_match:
                        fuente = found_match.group(1)


            titulo, fecha_publicacion = '', None
            for articulo_url in articulos_urls:
                yield {
                    'fuente': fuente,
                    'url': articulo_url,
                    'titulo': titulo,
                    'fecha_publicacion': fecha_publicacion,
                }
        except Exception as e:
            print(f"No se pudieron obtener noticias de {domain}")
