import tkinter as tk
import threading
import json
import urllib.request
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

URL_BASE  = "http://127.0.0.1:8001"
SESION_ID = "sesion_app"

CORAL      = "#FF6B6B"
CORAL_OSC  = "#E05555"
MENTA      = "#4ECDC4"
MENTA_OSC  = "#38B2AA"
LAVANDA    = "#A78BFA"
AMARILLO   = "#FFD93D"
AZUL_SUAVE = "#74B9FF"
ROSA       = "#FD79A8"

FONDO_1    = "#667EEA"
FONDO_2    = "#764BA2"

BLANCO     = "#FFFFFF"
BLANCO_90  = "#F0F4FF"
TEXTO_OSC  = "#2D3748"
TEXTO_MED  = "#4A5568"
TEXTO_CLAR = "#718096"

BURBUJA_USR_1 = "#FF6B6B"
BURBUJA_USR_2 = "#FF8E53"
BURBUJA_BOT   = "#FFFFFF"

CRISIS_BG  = "#FFF0F0"
CRISIS_TX  = "#C53030"


def _post(endpoint, datos):
    body = json.dumps(datos).encode("utf-8")
    req  = urllib.request.Request(
        f"{URL_BASE}{endpoint}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def _delete(endpoint):
    try:
        req = urllib.request.Request(f"{URL_BASE}{endpoint}", method="DELETE")
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def _salud():
    try:
        with urllib.request.urlopen(f"{URL_BASE}/salud", timeout=4) as r:
            return r.status == 200
    except Exception:
        return False


def _circulo(tam, color1, color2=None, letra=None, sombra=None):
    escala = 3
    s = tam * escala
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    if sombra:
        sombra_img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        ds = ImageDraw.Draw(sombra_img)
        ds.ellipse([escala*2, escala*2, s-1, s-1], fill=sombra)
        sombra_img = sombra_img.filter(ImageFilter.GaussianBlur(escala * 2))
        img = Image.alpha_composite(img, sombra_img)
        d = ImageDraw.Draw(img)

    if color2:
        for i in range(s):
            t   = i / s
            r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
            rc  = int(r1 + (r2 - r1) * t)
            gc  = int(g1 + (g2 - g1) * t)
            bc  = int(b1 + (b2 - b1) * t)
            d.line([(0, i), (s, i)], fill=(rc, gc, bc, 255))
        mask = Image.new("L", (s, s), 0)
        dm   = ImageDraw.Draw(mask)
        dm.ellipse([0, 0, s - 1, s - 1], fill=255)
        img.putalpha(mask)
    else:
        d.ellipse([0, 0, s - 1, s - 1], fill=color1)

    if letra:
        try:
            fnt = ImageFont.truetype("arial.ttf", int(s * 0.42))
        except Exception:
            fnt = ImageFont.load_default()
        bbox = d.textbbox((0, 0), letra, font=fnt)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text((s // 2 - tw // 2, s // 2 - th // 2 - 1), letra, fill="white", font=fnt)

    img = img.resize((tam, tam), Image.LANCZOS)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(tam, tam))


def _fondo_degradado(ancho, alto, c1, c2):
    img = Image.new("RGB", (ancho, alto))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    for y in range(alto):
        t  = y / alto
        rc = int(r1 + (r2 - r1) * t)
        gc = int(g1 + (g2 - g1) * t)
        bc = int(b1 + (b2 - b1) * t)
        for x in range(ancho):
            img.putpixel((x, y), (rc, gc, bc))
    return img


def _burbuja_usuario_img(texto, ancho_max=260):
    try:
        fnt = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        fnt = ImageFont.load_default()

    pad_x, pad_y = 16, 12
    palabras = texto.split()
    lineas, linea_actual = [], ""
    for p in palabras:
        prueba = (linea_actual + " " + p).strip()
        bb = ImageDraw.Draw(Image.new("RGB", (1,1))).textbbox((0,0), prueba, font=fnt)
        if bb[2] - bb[0] > ancho_max - pad_x * 2:
            if linea_actual:
                lineas.append(linea_actual)
            linea_actual = p
        else:
            linea_actual = prueba
    if linea_actual:
        lineas.append(linea_actual)

    bb_muestra = ImageDraw.Draw(Image.new("RGB",(1,1))).textbbox((0,0),"Ag",font=fnt)
    alt_linea  = bb_muestra[3] - bb_muestra[1] + 4
    ancho_real = max(
        (ImageDraw.Draw(Image.new("RGB",(1,1))).textbbox((0,0),l,font=fnt)[2] for l in lineas),
        default=40
    ) + pad_x * 2
    alto_real  = len(lineas) * alt_linea + pad_y * 2

    escala = 2
    w, h   = ancho_real * escala, alto_real * escala
    img    = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d      = ImageDraw.Draw(img)

    r1, g1, b1 = int(BURBUJA_USR_1[1:3],16), int(BURBUJA_USR_1[3:5],16), int(BURBUJA_USR_1[5:7],16)
    r2, g2, b2 = int(BURBUJA_USR_2[1:3],16), int(BURBUJA_USR_2[3:5],16), int(BURBUJA_USR_2[5:7],16)
    for i in range(w):
        t  = i / w
        rc = int(r1 + (r2 - r1) * t)
        gc = int(g1 + (g2 - g1) * t)
        bc = int(b1 + (b2 - b1) * t)
        d.line([(i, 0), (i, h)], fill=(rc, gc, bc, 255))

    radio = 20 * escala
    mask  = Image.new("L", (w, h), 0)
    dm    = ImageDraw.Draw(mask)
    dm.rounded_rectangle([0, 0, w-1, h-1], radius=radio, fill=255)
    img.putalpha(mask)

    try:
        fnt_e = ImageFont.truetype("arial.ttf", 14 * escala)
    except Exception:
        fnt_e = ImageFont.load_default()
    for i, linea in enumerate(lineas):
        y = (pad_y + i * alt_linea) * escala
        d.text((pad_x * escala, y), linea, fill="white", font=fnt_e)

    img = img.resize((ancho_real, alto_real), Image.LANCZOS)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(ancho_real, alto_real))


class AppSerena(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Serena")
        self.geometry("420x820")
        self.minsize(360, 600)
        self.configure(fg_color=BLANCO_90)

        self._cargando   = False
        self._bienvenida = None
        self._puntos_var = tk.StringVar(value="pensando...")
        self._tick       = 0

        self._av_s_hdr  = _circulo(44, CORAL, LAVANDA, "S", sombra="#FF6B6B55")
        self._av_s_chat = _circulo(32, CORAL, ROSA, "S")
        self._av_s_lg   = _circulo(70, CORAL, LAVANDA, "S", sombra="#FF6B6B44")
        self._av_tu     = _circulo(32, MENTA, AZUL_SUAVE, "Tu")

        self._ui()
        self.after(500, self._chequear_conexion)
        self.after(200, lambda: self._campo.focus_set())

    def _ui(self):
        self._header()
        self._chat()
        self._mostrar_bienvenida()
        self._entrada()

    def _header(self):
        h = tk.Frame(self, bg=BLANCO, height=68)
        h.pack(fill="x")
        h.pack_propagate(False)

        canvas = tk.Canvas(h, height=68, bg=BLANCO, highlightthickness=0)
        canvas.pack(fill="x")

        canvas.bind("<Configure>", lambda e: self._dibujar_header(canvas, e.width))
        self._header_canvas = canvas

        izq = ctk.CTkFrame(h, fg_color="transparent", bg_color=BLANCO)
        izq.place(x=14, rely=0.5, anchor="w")

        ctk.CTkLabel(izq, image=self._av_s_hdr, text="").pack(side="left")

        info = ctk.CTkFrame(izq, fg_color="transparent", bg_color=BLANCO)
        info.pack(side="left", padx=(10, 0))

        ctk.CTkLabel(
            info, text="Serena",
            font=ctk.CTkFont(family="Helvetica", size=17, weight="bold"),
            text_color=TEXTO_OSC, fg_color="transparent",
        ).pack(anchor="w")

        self._f_estado = ctk.CTkFrame(info, fg_color="transparent", bg_color=BLANCO)
        self._f_estado.pack(anchor="w")

        self._dot_hdr = ctk.CTkLabel(
            self._f_estado, text="●",
            font=ctk.CTkFont(size=8), text_color="#CBD5E0",
            fg_color="transparent",
        )
        self._dot_hdr.pack(side="left")

        self._lbl_estado = ctk.CTkLabel(
            self._f_estado, text=" verificando...",
            font=ctk.CTkFont(family="Helvetica", size=10),
            text_color=TEXTO_CLAR, fg_color="transparent",
        )
        self._lbl_estado.pack(side="left")

        self._btn_nuevo = ctk.CTkButton(
            h, text="Nueva",
            font=ctk.CTkFont(family="Helvetica", size=11, weight="bold"),
            fg_color=BLANCO_90, text_color=TEXTO_MED,
            hover_color="#E2E8F0", corner_radius=20,
            border_width=1, border_color="#E2E8F0",
            width=72, height=30,
            command=self._confirmar_limpiar,
        )
        self._btn_nuevo.place(relx=1.0, rely=0.5, x=-14, anchor="e")

        sep = tk.Frame(self, height=1, bg="#EDF2F7")
        sep.pack(fill="x")

    def _dibujar_header(self, canvas, ancho):
        canvas.delete("grad")
        for i in range(4):
            x = ancho - 60 + i * 8
            canvas.create_oval(x, 10, x+30, 40, fill="#F0E6FF", outline="", tags="grad")

    def _chat(self):
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BLANCO_90,
            corner_radius=0,
            scrollbar_button_color="#E2E8F0",
            scrollbar_button_hover_color=MENTA,
        )
        self._scroll.pack(fill="both", expand=True)
        self._scroll.bind_all("<MouseWheel>", self._on_wheel)

    def _on_wheel(self, e):
        self._scroll._parent_canvas.yview_scroll(int(-1*(e.delta/120)), "units")

    def _entrada(self):
        base = ctk.CTkFrame(self, fg_color=BLANCO, corner_radius=0, height=86)
        base.pack(fill="x")
        base.pack_propagate(False)
        self._entrada_frame = base

        sep = tk.Frame(base, height=1, bg="#EDF2F7")
        sep.pack(fill="x")

        row = ctk.CTkFrame(base, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=14, pady=10)

        self._campo = ctk.CTkTextbox(
            row,
            height=46,
            font=ctk.CTkFont(family="Helvetica", size=14),
            fg_color=BLANCO_90,
            border_width=2,
            border_color="#E2E8F0",
            corner_radius=22,
            text_color=TEXTO_OSC,
            wrap="word",
        )
        self._campo.pack(side="left", fill="x", expand=True)
        self._campo.bind("<Return>", self._on_enter)
        self._campo.bind("<Shift-Return>", self._shift_enter)

        self._btn = ctk.CTkButton(
            row,
            text="",
            image=_circulo(46, CORAL, ROSA),
            fg_color=BLANCO,
            hover_color=BLANCO_90,
            width=46, height=46,
            corner_radius=23,
            border_width=0,
            command=self._enviar,
        )
        self._btn.pack(side="left", padx=(8, 0))

        flecha = tk.Label(
            row, text="➤", bg=BLANCO,
            font=("Helvetica", 16),
            fg=BLANCO,
        )

    def _on_key(self, e):
        tiene = len(self._campo.get("1.0", "end").strip()) > 0
        color = "#EDF2F7" if not tiene else "#E2E8F0"
        pass

    def _mostrar_bienvenida(self):
        self._bienvenida = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._bienvenida.pack(fill="x", padx=16, pady=12)

        top = ctk.CTkFrame(
            self._bienvenida,
            fg_color=BLANCO,
            corner_radius=28,
        )
        top.pack(fill="x", pady=(0, 10))

        inner = ctk.CTkFrame(top, fg_color="transparent")
        inner.pack(padx=20, pady=20)

        ctk.CTkLabel(inner, image=self._av_s_lg, text="").pack(pady=(0, 10))

        ctk.CTkLabel(
            inner, text="Hola, soy Serena",
            font=ctk.CTkFont(family="Helvetica", size=22, weight="bold"),
            text_color=TEXTO_OSC,
        ).pack()

        ctk.CTkLabel(
            inner,
            text="Tu espacio seguro para hablar\nde como te sientes.",
            font=ctk.CTkFont(family="Helvetica", size=13),
            text_color=TEXTO_MED,
            justify="center",
        ).pack(pady=(6, 0))

        aviso = ctk.CTkFrame(
            self._bienvenida,
            fg_color="#FFFBEB",
            corner_radius=16,
            border_width=1,
            border_color="#FDE68A",
        )
        aviso.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            aviso,
            text="Soy un apoyo educativo, no un profesional.\nEn crisis llama al 800 290 0024 (SAPTEL, 24h).",
            font=ctk.CTkFont(family="Helvetica", size=11),
            text_color="#92400E",
            justify="center",
        ).pack(padx=14, pady=10)

        ctk.CTkLabel(
            self._bienvenida, text="Por donde quieres empezar?",
            font=ctk.CTkFont(family="Helvetica", size=12, weight="bold"),
            text_color=TEXTO_MED,
        ).pack(pady=(0, 8))

        sugs = [
            ("Ansiedad y nervios",       CORAL,   ROSA),
            ("Como calmarme",            MENTA,   AZUL_SUAVE),
            ("Identificar mis emociones",LAVANDA, "#C4B5FD"),
            ("Que es mindfulness",       AMARILLO,"#FDE68A"),
            ("Tecnica 5-4-3-2-1",        AZUL_SUAVE, MENTA),
            ("Emocion vs sentimiento",   ROSA,    CORAL),
        ]

        for texto, c1, c2 in sugs:
            self._chip(self._bienvenida, texto, c1, c2)

    def _chip(self, padre, texto, c1, c2):
        r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
        alfa_hex   = f"#{r1:02x}{g1:02x}{b1:02x}22"

        btn = ctk.CTkButton(
            padre, text=texto,
            font=ctk.CTkFont(family="Helvetica", size=12, weight="bold"),
            fg_color=BLANCO,
            text_color=TEXTO_OSC,
            hover_color=BLANCO_90,
            corner_radius=22,
            border_width=2,
            border_color="#E2E8F0",
            height=42,
            anchor="w",
            command=lambda t=texto: self._tap(t),
        )
        btn.pack(fill="x", padx=2, pady=3)

    def _on_enter(self, e):
        self._enviar()
        return "break"

    def _shift_enter(self, e):
        return None

    def _tap(self, texto):
        if self._bienvenida and self._bienvenida.winfo_exists():
            self._bienvenida.destroy()
            self._bienvenida = None
        self._campo.delete("1.0", "end")
        self._campo.insert("1.0", texto)
        self._enviar()

    def _enviar(self):
        if self._cargando:
            return
        texto = self._campo.get("1.0", "end").strip()
        if not texto:
            return

        if self._bienvenida and self._bienvenida.winfo_exists():
            self._bienvenida.destroy()
            self._bienvenida = None

        self._campo.delete("1.0", "end")
        self._burbuja_usuario(texto)
        self._cargando = True
        self._btn.configure(state="disabled")

        ind = self._indicador()

        def hilo():
            try:
                r       = _post("/chat", {"mensaje": texto, "sesion_id": SESION_ID})
                resp    = r.get("respuesta", "")
                tipo    = r.get("tipo", "normal")
                fuentes = r.get("fuentes", [])
            except Exception:
                resp    = "No pude conectarme. Verifica que el servidor este activo."
                tipo    = "error"
                fuentes = []
            self.after(0, lambda: self._recibir(resp, tipo, fuentes, ind))

        threading.Thread(target=hilo, daemon=True).start()

    def _recibir(self, texto, tipo, fuentes, ind):
        if ind.winfo_exists():
            ind.destroy()
        self._burbuja_bot(texto, tipo, fuentes)
        if tipo == "crisis":
            self._banner_crisis()
        self._cargando = False
        self._btn.configure(state="normal")
        self._campo.focus_set()
        self.after(120, lambda: self._scroll._parent_canvas.yview_moveto(1.0))

    def _banner_crisis(self):
        if hasattr(self, "_banner_frame") and self._banner_frame.winfo_exists():
            return

        self._banner_frame = tk.Frame(self, bg="#1A1A2E", pady=0)
        self._banner_frame.pack(fill="x", side="bottom", before=self._entrada_frame)

        contenido = tk.Frame(self._banner_frame, bg="#1A1A2E")
        contenido.pack(fill="x", padx=16, pady=12)

        icono = tk.Label(
            contenido, text="🕊",
            bg="#1A1A2E", fg="white",
            font=("Helvetica", 22),
        )
        icono.pack(side="left", anchor="n", padx=(0, 12))

        texto_frame = tk.Frame(contenido, bg="#1A1A2E")
        texto_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            texto_frame,
            text="Si tu o alguien que conoces esta en un momento dificil,",
            bg="#1A1A2E", fg="white",
            font=("Helvetica", 11, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            texto_frame,
            text="hay apoyo gratuito disponible ahora mismo.",
            bg="#1A1A2E", fg="#CBD5E0",
            font=("Helvetica", 11),
            anchor="w",
        ).pack(fill="x")

        botones = tk.Frame(texto_frame, bg="#1A1A2E")
        botones.pack(fill="x", pady=(8, 0))

        btn_llamar = tk.Button(
            botones,
            text="Llamar ahora  800 290 0024",
            bg="#FF6B6B", fg="white",
            font=("Helvetica", 11, "bold"),
            bd=0, padx=14, pady=7,
            cursor="hand2",
            activebackground="#E05555",
            activeforeground="white",
        )
        btn_llamar.pack(side="left", padx=(0, 8))

        btn_chat = tk.Button(
            botones,
            text="Hablar con mi especialista",
            bg="#2D3748", fg="white",
            font=("Helvetica", 11),
            bd=0, padx=14, pady=7,
            cursor="hand2",
            activebackground="#4A5568",
            activeforeground="white",
        )
        btn_chat.pack(side="left")

        cerrar = tk.Button(
            contenido,
            text="✕",
            bg="#1A1A2E", fg="#718096",
            font=("Helvetica", 13),
            bd=0, cursor="hand2",
            activebackground="#1A1A2E",
            activeforeground="white",
            command=self._cerrar_banner,
        )
        cerrar.pack(side="right", anchor="n", padx=(8, 0))

    def _burbuja_usuario(self, texto):
        fila = ctk.CTkFrame(self._scroll, fg_color="transparent")
        fila.pack(fill="x", padx=12, pady=4)

        contenido = ctk.CTkFrame(fila, fg_color="transparent")
        contenido.pack(side="right")

        ctk.CTkLabel(contenido, image=self._av_tu, text="").pack(
            side="right", anchor="s", padx=(6, 0), pady=(0, 2)
        )

        try:
            img_burbuja = _burbuja_usuario_img(texto, ancho_max=240)
            lbl = ctk.CTkLabel(contenido, image=img_burbuja, text="")
            lbl.image_ref = img_burbuja
            lbl.pack(side="right", padx=(0, 4))
        except Exception:
            bur = ctk.CTkFrame(contenido, fg_color=CORAL, corner_radius=18)
            bur.pack(side="right", padx=(0, 4))
            ctk.CTkLabel(
                bur, text=texto,
                font=ctk.CTkFont(family="Helvetica", size=13),
                text_color=BLANCO, wraplength=240,
            ).pack(padx=14, pady=10)

        self.after(80, lambda: self._scroll._parent_canvas.yview_moveto(1.0))

    def _burbuja_bot(self, texto, tipo="normal", fuentes=None):
        fila = ctk.CTkFrame(self._scroll, fg_color="transparent")
        fila.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(fila, image=self._av_s_chat, text="").pack(
            side="left", anchor="s", padx=(0, 8), pady=(0, 2)
        )

        col = ctk.CTkFrame(fila, fg_color="transparent")
        col.pack(side="left", fill="x", expand=True, padx=(0, 48))

        if tipo == "crisis":
            bg    = "#FFF5F5"
            fg    = "#7B2D2D"
            borde = "#FEB2B2"
        else:
            bg    = BLANCO
            fg    = TEXTO_OSC
            borde = "#E8EDF5"

        bur = ctk.CTkFrame(
            col, fg_color=bg, corner_radius=20,
            border_width=2 if tipo == "crisis" else 1,
            border_color=borde,
        )
        bur.pack(anchor="w", fill="x")

        if tipo == "crisis":
            aviso_top = ctk.CTkFrame(bur, fg_color="#FFEBEB", corner_radius=0)
            aviso_top.pack(fill="x")
            ctk.CTkLabel(
                aviso_top,
                text="Esto es importante",
                font=ctk.CTkFont(family="Helvetica", size=11, weight="bold"),
                text_color="#C53030",
            ).pack(padx=14, pady=(8, 4))
            sep_c = ctk.CTkFrame(bur, fg_color="#FEB2B2", height=1, corner_radius=0)
            sep_c.pack(fill="x")

        ctk.CTkLabel(
            bur, text=texto,
            font=ctk.CTkFont(family="Helvetica", size=13),
            text_color=fg,
            wraplength=240,
            justify="left", anchor="w",
        ).pack(padx=16, pady=12)

        if fuentes:
            sep = ctk.CTkFrame(bur, fg_color="#F1F5F9", height=1, corner_radius=0)
            sep.pack(fill="x", padx=12)

            pie = ctk.CTkFrame(bur, fg_color="transparent")
            pie.pack(fill="x", padx=12, pady=(6, 10))

            ctk.CTkLabel(
                pie, text="Del material del programa:",
                font=ctk.CTkFont(family="Helvetica", size=9, weight="bold"),
                text_color=MENTA_OSC,
            ).pack(anchor="w")

            for f in fuentes:
                nombre = f.get("titulo", "")
                cat    = f.get("categoria", "")
                if nombre:
                    etiqueta = ctk.CTkFrame(
                        pie,
                        fg_color=BLANCO_90,
                        corner_radius=8,
                        border_width=1,
                        border_color="#E2E8F0",
                    )
                    etiqueta.pack(anchor="w", pady=2)
                    ctk.CTkLabel(
                        etiqueta,
                        text=f"  {nombre}  {('· ' + cat) if cat else ''}  ",
                        font=ctk.CTkFont(family="Helvetica", size=10),
                        text_color=TEXTO_CLAR,
                    ).pack(padx=4, pady=2)

        self.after(80, lambda: self._scroll._parent_canvas.yview_moveto(1.0))

    def _indicador(self):
        fila = ctk.CTkFrame(self._scroll, fg_color="transparent")
        fila.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(fila, image=self._av_s_chat, text="").pack(
            side="left", anchor="s", padx=(0, 8), pady=(0, 2)
        )

        bur = ctk.CTkFrame(
            fila, fg_color=BLANCO, corner_radius=20,
            border_width=1, border_color="#E8EDF5",
        )
        bur.pack(side="left")

        lbl = ctk.CTkLabel(
            bur, textvariable=self._puntos_var,
            font=ctk.CTkFont(family="Helvetica", size=13, slant="italic"),
            text_color=TEXTO_CLAR,
        )
        lbl.pack(padx=16, pady=10)

        self._tick = 0
        self._animar()
        self.after(80, lambda: self._scroll._parent_canvas.yview_moveto(1.0))
        return fila

    def _animar(self):
        if not self._cargando:
            return
        frames = ["pensando   ", "pensando.  ", "pensando.. ", "pensando..."]
        try:
            self._puntos_var.set(frames[self._tick % 4])
        except Exception:
            return
        self._tick += 1
        self.after(380, self._animar)

    def _chequear_conexion(self):
        def hilo():
            ok = _salud()
            self.after(0, lambda: self._set_estado(ok))
        threading.Thread(target=hilo, daemon=True).start()
        self.after(12000, self._chequear_conexion)

    def _set_estado(self, ok):
        if ok:
            self._dot_hdr.configure(text_color=MENTA)
            self._lbl_estado.configure(text=" Lista para ayudarte", text_color=MENTA_OSC)
        else:
            self._dot_hdr.configure(text_color=CORAL)
            self._lbl_estado.configure(text=" Sin conexion", text_color=CORAL_OSC)

    def _confirmar_limpiar(self):
        d = ctk.CTkToplevel(self)
        d.title("")
        d.geometry("300x170")
        d.resizable(False, False)
        d.configure(fg_color=BLANCO)
        d.grab_set()
        d.lift()

        ctk.CTkLabel(
            d, text="Nueva conversacion",
            font=ctk.CTkFont(family="Helvetica", size=15, weight="bold"),
            text_color=TEXTO_OSC,
        ).pack(pady=(22, 6))

        ctk.CTkLabel(
            d, text="Se borrara el historial actual.",
            font=ctk.CTkFont(family="Helvetica", size=12),
            text_color=TEXTO_CLAR,
        ).pack()

        row = ctk.CTkFrame(d, fg_color="transparent")
        row.pack(pady=20)

        ctk.CTkButton(
            row, text="Cancelar",
            font=ctk.CTkFont(size=12),
            fg_color=BLANCO_90, text_color=TEXTO_MED,
            hover_color="#E2E8F0",
            border_width=1, border_color="#E2E8F0",
            corner_radius=22, width=110, height=38,
            command=d.destroy,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            row, text="Si, limpiar",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=CORAL, hover_color=CORAL_OSC,
            text_color=BLANCO,
            corner_radius=22, width=110, height=38,
            command=lambda: self._limpiar(d),
        ).pack(side="left", padx=6)

    def _cerrar_banner(self):
        if hasattr(self, "_banner_frame") and self._banner_frame.winfo_exists():
            self._banner_frame.destroy()

    def _limpiar(self, dialogo):
        dialogo.destroy()
        self._cerrar_banner()

        self._cargando = False
        self._btn.configure(state="normal", fg_color=CORAL, text="➤")

        for w in self._scroll.winfo_children():
            w.destroy()

        threading.Thread(
            target=lambda: _delete(f"/chat/historial?sesion_id={SESION_ID}"),
            daemon=True,
        ).start()

        self._bienvenida = None
        self._mostrar_bienvenida()

        self._campo.delete("1.0", "end")
        self.after(100, lambda: self._campo.focus_set())


if __name__ == "__main__":
    app = AppSerena()
    app.mainloop()