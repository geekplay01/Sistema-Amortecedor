# Etapa 19 — DES × R-D pelas linhas do servidor, filtros novos, edição do cross e Pedidos em aberto (19/11/2026)

Pedido: (1) rever Desenvolvimento e Redesenvolvimento (itens de DES aparecendo em R-D; R-D com «pendente compras» não bate: o usuário contou 55);
(2) filtros e botões mais modernos na Garantia e nas demais telas, com menos filtros; (3) Cobertura: editar «Nosso código» ali mesmo;
(4) Pedidos em aberto parecido com a imagem enviada (bolinha, código, fornecedor, pedido, pedido em, barra, dias, média do fornecedor, previsão).

## Fatos levantados (servidor DESENVOLVIMENTO_PRODUTOS, só SELECT, e cópia do banco)

- Linhas de amortecedor: DES 1.550 linhas / 1.548 códigos; R-D 1.210 linhas / 852 códigos; 532 códigos nos dois.
- **Bug 1 — exclusividade**: `normalize_dev` regravava como R-D as linhas DES de todo código que tinha alguma linha R-D. DES ativo aparecia no R-D
  (na cópia, 25 itens em PEDIDO CONFIRMADO, status que só existe em DES) e o DES recebido em 2026 de item depois redesenvolvido sumia da meta de DES.
- **Bug 2 — pendente compras do R-D**: o código tem várias aplicações R-D (uma recebida, outra em FINALIZANDO CIT). O app ignorava o sub status quando
  ALGUMA aplicação estava recebida → 23 itens. Por aplicação ainda não recebida: 234 (152 com DES + 54 sem DES em FINALIZANDO CIT; 24 + 4 em PENDENTE PARTNUMBER).
  Os 55 do usuário não foram reproduzidos (recortes: 234 · 115 sem amostra comprada · 58 sem linha DES · 54 FINALIZANDO CIT sem DES · 23 o app antigo).
- **Bug 3 — amostras**: as sugestões exigiam «fora do catálogo», o que tirava quase todo R-D (mas, pela Q3, R-D não deve ter sugestão).

## Decisões

| # | Tema | Decisão |
|---|---|---|
| Q1 | Pendente compras R-D | Por aplicação: a aplicação R-D marcada conta enquanto ELA não estiver em ITEM RECEBIDO. (Filtro dos 55 não informado.) |
| Q2 | DES × R-D | «O redesenvolvimento é com outro fornecedor do item já recebido, no catálogo: só quando o servidor tiver o status de R-D é que deve ser contabilizado.» → cada linha vale pelo tipo do servidor; sem exclusividade. |
| Q3 | Amostras | R-D não precisa de compra de amostra; sugestões só DES. Comprar item já desenvolvido = pedido manual (o formulário aceita AMD do catálogo). |
| Q4 | Filtros (padrão) | Busca + até 3 filtros principais em listas com o nome dentro; o resto em «Mais filtros»; etiquetas dos filtros ativos com ×; atalhos numa faixa; botões novos. **Mostrar como fica antes.** |
| Q5 | Garantia | Ano (3 anos + Todos), Tipo e Status visíveis; Fornecedor, Procedência, Lote, Unidade e Estado em «Mais filtros». **Tirar os quadrados cinzas dos botões e polir.** |
| Q6 | Demais telas | Tabela por tela (visível / Mais filtros / sai) para aprovar; manter um padrão. |
| Q7 | Cobertura | Editar «Nosso código» na célula (Catálogo e COFAP); correção local vale sobre CrossCatalogo/servidor; aba «Cross corrigido no app» em Anomalias; vazio = tira a ligação. |
| Q8 | Pedidos em aberto | Tabela como a imagem (bolinha, código sem MP-, fornecedor, pedido, pedido em, barra dias ÷ média, dias, média forn., previsão); o resto ao passar o mouse/abrir e no Excel. |
| Q10 | Meta DES (após a prévia) | «A meta de DES é tudo aquilo que passou de pedido confirmado para item recebido, em 2026. R-D é outra lógica: tudo que foi validado por mim e passou a ser item recebido com o fornecedor diferente do atual.» → DES sem exigir validação. |
| Q9 | Ordem | 1 DES×R-D · 2 amostras · 3 prévia dos filtros na Garantia (aprovar) · 4 filtros nas outras telas · 5 Cobertura · 6 Pedidos em aberto · 7 docs. |

## Checkpoints

- **Passos 1 e 2 — DES × R-D e amostras** (um commit: os testes dos dois estão no mesmo arquivo):
  `data_pipeline.normalize_dev` não regrava mais o tipo; `rd.py` sem `_excl`; `metas._select` sem «R-D prevalece»; `cobertura._des_rows` sem a exclusão;
  `statuses.view_sql`: pend_compras por aplicação no R-D; `goals._events`/`rd_validations` ignoram eventos `novo_item` (item que aparece já recebido não
  conta como recebido no dia — vale a coluna de data); `purchases.pending` só DES; `code_problem` e `/api/samples/codes` aceitam AMD do catálogo.
  Na cópia, depois de sincronizar o DES de novo: lista DES 759 → 1.230 códigos (inclui os recebidos que estavam como R-D); R-D com PEDIDO CONFIRMADO 25 → 0;
  R-D pendente compras 23 → 234; meta DES 2026 82 → 110 (DES recebidos em 2026 que depois ganharam R-D); validações do quadro de metas 267 → 282
  (linhas DES 64 → 96, R-D 226 → 194); sugestões de amostra 268 → 271 (DES que voltaram ao DES).
