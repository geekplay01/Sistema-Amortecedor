# PERFECT Shock Data

App Flask de uso interno (um usuário, um PC Windows) para amortecedores PERFECT: catálogo, DES/R-D, amostras, lados, compras, vendas e lead time. A interface, os textos e os commits são em **português**.

- Regras de negócio, cada uma com o arquivo que a implementa: [`REGRAS_DE_NEGOCIO.md`](REGRAS_DE_NEGOCIO.md). Leia antes de mudar qualquer cálculo, contagem ou filtro.
- Plano e decisões da etapa em curso (ponto de retomada após `/compact`): [`DECISOES_ETAPA21.md`](DECISOES_ETAPA21.md). Ao fim de cada passo, registre ali o checkpoint. Etapas concluídas: [`16`](DECISOES_ETAPA16.md), [`17`](DECISOES_ETAPA17.md), [`18`](DECISOES_ETAPA18.md), [`19`](DECISOES_ETAPA19.md), [`20`](DECISOES_ETAPA20.md).
- Textos que explicam uma tela não vão na tela: ficam em `regras_telas.py` (Configurações › Regras das telas; a tela mostra só o link «Regras da tela»).
- **Design:** antes de qualquer mudança visual (cor, layout, componente, gráfico, texto de interface), leia [`DESIGN.md`](DESIGN.md) e siga-o. Decisão de design nova ou que muda uma regra de lá entra no `DESIGN.md` no mesmo commit.

## Rodar e testar

- Python: sempre `.venv\Scripts\python.exe` (o Python global não tem pandas). Não há pytest nem node.
- App: `iniciar.bat` (porta 5000). Para testar contra uma cópia do banco, defina `PSD_DB` com o caminho da cópia. Mesmo assim, `queries.backup_create` grava em `backups\` do projeto: apague o que o teste criar.
- Testes: `.venv\Scripts\python.exe tools\testes.py` (≈1 min; um módulo por processo; no fim confere o hash do banco real e acusa se mudou). Filtro: `tools\testes.py pipeline`. Fica verde antes de qualquer commit.
- **`database.DB_PATH` é lido na importação.** `PSD_DB` precisa estar definido antes de qualquer `import` do app; senão o código grava no banco REAL (já aconteceu: 11/11/2026, restaurado do backup). `tests/__init__.py` aponta para um banco temporário, e `seed_db.guard(db)` aborta se o caminho for o real.
- Testes de integração usam `tests/seed_db.py` (banco sintético, determinístico, sem usuários nem dados de servidor) + `tests/fake_server.py` (SQLite no papel do SQL Server). Nunca copie `data/perfect_shock.db` para teste.
- SQLite: `with sqlite3.connect(...)` não fecha a conexão (só commit). Use `database.session()` ou `try/finally c.close()`; conexão aberta prende o arquivo no Windows e trava outra conexão por 5 s.
- Front sem build: JS puro em `static/js`, Tailwind pré-compilado. Ao usar uma classe Tailwind nova no JS ou no template, rode `python tools/tw_fallback.py`, senão ela não tem estilo offline.
- Uma tela por arquivo em `static/js/telas/<tela>.js`: lê o que precisa de `window.PSD` (núcleo `core.js`) e se registra com `PSD.tela(slug, desenhar)`. Tela nova = arquivo novo + entrada na lista de `templates/page.html`. Dashboard/Metas vêm de `pages_new.js`; Pedidos/Vendas/Garantia/FOB de `pages_exec.js`.
- JS/CSS recebem `?v=<hora em que o app abriu>` (`app._asset_version`): reabrir o app basta para o navegador baixar a versão nova.
- PowerShell 5.1 come as aspas de `python -c "..."`: escreva o script em arquivo e rode o arquivo.
- **Mapa do código (graphify):** depois de cada mudança em `.py` ou `.js`, atualize o mapa antes de encerrar o turno: `$env:GRAPHIFY_QUERY_LOG_DISABLE='1'; & "$env:USERPROFILE\.graphify\Scripts\graphify.exe" update .` (local, sem IA; saída em `graphify-out/`, fora do Git). Para achar onde algo está ou o que depende de quê, consulte antes com `graphify.exe query "<termo>"`; leia o arquivo antes de editar.

## Servidor SQL (somente leitura)

- O SQL Server `POWERBI` só recebe `SELECT`: `data_pipeline.assert_select` barra o resto, e o servidor nunca grava no catálogo. Credenciais em `~/.perfect_shock_data/.env`, carregadas por `data_pipeline.load_env()`.
- As colunas reais das views divergem dos nomes esperados. Quando uma tela vier vazia, liste primeiro as colunas da view e só depois mexa na lógica; alias faltando vira NULL sem erro. Exemplos: vendas usa `DATA_FATUR` e `VALOR_TOTAL_CIPI`; embarques usa `ETA_ATUAL` e `DATA_CHEGADA_FILIAL`.
- Subconsulta entre `EMBARQUES_DETALHADO` e `PEDIDOS_COMPRA_DETALHADO` precisa de `COLLATE DATABASE_DEFAULT`, porque as collations diferem.
- O faturamento de referência do BI é `VALOR_TOTAL_CIPI` com `LINHA = 'AMORTECEDOR'` exata. Conferido: outubro/2026 = R$ 25.467.272,00.

## Dados e repositório

- O `CatalogoAMD.xlsx` é a fonte da verdade do catálogo e prevalece sobre o banco. DES/R-D vêm só do servidor.
- O repositório (`github.com/geekplay01/Sistema-Amortecedor`) recebe **somente código e documentos**. Banco, backups, planilhas e `.env` ficam no PC: o `.gitignore` já os exclui. Antes de cada commit, confira `git status`.
- Git: não está no PATH. Use o que vem com o GitHub Desktop: `%LOCALAPPDATA%\GitHubDesktop\app-*\resources\app\git\cmd\git.exe`.
