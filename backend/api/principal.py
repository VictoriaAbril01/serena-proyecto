from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api.rutas.chat import rutas as rutas_chat
from backend.utilidades.configuracion import obtener_config

config = obtener_config()


@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    logger.info("Iniciando Serena API...")
    yield
    logger.info("Cerrando Serena API...")


app = FastAPI(
    title="Serena API",
    description="Asistente de bienestar emocional para adolescentes",
    version="1.0.0",
    lifespan=ciclo_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rutas_chat, prefix="/chat", tags=["chat"])


@app.get("/salud")
async def salud():
    return {"estado": "ok", "servicio": "serena-api"}


@app.get("/")
async def inicio():
    return {"mensaje": "Serena API activa", "docs": "/docs"}
