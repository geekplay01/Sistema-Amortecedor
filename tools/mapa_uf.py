"""Gera static/js/brasil_uf.js (contorno dos 27 estados para o mapa da tela Garantia) a partir da malha do IBGE.
Uso (uma vez; o arquivo gerado vai para o repositório e o mapa funciona offline):
    .venv\\Scripts\\python.exe tools\\mapa_uf.py <br_uf.json>
<br_uf.json> = GeoJSON da API de malhas do IBGE (dados públicos):
    https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson&qualidade=minima&intrarregiao=UF
Projeção simples (longitude × cos 15°S, latitude invertida), coordenadas arredondadas a 0,1 — leve e suficiente para um mapa por estado."""
import json, math, os, sys

UF = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
      "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}
REGIAO = {"N": "Norte", "NE": "Nordeste", "CO": "Centro-Oeste", "SE": "Sudeste", "S": "Sul"}
DE_REGIAO = {"1": "N", "2": "NE", "3": "SE", "4": "S", "5": "CO"}
W = 1000.0
K = math.cos(math.radians(15))

def main(src, dst):
    gj = json.load(open(src, encoding="utf-8"))
    polys = {}
    for f in gj["features"]:
        cod = str(f["properties"].get("codarea"))
        g = f["geometry"]; rings = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        polys[UF[cod]] = (cod, [[r for r in p] for p in rings])
    xs = [lon * K for _, ps in polys.values() for p in ps for r in p for lon, lat in r]; ys = [-lat for _, ps in polys.values() for p in ps for r in p for lon, lat in r]
    x0, y0 = min(xs), min(ys); s = W / (max(xs) - x0); H = (max(ys) - y0) * s
    P = lambda lon, lat: ((lon * K - x0) * s, (-lat - y0) * s)
    out = {}
    for uf, (cod, ps) in sorted(polys.items()):
        d, big, best = [], None, 0
        for p in ps:
            for i, r in enumerate(p):
                pts = [P(*c) for c in r]; seg = []
                for x, y in pts:
                    t = f"{x:.1f} {y:.1f}"
                    if not seg or seg[-1] != t: seg.append(t)
                d.append("M" + "L".join(seg) + "Z")
                if i == 0:      # rótulo no centróide do maior anel externo
                    a = cx = cy = 0
                    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
                        c = x1 * y2 - x2 * y1; a += c; cx += (x1 + x2) * c; cy += (y1 + y2) * c
                    if abs(a) > best: best = abs(a); big = (cx / (3 * a), cy / (3 * a)) if a else pts[0]
        out[uf] = {"d": "".join(d), "x": round(big[0], 1), "y": round(big[1], 1), "regiao": DE_REGIAO[cod[0]]}
    js = ("/* Contorno dos 27 estados (malha do IBGE, qualidade mínima) — gerado por tools/mapa_uf.py; não editar à mão.\n"
          "   window.PSD_BRASIL = {w, h, regioes, uf: {SP: {d, x, y, regiao}}} — usado pelo mapa da tela Garantia. */\n"
          f"window.PSD_BRASIL = {json.dumps({'w': W, 'h': round(H, 1), 'regioes': REGIAO, 'uf': out}, ensure_ascii=False, separators=(',', ':'))};\n")
    with open(dst, "w", encoding="utf-8") as fh: fh.write(js)
    print(f"{dst}: {len(out)} estados, {len(js) // 1024} KB")

if __name__ == "__main__":
    main(sys.argv[1], os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "js", "brasil_uf.js"))
