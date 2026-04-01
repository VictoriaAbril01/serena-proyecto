import sys
sys.path.insert(0, ".")

from backend.ingesta.extractor import procesar_pdfs
from loguru import logger

if __name__ == "__main__":
    logger.info("Extrayendo texto de PDFs...")
    docs = procesar_pdfs()
    if docs:
        logger.success(f"{len(docs)} paginas extraidas")
        logger.info("Siguiente: python scripts/02_construir_indice.py")
    else:
        logger.error("No se extrajeron documentos. Verifica los PDFs en backend/datos/pdfs/")
