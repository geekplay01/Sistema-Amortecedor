# Etapa 16 — decisões (sessão de perguntas, 10/11/2026)

Arquivo vivo: cada rodada acrescenta o que foi decidido. Serve de ponto de retomada entre telas (após cada `/compact`).

## Rodada 1 — decidido

| # | Tema | Decisão |
|---|---|---|
| Q1 | Prioridade | Ordem a confirmar na rodada 2 (resposta: «D após B, depois C e D»). |
| Q2 | Usuários | Só o Italo, no próprio PC. SQLite continua. Sem multiusuário por enquanto. |
| Q3 | Sincronização | Tarefa agendada do Windows roda a sincronização diária mesmo com o app fechado. |
| Q4 | Stack do front | Flask + JS puro + Tailwind pré-compilado, sem build. `pages.js` (142 KB) vira um módulo por tela. Extras pedidos: filtros melhores; itens **curtidos** primeiro; filtro DES / R-D; campos novos da planilha do catálogo no formulário; sistema exibido como **FORCE GAS** / **FORCE OIL**. |
| Q5 | Padronização visual | Uma tela por vez para o design system Tailwind, sem quebrar o Jinja2; checkpoint ao fim de cada tela (o `/compact` é rodado pelo usuário). |
| Q6 | Rede de segurança | Corrigir as falhas de teste e deixar a suíte rápida antes de evoluir; revisar organização do código e usar skills instaladas para evitar erros futuros. |
| Q7 | Valor de vendas | Manter com IPI (`VALOR_TOTAL_CIPI`). Compra de amostras não entra no faturamento. |
| Q8 | Saldos parados | Sinalizar e gerar lista exportável por pedido. Nada é gravado no ERP. |

## Fatos levantados após a rodada 1

- **Vendas — o número de referência bate exatamente.** R$ 25.467.272,00 = `VALOR_TOTAL_CIPI` de **outubro/2026**, `LINHA = 'AMORTECEDOR'` (exato). Não é preciso tirar o IPI. Linha pesada (R$ 54 mil) e kit (R$ 11 mil) ficam fora desse número. O app hoje soma as três linhas (`LIKE '%AMORTECEDOR%'`) e mostra o acumulado do ano (R$ 187,7 mi), por isso parecia não bater.
- Na view de vendas, `TIPO_NF` só tem «NORMAL» em out/2026; nenhuma nota de amostra aparece ali.
- **Planilha CatalogoAMD.xlsx (nova)** — colunas: Código Produto, Descrição Produto, Grupo, Lançamento, Números Referência, Veículos, Produtos Relacionados, Cód. Barras, Cód. NCM, Peso (Kg), Qtd. Emb., Medida, Observação, **Sistema**, **Familia**, **Diametro Haste**.
  - Sistema: 772 «FORCE GAS» e **142 com o texto «Código Produto»** (erro de fórmula na planilha). A Observação dessas 142 diz FORCE OIL.
  - Família: Estrutural 448 · Semi-estrutural 231 · Convencional 217 · Cartucho 13 · Cabine 5.
  - Diâmetro da haste (mm): 20, 22, 12.5, 12.4, 15, 25, 18…
  - Lançamento «Sim»: 58 itens.
- «Curtiu» / «Não curtiu» já vêm do servidor (colunas CURTIU/NAO_CURTIU de DESENVOLVIMENTO_PRODUTOS) e aparecem na lista R-D, mas não ordenam nem filtram.
- O projeto **não é um repositório git** e não tem `CLAUDE.md`.

## Rodada 2 — decidido (11/11/2026)

