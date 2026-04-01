from pydantic import BaseModel, Field
from typing import Optional


class SolicitudChat(BaseModel):
    mensaje: str = Field(..., min_length=1, max_length=800)
    sesion_id: Optional[str] = Field("default")


class FuenteDoc(BaseModel):
    titulo: str
    categoria: str
    archivo: str


class RespuestaChat(BaseModel):
    respuesta: str
    fuentes: list[FuenteDoc]
    tipo: str
    sesion_id: str
