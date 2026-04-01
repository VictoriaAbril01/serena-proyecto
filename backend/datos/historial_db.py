import sqlite3
import json
from pathlib import Path
from datetime import datetime

_DB = Path("backend/datos/conversaciones.db")

def _conn():
    con = sqlite3.connect(_DB)
    con.row_factory = sqlite3.Row
    return con

def inicializar():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                sesion_id  TEXT    NOT NULL,
                rol        TEXT    NOT NULL,
                texto      TEXT    NOT NULL,
                fecha      TEXT    NOT NULL
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_sesion ON mensajes(sesion_id)")
    return True

def guardar_turno(sesion_id: str, usuario: str, serena: str):
    ahora = datetime.now().isoformat()
    with _conn() as con:
        con.execute(
            "INSERT INTO mensajes (sesion_id, rol, texto, fecha) VALUES (?, ?, ?, ?)",
            (sesion_id, "usuario", usuario, ahora),
        )
        con.execute(
            "INSERT INTO mensajes (sesion_id, rol, texto, fecha) VALUES (?, ?, ?, ?)",
            (sesion_id, "serena", serena, ahora),
        )

def cargar_historial(sesion_id: str, ultimos: int = 12) -> list[dict]:
    with _conn() as con:
        filas = con.execute(
            """
            SELECT rol, texto FROM (
                SELECT rol, texto, id FROM mensajes
                WHERE sesion_id = ?
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY id ASC
            """,
            (sesion_id, ultimos),
        ).fetchall()
    pares, buf = [], {}
    for f in filas:
        if f["rol"] == "usuario":
            buf = {"usuario": f["texto"]}
        elif f["rol"] == "serena" and buf:
            buf["serena"] = f["texto"]
            pares.append(buf)
            buf = {}
    return pares

def borrar_historial(sesion_id: str):
    with _conn() as con:
        con.execute("DELETE FROM mensajes WHERE sesion_id = ?", (sesion_id,))

def contar_mensajes(sesion_id: str) -> int:
    with _conn() as con:
        return con.execute(
            "SELECT COUNT(*) FROM mensajes WHERE sesion_id = ?", (sesion_id,)
        ).fetchone()[0]