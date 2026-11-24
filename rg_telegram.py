# RG en Telegram - @RG_IA_BOT
# Corre RG en tu bot de Telegram, usando los mismos comandos que en Termux.
# El bot corre en tu teléfono, en Termux, así que la linterna y las llamadas
# siguen funcionando en tu teléfono, aunque le escribas desde Telegram.
#
# 1) Saca el token en Telegram, con @BotFather: /newbot o /mybots > tu bot > API Token
#    NUNCA pegues ese token en un chat, ni aquí con Nina.
# 2) En Termux, ponlo así (con tu token real, no este ejemplo):
#      export TELEGRAM_BOT_TOKEN="tu-token-aqui"
# 3) Instala la librería:
#      pip install python-telegram-bot
# 4) Baja este archivo y asistente_rg.py a la misma carpeta en Termux.
# 5) Corre:
#      python rg_telegram.py
#    Deja Termux abierto, si lo cierras el bot se apaga.
# 6) En Telegram, abre @RG_IA_BOT y escribe: hola, hora, fecha, enciende la linterna, música, llama al número
#
# Nota de voz: en Telegram, RG contesta con texto Y con nota de voz,
# con voz masculina en español de México (es-MX-JorgeNeural, con edge-tts).
# Instala: pip install edge-tts
# Si no hay internet para la voz, contesta solo con texto.

import os
import re
import subprocess
import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Reusa la lógica de RG
try:
    from asistente_rg import normalizar, cargar_prompt
except Exception:
    normalizar = lambda t: t.lower()
    cargar_prompt = lambda: "Soy RG, la versión virtual de mi compa."

PROMPT_RG = cargar_prompt()

def responder(texto):
    import re as _re
    numeros = _re.findall(r"\+?\d[\d\s\-]{6,}\d", texto)
    numero = _re.sub(r"[\s\-]", "", numeros[0]) if numeros else ""
    t = normalizar(texto)
    if not t:
        return "Dime qué ocupas, compa."
    if "llam" in t or "marca" in t:
        if numero:
            try:
                subprocess.run(["termux-telephony-call", numero], check=False)
            except Exception:
                pass
            return f"Llamando al {numero}, compa."
        return "Dime a qué número llamo, compa. Por ejemplo: llama al 8112345678."
    if "hola" in t:
        return "Qué onda compa, soy RG. Dime qué ocupas."
    if "gracias" in t:
        return "De nada compa, aquí ando para lo que ocupes."
    if "lintern" in t and ("enciend" in t or "prend" in t or "activ" in t):
        subprocess.run(["termux-torch", "on"], check=False)
        return "Encendiendo la linterna."
    if "lintern" in t and ("apag" in t or "desactiv" in t):
        subprocess.run(["termux-torch", "off"], check=False)
        return "Apagando la linterna."
    if "hor" in t:
        return f"Son las {datetime.datetime.now().strftime('%I:%M %p')}, compa."
    if "fech" in t or "que dia" in t:
        return f"Hoy es {datetime.datetime.now().strftime('%A %d de %B de %Y')}."
    if "googl" in t:
        return "Abriendo Google: https://www.google.com"
    if "music" in t or "canci" in t:
        return "Poniendo música: https://music.youtube.com"
    if "quien eres" in t or "presentat" in t:
        return "Soy RG, la versión virtual de mi compa. De Villas de San Francisco, Escobedo. Cotorreo y música."
    if "adios" in t or "salir" in t:
        return "Órale, nos vemos, compa. Aquí ando cuando me ocupes."
    return f"Te entendí '{texto}', pero eso todavía no lo tengo programado. Dime: linterna, hora, fecha, Google, música o llama al número."

def hacer_voz(texto, archivo="rg_voz.mp3"):
    # Genera un audio con voz masculina mexicana. Devuelve True si quedó.
    try:
        r = subprocess.run(
            ["edge-tts", "--voice", "es-MX-JorgeNeural",
             "--text", texto, "--write-media", archivo],
            capture_output=True, text=True, timeout=60)
        return os.path.exists(archivo) and os.path.getsize(archivo) > 0
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Qué onda compa, soy RG. Dime qué ocupas.\n"
        "Prueba: hora, fecha, enciende la linterna, música, llama al número."
    )

async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text or ""
    respuesta = responder(texto)
    # Primero la nota de voz, luego el texto, por si la voz falla.
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
        print("Falta el token. En Termux escribe:")
        print('export TELEGRAM_BOT_TOKEN="tu-token-aqui"')
        print("Y luego corre otra vez: python rg_telegram.py")
        return
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))
    app.add_handler(MessageHandler(filters.VOICE, voz))
    print("RG en Telegram está prendido. Abre @RG_IA_BOT y escríbele.")
    app.run_polling()

if __name__ == "__main__":
    main()
