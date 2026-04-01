import re as _re
import random as _random
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferWindowMemory
from loguru import logger

from backend.utilidades.configuracion import obtener_config
from backend.nucleo.incrustaciones.almacen import cargar_almacen

from backend.datos.historial_db import (
    inicializar       as _db_init,
    guardar_turno     as _db_guardar,
    cargar_historial  as _db_cargar,
    borrar_historial  as _db_borrar,
)
_db_init()

config = obtener_config()

_RESPUESTA_NO_ENCONTRADO = (
    "Esa informacion no esta en el material del programa.\n\n"
    "Puedo ayudarte con temas de emociones, mindfulness, regulacion emocional "
    "o los ejercicios de los cuadernos. Intentalo con otra pregunta."
)

_RESPUESTA_FUERA_TEMA = (
    "Lo siento, solo puedo ayudarte con temas de bienestar emocional y salud mental. "
    "Puedo hablar de emociones, mindfulness, regulacion emocional, ejercicios del programa, "
    "y tambien sobre suicidio y autolesion si lo necesitas."
)

_RESPUESTAS_CRISIS = [
    (
        "Gracias por contarme esto. Se necesita mucho valor para decirlo "
        "y me alegra que lo hayas hecho.\n\n"
        "Lo que sientes es real y merece atencion ahora mismo. "
        "Por favor habla hoy con alguien de confianza: un familiar, tu especialista o un maestro.\n\n"
        "Si necesitas hablar con alguien en este momento, "
        "llama al 800 290 0024 (SAPTEL, gratis, 24h, confidencial). "
        "No estas solo/a en esto."
    ),
    (
        "Escucharte decir eso me importa mucho. Gracias por confiar en mi.\n\n"
        "Lo que sientes tiene solucion aunque ahora no lo parezca. "
        "Necesitas hablar con alguien que pueda acompanarte de verdad.\n\n"
        "Llama al 800 290 0024 (SAPTEL, gratis, 24h). "
        "Pedir ayuda no es debilidad, es valentia."
    ),
    (
        "Gracias por contarme. Eso que sientes es muy pesado de cargar solo/a.\n\n"
        "Lo mas importante ahora es que no estes solo/a con esto. "
        "Habla hoy con tu especialista, un familiar o alguien en quien confies.\n\n"
        "Apoyo inmediato: 800 290 0024 (SAPTEL, gratis, 24 horas)."
    ),
]

_PROMPT = PromptTemplate(
    input_variables=["contexto", "historial", "pregunta"],
    template="""Eres Serena, asistente de bienestar emocional del programa Aplicate por tu Mente.
Trabajas con adolescentes de 13 a 18 anos, supervisada por especialistas.

REGLA ABSOLUTA:
Solo puedes responder usando la informacion del CONTEXTO que aparece abajo.
No uses conocimiento general. No inventes nada fuera del contexto.
Si el contexto no tiene informacion relevante para la pregunta, escribe exactamente: SIN_INFORMACION

CONTINUIDAD DE CONVERSACION — MUY IMPORTANTE:
Lee siempre el HISTORIAL antes de responder.
Si en el historial Serena hizo una pregunta (como "te gustaria hacerlo conmigo?" o "quieres intentarlo?"),
y el adolescente responde "si", "claro", "dale", "ok", "andale" o similar,
debes continuar exactamente con lo que ofreciste — no preguntes de nuevo.
Si ya empezaste un ejercicio en el historial, continua desde donde quedaste, no lo reinicies.

MODO INTERACTIVO:
Si el adolescente pregunta por un ejercicio (respiracion, 5 sentidos, semaforo, check-in, mindfulness, etc.):
- Preguntale si quiere hacerlo contigo ahora mismo
- Si acepta, guialo paso a paso, un paso a la vez
- Espera su respuesta antes de pasar al siguiente paso
- Reacciona con calidez a lo que dice (valida, anima)
- Al terminar pregunta como estuvo la experiencia

IDIOMA — REGLA OBLIGATORIA:
Responde SIEMPRE en espanol. Sin excepcion. Nunca en ingles ni en otro idioma.
Aunque el contexto tenga palabras en ingles, tu respuesta es en espanol.

COMO ESCRIBIR:
- Texto plano, sin asteriscos ni simbolos de formato
- Lenguaje sencillo y cercano para jovenes de 13 a 18 anos
- Maximo 4 oraciones cuando no estas guiando un ejercicio
- Nunca des diagnosticos ni reemplaces al especialista

CONTEXTO DEL MATERIAL:
{contexto}

HISTORIAL DE ESTA CONVERSACION:
{historial}

PREGUNTA ACTUAL: {pregunta}

RESPUESTA:"""
)

