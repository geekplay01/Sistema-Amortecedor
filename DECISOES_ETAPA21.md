# Etapa 21 — DES/R-D como o sistema PERFECT, chave de linha, regras das telas em Configurações e ajuste da animação (20/11/2026)

Pedido: (1) etiqueta FORCE GAS um pouco menor e o nome PERFECT AUTOMOTIVE melhor alinhado ao logo atrás (com o ui-ux-pro-max);
(2) DES/R-D: o sistema PERFECT mostra DES 338 na linha amortecedor e R-D 260 amortecedor + 12 linha pesada — descobrir por que o app puxa diferente;
chave Amortecedor · Amortecedor de moto · Linha pesada nas duas telas; pendente vendas, negociação finalizada e pendente negociação para «Mais filtros»;
validação aprovada, reprovada e pendente qualidade continuam no quadro; no DES, «Pendente controladoria» em «Mais filtros»;
(3) tirar os textos de regra das telas (começando por Pedidos em Aberto) e deixá-los em Configurações, para todos os módulos.

## Fatos levantados no servidor (só SELECT, aplicações que não são ITEM RECEBIDO)

| Tipo | FAMILIA | Linhas (itens) | Códigos | Observação |
|---|---|---|---|---|
| DES | AMORTECEDOR | 397 | 397 | marca PERFECT **338** · BPROAUTO 38 · MOTORCRAFT 12 · MOTRIO 9 |
| DES | AMORTECEDOR DE MOTO | 1 | 1 | LINHA = AMORTECEDOR |
| DES | AMORTECEDOR LINHA PESADA | 28 | 28 | 5 delas com LINHA = AMORTECEDOR |
| R-D | AMORTECEDOR | **260** | 240 | marca vazia 130 · PERFECT 128 · MOTORCRAFT 2 |
| R-D | AMORTECEDOR LINHA PESADA | **12** | 12 | |

- Por que o app divergia: (a) usava a LINHA, e o sistema PERFECT usa a **FAMILIA** (moto e parte da linha pesada vêm com LINHA «AMORTECEDOR»);
  (b) contava **códigos distintos**, e o sistema PERFECT conta **linhas (IDs)** — no R-D, 240 códigos = 260 itens; (c) no DES o sistema PERFECT só mostra a
  **marca PERFECT**. Os 140 curtidos do R-D também eram linhas (134 códigos).
- «Pendente controladoria» não existe hoje em nenhuma coluna da view (status ou sub status). O filtro procura o texto CONTROLADORIA em todas e mostra 0 até aparecer.
- Validação aprovada / reprovada / pendente qualidade também não vêm hoje; ficam no quadro com 0.

## Decisões

| # | Tema | Decisão |
|---|---|---|
| 1 | Universo | `rules.desc_sql` usa a FAMILIA (`rd_projects.family`, nova); sem FAMILIA (banco antigo) vale a LINHA/descrição. Padrão = Amortecedor; metas = amortecedor + linha pesada. |
| 2 | Chave de linha | Botões Amortecedor · Amortecedor de moto · Linha pesada no topo das duas telas (`?linha=moto|pesada`), com itens em andamento e códigos. |
| 3 | Marca | DES padrão = PERFECT ou marca vazia (as marcas de clientes saem); «Mais filtros › Marca» tem «Todas as marcas» e cada marca. R-D sem filtro de marca. |
| 4 | Contagem | Itens = linhas do servidor (número grande em estágios, quadro, KPIs e tela inicial); códigos embaixo. A lista continua agrupada por código. |
| 5 | Bloqueado no ERP | Continua fora (decisão da etapa 16): por isso o DES fica em 337 na cópia — AMD0345 (EM COTAÇÃO) está bloqueado no ERP. |
| 6 | Filtros | Negociação e vendas saem do quadro para «Mais filtros» (`negociacao=`, `vendas=`); validação aprovada/reprovada/pendente qualidade fixas no quadro (`sub=validacao:@APROVADA|@REPROVADA|@QUALIDADE`, juntam as grafias do servidor); DES: «Pendente controladoria» (`controladoria=1`). |
| 7 | Regras das telas | `regras_telas.py` → Configurações › Regras das telas (para todos os usuários), um cartão por tela; ao lado do título de cada tela, só o link «Regras da tela» (`/configuracoes#telas-<tela>`). Ficam nas telas só avisos de estado (falta sincronizar, planilha não carregada) e instruções de envio de arquivo. |
| 8 | Animação | Etiqueta 20% menor; nome recortado pelo vão inclinado da faixa laranja (o «A» de AUTOMOTIVE não é mais cortado), centrado no eixo do amortecedor e acima da ponta (amortecedor a 90%, mais baixo). O script de busca do ui-ux-pro-max não está instalado neste PC: valeram as regras de prioridade da própria skill (alinhamento, hierarquia, movimento reduzido). |

## Checkpoints

- [x] Animação (etiqueta, recorte e alinhamento do nome).
- [x] Servidor: FAMILIA no `DEV_WHERE` e em `rd_projects.family` (cópia do `extra` na migração); `rules.FAMILIAS`, `MARCA_PADRAO`, `marca_sql`.
- [x] `rd.py`: `_univ`, `facets(kind, status, f)` com `familias`, `marcas`, `controladoria`, `curtidos_l`; `items` com `linhas`; v_rd_flags com as três famílias.
- [x] Tela DES/R-D (chave de linha, contagem por itens, Mais filtros) e testes (`test_familia_do_servidor_marca_e_itens_por_linha`, test_03b).
- [x] Regras das telas: `regras_telas.py`, `/api/regras-telas`, Configurações, link no título; textos tirados de Pedidos em Aberto, Estoque, DES/R-D, Brands,
      Aplicações, Comparação, Lados, Anomalias, Metas, Dashboard, Pesquisa/Produtos, Pendências, Amostras, Fontes e ficha do item.
- Conferido na cópia: DES 337 (338 − AMD0345 bloqueado), moto 1, pesada 28; R-D 259 / 239 códigos, pesada 12, 140 curtidos. A cópia é de antes da última
  sincronização: no banco real, depois de sincronizar, o R-D deve dar 260.

## Para a próxima sincronização

- A FAMILIA é copiada do `extra` na migração; a sincronização seguinte grava direto e passa a trazer as linhas cuja FAMILIA é de amortecedor mesmo que a LINHA não seja.
