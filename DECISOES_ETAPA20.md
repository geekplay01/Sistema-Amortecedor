# Etapa 20 — DES/R-D só com o servidor, Estoque pela ESTOQUE_ANALISE_REPOSICAO, gráficos no escuro e animação inicial (20/11/2026)

Pedido: (1) cores dos gráficos no modo escuro; (2) melhorar o vídeo do início; (3) conferir no banco se os filtros de DES/R-D puxam certo —
o usuário contou 140 «curtidos» em pendente compras no R-D e 133 no DES — e acabar com itens que aparecem em DES/R-D sem estar («também em DES/R-D»);
(4) tirar o filtro de montadora e organizar os status de forma mais fluida; (5) Estoque vindo de ESTOQUE_ANALISE_REPOSICAO (total PRIVATE + FECT só dos
itens do controle, cobertura a partir disso, e ver o que é MP e o que é PA sem chamar atenção).

## Fatos levantados (servidor, só SELECT, LINHA exatamente «AMORTECEDOR», aplicações que não são ITEM RECEBIDO)

| Tipo | Itens / aplicações | Curtidos | Pend. compras | Pend. desenho forn. | Pend. projeto | Pend. partnumber | Pend. Inmetro |
|---|---|---|---|---|---|---|---|
| DES | 403 | 133 | 331 | 279 | 21 | 0 | 19 |
| R-D | 239 / 259 | 134 / 140 | 222 / 240 | 65 / 70 | 0 | 30 / 35 | 23 |

- O app mostrava DES 1.230 itens / 225 curtidos e R-D 790 / 265: contava os já recebidos e a linha pesada.
- Validação: nenhuma marca no servidor; as 2 «validação reprovada» do R-D no app eram marcação manual.
- Sub status que o app não mostrava: NEGOCIAÇÃO (finalizada / pendente), VENDAS (pendente / finalizada), CIT (pendente desenvolvimento).
  SUB_STATUS_VALIDACAO vem composto («PENDENTE DESENHO FORNECEDOR / PENDENTE COMPRAS»).
- Estoque do catálogo (914 itens): `QTD_EST_T_PRIVATE_E_FECT` = soma de PA + MP = 414 mil (PRIVATE PA 311 mil, MP 104 mil; FECT 0). O app mostrava 258 mil (armazém 04 − reservado).

## Decisões

| # | Tema | Decisão |
|---|---|---|
| Q1 | Universo | «Não separe nos módulos e na dashboard, mas em metas não precisa.» → telas e Dashboard só LINHA «AMORTECEDOR»; metas seguem com a linha pesada. |
| Q2 | Listas | Mostram o que está na SUGESTAO pela regra, abrindo em andamento (não recebido); o recebido fica no estágio ITEM RECEBIDO. Sai o selo «também DES/R-D». |
| Q3 | Controles | «Não é necessário ser manual, mostre somente o que está no servidor.» → sem marcação manual; só sub status do servidor. |
| Q4 | Status | Sem montadora; esteira de estágios sem setas, com contagem; todos os sub status do servidor, por coluna. |
| Q5 | Estoque | Fonte ESTOQUE_ANALISE_REPOSICAO; itens = catálogo; estoque = PRIVATE + FECT (PA + MP); cobertura = (estoque + a caminho) ÷ venda média de 12 meses do app. |
| Q6 | PA × MP | Total com barra fina PA × MP e dica (PA, MP, PRIVATE, FECT); «Contar: total / só PA / só MP» em Mais filtros. Mostrar print. |
| Q7 | Gráficos no escuro | Cores da marca mais claras, grade discreta, legenda legível, trilho do medidor escuro. Print antes de fechar. |
| Q8 | Animação inicial | Em código, «o mais parecido possível» com o vídeo. Prévia antes de trocar. |

## Checkpoints

- [x] Passo 1 — universo (`rules.desc_sql(pesada=False)`; metas e concorrentes com `pesada=True`). Commit da1712a.
- [x] Passo 2 — DES/R-D: `status=andamento` por padrão, esteira, quadro de sub status (`statuses.SUBS`, filtro `sub=`), colunas
      negotiation/sales/cit_substatus, sem marcação manual (`v_rd_flags` ignora `rd_flags`; rotas e barra em lote saíram), sem montadora e sem «também».
      Commit 8f96a5b.
- [x] Passo 3 — Estoque pela `ds_situacao` (stock_total, priv_pa, priv_mp, fect_pa, fect_mp), só catálogo, `conta=total|pa|mp`. Commit 4c60a98.
      Conferido na cópia: 885 itens, 416.234 peças (PA 320.457 · MP 95.778), cobertura 11,1 meses.
- [x] Passo 4 — tokens `--chart-1..7`, `--chart-grid`, `--chart-legend`, `--chart-track`; `PSDTW.grafico` traduz as cores da paleta clara. Commit a6b2aea.
- [x] Passo 5 — `templates/_amortecedor.html` (SVG + keyframes `.psd-sa`); tela inicial e Dashboard contam só em andamento. Commit bd31765.
- [x] Passo 6 — documentos (este arquivo, REGRAS_DE_NEGOCIO §3/§5/§6/§12, LEIA-ME, CLAUDE.md).
- [x] Passo 7 — animação refeita a pedido: semi-estrutural em 3D (desenho técnico do usuário, sem as medidas) com a etiqueta FORCE GAS enrolada no
      tubo. `<canvas>` em `static/js/amortecedor.js` (cilindro mapeado coluna a coluna, brilho holográfico só na etiqueta, olhal que mostra a face ao
      girar); faixas e nome seguem em SVG. `PSDSA.pose(seg)` congela um instante para conferir. Corrigido também o contorno escuro que o `svg{stroke}`
      global punha nas faixas.

## Para a próxima sincronização

- Negociação, vendas e CIT foram copiados do `extra` na migração; a próxima sincronização grava direto.
- O estoque da tela Estoque só aparece depois da 1ª sincronização com esta versão (a `ds_situacao` antiga não tem as colunas de estoque).
