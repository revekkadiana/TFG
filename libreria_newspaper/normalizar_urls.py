from urllib.parse import urlsplit, urlunsplit

def normalizar_url(url):
    partes_url = urlsplit(url)
    url_sin_fragmento = partes_url._replace(fragment="")  # Eliminar fragmento
    return urlunsplit(url_sin_fragmento)