| # | Tema | Decisão |
|---|---|---|
| Q9 | Ordem | 0 · base de testes e organização → **B** metas + DES/R-D (curtidas, filtros) → **D** qualidade (catálogo novo, sistema, saldos parados) → **C** vendas × estoque → **A** previsão de chegadas. |
| Q10 | Universo de vendas | Padrão = BI: `LINHA = 'AMORTECEDOR'` exata, `VALOR_TOTAL_CIPI` (com IPI). Linha pesada e kit só por seletor. Resumo: último mês fechado · mês atual parcial · acumulado do ano. |
| Q11 | Amostras | Nada a excluir das vendas (só notas NORMAL na view). Compra de amostras fica só nas telas de Amostras. |
| Q12 | Sistema | Lê a coluna N «Sistema»; valor inválido (ex.: «Código Produto») → usa a Observação; exibe **FORCE GAS** / **FORCE OIL** em telas, filtros e exports; pendência «Sistema inválido na planilha». |
| Q13 | Campos novos | Família, Diâmetro da haste e Lançamento na ficha, no formulário e como filtros (Produtos, Pesquisa); planilha prevalece. A coluna E «Números Referência» alimenta a busca por código de concorrente/OEM em Produtos. |
| Q14 | Curtidas | Listas DES e R-D: mais curtidos primeiro, desempate pelo status mais avançado; filtro Curtiu (todos / só curtidos / não curtidos). Filtro Tipo DES / R-D nas telas que misturam. |
| Q15 | Filtros | Barra única: busca, multisseleção, contagem, «limpar», filtros na URL, lembra o último uso. **«Pendente compras» é o filtro principal (atalho)**; clicar de novo no filtro ativo o limpa. |
| Q16 | Migração visual | Uma tela por etapa: DES/R-D → Metas → Produtos/Pesquisa/ficha → Lados → Amostras/Envio → demais. Checkpoint aqui ao fim de cada tela; o usuário roda `/compact`. |
| Q17 | Tarefa agendada | `schtasks` diário 06:30, usuário atual, só logado; arquivo de trava; não repete se já rodou no dia. |
| Q18 | Organização | Sim aos quatro (git, banco de teste pequeno + suíte rápida, `CLAUDE.md`, skills tdd / code-review / codebase-design). Versionamento numa **branch nova** em `github.com/geekplay01/Sistema-Amortecedor`. |
| Q19 | Saldos parados | Excel por pedido × código: pedido, fornecedor, código, descrição, saldo, emissão, dias sem embarque, última previsão, nº de adiamentos. Critério: 2× p90 da produção do fornecedor. |

## Fatos levantados após a rodada 2

- A busca de Produtos já acha código de concorrente/OEM sem pontuação (GP32530 = GP-32530 → AMD0100, «COFAP»). Hoje os códigos vêm quase todos do CrossCatalogo (3.945 concorrente + 1.096 OEM); a coluna E do CatalogoAMD só acrescentou 3 que faltavam — a mesma lista.
- **Git não está instalado neste PC** (nem GitHub Desktop/`gh`); há `winget`.
- O repositório `geekplay01/Sistema-Amortecedor` é **público** e hoje tem só `README.md` e `perfect_shock_data_etapa14.zip` na branch `main`.

## Checkpoints

### Passo 0a — rede de segurança dos testes (11/11/2026) ✅
- Suíte: ~18 min com 9 falhas → **61 s, tudo verde** (`tools\testes.py`).
- Causas das falhas: (1) `with conn()` não fechava a conexão → arquivo preso no Windows (3 erros); (2) `rules._setting_db` fazia `CREATE TABLE` dentro da migração → esperava 5 s pelo lock a cada `init_db` (também deixava a abertura do app 5 s mais lenta); (3) teste de integração copiava o banco real (sincronizações, usuário e garantias reais quebravam 3 testes); (4) `discover` misturava módulos no mesmo processo (test_04/test_13); (5) `test_importer` conferia contagens da planilha antiga.
- Correções: `database.session()`; leitura de configuração sem escrita; banco sintético `tests/seed_db.py`; `tests/__init__.py` + `seed_db.guard` (nenhum teste toca no banco real); `test_importer` vira unittest estrutural que pula sem `bases_exemplo`.
- **Incidente:** durante a troca para o banco sintético, uma rodada de teste gravou no banco real (ordem de import). Restaurado de `backups\pre_atualizacao_20261110_115132.db` — entre esse backup e o incidente só houve uma importação sem efeito (0 novos, 0 alterados). Cópia do estado afetado: `backups\poluido_pelo_teste_20261111_1035.db` (pode apagar depois de conferir o app).
- Próximo: passo 0b — tarefa agendada 06:30 + trava de sincronização.

