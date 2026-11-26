"""Gera static/img/favicon.ico com o MESMO desenho de static/img/favicon.svg (etapa 24 · próximo update Q1: um ícone só na aba).
Desenha em 1024 px com Pillow (os traços do SVG, em escala 16×) e reduz para 16, 32, 48 e 256 px.
Uso: .venv\\Scripts\\python.exe tools\\favicon_ico.py   (rodar de novo se o favicon.svg mudar)"""
import math, os
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = 16                                          # 64 (viewBox do SVG) × 16 = 1024 px
NAVY, SKY, RED, ORANGE, WHITE = "#202D56", "#64C4E9", "#E72B3B", "#F6A019", "#FFFFFF"

def desenhar():
    im = Image.new("RGBA", (64 * K, 64 * K), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 64 * K - 1, 64 * K - 1), radius=14 * K, fill=NAVY)
    t = math.tan(math.radians(-20))           # skewX(-20): x' = x + tan(-20°)·y
    for x, cor in ((17, SKY), (25, RED), (33, ORANGE)):
        y0, y1, w = 40, 56, 5
        d.polygon([((x + t * y0) * K, y0 * K), ((x + w + t * y0) * K, y0 * K), ((x + w + t * y1) * K, y1 * K), ((x + t * y1) * K, y1 * K)], fill=cor)
    s = 4 * K                                   # traço branco de 4 (escala do SVG)
    def circ(cx, cy, r): d.ellipse(((cx - r) * K - s / 2, (cy - r) * K - s / 2, (cx + r) * K + s / 2, (cy + r) * K + s / 2), outline=WHITE, width=s)
    circ(44, 10, 4); circ(44, 52, 4)
    d.line((44 * K, 14 * K, 44 * K, 24 * K), fill=WHITE, width=s)
    d.rounded_rectangle((37 * K - s / 2, 24 * K - s / 2, 51 * K + s / 2, 46 * K + s / 2), radius=3 * K + s / 2, outline=WHITE, width=s)
    d.line((37 * K, 31 * K, 51 * K, 31 * K), fill=WHITE, width=s)
    return im

if __name__ == "__main__":
    big = desenhar().resize((256, 256), Image.LANCZOS)
    out = os.path.join(BASE, "static", "img", "favicon.ico")
    big.save(out, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    big.save(os.path.join(os.environ.get("PSD_PREVIA", BASE), "favicon_previa.png")) if os.environ.get("PSD_PREVIA") else None
    print("gravado:", out, os.path.getsize(out), "bytes")
