from fastapi import APIRouter, HTTPException
from loguru import logger

from backend.api.esquemas import SolicitudChat, RespuestaChat, FuenteDoc
from backend.nucleo.cadena.serena import Serena

rutas = APIRouter()
_sesiones: dict[str, Serena] = {}


def obtener_serena(sesion_id: str) -> Serena:
    if sesion_id not in _sesiones:
        logger.info(f"Nueva sesion: {sesion_id}")
        _sesiones[sesion_id] = Serena()
    return _sesiones[sesion_id]


@rutas.post("", response_model=RespuestaChat)
async def chat(solicitud: SolicitudChat):
    try:
        serena = obtener_serena(solicitud.sesion_id or "default")
        resultado = serena.responder(solicitud.mensaje, solicitud.sesion_id or "default")
        fuentes = [FuenteDoc(**f) for f in resultado["fuentes"]]
        return RespuestaChat(
            respuesta=resultado["respuesta"],
            fuentes=fuentes,
            tipo=resultado["tipo"],
            sesion_id=solicitud.sesion_id or "default",
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rutas.delete("/historial")
async def limpiar_historial(sesion_id: str = "default"):
    if sesion_id in _sesiones:
        _sesiones[sesion_id].limpiar_historial(sesion_id)
    return {"mensaje": "Historial limpiado", "sesion_id": sesion_id}