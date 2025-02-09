import time
from datetime import datetime
from cargar_urls import cargar_urls_y_fecha_mas_reciente
from procesar_url import procesar_url
from guardar_csv import guardar_articulos_csv

def obtener_fecha_hoy():
    return datetime.now().strftime('%Y-%m-%d')

def main(urls):
    start_time = time.time()
    hoy = obtener_fecha_hoy()
    
    urls_pasadas, fecha_mas_reciente, url_mas_reciente, archivo_mas_reciente = cargar_urls_y_fecha_mas_reciente(hoy)
    print(f"Total de URLs cargadas desde archivos anteriores: {len(urls_pasadas)}")
    print(f"Fecha más reciente en los archivos anteriores: {fecha_mas_reciente}")
    print(f"URL de la fecha más reciente: {url_mas_reciente}")
    print(f"Archivo CSV de la fecha más reciente: {archivo_mas_reciente}")
    
    todos_los_articulos = []
    for url in urls:
        articulos = procesar_url(url, urls_pasadas, fecha_mas_reciente)
        todos_los_articulos.extend(articulos)
    
    # Ordenar artículos manejando 'Desconocido' al final
    todos_los_articulos.sort(key=lambda x: datetime.strptime(x[1], '%Y-%m-%d') if x[1] != 'Desconocido' else datetime.max)
    
    guardar_articulos_csv(todos_los_articulos, hoy)
    print(f"NUMERO TOTAL DE ARTICULOS: {len(todos_los_articulos)}")
    
    duration = time.time() - start_time
    print(f"Duración total de la ejecución: {duration:.2f} segundos")

if __name__ == "__main__":
    # Definir aquí la lista de URLs para probar el script
    # Lista de URLs de los sitios de noticias
    urls = [
    "https://www.elcomercio.es/",
    "https://www.lavozdeasturias.es/",
    "https://www.elpais.com/",
    "https://www.abc.es/",
    "https://www.lne.es/",
    "https://www.eldiario.es/",
    "https://www.elmundo.es/",
    "https://www.larazon.es/"
    ]

    main(urls)
