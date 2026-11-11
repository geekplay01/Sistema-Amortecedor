"""Baixa o TailwindCSS (Play CDN 3.4.17) para static/vendor/tailwind.js, para o sistema funcionar 100% offline.
Roda sozinho no iniciar.bat (só se o arquivo ainda não existir) e nunca derruba nada: sem internet/proxy, o layout continua correto
pelo static/css/tw-fallback.css (as mesmas classes escritas à mão) e usa o CDN quando houver internet."""
import os, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DST = os.path.join(ROOT, "static", "vendor", "tailwind.js")
URL = "https://cdn.tailwindcss.com/3.4.17"
def main():
    if os.path.exists(DST) and os.path.getsize(DST) > 100_000: print("TailwindCSS local já existe."); return 0
    try:
        data = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "PerfectShockData"}), timeout=20).read()
        if len(data) < 100_000 or b"tailwind" not in data[:200000].lower(): raise ValueError("resposta inesperada")
        os.makedirs(os.path.dirname(DST), exist_ok=True); open(DST, "wb").write(data); print(f"TailwindCSS salvo em static/vendor/tailwind.js ({len(data) // 1024} KB).")
    except Exception as e: print(f"Não baixei o TailwindCSS ({e.__class__.__name__}). Sem problema: o layout usa o CDN (com internet) ou o CSS reserva embutido.")
    return 0
if __name__ == "__main__": sys.exit(main())
