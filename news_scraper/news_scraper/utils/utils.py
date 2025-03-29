from urllib.parse import urljoin, urlparse
import re
import os
from datetime import datetime, timedelta
import dateutil
from dateutil import parser as date_parser

def get_base_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}/"


def is_full_url(url):
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])


def is_valid_sitemap_url(url, invalid_url_words):
    for invalid_word in invalid_url_words:
        if invalid_word in url:
            return False

    pattern = r'\b(1[0-9]{3}|20[0-1][0-9]|202[0-4])\b' # Matches 1000-1999, 2000-2019, and 2020-2024
    match_url = re.search(pattern, url)
    if match_url:
        return False
    else:
        return True


def normalize_url(url, base_url=None):
    if not is_full_url(url) and base_url:
        return urljoin(base_url, url)
    return url


def get_url_extension(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    _, extension = os.path.splitext(path)
    return extension


def extract_sitemap_urls(robots_text, invalid_url_words={}):
    sitemap_urls = set() #no admite duplicados
    for line in robots_text.splitlines():
        if line.lower().startswith('sitemap:'):
            sitemap_url = line.split(':', 1)[1].strip()
            if is_valid_sitemap_url(sitemap_url, invalid_url_words):
                sitemap_urls.add(sitemap_url)
    return sitemap_urls
    

def normalize_date(date_string, formato_entrada=None):
    try:
        # Convertir la cadena de fechas en un objeto datetime
        parsed_date = dateutil.parser.parse(date_string)
        # Formatea el objeto datetime como 'YYYY-MM-DD'
        return parsed_date.date()
    except (ValueError, TypeError):
        print(f"Formato de fecha inválido: '{date_string}'")
        return None


def get_current_date():
    return datetime.now().date()


def subtract_days_from_date(date: datetime.date, days: int) -> datetime.date:
    return date - timedelta(days=days)