- **Passo 1b — meta DES (Q10)** (`goals.des_recebidos`; `progress`, `events_list`, `rules_text`, `telas/metas.js`): PEDIDO CONFIRMADO → ITEM RECEBIDO no ano
  pela DATA_RECEBIDO do servidor (senão a transição vista), sem validação. Na cópia: 212 itens em 2026 (jan 17 · jun 23 · set 19 · out 44 · nov 103 — em
  novembro, 65 transições vistas pelas sincronizações e 38 datadas pelo servidor em 03/11); 52 deles validados por ITALOC; 30 também têm R-D; inclui itens
  de montadora (1BP…, a regra não pediu para tirar). Com o «já realizado antes do rastreio» de 58 cadastrado na tela, a meta mostra 270 de 125 —
  esse campo agora soma em dobro (a data do servidor cobre o ano todo) e deve ir a 0 na tela Metas (decisão do usuário).
- **Passo 3 — prévia dos filtros na Garantia** (aprovada: «O restante pode seguir»): componente `PSDTW.barra / pintarBarra / ligarBarra / botao` (tw.js) e estilos `.psd-fbar …`
  (marca.css): busca arredondada, Ano em botões lado a lado (3 anos + Todos), Tipo e Status em listas com contagem, «Mais filtros» (Fornecedor, Procedência,
  Lote, Unidade, Estado — lista longa ocupa a linha toda), etiquetas com × e «Limpar tudo», Excel azul-marinho à direita. Os «quadrados cinzas» eram o
  visual padrão do navegador em botões sem estilo (o Tailwind pré-compilado não traz o reset): `:where(main) :where(button)` zera fundo/borda com
  especificidade 0. Botões dos cards (Índice/Peças, Peças/Valor) no mesmo padrão (`.psd-seg.sm`).
- **Passo 4 — barra nas outras telas** (tabela da Q6; nenhum filtro some, só muda de lugar): Desenvolvimento/Redesenvolvimento (Status, Controle com grupos,
  Fornecedor; atalhos Pendente compras e Curtidos), Produtos (Linha, Família, Sistema), Pesquisa (Montadora, Modelo, Ano; o resto em «Mais filtros»; o campo
  separado «Código» saiu — a busca já procura código PERFECT/OEM/concorrente), Aplicações, Equivalências (multisseleção de critérios/diferenças/ausentes e
  pontuação mínima em «Mais filtros»), Lados (atalhos combinados mantidos), Brands, Desenhos (tamanho dos cartões ao lado do Excel), Estoque, Cobertura
  (por aba), Compra de amostras (as duas abas). Telas pequenas (Envio, Pendências, Anomalias, Fontes, Damping, Metas): atalhos e busca com o mesmo
  visual (`psd-chip`, busca arredondada com lupa), Excel com o ícone. Barra: grupos dentro da lista (`{g}`), faixa de atalhos, multisseleção (`multi`),
  atributo `data-ftg` (não colide com o `data-tg` das telas).
- **Passo 5 — editar «Nosso código» na Cobertura** (`cobertura.corrigir/desfazer/correcoes`, `cross_correcoes`; `/api/cobertura/cross` e `/desfazer`;
  `anomalias.corrigido`; `telas/cobertura.js`, `telas/anomalias.js`): correção = conjunto de códigos da referência (catálogo: troca de/para; COFAP: lista),
  aplicada em `_catalogo_rows` e `_cofap_rows` (o cache da COFAP inclui as correções). Toast com «Desfazer» (o fechar do toast passou a ser só o botão
  de fora). Conferido na cópia: SGB27608 ← AMD0356 tirou o código de «Não temos» (572 → 571) e o «Desfazer» voltou. Teste `test_35`.
- **Passo 6 — Pedidos em aberto como a imagem** (`pages_exec.js`, `marca.css`): «Linhas previstas» com bolinha (verde no prazo · laranja vai atrasar ·
  vermelha vencida · cinza parado), código sem MP-, fornecedor, pedido, pedido em, barra (dias desde o pedido ÷ mediana pedido → filial do fornecedor;
  degradê vermelho → laranja da marca), dias, média do fornecedor e previsão; o resto (etapa, quantidade, promessa, embarque, ETA, faixa, confiança) na
  dica ao passar o mouse e no Excel. As duas listas da tela (linhas previstas e pedidos) na barra de filtros nova.
- **Passo 7 — regras, LEIA-ME e testes**: REGRAS §3/§4/§9/§11; LEIA-ME com a etapa 19. Suíte verde, banco real intacto.

- **Ajuste final (pedido do usuário após a entrega)**: meta DES sem itens de montadora e sem os 58 de «já realizado antes do rastreio» — tudo do servidor
  (`goals.des_recebidos` só AMD…; `progress` ignora `prior_done` no DES; a tela Metas tira o campo do DES). Na cópia: 212 → **52** de 125.
  Os 55 do R-D («gostei» + pendente compras, contando pendente desenho do fornecedor): não fecham — na cópia e no servidor, R-D curtido com pendente
  compras numa aplicação não recebida = **129** (65 sem amostra comprada/enviada; 69 sem amostra comprada). Na tela: Redesenvolvimento → Controle
  «Pendente compras» + Curtidas «Curtidos» = 129.

**Etapa 19 concluída.** Pendente: no banco real, sincronizar uma vez (as linhas DES voltam ao tipo certo) e zerar o «já realizado antes do rastreio»
da meta DES na tela Metas, se fizer sentido (a data do servidor cobre o ano todo).
