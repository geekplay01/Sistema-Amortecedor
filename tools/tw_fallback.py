"""Gera static/css/tw-fallback.css: as MESMAS classes TailwindCSS usadas nas telas (page.html, tw.js, pages_exec.js), escritas à mão.
Serve para o layout funcionar mesmo SEM internet e sem o arquivo static/vendor/tailwind.js; com o Tailwind carregado, as regras dele
assumem (mesmas declarações), então não há conflito. Rode de novo se criar telas com classes novas:  python tools/tw_fallback.py"""
import re, os, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["templates/page.html", "static/js/tw.js", "static/js/pages_exec.js", "static/js/core.js"] + sorted("static/js/telas/" + os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "static", "js", "telas", "*.js")))
SP = {"0": "0", "px": "1px", "0.5": ".125rem", "1": ".25rem", "1.5": ".375rem", "2": ".5rem", "2.5": ".625rem", "3": ".75rem", "3.5": ".875rem", "4": "1rem", "5": "1.25rem", "6": "1.5rem", "7": "1.75rem", "8": "2rem", "9": "2.25rem", "10": "2.5rem", "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem", "32": "8rem", "64": "16rem"}
PAL = {"slate": {"50": "#f8fafc", "100": "#f1f5f9", "200": "#e2e8f0", "300": "#cbd5e1", "400": "#94a3b8", "500": "#64748b", "600": "#475569", "700": "#334155", "800": "#1e293b", "900": "#0f172a"},
       "blue": {"400": "#60a5fa", "500": "#3b82f6", "600": "#2563eb", "700": "#1d4ed8"}, "emerald": {"50": "#ecfdf5", "100": "#d1fae5", "200": "#a7f3d0", "300": "#6ee7b7", "500": "#10b981", "600": "#059669", "700": "#047857"}, "amber": {"500": "#f59e0b", "700": "#b45309"},
       "red": {"500": "#ef4444", "600": "#dc2626"}, "violet": {"500": "#8b5cf6", "600": "#7c3aed"}}
NAMED = {"white": "#ffffff", "transparent": "transparent", "card": "var(--card)", "line": "var(--line)", "ink": "var(--tx)", "mute": "var(--mut)", "cobalt": "var(--cobalt)", "surface": "var(--bg)"}
TS = {"xs": (".75rem", "1rem"), "sm": (".875rem", "1.25rem"), "base": ("1rem", "1.5rem"), "lg": ("1.125rem", "1.75rem"), "xl": ("1.25rem", "1.75rem"), "2xl": ("1.5rem", "2rem"), "3xl": ("1.875rem", "2.25rem")}
RAD = {"": ".25rem", "lg": ".5rem", "xl": ".75rem", "2xl": "1rem", "full": "9999px"}
BP = {"sm": 640, "md": 768, "lg": 1024, "xl": 1280}
STATIC = {"flex": "display:flex", "grid": "display:grid", "block": "display:block", "inline-flex": "display:inline-flex", "hidden": "display:none", "flex-col": "flex-direction:column", "flex-row": "flex-direction:row", "flex-wrap": "flex-wrap:wrap",
          "flex-1": "flex:1 1 0%", "shrink-0": "flex-shrink:0", "items-center": "align-items:center", "items-end": "align-items:flex-end", "justify-between": "justify-content:space-between", "justify-center": "justify-content:center",
          "fixed": "position:fixed", "absolute": "position:absolute", "relative": "position:relative", "sticky": "position:sticky", "static": "position:static",
          "overflow-hidden": "overflow:hidden", "overflow-y-auto": "overflow-y:auto", "overflow-x-auto": "overflow-x:auto", "truncate": "overflow:hidden;text-overflow:ellipsis;white-space:nowrap", "whitespace-nowrap": "white-space:nowrap",
          "text-left": "text-align:left", "text-right": "text-align:right", "text-center": "text-align:center", "uppercase": "text-transform:uppercase", "tabular-nums": "font-variant-numeric:tabular-nums",
          "font-medium": "font-weight:500", "font-normal": "font-weight:400", "animate-spin": "animation:psd-spin 1s linear infinite", "font-semibold": "font-weight:600", "font-bold": "font-weight:700", "leading-none": "line-height:1", "cursor-pointer": "cursor:pointer", "outline-none": "outline:2px solid transparent;outline-offset:2px",
          "border": "border-width:1px", "border-2": "border-width:2px", "border-t": "border-top-width:1px", "border-b": "border-bottom-width:1px", "border-r": "border-right-width:1px",
          "border-collapse": "border-collapse:collapse", "border-dashed": "border-style:dashed", "block ": "", "h-auto": "height:auto", "max-w-none": "max-width:none", "w-full": "width:100%", "h-full": "height:100%", "h-screen": "height:100vh", "min-w-0": "min-width:0",
          "shadow-sm": "box-shadow:0 1px 2px 0 rgb(0 0 0/.05)", "shadow-inner": "box-shadow:inset 0 2px 4px 0 rgb(0 0 0/.05)", "ring-1": "box-shadow:0 0 0 1px var(--tw-ring-color,rgba(59,130,246,.5))",
          "tracking-wide": "letter-spacing:.025em", "tracking-widest": "letter-spacing:.1em", "inset-x-0": "left:0;right:0", "inset-y-0": "top:0;bottom:0", "left-0": "left:0", "top-0": "top:0", "z-10": "z-index:10", "z-20": "z-index:20", "z-40": "z-index:40", "w-44": "width:11rem", "w-72": "width:18rem", "align-top": "vertical-align:top",
          "shadow-lg": "box-shadow:0 10px 15px -3px rgb(0 0 0/.1),0 4px 6px -4px rgb(0 0 0/.1)",
          "ring-2": "box-shadow:0 0 0 2px var(--tw-ring-color,rgba(59,130,246,.5))", "no-underline": "text-decoration-line:none", "w-14": "width:3.5rem", "w-48": "width:12rem",
          "mx-auto": "margin-left:auto;margin-right:auto", "ml-auto": "margin-left:auto", "w-36": "width:9rem", "items-start": "align-items:flex-start", "list-none": "list-style:none","grow": "flex-grow:1", "break-words": "overflow-wrap:break-word", "hidden ": ""}
