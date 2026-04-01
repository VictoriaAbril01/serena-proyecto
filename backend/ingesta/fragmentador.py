import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from loguru import logger

from backend.utilidades.configuracion import obtener_config

config = obtener_config()

DIR_ENTRADA = Path("backend/datos")
DIR_SALIDA  = Path("backend/datos/chunks")


def cargar_documentos() -> list[dict]:
    todos = []

    for nombre_archivo in ["materiales.json", "psiconecta.json"]:
        ruta = DIR_ENTRADA / nombre_archivo
        if ruta.exists():
            with open(ruta, encoding="utf-8") as f:
                docs = json.load(f)
            logger.info(f"  {nombre_archivo}: {len(docs)} documentos")
            todos.extend(docs)
        else:
            logger.debug(f"  {nombre_archivo}: no encontrado, se omite")

    if not todos:
        logger.error("No hay documentos. Ejecuta el extractor y/o el scraper.")
    else:
        logger.info(f"Total documentos cargados: {len(todos)}")

    return todos


def convertir_a_langchain(docs: list[dict]) -> list[Document]:
    resultado = []
    for d in docs:
        texto = d.get("texto", "").strip()
        if not texto:
            continue
        meta = {
            "titulo":    d.get("titulo", ""),
            "archivo":   d.get("archivo", d.get("url", "")),
            "fuente":    d.get("fuente", "pdf_material"),
            "categoria": d.get("categoria", "salud_mental"),
            "pagina":    d.get("pagina", 0),
            "url":       d.get("url", ""),
        }
        resultado.append(Document(page_content=texto, metadata=meta))
    logger.info(f"Documentos convertidos: {len(resultado)}")
    return resultado


def fragmentar(documentos: list[Document]) -> list[Document]:
    divisor = RecursiveCharacterTextSplitter(
        chunk_size=config.tamano_chunk,
        chunk_overlap=config.solapamiento_chunk,
        separators=["\n\n", "\n", ". ", "? ", "! ", " "],
    )
    fragmentos = divisor.split_documents(documentos)
    fragmentos = [f for f in fragmentos if len(f.page_content.strip()) > 60]

    for i, f in enumerate(fragmentos):
        f.metadata["id_chunk"] = f"chunk_{i:05d}"

    logger.success(f"Fragmentos generados: {len(fragmentos)}")
    return fragmentos


def guardar_fragmentos(fragmentos: list[Document]):
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    salida = DIR_SALIDA / "fragmentos.json"
    datos = [
        {"id_chunk": f.metadata["id_chunk"], "texto": f.page_content, "metadata": f.metadata}
        for f in fragmentos
    ]
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    logger.success(f"{len(fragmentos)} fragmentos -> {salida}")


def ejecutar() -> list[Document]:
    docs_raw = cargar_documentos()
    if not docs_raw:
        return []
    lc_docs = convertir_a_langchain(docs_raw)
    fragmentos = fragmentar(lc_docs)
    guardar_fragmentos(fragmentos)
    return fragmentos


if __name__ == "__main__":
    ejecutar()