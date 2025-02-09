from newspaper import build
from datetime import datetime
from normalizar_urls import normalizar_url

def procesar_url(url, urls_pasadas, fecha_mas_reciente):
    print(f"\nProcesando sitio: {url}")
    articulos = []

    try:
        paper = build(url, language='es', memoize_articles=False)
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

                articulos.append((titulo, fecha_publicacion, url_articulo))

            except Exception as e:
                print(f"Error procesando el artículo: {e}")

    except Exception as e:
        print(f"Error procesando el sitio: {e}")

    return articulos