SIDES = {"": ["{}"], "x": ["{}-left", "{}-right"], "y": ["{}-top", "{}-bottom"], "t": ["{}-top"], "b": ["{}-bottom"], "l": ["{}-left"], "r": ["{}-right"]}

def color(name):
    m = re.fullmatch(r"([a-z]+)(?:-(\d+))?(?:/(\d+))?", name)
    if not m: return None
    base, shade, alpha = m.groups(); hexv = PAL.get(base, {}).get(shade) if shade else NAMED.get(base)
    if not hexv: return None
    if alpha:
        if hexv.startswith("var("): return f"color-mix(in srgb,{hexv} {alpha}%,transparent)"
        h = hexv.lstrip("#"); r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16); return f"rgba({r},{g},{b},{int(alpha) / 100:g})"
    return hexv

def arb(v): return v[1:-1].replace("_", " ") if v.startswith("[") and v.endswith("]") else None
def space(v): a = arb(v); return a if a else SP.get(v)

def decl(u):
    """classe base (sem variante) → declarações CSS, ou None."""
    if u in STATIC: return STATIC[u] or None
    m = re.fullmatch(r"(-?)(p|m)([xytblr]?)-(.+)", u)
    if m and not m.group(1):
        v = space(m.group(4)); pr = {"p": "padding", "m": "margin"}[m.group(2)]
        if v is not None: return ";".join(f"{p.format(pr)}:{v}" for p in SIDES[m.group(3)])
    m = re.fullmatch(r"gap(-[xy])?-(.+)", u)
    if m and space(m.group(2)) is not None: return {None: "gap", "-x": "column-gap", "-y": "row-gap"}[m.group(1)] + ":" + space(m.group(2))
    m = re.fullmatch(r"(w|h|min-w|min-h|max-w|max-h)-(.+)", u)
    if m:
        pr = {"w": "width", "h": "height", "min-w": "min-width", "min-h": "min-height", "max-w": "max-width", "max-h": "max-height"}[m.group(1)]; v = m.group(2); a = arb(v)
        return f"{pr}:{a or {'full': '100%', 'screen': '100vh' if pr.endswith('h') or pr.endswith('height') else '100vw', 'auto': 'auto'}.get(v) or SP.get(v) or ''}" if (a or v in ("full", "screen", "auto") or v in SP) else None
    m = re.fullmatch(r"grid-cols-(\d+)", u)
    if m: return f"grid-template-columns:repeat({m.group(1)},minmax(0,1fr))"
    m = re.fullmatch(r"col-span-(\d+)", u)
    if m: return f"grid-column:span {m.group(1)}/span {m.group(1)}"
    m = re.fullmatch(r"text-(xs|sm|base|lg|xl|2xl|3xl)", u)
    if m: return f"font-size:{TS[m.group(1)][0]};line-height:{TS[m.group(1)][1]}"
    m = re.fullmatch(r"text-(\[.+\])", u)
    if m:
        a = arb(m.group(1)); return f"font-size:{a}" if re.search(r"(px|rem|em)$", a) else f"color:{a}"
    m = re.fullmatch(r"tracking-(\[.+\])", u)
    if m: return f"letter-spacing:{arb(m.group(1))}"
    m = re.fullmatch(r"rounded(?:-(lg|xl|2xl|full))?", u)
    if m: return f"border-radius:{RAD[m.group(1) or '']}"
    m = re.fullmatch(r"(bg|text|border|ring|placeholder|divide)-(.+)", u)
    if m:
        c = color(m.group(2))
        if c: return {"bg": f"background-color:{c}", "text": f"color:{c}", "border": f"border-color:{c}", "ring": f"--tw-ring-color:{c}", "placeholder": f"color:{c}", "divide": f"border-color:{c}"}[m.group(1)]
    m = re.fullmatch(r"border-t-(.+)", u)
    if m and color(m.group(1)): return f"border-top-color:{color(m.group(1))}"
    m = re.fullmatch(r"(top|left|right|bottom|inset)-(.+)", u)
    if m and space(m.group(2)) is not None: return f"{m.group(1)}:{space(m.group(2))}"
    return None

