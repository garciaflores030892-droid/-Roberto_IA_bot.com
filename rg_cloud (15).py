# RG en la nube - como Meta AI / Gemini, siempre prendido
# Esta versión corre en un servidor (Render / Railway), no en tu teléfono.
# Así RG está afuera, prendido siempre, aunque apagues el teléfono o se cierre Termux.
#
# Lo que SÍ hace en la nube:
#   - Contesta en Telegram con texto y nota de voz masculina (es-MX-JorgeNeural)
#   - hora, fecha, Google, música, hola, gracias, quién eres
#   - Si le pones GEMINI_API_KEY, contesta preguntas con IA, como Gemini
#
# Lo que NO puede hacer en la nube (porque el servidor no es tu teléfono):
#   - prender la linterna de tu teléfono
#   - hacer llamadas desde tu teléfono
# Esas dos cosas solo funcionan con la versión de Termux en tu teléfono.
#
# Cómo subirlo a Render (gratis):
#  1) Sube estos archivos a un repo en GitHub: rg_cloud.py, requirements-cloud.txt, Procfile
#  2) En render.com, New > Background Worker, elige tu repo
#  3) Build Command: pip install -r requirements-cloud.txt
#     Start Command: python rg_cloud.py
#  4) En Environment, agrega:
#       TELEGRAM_BOT_TOKEN = tu token nuevo de @BotFather (nunca lo pegues en un chat)
#       GEMINI_API_KEY = tu llave nueva de Gemini (opcional, para que conteste como IA)
#  5) Deploy. Ya queda prendido 24/7.
#
# En Railway es parecido: New Project > Deploy from GitHub, agrega las mismas variables.

import os
import subprocess
import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

ZONA = ZoneInfo("America/Monterrey")
PROMPT_RG = "Soy RG, la versión virtual de mi compa. De Villas de San Francisco, Escobedo. Cotorreo y música. Hablo en español, directo y con buena onda, como si fuera Roberto. Contesto corto."

def hacer_voz(texto, archivo="rg_voz.mp3"):
    try:
        r = subprocess.run(
            ["edge-tts", "--voice", "es-MX-JorgeNeural",
             "--text", texto, "--write-media", archivo],
            capture_output=True, text=True, timeout=60)
        return os.path.exists(archivo) and os.path.getsize(archivo) > 0
    except Exception:
        return False

def responder_con_ia(pregunta):
    llave = os.environ.get("GEMINI_API_KEY", "")
    if not llave:
        return None
    try:
        import json, urllib.request
        datos = {
            "system_instruction": {"parts": [{"text": PROMPT_RG}]},
            "contents": [{"parts": [{"text": pregunta}]}],
        }
        req = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + llave,
            data=json.dumps(datos).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read().decode("utf-8"))
        return resp["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None

def responder(texto):
    import unicodedata, re
    t = "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                if unicodedata.category(c) != "Mn")
    if not t.strip():
        return "Dime qué ocupas, compa."
    if "hola" in t:
        return "Qué onda compa, soy RG. Dime qué ocupas."
    if "gracias" in t:
        return "De nada compa, aquí ando para lo que ocupes."
    if "lintern" in t:
        return "La linterna solo la puedo prender en tu teléfono, compa. Esa parte vive en Termux, no en la nube."
    if "llam" in t:
        return "Las llamadas solo las puedo hacer desde tu teléfono, compa. En la nube no tengo tu línea."
    if "hor" in t:
        ahora = datetime.datetime.now(ZONA).strftime("%I:%M %p")
        return f"Son las {ahora}, compa."
    if "fech" in t or "que dia" in t:
        hoy = datetime.datetime.now(ZONA).strftime("%A %d de %B de %Y")
        return f"Hoy es {hoy}."
    if "googl" in t:
        return "Abriendo Google: https://www.google.com"
    if "music" in t or "canci" in t:
        return "Poniendo música: https://music.youtube.com"
    if "quien eres" in t or "presentat" in t:
        return "Soy RG, la versión virtual de mi compa. De Villas de San Francisco, Escobedo. Cotorreo y música."
    if "adios" in t or "salir" in t:
        return "Órale, nos vemos, compa. Aquí ando cuando me ocupes."
    respuesta = responder_con_ia(texto)
    if respuesta:
        return respuesta
    return f"Te entendí '{texto}', pero eso todavía no lo tengo programado. Dime: hora, fecha, Google, música, o pregúntame algo."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Qué onda compa, soy RG, en la nube. Dime qué ocupas.\n"
        "Prueba: hora, fecha, música, o pregúntame algo."
    )

async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text or ""
    respuesta = responder(texto)
    if hacer_voz(respuesta):
        try:
            with open("rg_voz.mp3", "rb") as f:
                await update.message.reply_voice(voice=f)
        except Exception:
            pass
    await update.message.reply_text(respuesta)

async def voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Por ahora mándame texto, compa. La nota de voz en Telegram todavía no la transcribo."
    )

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("Falta TELEGRAM_BOT_TOKEN en las variables de entorno.")
        return
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))
    app.add_handler(MessageHandler(filters.VOICE, voz))
    print("RG en la nube está prendido.")
    app.run_polling()

if __name__ == "__main__":
    main()
