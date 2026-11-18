"""Gera static/img/icones.svg: um único arquivo com todos os ícones do app (<symbol id="i-nome">), usado por <svg><use href=".../icones.svg#i-nome"/></svg>.
Fontes: static/icons/lucide/*.svg (Lucide, licença ISC — static/icons/lucide/LICENSE.txt) e static/icons/proprios/*.svg (desenhados para o app: amortecedor, mola, coxim…).
Ícone novo: salve o .svg (24×24, traço 2, sem preenchimento) numa das pastas e rode:  python tools/icones.py"""
import glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "img", "icones.svg")

def inner(path):
    s = open(path, encoding="utf-8-sig").read()
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    m = re.search(r"<svg[^>]*>(.*)</svg>", s, flags=re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

def build():
    syms = []
    for pasta in ("lucide", "proprios"):                       # o próprio vence o Lucide de mesmo nome
        for p in sorted(glob.glob(os.path.join(ROOT, "static", "icons", pasta, "*.svg"))):
            nome = os.path.splitext(os.path.basename(p))[0]
            syms = [x for x in syms if x[0] != nome] + [(nome, inner(p))]
    body = "\n".join(f'<symbol id="i-{n}" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{b}</g></symbol>' for n, b in sorted(syms))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n<!-- Ícones: Lucide (ISC, static/icons/lucide/LICENSE.txt) + próprios do PERFECT Shock Data. Gerado por tools/icones.py -->\n' + body + "\n</svg>\n")
    return len(syms)

if __name__ == "__main__":
    print(f"{build()} ícones em {os.path.relpath(OUT, ROOT)}")
