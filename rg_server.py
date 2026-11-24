# Servidor de RG: guarda la llave de Gemini y contesta a la app (RG.html / APK).
# Uso:
#   export GEMINI_API_KEY="tu-llave"      (nunca en el HTML ni en el chat)
#   export RG_TOKEN="una-clave-que-inventes"   (la app la manda para que nadie más use tu servidor)
#   export RG_MODELO="gemini-2.5-flash"   (opcional; pon uno más grande si quieres más poder)
#   python rg_server.py                   (puerto 8787, o el de la variable PORT)
import os, json, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
MODELO = os.environ.get("RG_MODELO", "gemini-2.5-flash")
LLAVE = os.environ.get("GEMINI_API_KEY", "")
TOKEN = os.environ.get("RG_TOKEN", "")
BUSCAR = os.environ.get("RG_BUSCAR", "1") == "1"   # búsqueda en Google en vivo
MEMORIA = os.path.join(HERE, "memoria.json")
MAX_TURNOS = 16


def prompt():
    try:
        with open(os.path.join(HERE, "prompt_rg.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "Eres RG, la versión virtual de Roberto. Español de México, corto y directo."


def cargar():
    try:
        with open(MEMORIA, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def guardar(h):
    try:
        with open(MEMORIA, "w", encoding="utf-8") as f:
            json.dump(h[-MAX_TURNOS:], f, ensure_ascii=False)
    except Exception:
        pass


def preguntar(texto):
    h = cargar()
    h.append({"role": "user", "parts": [{"text": texto}]})
    cuerpo = {"system_instruction": {"parts": [{"text": prompt()}]}, "contents": h[-MAX_TURNOS:]}
    if BUSCAR:
        cuerpo["tools"] = [{"google_search": {}}]
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent",
        data=json.dumps(cuerpo).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": LLAVE}, method="POST")
    with urllib.request.urlopen(req, timeout=45) as r:
        resp = json.loads(r.read().decode())
    partes = resp["candidates"][0]["content"]["parts"]
    out = "".join(p.get("text", "") for p in partes).strip()
    h.append({"role": "model", "parts": [{"text": out}]})
    guardar(h)
    return out


class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-RG-Token")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        self._json(200, {"ok": True, "modelo": MODELO, "llave": bool(LLAVE)})

    def do_POST(self):
        if TOKEN and self.headers.get("X-RG-Token") != TOKEN:
            return self._json(401, {"error": "token"})
        if not LLAVE:
            return self._json(500, {"error": "falta GEMINI_API_KEY"})
        try:
            n = min(int(self.headers.get("Content-Length", 0)), 8000)
            msg = json.loads(self.rfile.read(n).decode()).get("mensaje", "").strip()
            if not msg:
                return self._json(400, {"error": "vacío"})
            self._json(200, {"respuesta": preguntar(msg)})
        except Exception as e:
            self._json(502, {"error": str(e)[:200]})


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8787))
    print(f"RG server en puerto {puerto} · modelo {MODELO} · búsqueda {'sí' if BUSCAR else 'no'}")
    ThreadingHTTPServer(("0.0.0.0", puerto), H).serve_forever()
