# Etapa 24 — Excel da Pesquisa e módulo Validação (25/11/2026)

Pedido: (1) o Excel da Pesquisa de amortecedores com todos os dados, inclusive caixa e medidas da caixa, e o item selecionado no nome do arquivo;
(2) preparar o módulo **Validação** e a aba «Validar itens» em Desenvolvimento e Redesenvolvimento (primeiro Redesenvolvimento): desenho PERFECT
(com limpeza da máscara) × desenho do fornecedor, família do amortecedor, medidas lidas e nomeadas em inglês, aprovação e o F-008 em xlsx e pdf;
desenho aprovado sobe para Desenhos.

## Fatos levantados

- Excel da Pesquisa = o mesmo de Produtos (24 colunas), sem caixa, curso, Ø tubo, fixações nem NCM, e sem os itens de DES/R-D que a busca acha.
- Modelos F-008 em `bases_exemplo\VALIDATION`, um por família: Cartucho (10 medidas), Convencional (16), Estrutural (21), Semi-estrutural (14) e
  Semi-estrutural interferência (19). Cabine não tem modelo. Abas: «T. Validação - Validation test» (Nº, Note, OEM or Reference = F, Drawing or
  supplier = I, Tol.(+) = L, Tol.(−) = M, Ap = fórmula N, Improve = O; imagem da referência em S10:AJ34 e do fornecedor abaixo de A35;
  conclusão X em S50/S52), «Validation test - DampingForce», «Dados» (B9 código … B26 tipo), «Certificado», «Embalagem».
- Os PDFs de desenho não têm texto (imagem ou traço). O OCR do Windows (offline) leu mal («Lmax:553t3», «0189» por Ø189) e não leu cotas verticais.
- O Excel do PC gera PDF (COM). DES/R-D vêm só do servidor (somente leitura): o status da validação no servidor não muda pelo app.

## Decisões (grill, rodada 1)

