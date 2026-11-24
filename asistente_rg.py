# RG - Asistente virtual por voz para Android (Termux)
# Soy RG, la versión virtual de mi compa. De Villas de San Francisco, Escobedo. Cotorreo y música.
# Uso en Termux:
#   python asistente_rg.py
# Voz: usa la voz de Android con termux-speech-to-text, no necesita instalar Vosk.
# Si no hay micrófono, funciona escribiendo: solo escribe el comando y Enter.
# La llave de Gemini es opcional. Si la pones, RG contesta con IA; si no, contesta offline.
#   export GEMINI_API_KEY="tu-llave-nueva"
# Nunca pegues tu llave en un chat.

import os
import sys
import json
import subprocess
import datetime
import webbrowser

PROMPT_FILE = "prompt_rg.txt"

def cargar_prompt():
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "Soy RG, la versión virtual de mi compa. De Villas de San Francisco, Escobedo. Cotorreo y música."

PROMPT_RG = cargar_prompt()

def normalizar(texto):
    # Quita acentos y corrige teclas que se confunden: 9 por o, 0 por o, etc.
    # Así "que h9ra es" se entiende como "que hora es".
    import unicodedata
    t = texto.lower().strip()
    t = t.replace("9", "o").replace("0", "o").replace("1", "i")
    t = "".join(c for c in unicodedata.normalize("NFD", t)
                if unicodedata.category(c) != "Mn")
    return t

def decir(texto):
    print(f"RG: {texto}")
    # Voz masculina / más grave: pitch 0.7, un poco más lenta.
    # Si en tu teléfono sigue sonando femenina, cambia la voz en
    # Ajustes de Android > Idioma > Salida de texto a voz > Google,
    # voz en español, masculina. El pitch aquí ya la hace más grave.
    try:
        subprocess.run(["termux-tts-speak", "-p", "0.7", "-r", "0.95",
                        "-l", "es-MX", texto], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def linterna_on():
    decir("Encendiendo la linterna")
    try:
        subprocess.run(["termux-torch", "on"], check=False)
    except Exception:
        print("No pude prender la linterna en este equipo.")

def linterna_off():
    decir("Apagando la linterna")
    try:
        subprocess.run(["termux-torch", "off"], check=False)
    except Exception:
        print("No pude apagar la linterna en este equipo.")

def llamar(numero):
    decir(f"Llamando al {numero}, compa.")
    try:
        subprocess.run(["termux-telephony-call", numero], check=False)
    except Exception:
        print("No pude hacer la llamada en este equipo. Revisa el permiso de teléfono de Termux:API.")

def abrir(url, mensaje):
    decir(mensaje)
    try:
        subprocess.run(["termux-open", url], check=False)
    except Exception:
        webbrowser.open(url)

def responder_con_ia(pregunta):
    # Opcional: si hay GEMINI_API_KEY, usa Gemini. Si no, devuelve None.
    llave = os.environ.get("GEMINI_API_KEY", "")
    if not llave:
        return None
    try:
        import urllib.request
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
    except Exception as e:
        print(f"(IA no disponible: {e})")
        return None

def ejecutar(texto):
    # El número se saca del texto original, antes de normalizar,
    # porque normalizar cambia los 9 y 0 por letras.
    import re
    numeros = re.findall(r"\+?\d[\d\s\-]{6,}\d", texto)
    numero = re.sub(r"[\s\-]", "", numeros[0]) if numeros else ""
    t = normalizar(texto)
    if not t:
        return True

    if "llam" in t or "marca" in t:
        if numero:
            llamar(numero)
        else:
            decir("Dime a qué número llamo, compa. Por ejemplo: llama al 8112345678.")
        return True
    if "hola" in t:
        decir("Qué onda compa, soy RG. Dime qué ocupas.")
        return True
    if "gracias" in t:
        decir("De nada compa, aquí ando para lo que ocupes.")
        return True
    if "lintern" in t and ("enciend" in t or "prend" in t or "activ" in t):
        linterna_on()
        return True
    if "lintern" in t and ("apag" in t or "desactiv" in t):
        linterna_off()
        return True
    if "hor" in t:
        ahora = datetime.datetime.now().strftime("%I:%M %p")
        decir(f"Son las {ahora}, compa.")
        return True
    if "fech" in t or "que dia" in t:
        hoy = datetime.datetime.now().strftime("%A %d de %B de %Y")
        decir(f"Hoy es {hoy}.")
        return True
    if "googl" in t:
        abrir("https://www.google.com", "Abriendo Google.")
        return True
    if "music" in t or "canci" in t:
        abrir("https://music.youtube.com", "Poniendo música, compa.")
        return True
    if "quien eres" in t or "presentat" in t:
        decir("Soy RG, la versión virtual de mi compa. De Villas de San Francisco, Escobedo. Cotorreo y música.")
        return True
    if "adios" in t or "salir" in t or "apagat" in t:
        decir("Órale, nos vemos, compa. Aquí ando cuando me ocupes.")
        return False

    respuesta = responder_con_ia(texto)
    if respuesta:
        decir(respuesta)
    else:
        decir(f"Te entendí '{texto}', pero eso todavía no lo tengo programado. Dime: linterna, hora, fecha, Google, música o llama al número.")
    return True

def es_llamada(texto):
    # Palabra para prender a RG, como "Hey Meta" o "Hey Gemini": "Oye RG".
    t = normalizar(texto)
    return ("oye" in t and "rg" in t) or ("hey" in t and "rg" in t) or t.strip() in ("oye rg", "rg")
    # Usa la voz de Android, con Termux:API. Abre el micrófono del teléfono.
    try:
        r = subprocess.run(["termux-speech-to-text"],
                           capture_output=True, text=True, timeout=60)
        texto = (r.stdout or "").strip()
        # termux-speech-to-text a veces devuelve JSON, sácalo si es así
        if texto.startswith("{"):
            try:
                texto = json.loads(texto).get("text", "") or texto
            except Exception:
                pass
        return texto or None
    except Exception:
        return None

def escuchar():
    # Primero escribe. Si solo presionas Enter, ahí sí abre el micrófono.
    # Así no se mezcla lo que escribes con la voz.
    texto = input("Tú (escribe tu comando, o Enter para hablar): ").strip()
    if texto:
        return texto
    print("Habla ahora...")
    texto = escuchar_por_voz_android()
    if texto:
        print(f"Tú: {texto}")
        return texto
    return input("Tú (escribe tu comando): ").strip()

def main():
    print("=== RG - Asistente virtual ===")
    print(PROMPT_RG)
    print()
    print("RG está dormido. Llámalo: 'Oye RG'")
    print("También puedes escribir un comando directo, o Enter para hablar.")
    decir("Aquí ando, compa. Llámame: Oye RG.")
    while True:
        try:
            texto = escuchar()
        except (KeyboardInterrupt, EOFError):
            decir("Nos vemos, compa.")
            break
        if not texto:
            continue
        if es_llamada(texto):
            decir("Dime, compa, ¿qué ocupas?")
            try:
                comando = escuchar()
            except (KeyboardInterrupt, EOFError):
                decir("Nos vemos, compa.")
                break
            if not comando:
                continue
            if not ejecutar(comando):
                break
            print("RG está dormido. Llámalo: 'Oye RG'")
            continue
        # Si escribió un comando directo sin llamarlo, también se ejecuta.
        if not ejecutar(texto):
            break
        print("RG está dormido. Llámalo: 'Oye RG'")

if __name__ == "__main__":
    main()
