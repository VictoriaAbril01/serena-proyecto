import json
import time
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from loguru import logger

URL_BASE   = "https://psiconecta.org"
DIR_SALIDA = Path("backend/datos")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}

CATEGORIAS_UTILES = [
    "/adolescentes",
    "/temas-de-salud",
]

CATEGORIAS_RAW = {
    "adolescentes": f"{URL_BASE}/adolescentes",
    "temas_salud":  f"{URL_BASE}/temas-de-salud",
}

TAGS_UTILES = [
    "Ansiedad y Estrés", "Emociones", "Bienestar", "Autocuidado", "Depresión", "Bullying", 
    "Relaciones interpersonales", "Vida saludable", "Duelo", "Trauma", "suicidio", "autolesiones", "autoestima", 
]

MAX_PAGINAS_POR_CATEGORIA = 5
MAX_ARTICULOS_TOTAL       = 80


def _get(url: str) -> BeautifulSoup | None:
    for intento in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            r.encoding = "utf-8"
            return BeautifulSoup(r.text, "lxml")
        except Exception as e:
            logger.warning(f"Intento {intento+1} fallido: {url} -> {e}")
            time.sleep(2)
    return None


def _limpiar(texto: str) -> str:
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    lineas = [l.strip() for l in texto.splitlines() if len(l.strip()) > 3]
    return '\n'.join(lineas).strip()


def _inferir_categoria(tags: list[str], titulo: str) -> str:
    titulo_l = titulo.lower()
    tags_l   = " ".join(tags).lower()

    if "suicidio" in tags_l or "suicidio" in titulo_l:
        return "suicidio"
    if "autolesiones" in tags_l or "autolesiones" in titulo_l:
        return "autolesiones"
    if "ansiedad" in tags_l or "ansiedad" in titulo_l or "estres" in titulo_l:
        return "ansiedad_estres"
    if "emocion" in tags_l or "emocion" in titulo_l:
        return "emociones"
    if "depresion" in tags_l or "depresion" in titulo_l:
        return "depresion"
    if "autocuidado" in tags_l or "bienestar" in tags_l:
        return "bienestar"
    if "bullying" in tags_l or "violencia" in tags_l:
        return "relaciones"
    if "sueno" in tags_l or "sueño" in titulo_l:
        return "sueno"
    if "duelo" in tags_l:
        return "duelo"
    return "salud_mental"


def _extraer_articulo(url: str) -> dict | None:
    soup = _get(url)
    if not soup:
        return None

    titulo_tag = soup.find("h1")
    if not titulo_tag:
        return None
    titulo = titulo_tag.get_text(strip=True)

    if not titulo or len(titulo) < 5:
        return None

    contenido_div = (
        soup.find("div", class_="post-content")
        or soup.find("div", class_="entry-content")
        or soup.find("article")
    )
    if not contenido_div:
        return None

    for tag in contenido_div.find_all(["script", "style", "nav", "aside", "form"]):
        tag.decompose()

    parrafos = []
    for elem in contenido_div.find_all(["p", "h2", "h3", "li"]):
        texto = elem.get_text(separator=" ", strip=True)
        if len(texto) > 30:
            parrafos.append(texto)

    texto_completo = _limpiar("\n".join(parrafos))

    if len(texto_completo) < 100:
        return None

    tags = [
        t.get_text(strip=True)
        for t in soup.find_all("a", class_=lambda c: c and "tag" in c.lower())
    ]

    return {
        "titulo":    titulo,
        "url":       url,
        "fuente":    "psiconecta_web",
        "categoria": _inferir_categoria(tags, titulo),
        "tags":      tags[:8],
        "texto":     texto_completo,
    }


def _obtener_links_categoria(url_categoria: str, max_paginas: int) -> list[str]:
    links = []
    url   = url_categoria

    for pagina in range(1, max_paginas + 1):
        logger.info(f"  Pagina {pagina}: {url}")
        soup = _get(url)
        if not soup:
            break

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/blog/" in href and href not in links:
                if not href.startswith("http"):
                    href = URL_BASE + href
                links.append(href)

        siguiente = soup.find("a", string=re.compile(r"siguiente|next|>", re.IGNORECASE))
        if not siguiente:
            siguiente = soup.find("a", rel="next")

        if siguiente and siguiente.get("href"):
            url = siguiente["href"]
            if not url.startswith("http"):
                url = URL_BASE + url
            time.sleep(0.6)
        else:
            break

    return list(dict.fromkeys(links))


def ejecutar_scraping() -> list[dict]:
    logger.info("Iniciando scraping de psiconecta.org...")
    todos_links: list[str] = []

    for nombre, url_cat in CATEGORIAS_RAW.items():
        logger.info(f"Categoria: {nombre}")
        links = _obtener_links_categoria(url_cat, MAX_PAGINAS_POR_CATEGORIA)
        logger.info(f"  {len(links)} links encontrados")
        todos_links.extend(links)
        time.sleep(0.8)

    todos_links = list(dict.fromkeys(todos_links))[:MAX_ARTICULOS_TOTAL]
    logger.info(f"Total de articulos a procesar: {len(todos_links)}")

    articulos = []
    for i, url in enumerate(todos_links, 1):
        logger.info(f"[{i}/{len(todos_links)}] {url}")
        art = _extraer_articulo(url)
        if art:
            articulos.append(art)
            logger.info(f"  -> OK: '{art['titulo'][:60]}' ({len(art['texto'])} chars)")
        else:
            logger.debug(f"  -> Sin contenido util")
        time.sleep(0.5)

    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    salida = DIR_SALIDA / "psiconecta.json"
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(articulos, f, ensure_ascii=False, indent=2)

    total_chars = sum(len(a["texto"]) for a in articulos)
    logger.success(f"{len(articulos)} articulos guardados en {salida} ({total_chars:,} chars)")
    return articulos


if __name__ == "__main__":
    ejecutar_scraping()