import sys

# Pon aquí el código que generaste en Termux
CODIGO_VALIDO = "TU-CODIGO-AQUI"

print("=== SISTEMA DE IA BLOQUEADO ===")
clave = input("Ingresa tu código de activación: ").strip()

if clave != CODIGO_VALIDO:
    print("❌ Código incorrecto. Acceso denegado.")
    sys.exit()

print("\n✅ ¡Acceso concedido! Inteligencia Artificial activada.\n")

# Ciclo de conversación de tu IA
while True:
    mensaje = input("Tú: ")
    if mensaje.lower() in ["salir", "exit"]:
        print("IA: ¡Nos vemos, compa!")
        break
    
    # Aquí conectarías tu modelo (Ollama, API de Gemini, OpenAI, etc.)
    print(f"IA: Recibí tu mensaje -> '{mensaje}'")
