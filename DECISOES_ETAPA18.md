# Etapa 18 — Garantia pelo servidor, página COFAP e amostras só PERFECT (19/11/2026)

Pedido: (1) Garantia com visual novo e alimentada direto do servidor (comparar antes com a planilha «Analítico de Garantias»); (2) página só da COFAP na
Cobertura de concorrentes: o que temos e o que não temos da planilha COFAP × frota, sem motos e sem contar DES de montadora; (3) Compra de amostras voltou a
listar itens de montadora: virar regra de negócio.

## Fatos levantados (cópia do banco + servidor, só SELECT)

- **Garantia — planilha × servidor** (`ANALITICO_GARANTIA_DEVOLUCAO`, FAMILIA AMORTECEDOR e AMORTECEDOR LINHA PESADA):
  - servidor 36.171 linhas × planilha 35.718 (planilha exportada ≈ 11/11; servidor até 18/11).
  - Autorização × código: 33.577 de 33.578 da planilha batem; o servidor tem +426, todos de 2026 (cadastrados depois da exportação).
  - Diferenças = atualizações posteriores: 699 status que avançaram, ≈ 240 análises concluídas (defeito, procedência, responsável, fornecedor), 356 valores
    (quase todos de 2026, ocorrências ainda em análise). Padrão da tela em 2026: planilha 8.758 peças / R$ 1,15 mi; servidor 9.094 peças / R$ 1,20 mi.
  - Correspondência de colunas: NF = `NF_ORI`-`SERIE_ORI`; Lote e Data de fabricação = `LOTE_GRV`, `DATA_FABRICACAO_GRV`; Responsável = `DEPARTAMENTO`;
    Fornecedor = `FORNECEDOR_SHORT_GRV`; Tipo I/P = `PROC_IMPROC`; Valor C.IPI = `VALOR`; Status = `STATUS_AUTO`.
- **COFAP** (`COFAP_AMORTECEDORES_x_FROTA.xlsx`, 70.072 linhas veículo × ano): classificação Leves 42.407 · Caminhões 13.096 · Motos 10.246 · Ônibus 4.323.
  Sem motos: 1.481 códigos COFAP distintos (`;` separa vários). Pelo nosso cross: 796 no catálogo, 102 em DES AMD, 583 não temos (frota 30 mi × 106 mi).
  A coluna «Amortecedor PERFECT» é por **veículo**, não por código (347 dos 583 estão em veículo com algum AMD).
- **Amostras**: 336 sugestões, 64 de montadora (47 BPROAUTO `1BP…`, 9 MOTRIO numéricos, 8 MOTORCRAFT PN Ford). Não havia regra no código (histórico desde a etapa 15).

## Decisões

| # | Tema | Decisão |
|---|---|---|
| Q1 | Fonte da garantia | Só o servidor, FAMILIA AMORTECEDOR e AMORTECEDOR LINHA PESADA, todos os anos. A sincronização grava a tabela da tela (substitui). A planilha deixa de ser lida (a Atualização avisa). Cliente só no banco local; CNPJ não é guardado. |
| Q2 | Campos | Como na planilha (correspondência acima) + UF, Lote válido/vencido e Status do item. **UF vira mapa do Brasil interativo**: índice de garantia por estado/região e o amortecedor com mais garantia em cada um. |
| Q3 | Comparação | Só registrada aqui (fatos acima); não vira tela. |
| Q4 | Visual da Garantia | Somente: KPIs com variação × mesmo período do ano anterior; mensal peças e valor com a linha do ano anterior; Pareto de defeitos; mapa por UF; top códigos com link para a página do item; lotes e fornecedores lado a lado; atalhos em fichas. Print antes de fechar. (Rosca de procedência **não**.) |
| Q5 | Página COFAP | 3ª aba da Cobertura de concorrentes («COFAP»), Excel próprio. |
| Q6 | Universo COFAP | Códigos distintos da coluna «Amortecedor COFAP», sem Motos; `;` separa; classificação vira atalho. |
| Q7 | «Temos» | Cross: referência de item do catálogo = «Temos · catálogo»; de DES/R-D **AMD** fora do catálogo e não cancelado = «Em desenvolvimento»; o resto = «Não temos». Montadora nunca conta. |
| Q8 | Pista da Fraga (AMD no veículo) | **Não fazer por enquanto.** |
| Q9 | Ordem | Frota da planilha (Frota2024; veículo × ano uma vez); principais veículos; «Não temos» com curva A/B/C pela frota (80/95%). |
| Q10 | Montadora na aba Desenvolvimento | Sai também da curva por frota da aba Desenvolvimento. |
| Q11 | Amostras | Sugestões só PERFECT (AMD…) — lista, contadores e Excel. **O formulário do pedido também só aceita código PERFECT em desenvolvimento** (DES/R-D). «Pendente compras» segue valendo nas outras telas. |
| Q12 | Ordem | 1 amostras · 2 garantia pelo servidor · 3 visual da Garantia (print) · 4 COFAP · 5 montadora fora da aba Desenvolvimento · 6 regras, LEIA-ME, testes. Um commit por passo. |

## Checkpoints

- **Passo 1 — amostras só PERFECT** (`purchases.py`, `app.py`, `telas/amostras.js`): sugestões com `upper(code) LIKE 'AMD%'`; `purchases.code_problem` recusa no
  pedido novo (ou com código trocado) o que não é AMD ou não está em `rd_projects` (API 400 com o motivo; aviso no formulário); `/api/samples/codes` sugere
  só AMD de DES/R-D. Na cópia: 336 → 272 sugestões.
