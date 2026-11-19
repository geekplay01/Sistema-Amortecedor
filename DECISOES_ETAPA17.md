# Etapa 17 — decisões (sessão de perguntas, 18/11/2026)

Pedido do usuário: design moderno em todos os módulos (cores do logo, ícones do mundo de peças, gráficos, filtros, formulários, transições, mensagens), filtros limpos ao sair do módulo, página visual do item, concorrentes do servidor, módulo Cobertura de concorrentes, Linha e híbrido/elétrico, BI03 (IPI, peso líquido, código de barras), sem posição/ID na interface e nomes de arquivo simples.

## Fatos levantados

- **Servidor:** `[POWERBI].[dbo].[DESENVOLVIMENTO_CONCORRENTES]` (tabela, 37.340 linhas): `ID` (= `DESENVOLVIMENTO_PRODUTOS.ID`), `COD_CONCORRENTE`, `CONCORRENTE`, `REFERENCIA`. Uma referência por ID × concorrente. Amortecedor (LINHA AMORTECEDOR e LINHA PESADA): 5.497 referências, 2.333 IDs, 1.548 códigos; 908 dos 914 do catálogo têm concorrente. Maior «concorrente»: OEM (11.938). Nomes duplicados: ISAPA (99 e 113), HIPPER FREIOS / HIPPERFREIOS, «N° INDISA», «N° URBA».
  - Mesma referência em vários IDs do mesmo código: 1.868 (mesmo item, várias aplicações). Mesma referência em 2+ códigos PERFECT: 146 (ex.: MONROE 27016 → 3). Mesmo código + concorrente com referências diferentes: 108.
  - Exemplo de divergência com o catálogo: AMD0100 NAKATA HG33066 (servidor) × HG33064 (CatalogoAMD).
- **Não existe BI03 no servidor.** O BI03 é a planilha `bases_exemplo\003(16-11).xls` (cadastro de produtos do Protheus, xls antigo, 95 MB, 53.363 linhas × 113 colunas; ler com xlrd ≈ 1 min). Colunas usadas: `Codigo`, `Tipo` (PA = acabado; MP- = matéria-prima), `Desc. Linha`, `Aliq. IPI`, `Peso Liquido`, `Cod Barras`. Amortecedor PA: 1.647 (+96 linha pesada). Tem os 914 do catálogo; 1.454 dos 1.864 códigos de DES/R-D como PA. Contra o app: EAN difere em 1, peso difere em 94 (ex.: AMD01110 2,10 × 4), 12 sem peso no app. IPI 10,4 ou 2,6.
- **CatalogoAMD.xlsx (18/11):** colunas novas **Linha** (ex.: LINHA LEVE, LINHA PICK-UP E UTILITÁRIOS) e **Hibrido ou elétrico**.
- **Fraga:** `bases_exemplo\LANÇAMENTOS 2026.xlsx` (75.850 veículos × ano de venda; marca, nome, modelo, início/fim de produção, Frota1960…Frota2031, frota por UF; sem código de peça). `Downloads\COFAP_AMORTECEDORES_x_FROTA.xlsx` (70.072 linhas: CodigoFraga, veículo, Frota2024, «Amortecedor PERFECT», «Amortecedor COFAP»).
  - DES em andamento (430): 364 acham frota pelo veículo + anos na LANÇAMENTOS; 111 pela referência COFAP no arquivo COFAP × Fraga. FROTA do servidor quase vazia nos itens em andamento (EM COTAÇÃO 101/290, FINALIZANDO CIT 4/272).
- **Logo:** azul-marinho `#202D56`, vermelho `#E72B3B`, laranja `#F6A019`, azul-claro `#64C4E9`; quatro faixas inclinadas.
- Fonte atual: Segoe UI do Windows. Gráficos: SVG feitos à mão. Filtros: `PSDTW.filtros` guarda a última visita em `localStorage`. Nome de arquivo: `exporter.friendly_name` («Perfect Shock Data - Módulo (filtros) - dd-mm-aaaa hhHmm.xlsx»).
- Nenhum status/sub-status «cadastro Protheus» no servidor.
- A ferramenta de busca da skill ui-ux-pro-max não está instalada no PC: recomendações de design vêm das regras gerais da skill.

## Decisões

