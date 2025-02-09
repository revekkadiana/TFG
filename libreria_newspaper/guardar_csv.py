import os
import csv

def guardar_articulos_csv(articulos, hoy, carpeta_csv='archivos'):
    archivo_hoy = os.path.join(carpeta_csv, f'articulos_{hoy}.csv')
    with open(archivo_hoy, mode='w', newline='', encoding='utf-8') as archivo_csv_hoy:
        escritor_csv = csv.writer(archivo_csv_hoy)
        escritor_csv.writerow(['Título', 'Fecha de Publicación', 'URL'])

        for titulo, fecha_publicacion, url_articulo in articulos:
            escritor_csv.writerow([titulo, fecha_publicacion, url_articulo])

    print(f"Archivo CSV guardado: {archivo_hoy}")
