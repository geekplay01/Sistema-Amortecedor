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