| # | Tema | Decisão |
|---|------|---------|
| Q1 | Cores | Paleta do logo: azul-marinho no menu, títulos e botões principais; vermelho = ruptura/erro; laranja = risco/aviso; azul-claro = destaques e gráficos; verde só «OK». Quatro faixas inclinadas como detalhe (topo do menu, KPIs, carregamento). Temas claro e escuro. |
| Q17 | Tema claro | Mais legível: fundo `#F4F6FA`, cartões brancos com borda fina, texto `#1B2238` / secundário `#5A6378` (contraste ≥ 4,5:1), cabeçalho de tabela com fundo próprio, zebra suave, menu azul-marinho nos dois temas; conferir contraste em todas as telas. |
| Q2 | Fonte | Barlow (títulos, KPIs, números) salva em `static/fonts`; Segoe UI no texto e nas tabelas. Download autorizado. |
| Q3 | Ícones | Lucide (SVG, salvo no app) + 8–10 ícones próprios (amortecedor dianteiro/traseiro, mola, coxim, caixa, navio, contêiner, Inmetro, desenho técnico). Favicon/logo do menu: amortecedor estilizado nas cores PERFECT. Sem emoji. |
| Q4 | Densidade | Compacta confortável: tabelas 14 px / linhas 36 px; formulários 16 px / campos 40 px; espaçamento em múltiplos de 4 px. |
| Q5 | Gráficos | Chart.js 4 salvo no app (download autorizado): dicas, legenda, paleta, temas claro e escuro. |
| Q6 | Transições | Transição de página do navegador (150–200 ms), esqueleto enquanto carrega, menu parado, respeita «reduzir movimento». |
| Q7 | Mensagens | Aviso no canto (some em 4 s; erro só ao fechar); toda exclusão confirma em caixa do app dizendo o que apaga e se dá para desfazer; envio mostra progresso por arquivo. |
| Q8 | Filtros | Tela aberta pelo menu vem **limpa** (sai a memória da última visita). Filtros continuam na URL: Voltar do navegador e links entre telas abrem filtrados. |
| Q9 | Item | Página própria `/item/<código>` (Pesquisa e qualquer código clicável), índice fixo: topo (desenho/foto, selos sistema/família/linha/híbrido/lançamento), aplicações e lados, concorrentes e OEM, vendas 12 meses + curva ABC, estoque/cobertura/projeção, pedidos e chegadas, linha do tempo DES/R-D e amostras, garantia, desenhos, Inmetro, FOB, Brands, pendências/anomalias. Seção vazia recolhida com «sem registro». A ficha antiga sai. |
| Q10/Q18 | Fonte dos concorrentes | **Itens em desenvolvimento: servidor** (DESENVOLVIMENTO_CONCORRENTES pelo ID). **Itens do catálogo: CrossCatalogo.xlsx prevalece por item**; item do catálogo que não está no CrossCatalogo (ex.: acabou de virar ITEM RECEBIDO) usa o servidor, sem precisar atualizar a planilha. «Números Referência» do CatalogoAMD continuam. Anomalias ganha a aba **«Cross × servidor»** (mesmo concorrente com referência diferente). |
| Q11 | Universo | IDs de LINHA AMORTECEDOR e AMORTECEDOR LINHA PESADA, não bloqueados no ERP, qualquer status. Nomes iguais com grafia diferente viram um (ISAPA, HIPPER FREIOS); «N° INDISA»/«N° URBA» = INDISA/URBA. |
| Q19 | OEM | Separado como «Código original (montadora)»; aparece na página do item e na busca; não conta como concorrente na Cobertura. |
| Q20 | Repetidos | Listas com todas as linhas. Anomalias ganha a aba **«Concorrentes repetidos»**: mesma referência em 2+ códigos PERFECT (146) e mesmo código + concorrente com referências diferentes (108). Mesma referência em vários IDs do mesmo código (1.868) não é anomalia: aparece uma vez com «n aplicações». |
| Q12/Q13 | Cobertura de concorrentes | Módulo novo. Base: **só catálogo** — por concorrente: código dele, nosso código, descrição, aplicação, **curva ABC de vendas** do nosso item (universo do BI) e situação do estoque; código abre a página do item. Cartões por concorrente (códigos cobertos, quantos A/B/C), atalhos concorrente/curva/linha com contagem = lista, Excel com filtros. **Campo à parte: DES em andamento** com curva própria (Q27). |
| Q27 | Curva dos DES | Frota do item = soma da frota dos veículos da LANÇAMENTOS que batem com a aplicação (marca, nome do veículo, ano de venda dentro dos anos da aplicação; várias aplicações somam). Sem casamento: arquivo COFAP × Fraga pela referência COFAP do servidor; por último FROTA do servidor. A ≤ 80% da frota acumulada, B ≤ 95%, C o resto; sem frota = «sem dado». Mostra a origem e, na dica, os veículos. Selo «Lançamento» para veículo com início de produção ≥ 2024. |
| Q22 | Internet | «Dados de internet» = planilha LANÇAMENTOS 2026. |
| Q28 | Ano da frota | Frota do ano atual (Frota2026); muda sozinho na virada do ano. |
| Q23 | Universo da curva | DES em andamento: sem ITEM RECEBIDO, sem cancelado, não bloqueado (mesmo universo do «sem projeto»). R-D fora. |
| Q29 | Planilhas Fraga | O usuário copia `COFAP_AMORTECEDORES_x_FROTA.xlsx` para bases_exemplo. Ambas entram pela Atualização de dados (nomes «LANÇAMENTOS aaaa» e «…x_FROTA»), cada carga substitui a anterior, só as colunas usadas são guardadas. |
| Q14 | Linha e Híbrido | Campos do produto vindos do CatalogoAMD; filtro e atalho em Produtos, Pesquisa e Cobertura; selo na página do item; colunas no Excel. Híbrido vazio = «não informado». |
| Q15 | BI03 | Planilha «003(dd-mm).xls» pela Atualização de dados; só Tipo PA com Desc. Linha AMORTECEDOR / AMORTECEDOR LINHA PESADA. **Prevalece** em peso líquido e código de barras (catálogo e DES/R-D) sobre o CatalogoAMD. Diferenças com o CatalogoAMD (hoje 94 pesos, 1 EAN) numa aba de Anomalias. Os 12 «sem peso» fecham. |
| Q25 | IPI | IPI do servidor (DESENVOLVIMENTO_PRODUTOS) para DES/R-D e para os itens do catálogo que vieram do desenvolvimento; IPI do BI03 só para quem não tem linha no servidor. |
| Q24/Q30 | Pendente cadastro Protheus | Aba em Anomalias: DES/R-D em andamento (não recebidos, não cancelados, não bloqueados) que não estão no BI03 como PA; situação única «Pendente cadastro Protheus». Colunas: código, tipo, status, fornecedor, aplicação. Atalhos por tipo e status, Excel, contagem = lista. |
| Q16 | Posição e ID | Saem da interface (listas, ficha, filtros). Ordem padrão continua a do catálogo; Excel mantém as colunas. |
| Q16/Q26 | Nome dos arquivos | «PerfectAmortecedores - <nome da tela como no menu> - dd-mm.xlsx», sem filtros e sem hora; filtros seguem na aba «Filtros aplicados». |