### Passo 0b — sincronização com o app fechado (11/11/2026) ✅
- Tarefa «PERFECT Shock Data - sincronizacao diaria»: 06:30, usuário italo.cuellas, só logado, `StartWhenAvailable`, limite 1 h, janela minimizada → `sincronizar.bat` → `data_pipeline.py diaria`.
- `daily()`: só sincroniza se não houve OK no dia. Trava entre processos `data\sincronizacao.lock` (atômica; descartada após 45 min). Testes: `test_trava_entre_processos`, `test_diaria_nao_repete_no_mesmo_dia`.
- Teste real: disparada pelo Agendador às 11:20 → «pulada — já sincronizado hoje (11:11:27)», código 0. A primeira sincronização de fato pela tarefa será em 12/11 06:30 (conferir `data\sincronizacao_log.txt`).
- Backup antes do teste: `backups\pre_tarefa_agendada_20261111.db`.
- Próximo: passo 0c — quebrar `pages.js` em módulos por tela.

### Passo 0c — pages.js dividido por tela (11/11/2026) ✅
- `pages.js` (881 linhas, 142 KB) → `core.js` (utilitários, ficha, lista paginada, controle de status, miniaturas de desenho) + `telas/`: catalogo, desenvolvimento, desenhos, amostras, envio, lados, brands, dados. Divisão feita por script, código copiado sem alteração; cada linha conferida (foi para exatamente um lugar).
- Interface de cada tela: `PSD.tela(slug, desenhar)`; `page.html` carrega o núcleo, as telas e chama `PSD.iniciar()`.
- Fim do Ctrl+F5: JS/CSS com `?v=` da hora em que o app abriu.
- Verificado no navegador (cópia do banco, porta 5055): as 23 telas carregam com conteúdo e sem erro de script; ficha do produto, detalhe de DES/R-D, busca por concorrente (GP32530 → AMD0100) e painel do servidor funcionam.
### Etapa B · tela DES/R-D (11/11/2026) ✅
- API `rd.items`: ordem padrão curtidos → status mais avançado → código (`ordem=status|codigo`); filtro `curtiu=sim|sem|nao`; facets com `curtidos`/`nao_curtidos`. Excel segue os mesmos filtros e ordem.
- Tela em Tailwind (`telas/desenvolvimento.js`): KPIs, atalhos (Pendente compras em destaque, Curtidos, status) que ligam/desligam, filtros na URL + última visita (`PSDTW.filtros`, reutilizável), lote de controle de status, temas claro/escuro verificados.
- Observação para a etapa D: em R-D, 760 de 790 itens têm «Pendente compras» no sub status, inclusive 766 já recebidos — provável sub status velho no servidor.
- Próximo: Metas (migração visual + filtro DES/R-D).

### Etapa B · tela Metas & Validação (11/11/2026) ✅
- Tela própria `telas/metas.js` (saiu de `pages_new.js`; `PSDTW.validationBlock` removido). Filtros na URL + última visita: `year`, `tipo` (des/rd; chip ativo clicado de novo limpa; «Todos»), `conta` (sim/nao) na lista de recebidos.
- Tipo filtra KPIs de validação, série mensal, cartões de meta, lista de recebidos (`/api/goals/events?kind=`) e esconde «Validações R-D» quando o tipo é DES.
- `/api/goals/events` passou a aceitar `limit` (antes cortava em 80 sem avisar: eram 341 recebidos em 2026). A tela pede a lista inteira; os contadores «conta / não conta» agora são exatos.
- Percentuais em pt-BR (65,6%). Corrigido o texto da base «item recebido» do cartão DES (lia `recebidos_no_ano`, campo que não existe).
- Observação: na base «validação», a coluna «Conta?» de R-D segue a regra de recebimento (0 de 168 em 2026) — a meta R-D soma validações (197). A tela explica isso no cartão; regra não alterada.
- Próximo: Produtos/Pesquisa/ficha (Q13: Família, Diâmetro da haste, Lançamento; busca pela coluna E).

