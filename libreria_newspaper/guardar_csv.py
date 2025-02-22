import os
import csv

def guardar_articulos_csv(articulos, hoy, carpeta_base='libreria_newspapery', subcarpeta='archivos'):
    # Construir la ruta completa
    carpeta_csv = os.path.join(carpeta_base, subcarpeta)
    
    # Crear la carpeta si no existe
    os.makedirs(carpeta_csv, exist_ok=True)
    
    # Ruta del archivo CSV
    archivo_hoy = os.path.join(carpeta_csv, f'articulos_{hoy}.csv')
    
    # Guardar el archivo CSV
    with open(archivo_hoy, mode='w', newline='', encoding='utf-8') as archivo_csv_hoy:
        escritor_csv = csv.writer(archivo_csv_hoy)
        escritor_csv.writerow(['Título', 'Fecha de Publicación', 'URL'])
        
        for titulo, fecha_publicacion, url_articulo in articulos:
            escritor_csv.writerow([titulo, fecha_publicacion, url_articulo])
    
    print(f"Archivo CSV guardado en: {archivo_hoy}")
