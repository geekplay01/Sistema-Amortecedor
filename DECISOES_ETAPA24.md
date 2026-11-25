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
- [ ] Usuário: validar o fluxo de R-D na prática; depois, liberar a aba em Desenvolvimento.