### Etapa B · Produtos, Pesquisa e ficha (11/11/2026) ✅
- Importação do CatalogoAMD (`loaders.L_catalogo`): lê **Sistema** (FORCE GAS/OIL; inválido → usa a Observação e abre pendência `campo_invalido/sistema`, que some quando a planilha é corrigida), **Familia** (gravada em maiúsculas, igual aos certificados Inmetro, para não gerar conflito falso), **Diametro Haste** (`dimensions.rod_diameter_mm`) e **Lançamento** (coluna presente e vazia = «N»). Aliases novos em `importer.ALIASES`.
- A planilha atual já vem corrigida: 772 FORCE GAS + 142 FORCE OIL (os 142 «Código Produto» da rodada 1 sumiram). Hoje o banco real tem 141 itens sem sistema e nenhum Ø de haste: **é preciso reimportar o CatalogoAMD** (Atualizar bases) para os campos aparecerem. Na cópia de teste a reimportação atualizou 146 produtos, sem conflito.
- API: `/api/products` filtra `family`, `rod`, `launch` (S/N) e `system`; `/api/products/facets` dá as opções com contagem. Excel de Produtos/Pesquisa com Ø haste e Lançamento, sistema como FORCE GAS/OIL, filtros legíveis no nome e na aba «Filtros aplicados».
- Telas `telas/produtos.js` (Produtos e Pesquisa, saíram de `catalogo.js`): KPIs, atalhos que ligam/desligam (Lançamentos, FORCE GAS, FORCE OIL, cada família), filtros na URL + última visita, referência que casou na busca (coluna E já alimentava a busca: GP32530 → AMD0100 «COFAP»). Pesquisa mantém aplicação, código por tipo, origem e os blocos DES/R-D.
- Ficha: topo com Sistema, Família, Ø haste, Lançamento e posição em destaque; dados em grade Tailwind. Seções (códigos, aplicações…) seguem no estilo antigo.
- Não existe formulário de edição de produto (o catálogo vem só da planilha, que prevalece): «no formulário» do Q13 ficou como ficha + filtros.
- Sistema exibido como FORCE GAS / FORCE OIL em todo o app (`SYS` no núcleo, Dashboard, Excel).
- Próximo: Lados.

### Item inativado sai de DES/R-D pelo bloqueio do ERP (11/11/2026) ✅
- DES e R-D com «os mesmos produtos» eram 182 pares parecidos (mesma descrição/veículo, códigos diferentes): está certo. O problema real eram AMD0184/AMD0185, inativados pelo usuário mas ainda vindos de `DESENVOLVIMENTO_PRODUTOS` (a view não tem coluna de situação).
- Decisão do usuário: inativar = **bloquear no ERP**. Novo conjunto `situacao` na sincronização (`ESTOQUE_ANALISE_REPOSICAO`, só LINHA amortecedor, só código/ATIVO/BLOQ/LINHA, sem `extra`) → `ds_situacao`; `rules.desc_sql` exclui bloqueado/inativo de listas e contadores; metas não mudam.
- Na cópia: 2.059 códigos lidos, 68 bloqueados; saem 10 de DES e 7 de R-D. AMD0184/0185 ainda vinham BLOQ=NAO na view no dia do bloqueio (a view do POWERBI deve atualizar em lote): saem na sincronização seguinte à atualização.

### Etapa B · tela Lados (11/11/2026) ✅
- `telas/lados.js` em Tailwind: 4 KPIs (escopo, traseiro confirmado, dianteiro SEM traseiro, sem par), legenda das 5 fontes do outro eixo na ordem de confiança, atalhos que ligam/desligam (cada atalho troca os outros; o select combina), filtros com contagem, «Limpar filtros» mantém o escopo, filtros na URL + última visita, Excel com os mesmos filtros.
- Candidato do outro eixo fora do catálogo abre a lista certa (DES ou R-D pelo tipo do servidor; antes ia sempre para DES). Situação «inativo/em breve» aparece ao lado do código.
- API `/api/sides`: `stats` ganhou `com_par`, `direito`, `esquerdo`, `ativo`, `em_breve`, `inativo`. Teste `test_19`: cada número da tela = total da lista com o filtro do atalho, nos dois escopos.
- `PSDTW.filtros`: o aviso «filtros da última visita» some na primeira mudança de filtro (antes ficava até recarregar, inclusive depois de «Limpar»). Vale para DES/R-D, Metas, Produtos/Pesquisa e Lados.
- Na cópia: 354 itens com lados (346 pares da planilha + 8 automáticos, nenhum sem par), 308 dianteiros com traseiro confirmado, 4 sem traseiro; `/api/sides` ≈ 0,4 s.
- Próximo: Amostras/Envio.

- (plano anterior) **B** — Desenvolvimento/Redesenvolvimento (curtidas primeiro, filtro Curtiu, «Pendente compras» como atalho que liga/desliga, barra de filtros na URL) e migração visual dessa tela.
