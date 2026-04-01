import json
import re
from pathlib import Path

import pdfplumber
from loguru import logger
from tqdm import tqdm

DIR_PDFS   = Path("backend/datos/pdfs")
DIR_SALIDA = Path("backend/datos")

_EJERCICIOS_CONOCIDOS = {
    "MIS EMOCIONES": (
        "Ejercicio para identificar emociones. "
        "Los sentimientos son sensaciones fisicas que sientes en tu cuerpo. "
        "Emociones basicas: feliz, triste, calmado, frustrado, enfadado, asustado. "
        "Para cada emocion se explora como se siente en el cuerpo. "
        "Sirve para reconocer y nombrar lo que sentimos."
    ),
    "MIS SENTIMIENTOS": (
        "Ejercicio de autoconocimiento emocional. "
        "Completar frases: me siento feliz cuando..., me siento triste cuando..., "
        "me siento enfadado cuando..., me siento tranquilo cuando..., "
        "me siento frustrado cuando..., me siento asustado cuando... "
        "Ayuda a identificar los detonantes de cada emocion."
    ),
    "SINTONIZA TUS CINCO SENTIDOS": (
        "Ejercicio de mindfulness 5-4-3-2-1 o 54321. "
        "Tecnica de conexion a tierra para el momento presente. "
        "Paso 1: nombra 5 cosas que ves. "
        "Paso 2: nombra 4 cosas que sientes con el tacto. "
        "Paso 3: nombra 3 cosas que escuchas. "
        "Paso 4: nombra 2 cosas que puedes oler. "
        "Paso 5: nombra 1 cosa que puedes saborear. "
        "Se usa para calmar la ansiedad y traer la mente al presente."
    ),
    "MINDFULNESS ACTIVIDAD": (
        "Actividad de atencion plena o mindfulness. "
        "Ejercicio de respiracion consciente: siéntate derecho, "
        "cierra los ojos, respira durante 5 minutos. "
        "Inhala 3 segundos, manten 4 segundos, exhala 5 segundos. "
        "Al inhalar piensas en alegria y paz, al exhalar sueltas tristeza y cansancio. "
        "Tambien incluye atencion plena en actividades cotidianas como jardineria. "
        "Ayuda a regular emociones y calmar el sistema nervioso."
    ),
    "REFLEXION DIARIA": (
        "Ejercicio de reflexion diaria para el bienestar emocional. "
        "Registra: tres momentos del dia, algo que te inspiro, algo que te sorprendio, "
        "una persona que te hizo reir, una cosa que lograste. "
        "Segunda version: cosas por las que estoy agradecido hoy, "
        "lo mas dificil que conseguiste, colorea tu estado de animo. "
        "Emociones posibles: feliz, asustado, confundido, cansado, triste, decepcionado."
    ),
    "CHECK-IN DIARIO": (
        "Registro diario de emociones. Como me siento hoy. "
        "Opciones: feliz, triste, cansado, emocionado, enfadado, frustrado, "
        "esperanzado, divertido, nervioso, aburrido, concentrado. "
        "Tambien incluye razon de mi calificacion y objetivos para hoy. "
        "Algo que espero conseguir hoy. Util para el autoconocimiento diario."
    ),
    "EXPLORANDO MI ENFADO": (
        "Ejercicio para trabajar el enojo y la regulacion emocional. "
        "Preguntas: que te hizo sentir enfadado, que pensamientos vinieron a tu cabeza, "
        "como respondiste, que puedes hacer la proxima vez que ocurra lo mismo. "
        "Sirve para reflexionar sobre el enojo y desarrollar estrategias de regulacion."
    ),
    "CUANDO ME ENFADO": (
        "Ejercicio para manejar el enojo. "
        "Escribe 5 cosas que te hacen sentir enfadado. "
        "Escribe 5 acciones que te ayudan a tranquilizarte. "
        "Identifica detonantes del enojo y estrategias de calma."
    ),
    "DEJANDO IR MIS PENSAMIENTOS": (
        "Ejercicio para manejar pensamientos ansiosos. "
        "Escribe los pensamientos que te preocupan o que necesitas soltar. "
        "Luego habla de ellos con alguien de confianza. "
        "Ayuda a externalizar los pensamientos negativos y pedir apoyo."
    ),
    "MIS PREOCUPACIONES": (
        "Ejercicio para trabajar la ansiedad y las preocupaciones. "
        "Anota todas las preocupaciones que siguen surgiendo. "
        "Sirve para sacar los pensamientos de la cabeza y verlos con perspectiva."
    ),
    "LIBERA TUS PREOCUPACIONES": (
        "Ejercicio de visualizacion para soltar preocupaciones. "
        "Imagina un arbol que absorbe tus preocupaciones cuando lo abrazas. "
        "Dibuja o escribe tus preocupaciones. "
        "Luego habla de ellas con alguien de confianza."
    ),
    "ME SIENTO TRISTE": (
        "Ejercicio para explorar la tristeza. "
        "Dibuja como se ve tu cara cuando estas triste. "
        "Escribe 4 cosas que te hacen sentir triste. "
        "Escribe 4 formas en que expresas la tristeza. "
        "La tristeza tiene diferentes caras para cada persona."
    ),
    "SENTIR ALEGRIA": (
        "Ejercicio para conectar con la alegria y el bienestar. "
        "Escribe 5 cosas que te hacen sentir feliz. "
        "Describe tu lugar feliz: que ves, oyes, sientes y hueles ahi."
    ),
    "SEIS SOMBREROS": (
        "Tecnica de los seis sombreros para pensar y tomar decisiones. "
        "Sombrero amarillo: positividad y beneficios. "
        "Sombrero verde: creatividad e ideas nuevas. "
        "Sombrero rojo: emociones e intuicion. "
        "Sombrero blanco: datos y hechos objetivos. "
        "Sombrero negro: riesgos y peores escenarios. "
        "Sombrero azul: control del proceso y perspectiva general."
    ),
    "TERMOMETRO": (
        "Termometro de emociones para identificar estados de animo. "
        "Emociones: feliz, triste, dolido, timido, enamorado, divertido, asustado, cansado. "
        "Colorea segun el nivel de intensidad de cada emocion. "
        "Sirve para aprender a medir y comunicar la intensidad de lo que sientes."
    ),
    "MI REGISTRO": (
        "Registro semanal de bienestar emocional. "
        "Como te sientes esta semana (escala visual). "
        "Cual fue la parte mas frustrante de tu semana. "
        "Cual fue la parte mas agradable de tu semana. "
        "Algo mas que quieras compartir. Sirve para el seguimiento emocional."
    ),
    "HOY ME SIENTO": (
        "Ejercicio de check-in emocional del dia. "
        "Colorea los frascos segun como te sientas hoy. "
        "Emociones: feliz, ansioso, divertido, sorprendido, enfadado. "
        "Forma rapida de identificar y nombrar el estado emocional actual."
    ),
    "QUE ES EL MINDFULNESS": (
        "Definicion y beneficios del mindfulness o atencion plena. "
        "El mindfulness es una practica de centrar la conciencia en el momento presente "
        "sin distracciones ni juicios. "
        "Beneficios: mejora la actividad cerebral y creatividad, "
        "reduce el estres y las preocupaciones, mejora el humor y la autoestima, "
        "incrementa conductas positivas, mejora la toma de decisiones, "
        "mejora la calidad del sueno, ayuda en las relaciones sociales. "
        "El mindfulness es un superpoder."
    ),
    "MIS PENSAMIENTOS": (
        "Ejercicio de registro de pensamientos para la regulacion emocional. "
        "Escribe o dibuja cualquier pensamiento que siga surgiendo. "
        "Ayuda a externalizar y tomar conciencia de los pensamientos recurrentes."
    ),
}


