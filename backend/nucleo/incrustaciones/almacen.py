import json
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from loguru import logger

from backend.utilidades.configuracion import obtener_config

config = obtener_config()
_almacen = None


_emb_singleton = None

def obtener_embeddings():
    global _emb_singleton
    if _emb_singleton is None:
        logger.info("Cargando modelo de embeddings (primera vez)...")
        _emb_singleton = HuggingFaceEmbeddings(
            model_name=config.modelo_embeddings,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 32},
        )
        logger.success("Embeddings listos")
    return _emb_singleton


def construir_almacen(fragmentos: list[Document]) -> Chroma:
    Path(config.directorio_embeddings).mkdir(parents=True, exist_ok=True)
    emb = obtener_embeddings()
    logger.info(f"Generando embeddings para {len(fragmentos)} fragmentos...")
    almacen = Chroma.from_documents(
        documents=fragmentos,
        embedding=emb,
        collection_name=config.coleccion,
        persist_directory=config.directorio_embeddings,
    )
    logger.success(f"Almacen listo: {len(fragmentos)} fragmentos en {config.directorio_embeddings}")
    return almacen


def cargar_almacen() -> Chroma:
    global _almacen
    if _almacen is None:
        emb = obtener_embeddings()
        _almacen = Chroma(
            collection_name=config.coleccion,
            embedding_function=emb,
            persist_directory=config.directorio_embeddings,
        )
        total = _almacen._collection.count()
        logger.info(f"Almacen cargado: {total} fragmentos")
    return _almacen


if __name__ == "__main__":
    ruta = Path("backend/datos/chunks/fragmentos.json")
    if not ruta.exists():
        logger.error("Ejecuta primero el fragmentador.")
    else:
        with open(ruta, encoding="utf-8") as f:
            raw = json.load(f)
        fragmentos = [Document(page_content=r["texto"], metadata=r["metadata"]) for r in raw]
        construir_almacen(fragmentos)