_CONFIRMACIONES_EXACTAS = {
    "si", "sí", "dale", "ok", "okay", "claro", "andale", "ándale",
    "va", "bueno", "listo", "sale", "esta bien", "está bien", "adelante",
    "claro que si", "claro que sí", "si me parece", "me late",
    "si quiero", "quiero hacerlo", "hagamoslo", "hagámoslo",
    "si por favor", "porfa si", "vamos", "continua", "continúa", "sigue",
}

def _es_confirmacion(texto: str) -> bool:
    t = texto.lower().strip().rstrip("!?. ")
    t = t.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
    return t in _CONFIRMACIONES_EXACTAS

_PALABRAS_CRISIS = [
    "suicidio", "suicidarme", "matarme", "no quiero vivir", "quitarme la vida",
    "hacerme dano", "hacerme daño", "cortarme", "lastimarme", "autolesion",
    "autolesionarme", "no tiene sentido vivir", "mejor muerto", "mejor muerta",
    "no quiero seguir", "quiero morir", "acabar con todo", "desaparecer para siempre",
    "pensamientos suicidas", "quiero hacerme dano", "me quiero quitar",
    "ojalá no hubiera nacido", "quisiera dormirme y no despertar",
    "todo seria mejor sin mi", "ya no aguanto mas vivir",
]

_TEMAS_BLOQUEADOS = [
    "politica", "política", "gobierno", "presidente", "partido politico",
    "congreso", "senado", "diputado", "constitucion",
    "futbol", "fútbol", "beisbol", "basquetbol", "jugador de",
    "equipo de futbol", "liga mx", "champions",
    "receta de", "como cocinar", "ingredientes para",
    "matematicas", "álgebra", "calculo diferencial", "geometria",
    "fisica cuantica", "quimica organica", "biologia celular",
    "programacion en", "javascript", "html y css",
    "videojuego", "pelicula de", "serie de netflix", "anime",
    "dragon ball", "naruto", "one piece", "pokemon",
    "cantante de", "banda de musica", "cancion de",
    "tarea de matematicas", "examen de historia",
    "economia mundial", "bolsa de valores",
    "religion cristiana", "iglesia", "dios existe",
]


def _normalizar(t: str) -> str:
    return t.lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")


def _tiene_crisis(texto: str) -> bool:
    t = _normalizar(texto)
    return any(p in t for p in _PALABRAS_CRISIS)


def _es_fuera_tema(texto: str) -> bool:
    t = _normalizar(texto)
    return any(b in t for b in _TEMAS_BLOQUEADOS)


def _limpiar_md(texto: str) -> str:
    texto = _re.sub(r'\*\*(.+?)\*\*', r'\1', texto)
    texto = _re.sub(r'\*(.+?)\*',     r'\1', texto)
    texto = _re.sub(r'__(.+?)__',     r'\1', texto)
    texto = _re.sub(r'_(.+?)_',       r'\1', texto)
    texto = _re.sub(r'^#{1,6}\s+', '', texto, flags=_re.MULTILINE)
    texto = _re.sub(r'`(.+?)`',       r'\1', texto)
    return texto.strip()


def _nombre_legible(archivo: str) -> str:
    if not archivo:
        return ""
    if archivo.startswith("http"):
        seg = archivo.rstrip("/").split("/")[-1]
    else:
        seg = archivo.replace(".pdf", "")
    return _re.sub(r"[\-_]+", " ", seg).strip().title()


def _nombre_categoria(cat: str) -> str:
    mapa = {
        "mindfulness":           "Mindfulness",
        "regulacion_emocional":  "Regulacion emocional",
        "inteligencia_emocional":"Inteligencia emocional",
        "emociones":             "Emociones",
        "salud_mental":          "Salud mental",
        "ansiedad_estres":       "Ansiedad y estres",
        "prevencion_suicidio":   "Prevencion",
        "bienestar":             "Bienestar",
    }
    return mapa.get(cat, cat.replace("_", " ").title())