| # | Tema | Decisão |
|---|---|---|
| Q1 | Colunas da Pesquisa | Caixa + «Medidas da caixa (C x L x A, mm)» em outra coluna; curso, comprimento do corpo, Ø tubo, fixações (com medidas), NCM, descrições em inglês e espanhol, nº Inmetro; abas «Aplicações» e «DES e R-D» |
| Q2 | Nome do arquivo | Na Pesquisa, o item selecionado (código buscado; montadora, modelo e ano) entra no nome; as outras telas seguem a etapa 17 |
| Q3 | Leitura das medidas | **API do Claude**: lê os dois desenhos e lista as medidas; não aprova nada, a aprovação é do usuário |
| Q4 | Desenho PERFECT | Enviado na hora; abre numa ferramenta de seleção para apagar (Delete) ou limpar a máscara |
| Q5 | Família | Os 5 modelos de `bases_exemplo\VALIDATION`, medidas da coluna B na ordem; linhas livres com nome digitado |
| Q6 | F-008 | Como a foto de referência do usuário: desenho PERFECT em «Drawing image and/or picture of OEM/Reference», do fornecedor em «Drawing image and/or Sample received»; PERFECT na coluna F, fornecedor na I; texto compara como texto |
| Q7 | Damping force | Entra no mesmo fluxo (aba DampingForce do modelo) |
| Q8 | Aprovação | A/R por linha como no modelo (OK/N força); Aprovar ou Reprovar marca o X; as duas geram xlsx e pdf; só Aprovar sobe o desenho |
| Q9 | Nome e dados | `F-008 - Validation Test - Rev.00 - <CÓD PERFECT> - <FORNECEDOR> - <CÓD FORNECEDOR> - REV.00`, sem alterar; aba Dados preenchida; PDF pelo Excel; arquivos em `data\validacoes\` |
| Q10 | Desenhos | Sobe o PDF original do fornecedor (`RED - <cód> - <forn> - <cód forn> - REV.00.pdf`), origem «Validação» |
| Q11 | Aba em R-D | «Validar itens» com «Iniciar validação», que abre a bancada; rascunho salvo; DES depois que o fluxo de R-D for aprovado |
| Q12 | Menu | Tela «Validação» no menu com todas as validações, controles no padrão das outras telas; clicar abre a mesma bancada (skill `frontend-design`) |
| Q13 | Maquete | Antes de programar: `maquetes/etapa24_validacao_{claro,escuro}.png` |

## Decisões (grill, rodada 2 — «Sim, aprovo tudo», com a maquete)

| # | Tema | Decisão |
|---|---|---|
| R1 | Chave da API | `ANTHROPIC_API_KEY` no `~/.perfect_shock_data/.env` (o usuário coloca); Claude Opus 5.5; sem chave, medidas digitadas |
| R2 | Marcas | Na tela, número nos dois desenhos e nome em inglês na tabela/ao passar o mouse; no F-008 como a foto: números no desenho do fornecedor, PERFECT só com a máscara limpa |
| R3 | Posição | O Claude devolve a posição aproximada; arrastar corrige; clicar no número da linha e depois no desenho cria a marca |
| R4 | Improve | Linha R recebe «CHANGE TO <valor PERFECT>», editável |
| R5 | Máscara | Seleção retangular; Delete apaga; «Manter só a seleção»; Desfazer; versão limpa só na validação |
| R6 | Cabeçalho | Data de recebimento informada (hoje por padrão); revisões 0; departamento e assinaturas como no modelo |

Decididos na implementação (registrados aqui):
- Desenho aprovado entra em Desenhos como **revisão vigente** (uma acima da maior do código), mantendo o nome «… - REV.00» pedido; senão um desenho novo REV.00 ficaria atrás da revisão antiga do fornecedor anterior.
- Os modelos têm **duas fórmulas de damping** (Cartucho = faixa; demais = diferença relativa); a tela usa a do modelo da família.
- Texto diferente sem tolerância (ex.: PA6 × PLASTIC) vai ao F-008 com «N» na Tol.(+), porque a fórmula do modelo daria #VALOR!.
- A máscara é guardada como lista de operações e aplicada no servidor sobre o desenho original (o «Desfazer» funciona depois de reabrir).
- Instalar o SDK `anthropic` no .venv ficou com o usuário (a instalação automática foi bloqueada aqui); o app avisa na bancada o que falta.

## Checkpoints

- [x] Excel da Pesquisa (Q1–Q2): `exporter._pesquisa` e `_selecao`; teste `test_27b`; conferido na cópia (AMD0128: caixa PP014, «610 x 130 x 75»; FIAT TORO: 5 produtos, 14 DES/R-D, nome com «FIAT TORO»). Suíte de integração verde.
- [x] Maquete da Validação (tela do menu, aba de R-D, passos 1 a 4) nos dois temas; aprovada.
- [x] `validacao.py` (tabela `validacoes`, SCHEMA_V8), rotas `/api/validacao…`, tela `telas/validacao.js`, aba no R-D, menu, Excel da lista, CSS (`.psd-banc` …), ícones (clipboard-check, eraser, crop, square-dashed), regras das telas, DESIGN.md §3/§6.4c/§7, REGRAS §13.
- [x] Testes: `tests/test_validacao.py` (regras A/R e damping, famílias, fluxo completo com dublê do Claude, máscara, F-008, Desenhos) e `test_38` (rotas). Suíte 5/5 verde.
- [x] Conferido na cópia (porta 5055): aba Validar itens (65 pendentes), bancada AMD0100 com os desenhos reais (E-WIN como PERFECT, ZS DQ41746), máscara por arrastar + Delete + Ctrl+Z, linha ↔ cotas, Ap ao digitar, passo 4, lista e Excel. PDF pelo Excel do PC: 2 páginas, layout como a foto (`maquetes/etapa24_F-008_exemplo.pdf`).
- [x] Commit `1a155c2`, push conferido (origin/etapa-16).

## Ajuste (25/11/2026) — sem a API

O usuário instalou o SDK, mas não tem chave da API e perguntou se dava para não usar a API. Teste do OCR do Windows (offline) em 15 recortes ampliados das cotas reais:
não leu «Lmax=553±3» (nem com traço engrossado), trocou «S=157» por «S:151», «Lmax=577±3» por «Lmox-577*3» e «365±3» (ZS) por «55±3»; acertou só 3 cotas do desenho vetorial.

| # | Pergunta | Decisão («Sim para todas») |
|---|---|---|
| Q1 | Como entram as medidas sem API | Digitação no desenho: linha marcada, clique na cota abre o campo ali, Enter grava e passa à próxima; sem OCR |
| Q2 | Zoom | Roda do mouse, arrastar para mover, «+ − Ajustar» e tela cheia |
| Q3 | Leitura pelo Claude | Fica, mas desligada por padrão: chave em Configurações › Regras de negócio («Ler medidas com o Claude (API) na Validação») |
| Q4 | SDK e LEIA-ME | `anthropic` opcional no requirements; LEIA-ME com os passos da API só como opcionais |

- [x] `rules.validacao_ia` + `/api/settings` + Configurações; `validacao.ia_disponivel` desligada não oferece nem chama a API (teste garante que `_chamar_claude` não é chamado).
- [x] Passo 3: «Digitar no desenho», campo no ponto (`.psd-vpop`, «553±3» separa as tolerâncias), avanço de linha, zoom/arrastar, tela cheia (bloco vai para o `<body>`), Esc em camadas.
- [x] Conferido na cópia: LMAX digitado no PERFECT com zoom (553 / 3 / −3, número no desenho, avançou para LMIN); LMIN do fornecedor em tela cheia (gravado com a posição); Esc fechou a tela cheia; Configurações mostra a opção desligada. Testes verdes.
- [x] Commit `24ab28b`, push conferido.

## Ajuste 2 (25/11/2026) — mola, marcação rápida, animação das chaves, damping e velocidade

Medido na cópia antes: bancada 20 ms; contagem «Validar itens» 0,5–0,9 s a cada abertura do R-D; lista da Validação 0,7 s (3,9 s na 1ª); desenhos de 800 KB
baixados de novo a cada gravação que redesenha. Achado na conferência: o ouvinte de cliques do passo 3 ficava em `#vbc` e se acumulava a cada troca de passo
(«Pular linha» pulava várias linhas, «Sobrepor» abria duas vezes) — provável parte dos «bugs» sentidos.

