import os
import csv
from datetime import datetime
from normalizar_urls import normalizar_url

def cargar_urls_y_fecha_mas_reciente(hoy, carpeta_csv='archivos'):
    carpeta_csv = os.path.join(os.path.dirname(__file__), carpeta_csv)  # Ruta absoluta

    urls_pasadas = set()
    fecha_mas_reciente = None
    url_mas_reciente = None
    archivo_mas_reciente = None

    archivos_csv = [f for f in os.listdir(carpeta_csv) if f.endswith('.csv') and f != f'articulos_{hoy}.csv']
    for archivo_csv in archivos_csv:
        ruta_completa = os.path.join(carpeta_csv, archivo_csv)
        with open(ruta_completa, mode='r', newline='', encoding='utf-8') as archivo_csv_pasado:
            lector_csv = csv.reader(archivo_csv_pasado)
            next(lector_csv)  # Saltar la cabecera
            for fila in lector_csv:
                url_normalizada = normalizar_url(fila[2])  # La URL está en la tercera columna
                urls_pasadas.add(url_normalizada)

                try:
                    fecha = datetime.strptime(fila[1], '%Y-%m-%d')
                    if fecha_mas_reciente is None or fecha > fecha_mas_reciente:
                        fecha_mas_reciente = fecha
                        url_mas_reciente = url_normalizada
                        archivo_mas_reciente = archivo_csv
                except ValueError:
                    pass  # Ignorar fechas inválidas

    return urls_pasadas, fecha_mas_reciente, url_mas_reciente, archivo_mas_reciente
