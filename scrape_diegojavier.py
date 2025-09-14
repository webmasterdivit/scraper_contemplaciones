#!/usr/bin/env python3
"""
Scraper ligero para: https://diegojavier.wordpress.com/author/diegojavier/
Extrae: title, post_url, blog_date, ciclo, liturgical_day, gospel_reading, other_readings
Salida: contemplaciones_diejojavier_all.csv
Requisitos: requests, beautifulsoup4, lxml, pandas
Instalación: pip install requests beautifulsoup4 lxml pandas
"""

import re
import time
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import logging
import os
logging.basicConfig(filename="scrap.log", level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

BASE_AUTHOR = "https://diegojavier.wordpress.com/author/diegojavier/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ContemplacionesScraper/1.0)"}

# regexes útiles
POST_URL_RE = re.compile(r"https://diegojavier\.wordpress\.com/\d{4}/\d{2}/[a-z0-9\-]+/?")
BIBLE_CITATION_RE = re.compile(
    r"\b(?:Mt|Mt\.|Mateo|Mc|Mc\.|Marcos|Lc|Lc\.|Lucas|Jn|Jn\.|Juan|Jn|Juan|Hech|Hechos|Rm|Romanos|Is|Isaías|Ezq|Ezequiel)\s*[0-9IVXLivxl]+(?:[:,\.\s]\s*[0-9\-\–\;,\s]+)?",
    flags=re.IGNORECASE)
CYCLE_RE = re.compile(r"\b([1-3]?\s?º?\s?Domingo.*|Adviento.*|Pascua.*|Sagrado Corazón.*|Navidad.*|Cuaresma.*|Tiempo Ordinario.*|Ciclo\s?[ABCabc]|C\s?\d{4})",
                      flags=re.IGNORECASE)
CYCLE_TAG_RE = re.compile(r"\b([ABC])\b", flags=re.IGNORECASE)
PAGINATION_LIMIT = 30  # límite de páginas de autor a rastrear (ajustable)

session = requests.Session()
session.headers.update(HEADERS)

def get_soup(url):
    r = session.get(url, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")

def find_post_links_from_author_page(soup):
    # Busca enlaces absolutos que coincidan con el patrón de posts (año/mes/slug)
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = POST_URL_RE.search(href)
        if m:
            links.add(m.group(0).rstrip("/"))
    return sorted(links)

def extract_from_post(url):
    soup = get_soup(url)
    # Título
    title_tag = soup.find(['h1','h2'], class_=re.compile(r"entry-title|post-title", re.I)) or soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else soup.title.get_text(strip=True)
    # Fecha
    date_tag = soup.find('time')
    blog_date = date_tag.get('datetime')[:10] if date_tag and date_tag.get('datetime') else (date_tag.get_text(strip=True) if date_tag else "")
    # Contenido (texto)
    article = soup.find('article') or soup.find('div', class_=re.compile(r"entry-content|post-content", re.I)) or soup
    content_text = article.get_text(separator="\n", strip=True)

    # Ciclo / liturgical_day: intento extraer del título (entre paréntesis o sufijo)
    ciclo = ""
    liturgical_day = ""
    # buscar paréntesis en el título
    par = re.search(r"\(([^)]+)\)", title)
    if par:
        candidate = par.group(1)
        # extraer letra de ciclo si aparece (A/B/C)
        m_c = CYCLE_TAG_RE.search(candidate)
        if m_c:
            ciclo = m_c.group(1).upper()
        liturgical_day = candidate.strip()
    else:
        # si no hay paréntesis, buscar en el texto un patrón
        m = CYCLE_RE.search(title)
        if m:
            liturgical_day = m.group(0).strip()
            m2 = CYCLE_TAG_RE.search(m.group(0))
            if m2:
                ciclo = m2.group(1).upper()

    # Si no se encontró, intentar buscar ciclos en el contenido (p.ej. "Ciclo C")
    if not ciclo:
        m = re.search(r"\bCiclo\s*([ABC])\b", content_text, re.I)
        if m:
            ciclo = m.group(1).upper()
    # Extraer lecturas bíblicas (busca citas típicas como "Lc 10, 1-12; 17-20")
    citations = BIBLE_CITATION_RE.findall(content_text)
    # limpiemos y prioricemos lecturas evangélicas (Mt, Mc, Lc, Jn)
    gospel_candidates = [c.strip() for c in citations if re.search(r"\b(Lc|Lucas|Mateo|Mt|Marcos|Marcos|Juan|Jn)\b", c, re.I)]
    gospel_reading = "; ".join(gospel_candidates) if gospel_candidates else (citations[0] if citations else "")

    # other_readings: juntamos las otras citas que no sean evangelio
    other_readings = "; ".join([c.strip() for c in citations if c.strip() not in gospel_candidates])

    return {
        "title": title,
        "post_url": url,
        "blog_date": blog_date,
        "ciclo": ciclo,
        "liturgical_day": liturgical_day,
        "gospel_reading": gospel_reading,
        "other_readings": other_readings
    }

def crawl_all_posts():
    found_posts = set()
    all_rows = []
    # Recorremos páginas de autor hasta límite o hasta que no haya nuevas entradas
    for page in range(1, PAGINATION_LIMIT+1):
        page_url = BASE_AUTHOR if page == 1 else f"{BASE_AUTHOR}page/{page}/"
        try:
            soup = get_soup(page_url)
        except Exception as e:
            print(f"[!] Error abriendo {page_url}: {e}")
            break
        links = find_post_links_from_author_page(soup)
        if not links:
            # si no hay links en esta página, detenemos
            break
        new_links = [l for l in links if l not in found_posts]
        if not new_links:
            # no hay nuevas entradas -> terminar
            break
        print(f"[+] Página {page}: {len(new_links)} nuevas entradas encontradas.")
        for link in new_links:
            try:
                row = extract_from_post(link)
                all_rows.append(row)
                found_posts.add(link)
                # Loguear la entrada procesada
                logging.info(f"Entrada procesada: {row['title']} | URL: {row['post_url']} | Fecha: {row['blog_date']}")
                # pequeña pausa para no saturar el sitio
                time.sleep(0.8)
            except Exception as e:
                logging.error(f"Error procesando {link}: {e}")
                print(f"[!] Error procesando {link}: {e}")
        # pequeña pausa entre páginas
        time.sleep(1.0)
    return all_rows

def save_csv(rows, path="contemplaciones_diejojavier_all.csv"):
    # Asegura que el directorio 'salida' exista
    os.makedirs("salida", exist_ok=True)
    output_path = os.path.join("salida", "contemplaciones_diejojavier_all.csv")
    df = pd.DataFrame(rows, columns=[
        "title", "post_url", "blog_date", "ciclo", "liturgical_day", "gospel_reading", "other_readings"
    ])
    df.to_csv(output_path, index=False)
    print(f"[+] Guardado {len(df)} entradas en {output_path}")

if __name__ == "__main__":
    print("Comenzando rastreo del autor...")
    rows = crawl_all_posts()
    save_csv(rows)
    print("Listo. Revisa el CSV generado.")
