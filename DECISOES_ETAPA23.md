# Etapa 23 — Revisão de design: tirar a cara de IA (24/11/2026)

Pedido: «quero uma skill para melhorar o design do projeto, para tirar a cara de IA» → instalada a skill `frontend-design` (anthropics/skills, em
`.claude/skills`, fora do Git) e feita a revisão do app com ela.

## Fatos levantados (Dashboard, Desenvolvimento e Estoque na cópia do banco; contagem no código das telas)

- **Caixas iguais em tudo**: Dashboard com 14 cartões do mesmo tamanho, raio, sombra e faixa em degradê (10 atalhos); Desenvolvimento com 13 caixas
  antes da lista (4 KPIs + 6 estágios + 3 sub status).
- **Rótulos em CAIXA ALTA espaçada** em cartões, títulos de bloco, grupos do menu e cabeçalhos de tabela (≈ 36 caixas-altas e 60 espaçamentos de letra),
  prescritos pelo próprio DESIGN.md §4.
- **Textos emendados com «·»**: 222 na interface (fora de comentários); na tela de Desenvolvimento, uma linha explicava a regra
  («contagem em… clique para filtrar…»), contra o §2.3.
- **Números repetidos e degradês**: 337 e 527 duas vezes no Desenvolvimento (contra o §2.2); degradê na faixa dos atalhos, no avatar do escuro (violeta
  `#6D4FD8`, fora da marca) e na barra de prazo dos pedidos (contra o §5).
- Mantido: paleta da marca, Barlow + Segoe UI, numeração do menu (é uma sequência real), movimento contido, modo escuro da etapa 22.

## Decisões (grill + maquete `maquetes/etapa23_design_{claro,escuro}.png`, aprovada «Aprovada, aplicar»)

| # | Tema | Decisão |
|---|---|---|
| Q1 | Onde começar | Nos componentes comuns (`tw.js`, `marca.css`), conferindo primeiro Dashboard e Desenvolvimento |
| Q2 | Rótulos | Caixa normal, Barlow 600 13 px (`.psd-rot`); status do servidor continuam como o servidor manda. Nos botões de estágio, o nome em caixa normal com siglas (CIT) |
| Q3 | «·» | Uma informação por linha (linha de apoio do KPI: `PSDTW.kpi` troca « · » por quebra) ou vírgula em lista; numeração de etapas («1 · Em produção») e títulos de aba do navegador ficam. «N itens · N códigos» mostra um número só quando são iguais. A regra da tela foi para `regras_telas.py` |
| Q4 | Números | KPIs vizinhos = uma faixa só, dividida por linhas finas (CSS no contêiner, sem mudar as telas); sem a linha colorida embaixo; só alerta (vermelho/laranja) muda a cor do número. DES/R-D: sem a fileira de KPIs; os estágios são a faixa («Curtidos» e «Pendente compras» ficam nos atalhos) |
| Q5 | Atalhos do Dashboard | Lista em duas colunas (número, nome, descrição); primeiro o que pede ação, depois os cadastros; zerados no fim, apagados; sem sombra, faixa nem «pulo» no hover |
| Q6 | Degradês | Barra de prazo laranja lisa; avatar do escuro no azul da marca; fundo da tela inicial continua (vitrine) |
| Q7 | Único destaque | A faixa inclinada do logo (`--inc`, paralelogramo azul-claro) marca o que está selecionado: estágio, item atual do menu, opção do seletor de linha e do seletor segmentado |

## Checkpoints

- [x] Skill `frontend-design` instalada; revisão e maquete (claro e escuro) aprovadas.
- [x] `marca.css`: rótulos, faixa de KPIs, estágios, atalhos, faixa inclinada, sem degradê. `tw.js`: KPI e cabeçalho de tabela. Telas: 25 arquivos sem «·» em texto de tela.
- [x] Desenvolvimento/Redesenvolvimento sem a fileira de KPIs; Dashboard com a lista de atalhos (`app.CARDS` reordenado; zerados no fim por `app.js`).
- [x] Conferido na cópia (porta 5055): 27 telas sem erro de JavaScript e sem rótulo em caixa alta; Dashboard, Desenvolvimento (clique no estágio filtra e marca), Pedidos em Aberto e Vendas no claro e no escuro. Suíte 4/4 verde; graphify atualizado.

## Ajuste (24/11/2026) — busca rápida da tela inicial e ícone de tema

| # | Pergunta | Decisão |
|---|---|---|
| Q1 | Lista de sugestões da tela inicial (azul-marinho do menu nos dois temas; texto escuro sobre escuro no claro) | Mesmo visual da `.psd-sug`, no tema; selos como no Brands |
| Q2 | Teclado | ↑/↓ marcam, Enter abre, Esc fecha; só a resposta da última busca é desenhada |
| Q3 | Animação do ícone de tema | O ícone que entra gira e cresce, 0,35 s; só o ícone; «reduzir movimento» desliga |

- [x] Conferido na cópia: lista branca no claro e `#141A28` no escuro, ↓↓ marca o 2º item; ícone anima nos dois sentidos (`psd-tema-sol` / `psd-tema-lua`).
