import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importer as im
B = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bases_exemplo")
f = lambda p: glob.glob(os.path.join(B, p))[0]

assert im.normalize_code("MP-AMD0243") == ("AMD0243", True)
assert im.normalize_code("BJ3A/18045/DA/") == ("BJ3A18045DA", False)
assert im.normalize_code("0012") == ("0012", False)          # zeros à esquerda preservados

cat = im.preview(f("CatalogoAMD.xlsx")); assert cat["rows_total"] == 912 and cat["header_row"] == 0
assert cat["mapping"]["Código do Produto"] == "perfect_code" and cat["mapping"]["Cód. NCM"] == "ncm"
rd = im.preview(f("DadosR-D*")); assert rd["rows_total"] == 2262 and rd["mapping"]["SUGESTAO"] == "rd_kind"
z = im.preview(f("ZS.csv")); assert z["mapping"]["Cod.Prod.For"] == "supplier_code" and z["mapping"]["Produto"] == "erp_code"
zp = im.preview(f("C*ZSxPERFECT.xlsx")); assert zp["mapping"]["PERFECT CODE"] == "perfect_code" and zp["rows_total"] == 832
assert im.preview(f("Itens*"), "MOTORCRAFT")["mapping"]["PN PERFECT (CORRESP.)"] == "perfect_code"
est = im.preview(f("Estrutura*")); assert est["rows_total"] == 5348, est["rows_total"]

df, _ = im.read_table(f("CaixasAMD.xlsx")); rows, w = im.parse_boxes(df)
d = {r["code"]: r for r in rows}
assert len(rows) == 25 and d["PP013B"]["length_mm"] == 425 and d["PP013B"]["width_mm"] == 85
print("OK; avisos de caixas:", *w, sep="\n  ")