def esc(t): return re.sub(r"([^a-zA-Z0-9_-])", r"\\\1", t)

def rule(tok):
    """token com variantes → (ordem, bloco CSS) ou None."""
    parts = tok.split(":"); base, vs = parts[-1], parts[:-1]
    if base.startswith("divide-y"): d, sel_tail = "border-top-width:1px", " > :not([hidden]) ~ :not([hidden])"
    elif base.startswith("divide-") and decl(base): d, sel_tail = decl(base), " > :not([hidden]) ~ :not([hidden])"
    else: d, sel_tail = decl(base), ""
    if not d: return None
    sel = "." + esc(tok); pseudo = ""; media = None; grp = False; order = 0
    for v in vs:
        if v in BP: media = BP[v]; order = max(order, 1 + BP[v] // 100)
        elif v == "hover": pseudo += ":hover"; order = max(order, 1)
        elif v == "focus": pseudo += ":focus"; order = max(order, 1)
        elif v == "group-hover": grp = True; order = max(order, 1)
        else: return None
    if base.startswith("placeholder-"): pseudo += "::placeholder"
    s = (".group:hover " + sel if grp else sel) + pseudo + sel_tail
    blk = f"{s}{{{d}}}"
    return order, (f"@media(min-width:{media}px){{{blk}}}" if media else blk)

def main():
    toks = set()
    for f in FILES:
        for t in re.findall(r"[^\s\"'`<>=,;{}]+", open(os.path.join(ROOT, f), encoding="utf-8").read()): toks.add(t.strip("()"))
    out, seen = [], set(); miss = []
    for t in sorted(toks):
        r = rule(t)
        if r: out.append((r[0], t, r[1]))
        elif re.fullmatch(r"(?:(?:sm|md|lg|xl|hover|focus|group-hover):)*(?:-?[a-z]+(?:-[a-z0-9\[\]\./%#_(),-]+)+)", t) and not t.startswith(("data-", "aria-", "psd-", "http", "tw-")): miss.append(t)
    out.sort(key=lambda x: (x[0], x[1]))
    css = "/* GERADO por tools/tw_fallback.py — classes TailwindCSS usadas nas telas (funciona sem internet). Não edite à mão. */\n" + "\n".join(b for _, _, b in out) + "\n"
    css += "\n@keyframes psd-spin{to{transform:rotate(360deg)}}\n"
    open(os.path.join(ROOT, "static", "css", "tw-fallback.css"), "w", encoding="utf-8").write(css)
    print(f"{len(out)} regras escritas ({len(css)} bytes).")
    if "--miss" in sys.argv: print("candidatas sem regra:", " ".join(sorted(miss)))
if __name__ == "__main__": main()