| # | Pergunta | Decisão («Sim para todas») |
|---|---|---|
| Q1 | Item com mola | Chave no passo 2; LMAX2 logo abaixo do LMAX; sai ao desligar |
| Q2 | Marcar mais rápido | «Só marcar» (padrão) \| «Marcar e digitar»; Ctrl+Z; duplo clique abre o valor |
| Q3 | Nome da cota | Editável na tabela, só nesta validação, vai para o F-008 |
| Q4 | Animação das chaves | Destaque desliza (0,2 s) em toda `.psd-seg`/`.psd-linha` do app; abas do R-D sem recarregar |
| Q5 | Damping | Enter → valor ao lado; Shift+Enter volta; colar preenche a linha; «±» guarda o nominal |
| Q6 | Velocidade | Pendentes guardados até o banco mudar (e calculados ao abrir); imagem leve 1600 px com chave estável |
| Q7 | Seguir | «Sobrepor» agora; teste do PaddleOCR depois (instalação pelo usuário); DXF com os fornecedores |

- [x] Feito e conferido na cópia: mola (LMAX, LMAX2, LMIN), só marcar + Ctrl+Z, nome trocado gravado, duplo clique → 553/3/−3, damping (Enter, colar, ±),
  sobrepor (abre, fecha com Esc, um só), abas sem recarregar com o destaque deslizando, ouvinte do passo 3 corrigido. Testes verdes.
