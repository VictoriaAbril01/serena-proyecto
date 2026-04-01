import sys
sys.path.insert(0, ".")

from backend.ingesta.scraper_psiconecta import ejecutar_scraping
from loguru import logger

if __name__ == "__main__":
    logger.info("Scrapeando psiconecta.org...")
    articulos = ejecutar_scraping()
    if articulos:
        logger.success(f"{len(articulos)} articulos descargados")
        logger.info("Siguiente: reconstruye el indice con python scripts/02_construir_indice.py")
    else:
        logger.error("No se descargaron articulos")