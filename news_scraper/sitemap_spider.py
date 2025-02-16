import scrapy
class SitemapSpider(scrapy.Spider):
    name = 'sitemap_spider'
    start_urls = ['https://www.elcomercio.es/sitemap.xml',
                  'https://www.lne.es/sitemap_google_news_52e19.xml',
                  'https://www.larazon.es/sitemaps/news.xml',
                  'https://www.lavanguardia.com/sitemap-google-news.xml',
                  'https://www.rtpa.es/sitemap-noticias.xml',
                  'https://www.europapress.es/news_sitemap_1.xml',
                  'https://www.abc.es/sitemap.xml',
                  'https://www.20minutos.es/sitemap-google-news.xml',
                  'https://www.elperiodico.com/es/google-news.xml',
                  'https://www.eldiario.es/sitemap_google_news_25b87.xml']
    #custom_settings = {
    #    'ROBOTSTXT_OBEY': False
    #}

    namespaces = {
        'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',  # Default namespace
        'news': 'http://www.google.com/schemas/sitemap-news/0.9'
    }

    def parse(self, response):
        # Extraer datos de cada tag <url>
        for url in response.xpath('//ns:url', namespaces=self.namespaces):
            loc = url.xpath('./ns:loc/text()', namespaces=self.namespaces).get()
            title = url.xpath('./news:news/news:title/text()', namespaces=self.namespaces).get()
            publication_date = url.xpath('./news:news/news:publication_date/text()', namespaces=self.namespaces).get()
            publisher = url.xpath('./news:news/news:publication/news:name/text()', namespaces=self.namespaces).get()

            yield {
                'fuente': publisher,
                'url': loc,
                'titulo': title,
                'fecha_publicacion': publication_date,
            }
    