- Node.js 26.13.1 portátil instalado em `%LOCALAPPDATA%\nodejs` (sem administrador; fora do PATH) para o `npx skills find`.
- [x] Commit `4b7126c`.

## Ajuste 3 (25/11/2026) — par LD/LE, lançamento mais rápido, skills e sugestões

Fatos (cópia): 65 pendentes de validação no R-D; 26 com lados e par (todos pela planilha Lados), 33 LD/LE num item só, 6 fora do catálogo; nos exemplos o par
também está pendente (AMD0138/0139, AMD0928/0929, AMD1714/1715).

| # | Pergunta | Decisão |
|---|---|---|
| Q1 | O que o par recebe | Tudo (família, mola, medidas, tolerâncias, melhorias, damping, conferência, fornecedor) e a decisão |
| Q2 | Desenhos do par | PERFECT do vigente do par em Desenhos; fornecedor enviado; posições copiadas, «Espelhar posições» |
| Q3 | Quando conclui | Convite «Validar também …?» ao concluir; o usuário conclui o par (mesma decisão em destaque) |
| Q4 | Código do fornecedor | **Do nome do arquivo do desenho, nos dois lados** (resposta do usuário) |
| Q5 | Lançamento | PERFECT já preenchido, posições reaproveitadas, tabela como planilha |
| Q6 | Skills | `refactoring-ui` e `database-schema-designer` instaladas em `.claude/skills` (fora do Git; só texto) |
| Q7 | Arquitetura e design | Etapa 25 (abaixo) |

- [x] `ler_nome`, `_preencher_perfect`, `par`, `preparar_par`, `_fonte_posicoes` (reaproveitar), espelhar; bancada com aviso do par, link no cabeçalho, convite ao concluir,
  decisão em destaque; tabela como planilha. Correção: validação nova começa com a pasta vazia (o SQLite reaproveita o número de uma apagada).
- [x] Conferido na cópia: AMD0138 (LD) com código lido do nome (ZS, DQ41746) e PERFECT do catálogo; concluída → AMD0139 (LE) pronta, com o PERFECT vigente dela,
  aviso e «Espelhar»; Enter desce na coluna; colar coluna; «Abrir AMD0139» no lado concluído. Testes verdes.

### Sugestões para a etapa 25 (levantadas pelo mapa do código)
- Arquitetura: `app.py` (716 linhas, quase todas as rotas) em Blueprints por módulo; `validacao.js` (≈ 500 linhas) em um arquivo por passo; `q()`/`q1()` (130 e 80 ligações) com consultas por domínio.
- Dados: medidas da validação em tabela própria (hoje JSON) para o painel de reprovações; visão «item» (catálogo + DES/R-D + desenhos + validações pelo código, hoje texto solto em ~8 tabelas); FTS5 na busca rápida.
- Design: painel da Validação (reprovação por fornecedor, medidas que mais falham, tempo por validação); Ctrl+K; terminar a migração do `style.css` antigo.
- Lançamento (ficaram para depois): botões «= PERFECT» e «OK» por linha; importar a tabela de medidas do fornecedor (Excel/CSV); ler DXF; teste do PaddleOCR.

- [ ] Usuário: validar o fluxo de R-D na prática (inclusive um par LD/LE); depois, liberar a aba em Desenvolvimento.

## Update 4 (25/11/2026) — «Sim para todas» (Q1–Q9)