def _limpiar(texto: str) -> str:
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    lineas = [l.strip() for l in texto.splitlines() if len(l.strip()) > 3]
    return '\n'.join(lineas).strip()


def _inferir_categoria(nombre: str, texto: str) -> str:
    n = nombre.lower()
    t = texto.lower()
    if "mindfulness" in n or "mindfulness" in t or "atencion plena" in t:
        return "mindfulness"
    if "regulacion" in n or "regulacion" in t or "regular" in t:
        return "regulacion_emocional"
    if "rebelde" in n or "inteligencia emocional" in t:
        return "inteligencia_emocional"
    if "emocion" in t or "sentimiento" in t:
        return "emociones"
    if "suicidio" in t or "crisis" in t or "prevencion" in t:
        return "prevencion_suicidio"
    return "salud_mental"


def _buscar_enriquecimiento(titulo_pagina: str) -> str:
    titulo_norm = re.sub(r'\s+', ' ', titulo_pagina.upper().strip())
    for clave, descripcion in _EJERCICIOS_CONOCIDOS.items():
        if clave in titulo_norm or titulo_norm in clave:
            return descripcion
    return ""


def extraer_pdf(ruta: Path) -> list[dict]:
    paginas = []
    try:
        with pdfplumber.open(ruta) as pdf:
            for i, pagina in enumerate(pdf.pages, 1):
                texto = pagina.extract_text()
                if not texto:
                    continue
                texto = _limpiar(texto)
                if len(texto) < 20:
                    continue

                lineas = texto.splitlines()
                titulo = lineas[0].strip() if lineas else ""

                enriquecimiento = _buscar_enriquecimiento(titulo)
                if enriquecimiento:
                    texto_final = f"{texto}\n\n{enriquecimiento}"
                else:
                    texto_final = texto

                if len(texto_final) > 30:
                    paginas.append({"pagina": i, "texto": texto_final, "titulo_pag": titulo})

    except Exception as e:
        logger.error(f"Error en {ruta.name}: {e}")
    return paginas


def procesar_pdfs():
    archivos = list(DIR_PDFS.glob("**/*.pdf"))
    if not archivos:
        logger.warning(f"No hay PDFs en {DIR_PDFS}")
        return []

    logger.info(f"Procesando {len(archivos)} PDFs...")
    documentos = []

    for ruta in tqdm(archivos, desc="Extrayendo"):
        logger.info(f"  -> {ruta.name}")
        paginas = extraer_pdf(ruta)

        for p in paginas:
            documentos.append({
                "titulo":    f"{ruta.stem} — {p['titulo_pag']}",
                "archivo":   ruta.name,
                "fuente":    "pdf_material",
                "categoria": _inferir_categoria(ruta.name, p["texto"]),
                "pagina":    p["pagina"],
                "texto":     p["texto"],
            })

        logger.info(f"    {len(paginas)} paginas extraidas de {ruta.name}")

    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    salida = DIR_SALIDA / "materiales.json"
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(documentos, f, ensure_ascii=False, indent=2)

    total = sum(len(d["texto"]) for d in documentos)
    logger.success(f"{len(documentos)} paginas -> {salida} ({total:,} chars)")
    return documentos


if __name__ == "__main__":
    procesar_pdfs()