from newspaper import build
from datetime import datetime
from normalizar_urls import normalizar_url
from newspaper import build, Config

def procesar_url(url, urls_pasadas, fecha_mas_reciente):
    print(f"\nProcesando sitio: {url}")
    # articulos = []
    articulos=set()

    try:
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0 (Linux; Android 10; Pixel 3 XL Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'
        config.request_timeout = 10
        config.language= 'es'
        config.request_timeout = 5
        config.thread_timeout_seconds = 5
        config.memoize_articles = False
        config.fetch_images = False
        config.follow_meta_refresh = True
        config.number_threads = 16
        config.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
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
        paper = build(url, language='es', config=config)
        for article in paper.articles:
            url_articulo = normalizar_url(article.url)

            if url_articulo in urls_pasadas:
                print(f"Artículo ya procesado previamente, ignorado: {url_articulo}")
                continue

            try:
                article.download()
                article.parse()

                titulo = article.title
                fecha_publicacion = article.publish_date

                if not fecha_publicacion:
                    fecha_publicacion = 'Desconocido'
                else:
                    fecha_publicacion = fecha_publicacion.strftime('%Y-%m-%d')

                    if fecha_mas_reciente and datetime.strptime(fecha_publicacion, '%Y-%m-%d') < fecha_mas_reciente:
                        print("Artículo ignorado porque es más antiguo que la fecha más reciente registrada.")
                        continue

                articulos.add((titulo, fecha_publicacion, url_articulo))

            except Exception as e:
                print(f"Error procesando el artículo: {e}")

    except Exception as e:
        print(f"Error procesando el sitio: {e}")

    return articulos

