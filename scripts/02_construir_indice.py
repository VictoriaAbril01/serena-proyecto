import sys
sys.path.insert(0, ".")

from backend.ingesta.fragmentador import ejecutar
from backend.nucleo.incrustaciones.almacen import construir_almacen
from loguru import logger

if __name__ == "__main__":
    logger.info("Construyendo indice vectorial...")

    logger.info("1/2 Fragmentando documentos...")
    fragmentos = ejecutar()
    if not fragmentos:
        logger.error("Sin fragmentos. Ejecuta primero 01_extraer.py")
        sys.exit(1)

    logger.info(f"2/2 Generando embeddings para {len(fragmentos)} fragmentos...")
    construir_almacen(fragmentos)

    logger.success(f"Indice listo con {len(fragmentos)} fragmentos")
    logger.info("Levanta la API: uvicorn backend.api.principal:app --reload --port 8000")