| # | Pedido | Decisão |
|---|---|---|
| Q1 | Abrir sem o cmd | `pythonw`; atalho `PERFECT Shock Data.vbs`; botão «Fechar o sistema»; uma instância; log em `data\app_log.txt` |
| Q2 | Damping no F-008 | Recorte da tabela de damping de cada desenho (passo 4) para a aba DampingForce |
| Q3 | Rodinha | Rodinha apertada arrasta o desenho; rodinha gira = zoom; clique esquerdo marca |
| Q4 | Excluir | Qualquer validação; o arquivo em Desenhos fica |
| Q5 | Revisões | «Nova revisão» Rev.01… no lugar de duplicar; último REV do nome e TEST REVISION (B25); lista agrupada |
| Q6 | Marcadores no Excel | Caixas de texto («Medida n») pelo Excel do PC; sem Excel, pintados |
| Q7 | Anomalias | Descrição e aplicação em todas as abas e no Excel |
| Q8 | Planilhas | Arrastar e soltar + Ctrl+V em todos os módulos que recebem planilha |
| Q9 | Gráficos | Revisão com a skill `dataviz`; maquete antes/depois para aprovação |

- [x] Q1, Q4/Q5, Q3, Q2 (recorte; CSS do passo 4), Q6 (conferido no Excel do PC: 7 caixas, PDF gerado). Testes de validação verdes.
- [x] **Incidente (25/11/2026):** a prévia com o banco de cópia gravava em `data\validacoes` (mesmos números) e a limpeza da demonstração apagou as pastas
  das validações reais 1 (AMD0453) e 3 (AMD0456). Restauradas a partir dos originais em Downloads (desenhos, máscara refeita pelo banco, F-008 xlsx/pdf
  refeitos; o banco não foi tocado). Correção: `database.DATA_DIR` = pasta do banco; validações, desenhos e fotos ficam ao lado dele (teste novo).
- [x] Q7: `anomalias.itens`/`com_itens` (catálogo; sem catálogo, DES/R-D) — descrição e aplicação em todas as abas (repetidos e corrigido: por código) e no Excel. Teste.
- [x] Q8: `PSDTW.zonaPlanilha` + `ligarPlanilha` (clique, arrastar, Ctrl+V de arquivo, filtro de extensão) em Atualização de dados, FOB, Vendas (BI),
  Damping (regra) e Importação de Excel (a página carrega o `tw.js`). Conferido no navegador (colar .txt recusa; soltar .xlsx envia).
- [x] Q9 (26/11/2026): maquete aprovada («Aprovo, aplicar») e aplicada. Paleta nova em `--chart-1..7` + `--chart-1s` + `--chart-trilho` (validada nos dois
  temas); padrões em `PSDTW.grafico` (barra ≤ 24 px e ponta de 4 px, pilha com vão de 2 px, linha de 2 px monótona com bolinha só no fim, grade só no eixo
  dos valores, legenda só com 2+ séries, rótulo seletivo, cursor, divisória); `PSDTW.segmentos` (rosca → barra segmentada) e `PSDTW.medidor` (meia-rosca →
  medidor). Telas: Dashboard, Metas, Vendas (+ tabela por classe), Pedidos (cor do fornecedor = selo da tabela; trio ZS/E-WIN/XGM validado), Garantia
  (Pareto com um eixo e divisória 80%; ano anterior em cinza), Item, Cobertura (curva em degraus de azul + legenda), Guia visual. Achados na conferência:
  as cores dos eixos não trocavam com o tema (agora lidas do token a cada desenho), linha suavizada furava o zero (monótona), rótulo da última barra
  cortado (preso ao quadro), nomes pulados no ranking deitado. Conferido no navegador (cópia, porta 5055), claro e escuro, e a troca de tema ao vivo.
- [x] Documentação do Update 4: DESIGN.md (§3, §6.1 botão Fechar, §6.4 item identificado, §6.4c rodinha/recorte/revisões, §6.5 envio de planilha,
  §6.6 gráficos reescrita, §10), REGRAS_DE_NEGOCIO (§2 Anomalias, §12 gráficos, §13 Update 4, abertura, planilhas), `regras_telas.py` (Garantia, Validação), LEIA-ME.
