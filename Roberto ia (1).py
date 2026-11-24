import os
import logging
import httpx
from datetime import datetime
from zoneinfo import ZoneInfo
import tools_rg
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)

# --- Configuración (variables de entorno) ---
TOKEN = os.environ["TELEGRAM_TOKEN"]          # el que te da @BotFather
OWNER_ID = int(os.environ["OWNER_ID"])        # tu ID de Telegram (usa @userinfobot)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
MAX_HISTORY = 20                              # mensajes que recuerda por chat

with open("prompt_rg.txt", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

history: dict[int, list[dict]] = {}


async def ask_ollama(messages: list[dict]) -> str:
    ahora = datetime.now(ZoneInfo("America/Monterrey"))
    system = f"{SYSTEM_PROMPT}\n\nFecha y hora actual: {ahora:%A %Y-%m-%d %H:%M} (hora de Monterrey)."
    convo = [{"role": "system", "content": system}] + messages

    async with httpx.AsyncClient(timeout=180) as client:
        for _ in range(5):  # máximo 5 rondas de herramientas
            payload = {"model": MODEL, "messages": convo, "tools": tools_rg.TOOLS, "stream": False}
            r = await client.post(OLLAMA_URL, json=payload)
            r.raise_for_status()
            msg = r.json()["message"]
            calls = msg.get("tool_calls")
            if not calls:
                return msg["content"]
            convo.append(msg)
            for call in calls:
                fn = call["function"]
                resultado = tools_rg.run_tool(fn["name"], fn.get("arguments") or {})
                convo.append({"role": "tool", "content": resultado})
    return "Me enredé con las herramientas, intenta de nuevo."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("Qué onda, soy RG. Dime en qué te ayudo.")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    history.pop(update.effective_chat.id, None)
    await update.message.reply_text("Listo, memoria de esta conversación borrada.")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Solo tú puedes usarlo (protege tu info personal)
    if update.effective_user.id != OWNER_ID:
        return

    chat_id = update.effective_chat.id
    msgs = history.setdefault(chat_id, [])
    msgs.append({"role": "user", "content": update.message.text})

    try:
        reply = await ask_ollama(msgs[-MAX_HISTORY:])
    except Exception as e:
        logging.exception("Error con Ollama")
        await update.message.reply_text(f"Falló el modelo: {e}")
        msgs.pop()
        return

    msgs.append({"role": "assistant", "content": reply})
    del msgs[:-MAX_HISTORY]
    await update.message.reply_text(reply)


async def revisar_recordatorios(context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.now(ZoneInfo("America/Monterrey"))
    for texto in tools_rg.recordatorios_vencidos(ahora):
        await context.bot.send_message(chat_id=OWNER_ID, text=f"⏰ Recordatorio: {texto}")


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.job_queue.run_repeating(revisar_recordatorios, interval=30, first=5)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()


if __name__ == "__main__":
    main()