def _verificar_ollama() -> bool:
    import httpx
    try:
        r = httpx.get(f"{config.ollama_url}/api/tags", timeout=3)
        modelos = [m["name"] for m in r.json().get("models", [])]
        return any(config.modelo_llm.split(":")[0] in m for m in modelos)
    except Exception:
        return False


class Serena:
    def __init__(self):
        logger.info(f"Iniciando Serena | modelo={config.modelo_llm}")
        if not _verificar_ollama():
            logger.warning(f"Modelo '{config.modelo_llm}' no detectado en Ollama.")

        self.llm = ChatOllama(
            model=config.modelo_llm,
            base_url=config.ollama_url,
            temperature=config.temperatura,
            num_ctx=config.contexto,
            num_thread=config.hilos,
            num_predict=180,
            repeat_penalty=1.05,
            top_k=20,
            top_p=0.8,
        )
        self.almacen    = cargar_almacen()
        self.cadena_llm = _PROMPT | self.llm | StrOutputParser()
        self.memoria    = ConversationBufferWindowMemory(
            k=6,
            human_prefix="Adolescente",
            ai_prefix="Serena",
        )
        logger.success("Serena lista")

    def responder(self, mensaje: str, sesion_id: str = "default") -> dict:
        logger.info(f"Mensaje: {mensaje[:80]}")

        if _tiene_crisis(mensaje):
            logger.warning("Crisis detectada")
            return {"respuesta": _random.choice(_RESPUESTAS_CRISIS), "fuentes": [], "tipo": "crisis"}

        if _es_fuera_tema(mensaje):
            logger.info("Fuera de tema bloqueado")
            return {"respuesta": _RESPUESTA_FUERA_TEMA, "fuentes": [], "tipo": "fuera_tema"}

        es_conf = _es_confirmacion(mensaje)

        if es_conf and getattr(self, "_ultimo_contexto", None):
            logger.info("Confirmacion — reutilizando contexto anterior")
            resultados = getattr(self, "_ultimos_resultados", [])
            contexto   = self._ultimo_contexto
        else:
            resultados = self.almacen.similarity_search_with_score(mensaje, k=config.resultados_top)
            if not resultados:
                return {"respuesta": _RESPUESTA_NO_ENCONTRADO, "fuentes": [], "tipo": "sin_info"}
            logger.info(f"Score top: {resultados[0][1]:.4f}")
            contexto = "\n\n---\n\n".join(
                (d.page_content[:800] + "..." if len(d.page_content) > 800 else d.page_content)
                for d, _ in resultados
            )
            self._ultimo_contexto    = contexto
            self._ultimos_resultados = resultados

        mensajes_previos = _db_cargar(sesion_id, ultimos=12)
        for m in mensajes_previos:
            self.memoria.save_context(
                {"input": m["usuario"]},
                {"output": m["serena"]},
            )

        historial = self.memoria.load_memory_variables({}).get("history", "")

        respuesta_raw = self.cadena_llm.invoke({
            "contexto":  contexto,
            "historial": historial,
            "pregunta":  mensaje,
        })

        respuesta = _limpiar_md(respuesta_raw)

        if "SIN_INFORMACION" in respuesta.upper() or len(respuesta.strip()) < 10:
            return {"respuesta": _RESPUESTA_NO_ENCONTRADO, "fuentes": [], "tipo": "sin_info"}

        self.memoria.save_context({"input": mensaje}, {"output": respuesta})

        _db_guardar(sesion_id, mensaje, respuesta)

        vistas, fuentes = set(), []
        for doc, _ in resultados:
            archivo = doc.metadata.get("archivo", "")
            nombre  = _nombre_legible(archivo)
            if nombre and nombre not in vistas:
                vistas.add(nombre)
                fuentes.append({
                    "titulo":    nombre,
                    "categoria": _nombre_categoria(doc.metadata.get("categoria", "")),
                    "archivo":   archivo,
                })

        return {"respuesta": respuesta, "fuentes": fuentes, "tipo": "normal"}

    def limpiar_historial(self, sesion_id: str = "default"):
        self.memoria.clear()
        _db_borrar(sesion_id)
        logger.info(f"Historial limpiado: {sesion_id}")