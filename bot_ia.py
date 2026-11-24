import json, os, subprocess, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ALLOWED_ID = os.environ.get("TELEGRAM_ALLOWED_ID")
HISTORIAL_FILE = os.path.expanduser("~/historial_bot.json")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
SYSTEM_INSTRUCTION = "Eres un asistente directo, claro y sin rodeos en Termux. Responde en español. Si debes ejecutar un comando en Termux, pon al final una línea exacta: EXEC: <comando>"

def ejecutar_comando(comando: str) -> str:
    try:
        res = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=30)
        return (res.stdout + res.stderr).strip() or "Comando ejecutado sin salida."
    except Exception as e:
        return f"Error al ejecutar: {e}"

def cargar_historial():
    if not os.path.exists(HISTORIAL_FILE):
        return []
    try:
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [{"role": x["role"], "parts": [{"text": x["text"]}]} for x in raw[-30:]]
    except Exception:
        return []

def guardar_turno(user_text: str, model_text: str):
    raw = []
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            raw = []
    raw.extend([{"role": "user", "text": user_text}, {"role": "model", "text": model_text}])
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(raw[-60:], f, ensure_ascii=False, indent=2)

def es_usuario_autorizado(update: Update) -> bool:
    u = update.effective_user
    return bool(ALLOWED_ID and u and str(u.id) == str(ALLOWED_ID).strip())

def llamar_gemini(contents: list) -> str:
    r = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json={"system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]}, "contents": contents},
        timeout=60,
    )
    r.raise_for_status()
    cands = r.json().get("candidates") or []
    parts = (cands[0].get("content", {}).get("parts") or []) if cands else []
    return "".join(p.get("text", "") for p in parts).strip() or "Respuesta vacía."

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if not es_usuario_autorizado(update):
        await update.message.reply_text("Acceso no autorizado.")
        return
    user_text = update.message.text.strip()
    history = cargar_historial()
    history.append({"role": "user", "parts": [{"text": user_text}]})
    try:
        reply_text = llamar_gemini(history)
    except Exception as e:
        await update.message.reply_text(f"Error consultando Gemini: {e}")
        return
    cmds = [l.split("EXEC:", 1)[1].strip() for l in reply_text.splitlines() if l.strip().startswith("EXEC:")]
    if cmds:
        salidas = [f"$ {c}\n{ejecutar_comando(c)}" for c in cmds]
        reply_text += "\n\n" + "\n\n".join(salidas)
    guardar_turno(user_text, reply_text)
    for i in range(0, len(reply_text), 4000):
        await update.message.reply_text(reply_text[i:i + 4000])

def main():
    if not (GEMINI_API_KEY and TELEGRAM_TOKEN and ALLOWED_ID):
        raise RuntimeError("Falta GEMINI_API_KEY, TELEGRAM_BOT_TOKEN o TELEGRAM_ALLOWED_ID en ~/.bashrc")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    print("Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