## Ordem combinada (Q31/Q32)
1. Ajustes rápidos (nomes de arquivo, posição/ID, filtros limpos). 2. Dados (Linha/Híbrido, BI03, concorrentes do servidor, planilhas Fraga). 3. Base do design — começa por uma **página de prévia** (só na cópia) para aprovação. 4. Página do item. 5. Cobertura de concorrentes. 6. Revisão tela a tela.

## Checkpoints

### Passo 1 · nomes de arquivo, posição/ID e filtros limpos (18/11/2026) ✅
- `exporter.friendly_name` → «PerfectAmortecedores - <tela do menu> - dd-mm.xlsx» (LABELS = nomes do menu: Desenvolvimento, Redesenvolvimento, Estoque, Lados…); damping acrescenta o código do ensaio; CSV de Pedidos, Vendas e FOB via `PSDTW.nome`.
- `PSDTW.filtros`: só a URL; apaga o `psd-filtros-*` antigo do navegador. Saiu o aviso «filtros da última visita» das 14 telas, o `?limpo=1` do Dashboard e a aba lembrada de Anomalias (trocar de aba abre limpa).
- Posição no catálogo saiu de Produtos/Pesquisa, Aplicações, Comparação e ficha; «#» do ensaio saiu do Damping (lista, aviso e confirmação).
- Teste `test_30`. Na cópia: Produtos com `?system=gas` 772 → ao voltar pelo menu, 914 sem filtro; nenhum erro no console (Produtos, Aplicações, Metas, Damping, Anomalias, Dashboard).

