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

class NewsUrlExtractorSpider(scrapy.Spider):
    name = 'news_extractor'

    def __init__(self, date="2025-01-01", *args, **kwargs):
        super(NewsUrlExtractorSpider, self).__init__(*args, **kwargs)
        self.from_date = datetime.strptime(date, '%Y-%m-%d').date()
        self.invalid_url_words = {'section', 'tag', 'template',
                                  'category', 'author', 'page-sitemap'
                                  'categories', 'video', 'image', 'temas',
								                  'live', 'microsite', 'focus', 'blog',
                                  'ocio', 'cine', 'board', 'character'}


    # Lista de páginas web
    start_urls=[
        'https://www.elcomercio.es/',
        'https://www.lne.es/',
        'https://www.lavanguardia.com/',
        'https://www.larazon.es/',
        'https://www.rtpa.es/',
        'https://www.europapress.es/',
        'https://www.abc.es/',
        'https://www.20minutos.es/',
        'https://www.elperiodico.com/',
        'https://www.eldiario.es/',
        'https://www.elconfidencial.com/',
        'https://www.culturalgijonesa.org/',
        'https://www.elespanol.com/',
        'https://www.nortes.me/',
        'https://www.asturiasmundial.com/',
        'https://www.tribunasalamanca.com/',
        'https://migijon.com/',
        'https://www.telecinco.es/',
        'https://www.laprovincia.es/',
        'https://www.laopiniondemalaga.es/',
        'https://www.elfielato.es/',
        'https://www.teleprensa.com/',
        'https://www.infobae.com/',
        'https://www.lavozdeasturias.es/', #newspaper
        'https://cualia.es/', #newspaper
        'https://www.lavozdegalicia.es/', # newspaper
        'http://www.gentedigital.es/', #newspaper
    ]

    # Metadata: nombre y sitemap
    metadata_urls={
        'https://www.elcomercio.es/': {'nombre': 'El Comercio'},
        'https://www.lne.es/': {'nombre': 'La Nueva España'},
        'https://www.lavanguardia.com/': {'nombre': 'La Vanguardia',
                                          'sitemap': 'sitemap-google-news.xml'},
        'https://www.larazon.es/': {'nombre': 'La Razón'},
        'https://www.rtpa.es/': {'nombre': 'Radiotelevisión del Principado de Asturias (RTPA)',
                                 'sitemap': 'sitemap-noticias.xml'},
        'https://www.europapress.es/': {'nombre': 'Europa Press'},
        'https://www.abc.es/': {'nombre': 'ABC'},
        'https://www.20minutos.es/': {'nombre': '20 Minutos',
                                      'sitemap': 'sitemap-google-news.xml'},
        'https://www.elperiodico.com/' : {'nombre': 'El Periódico',
                                          'sitemap': 'google-news.xml'},
        'https://www.eldiario.es/' : {'nombre': 'ElDiario.es'},
        'https://www.lavozdeasturias.es/': {'nombre': 'La Voz de Asturias'}, #newspaper
        'https://www.elconfidencial.com/': {'nombre': 'El Confidencial',
                                            'sitemap': 'newsitemap_4.xml'},
        'https://cualia.es/': {'nombre': 'Cualia'}, #newspaper
        'https://www.culturalgijonesa.org/': {'nombre': 'Cultural Gijonesa'},
        'https://www.elespanol.com/' : {'nombre': 'El Español',
                                        'sitemap': 'sitemap_google_news.xml'},
        'https://www.nortes.me/': {'nombre': 'Nortes'},
        'https://www.lavozdegalicia.es/': {'nombre': 'La Voz de Galicia'},
        'https://www.asturiasmundial.com/': {'nombre': 'Asturias Mundial'},
        'https://www.tribunasalamanca.com/': {'nombre': 'Tribuna Salamanca'},
        'https://migijon.com/': {'nombre': 'Mi Gijón'},
        'http://www.gentedigital.es/' : {'nombre': 'Gente Digital'}, #newspaper
        'https://www.infobae.com/' : {'nombre': 'Infobae',
                                      'sitemap': 'arc/outboundfeeds/news-sitemap2/'},
        'https://www.telecinco.es/' : {'nombre': 'Telecinco'},
        'https://www.laprovincia.es/' : {'nombre': 'La Provincia'},
        'https://www.laopiniondemalaga.es/': {'nombre': 'La Opinión de Málaga'},
        'https://www.elfielato.es/': {'nombre': 'El Fielato y El Nora'},
        'https://www.teleprensa.com/': {'nombre': 'Teleprensa'}
    }


    custom_settings = {
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0"
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
            raise ValueError(f"Formato de fecha inválido: '{date_string}'")

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

    def parse(self, response):
        robots_url = urljoin(response.url, "/robots.txt")
        print(f'Robots URL: {robots_url}')
        yield scrapy.Request(robots_url, callback=self.parse_robots, meta={'domain': response.url})


    def parse_robots(self, response):
        if response.status != 200:
            print(f"Error al acceder a la url: {response.status}")
            return

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
                if file_extension.lower() == ".xml" and self.is_valid_xml_url(sitemap_url):
                    current_sitemap_urls.add(sitemap_url)

        if len(current_sitemap_urls) > 0:
            print(f"Se encontraron los siguientes enlaces xml: {current_sitemap_urls}")
            for sitemap_url in current_sitemap_urls:
                print(f"Accediendo al siguiente enlace... {sitemap_url}")
                #yield scrapy.Request(sitemap_url, callback=self.parse_sitemap)  # Llamada recursiva
                yield scrapy.Request(sitemap_url, callback=lambda response: self.parse_sitemap(response, domain) )

        elif domain_base in self.metadata_urls and 'sitemap' in self.metadata_urls[domain_base]:
            print("No se encontraron enlaces xml en robots.txt.", end=" ")
            sitemap_name = self.metadata_urls[domain_base]['sitemap']
            #sitemap_name = self.sitemap_urls[domain]
            sitemap_url = urljoin(domain_base, sitemap_name)
            print(f"Accediendo al siguiente enlace especificado... {sitemap_url}")
            #yield scrapy.Request(sitemap_url, callback=self.parse_sitemap)
            yield scrapy.Request(sitemap_url, callback=lambda response: self.parse_sitemap(response, domain_base) )
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

            # Verificar que la url es un archivo xml
            parsed_url = urlparse(sitemap_loc)
            file_path = parsed_url.path
            file_name, file_extension = os.path.splitext(file_path)

            if file_extension.lower() == ".xml" and self.is_valid_xml_url(sitemap_loc):#'section' not in sitemap_loc:
                #print(f'Se encontró otro xml dentro del archivo actual: {sitemap_loc}') ## lots of outputs
                if sitemap_loc:
                    #yield scrapy.Request(sitemap_loc, callback=self.parse_sitemap)  # Llamada recursiva
                    yield scrapy.Request(sitemap_loc, callback=lambda response: self.parse_sitemap(response, domain) )
            elif file_extension.lower() == '.gz'  and self.is_valid_xml_url(sitemap_loc):#'section' not in sitemap_loc:
                print(f"Se encontró archivo comprimido {sitemap_loc}")
                #yield scrapy.Request(sitemap_loc, callback=self.parse_sitemap_gz)
                yield scrapy.Request(sitemap_loc, callback=lambda response: self.parse_sitemap_gz(response, domain) )


        # Extraer datos de cada tag <url>
        for url in response.xpath('//ns:url', namespaces=self.namespaces):

            loc = url.xpath('./ns:loc/text()', namespaces=self.namespaces).get()
            title = url.xpath('./news:news/news:title/text()', namespaces=self.namespaces).get()
            publication_date = url.xpath('./news:news/news:publication_date/text()', namespaces=self.namespaces).get()
            fuente = url.xpath('./news:news/news:publication/news:name/text()', namespaces=self.namespaces).get()

            if loc is None:
                break

            title = "" if title is None else title
            if publication_date is None:
               publication_date = url.xpath('./ns:lastmod/text()', namespaces=self.namespaces).get()

            if publication_date is not None:
                publication_date_comp = self.normalize_date(publication_date)
                #publication_date_ = dateutil.parser.parse(publication_date).date()
                if publication_date_comp < self.from_date:
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
        #yield from self.parse_sitemap(selector)
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
