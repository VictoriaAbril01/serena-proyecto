from pydantic_settings import BaseSettings
from functools import lru_cache


class Configuracion(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    modelo_llm: str = "qwen3:1.7b"
    temperatura: float = 0.4
    contexto: int = 1536
    hilos: int = 4

    modelo_embeddings: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    directorio_embeddings: str = "./backend/datos/embeddings"
    coleccion: str = "serena_conocimiento"

    tamano_chunk: int = 400
    solapamiento_chunk: int = 60
    resultados_top: int = 3

    host: str = "0.0.0.0"
    puerto: int = 8000
    clave_admin: str = "serena-admin-2024"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def obtener_config() -> Configuracion:
    return Configuracion()