### Passo 2a/2b · Linha, Híbrido e BI03 (18/11/2026) ✅
- CatalogoAMD: colunas «Linha» → `products.catalog_line` (maiúsculas) e «Hibrido ou elétrico» → `products.hybrid` ('S'/'N'; vazio = NULL = não informado). Coluna presente = a planilha manda, inclusive quando esvazia (`loaders._catalog_extras`). O peso/EAN da planilha fica em `cat_weight_kg`/`cat_ean`.
- Produtos/Pesquisa: filtros `linha` (`sem` = sem linha) e `hibrido` (S/N/nd), atalhos «Híbrido ou elétrico» e um por linha, coluna Linha e selo «híbrido/elétrico»; Excel com Linha e Híbrido.
- BI03 (`bi03.py`): planilha «003(dd-mm).xls» reconhecida pelo nome (`updater.ESPECIAIS`, logo depois do CatalogoAMD); lê só 6 colunas (~20 s, guardada em memória entre Verificar e Aplicar); guarda só PA de amortecedor (tabela `bi03`, substitui a carga anterior). Peso e EAN do BI03 gravados em `products` e mantidos quando o CatalogoAMD é reimportado; pendências «Campo ausente» de peso/EAN que o BI03 resolveu são fechadas. IPI: `bi03.ipi(código)` = servidor (`extra.IPI`), senão BI03.
- Anomalias: abas **«Peso e EAN × BI03»** e **«Pendente cadastro Protheus»** (atalhos de tipo e status, contagem = lista); Excel com as quatro abas.
- Testes: `test_modulos.CatalogoPlanilha.test_linha_e_hibrido`, `test_modulos.Bi03Protheus`.
- Na cópia (CatalogoAMD de 18/11 + 003(16-11)) — números abaixo: linhas Leve 678 · Pick-up e utilitários 157 · Pesada 79; híbrido/elétrico 25 (889 não). BI03: 1.743 PA de amortecedor, os 914 do catálogo; peso gravado em 106 produtos e EAN em 1; Anomalias «Peso e EAN» 95 (94 pesos + 1 EAN); «Pendente cadastro Protheus» 95, todos DES (88 EM COTAÇÃO, 7 PENDENTE PARTNUMBER FORNECEDOR). Pendências «sem peso» 12 → 0.

### Passo 2c · concorrentes do servidor (18/11/2026) ✅
- Sincronização: conjunto novo `concorrentes` (DESENVOLVIMENTO_CONCORRENTES → `ds_concorrentes`, 4 colunas, ~37 mil linhas, < 1 s). Depois da carga, `concorrentes.build()` liga cada referência ao código pelo ID (`rd_projects.extra.ID`) no universo amortecedor/linha pesada, não bloqueado no ERP, qualquer status → tabela `concorrentes`.
- Nomes unificados (`concorrentes.nome`: «N° INDISA» → INDISA, «HIPPERFREIOS» → HIPPER FREIOS); **OEM** marcado à parte (`is_oem`).
- Regra Q18 (`concorrentes.para_item`): catálogo com o item no CrossCatalogo → CrossCatalogo; catálogo sem ele ou item em desenvolvimento → servidor. A **busca** procura nas duas fontes (Produtos/Pesquisa, DES/R-D, busca reversa de Pedidos e Equivalências); a linha mostra a referência que casou.
- Compra de amostras e detalhe de DES/R-D: referências do servidor (`purchases.rd_cross_index`; a planilha antiga só se o servidor não tiver sincronizado).
- Anomalias: **«Cross × servidor»** (mesmo concorrente, nenhuma referência em comum) e **«Concorrentes repetidos»** (mesma referência em 2+ códigos; mesmo código e concorrente com 2+ referências). Excel com as abas.
- Teste `test_modulos.ConcorrentesServidor`.
- Na cópia (trazido do servidor só com SELECT): 37.355 linhas; 5.497 ligadas (3.643 de concorrentes em 1.010 códigos; 1.854 OEM em 1.268). Cross × servidor 241 (ex.: AMD0100 NAKATA HG33064 × HG33066); repetidos 156 + 61. Só 7 itens do catálogo não estão no CrossCatalogo e usam o servidor. Pesquisa «HG33066» → AMD0100 («NAKATA HG33066»).

### Passo 2d · planilhas da Fraga (18/11/2026) ✅
- `fraga.py`: «LANÇAMENTOS aaaa.xlsx» → `fraga_veiculos` (código Fraga, marca, veículo, modelo, ano de venda, início/fim de produção, status, classificação e a frota do **ano atual**, coluna «Frota<ano>»); «…x_FROTA.xlsx» → `fraga_pecas` (veículo × amortecedor COFAP/PERFECT, Frota2024). Reconhecidas pelo nome (`updater.ESPECIAIS`), leitura só das colunas usadas, cada carga substitui a anterior; a verificação não grava.
- Teste `test_modulos.FragaPlanilhas`.
- Na cópia: LANÇAMENTOS 2026 = 75.850 linhas, frota 2026 = 72,0 mi; COFAP × frota = 70.072 linhas (41.990 com COFAP, 27.385 com PERFECT). As duas juntas levam ~90 s (Verificar e Aplicar leem uma vez: a leitura fica em memória).
- **No banco real:** copiar `COFAP_AMORTECEDORES_x_FROTA.xlsx` de Downloads para bases_exemplo e aplicar as duas em Atualização de dados. A curva (Q27) usa essas tabelas no passo 5.

### Passo 3 · base do design e prévia (18/11/2026) — aguardando aprovação
- Recursos salvos no app (baixados do jsDelivr com autorização): Chart.js 4.4.4 (`static/vendor/chart.umd.js`, MIT), Barlow 500/600/700 (`static/fonts`, OFL), 62 ícones Lucide (`static/icons/lucide`, ISC) + 8 próprios (`static/icons/proprios`: amortecedor, amortecedor-dianteiro, mola, coxim, caixa-amortecedor, selo-inmetro, lançamento, vai-faltar). `tools/icones.py` gera o arquivo único `static/img/icones.svg` (70 ícones). Favicon novo: `static/img/favicon.svg`.
- `static/css/marca.css` (depois de style.css e tw-fallback.css): tokens do tema claro (fundo #F4F6FA, cartão branco, texto #1B2238/#5A6378, cabeçalho de tabela próprio, zebra) e escuro; menu azul-marinho nos dois temas com a faixa azul-clara no item atual; Barlow nos títulos e números; tabelas 14 px/36 px; campos 16 px/40 px; foco visível; avisos no canto; caixa de confirmação; esqueleto e carregamento com as faixas do logo; transição de página (view transitions, menu parado) e «reduzir movimento».
- `tools/tw_fallback.py`: a escala «blue» das telas virou a escala da marca (variáveis por tema); vermelho e laranja do logo; textos coloridos com variáveis por tema (contraste nos dois temas); `bg-thead`, `bg-navy`, `font-display`.
- `tw.js`: `kpi` novo (rótulo, número em Barlow, linha de baixo na cor do significado, ícone opcional), `table` com `psd-tbl` (zebra, cabeçalho próprio), `ico`, `toast`, `confirmar`, `carregando`, `esqueleto`, `grafico` (Chart.js com cores, fonte e grade do tema; redesenha ao trocar o tema).
- Menu e topo (`page.html`) com os ícones do arquivo único; `app.PAGES` guarda o nome do ícone. `.svg` também recebe `?v=` (ícone novo aparece ao reabrir o app).
- Prévia: `/guia-visual` (fora do menu; `app.HIDDEN`) com paleta, tipografia, ícones, KPIs, atalhos, filtros, formulário, tabela, gráficos, avisos, confirmação e carregamento (números de exemplo). Testes: `test_11` (menu, marca.css, Chart.js, ícones do menu no arquivo único, guia visual).
- Corrigido: botão que é link (ex.: «Baixar Excel») ficava com o texto na cor de link sobre o fundo azul.
- **Aprovado pelo usuário em 19/11/2026** («Aprovado, siga»).

### Passo 4 · página do item (19/11/2026) ✅
- `item.py` + `/api/item/<código>` + página `/item/<código>` (`telas/item.js`). Reúne: topo (desenho/miniatura, origem catálogo/DES/R-D, sistema, família, linha, híbrido, lançamento, curva ABC, situação do estoque, 4 KPIs), dados (EAN/peso do BI03, IPI, NCM, caixa, medidas), aplicações (catálogo + DES/R-D) e par de lados, concorrentes e OEM (regra Q18, com a fonte), vendas 12 meses (gráfico, curva ABC dos 12 meses fechados no universo do BI — `curva_abc.classes`), estoque/cobertura/projeção (gráfico saldo × chegadas), pedidos em aberto com chegada prevista e alertas, desenvolvimento (aplicações com início/pedido confirmado/amostras e mudanças de status), amostras, garantia (peças, ocorrências, % procedente, por ano, defeitos), desenhos/projeto, Inmetro, FOB com melhor preço, Brands, pendências e em quais abas de Anomalias o código aparece. Seção vazia = recolhida com «sem registro».
- A ficha antiga (janela) saiu: todo `data-ficha` abre `/item-id/<id>` → `/item/<código>` (Ctrl/botão do meio = nova aba). O menu do código clicável ganhou «Página do item»; o detalhe de DES/R-D tem o botão «Página do item».
- Desempenho: ~0,7 s por item (garantia por consulta direta ao código; estoque e curva em memória até a próxima sincronização). A 1ª abertura depois de sincronizar calcula a previsão (~13 s), como a tela Estoque.
- `tw.js`: gráfico misto (barra + linha) respeita o tipo de cada série.
- Teste `test_31`. Na cópia: AMD0637 (curva A, ruptura, 36 linhas de pedido, falta em nov/26 antes de chegar), AMD0100 (anomalia Cross × servidor), AMD0340 (só DES, pendente cadastro Protheus).

### Passo 5 · Cobertura de concorrentes (19/11/2026) ✅
- Tela nova `/cobertura` (menu 3 · Catálogo; `cobertura.py`, `telas/cobertura.js`, `/api/cobertura`, Excel `/api/export/cobertura.xlsx` com as abas Catálogo e Desenvolvimento).
- **Catálogo:** concorrente × referência × nosso código (só catálogo; referência pela regra Q18; OEM fora), com descrição, aplicação, linha, curva ABC de vendas (12 meses fechados, universo do BI) e situação do estoque. Cartões por concorrente (códigos cobertos e barra A/B/C; clique filtra), atalhos de curva e linha, busca; contagem = lista.
- **Desenvolvimento:** DES em andamento (sem ITEM RECEBIDO/cancelado, universo amortecedor, não bloqueado; R-D fora) com frota da Fraga pelo veículo e anos da aplicação (mesmo veículo × ano conta uma vez), reserva COFAP × Fraga e FROTA do servidor; curva A/B/C pela frota acumulada (80/95); selo Lançamento (início de produção ≥ 2024); gráfico das 15 maiores frotas; dica com os veículos que somaram.
- `estoque.mapa()`: linha do Estoque por código em memória (usada aqui e na página do item).
- Teste `test_32`. Na cópia: 3.956 referências de 17 concorrentes cobrindo 874 dos 914 itens (95,6%); COFAP 795 códigos (149 curva A). Desenvolvimento: 410 itens, 377 com frota (344 Fraga·veículos, 16 Fraga·COFAP, 17 servidor), frota somada 25,7 mi, curva A 65 · B 75 · C 237 · sem frota 33; 105 com lançamento. Maior: AMD0835 (Gol 2001–2016, 1,9 mi).

### Passo 6 · revisão tela a tela (19/11/2026) ✅
- Gráficos: `charts.js` mantém a interface (PSDCharts.gauge/funnel/bars/hbars/donut/line) e desenha pelo Chart.js com as cores da marca (cores antigas trocadas; verde só para «OK»). Dashboard, Metas, Pedidos, Vendas e Garantia mudaram sem mexer nas telas.
- Caixas do navegador: os 23 `alert`/`confirm`/`prompt` viraram `PSDTW.toast`/`PSDTW.erro` e `PSDTW.confirmar` (com campo para a nova senha). Exclusões (ensaio, desenho, envio, amostra, usuário, restaurar backup) dizem o que sai e se dá para desfazer; inclusões e exclusões mostram aviso no canto.
- Envio com progresso por arquivo (`PSDTW.enviar`): Desenhos e Atualização de dados.
- Diálogos antigos, botões, selos, avisos, tabelas `.tbl`, cartões do Dashboard e tela inicial reestilizados no `marca.css`. Damping: o nº do ensaio saiu também do cabeçalho do formulário.
- Curva ABC sem verde (A azul-marinho, B azul-claro, C cinza) na Cobertura e na página do item.
- `test_30` barra `alert`/`confirm`/`prompt` nas telas. Na cópia: as 27 telas abrem sem erro de script; gráficos via Chart.js no Dashboard (5), Metas (3), Vendas (3), Pedidos (2) e Garantia (1).
- LEIA-ME: seção da etapa 17 e passos no banco real.
- **Etapa 17 concluída** (passos 1 a 6).
