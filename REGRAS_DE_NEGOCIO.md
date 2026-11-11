# PERFECT Shock Data — Regras de negócio (levantadas do código, etapa 15 · 10/11/2026)

Cada regra cita o arquivo onde ela está implementada. Onde a etapa 15 mudou algo, está marcado **[novo]** ou **[corrigido]**.

## 1. Fontes de dados

| Dado | Fonte oficial | Quem grava | Arquivo |
|---|---|---|---|
| Catálogo (produtos, posição, peso, EAN, NCM, medidas, sistema óleo/gás) | `bases_exemplo/CatalogoAMD.xlsx` | Atualização de dados / Importação | `loaders.py · L_catalogo` |
| Aplicações do catálogo (Veículos), referências (Números Referência), Produtos Relacionados | `CatalogoAMD.xlsx` **[novo]** e `CrossCatalogo.xlsx` | idem | `loaders.py · _refs_vehicles, _related` |
| Par LD × LE | `Lados - Amortecedores.xlsx` | idem | `loaders.py · L_lados` |
| Desenvolvimento / Redesenvolvimento | Servidor SQL `DESENVOLVIMENTO_PRODUTOS` | sincronização | `data_pipeline.py` |
| Compras, embarques, vendas, estoque, garantia | Servidor SQL (views `PEDIDOS_COMPRA_DETALHADO`, `EMBARQUES_DETALHADO`, `VENDAS_FATURAMENTO_DETALHADO`, `EST DISP`, `ANALITICO_GARANTIA_DEVOLUCAO`) | sincronização | `data_pipeline.py · DATASETS` |
| Compra de amostras, caixas, estrutura, Inmetro, de-para ZS, Motorcraft, damping | planilhas de `bases_exemplo` (pelo NOME do arquivo) | Atualização de dados | `updater.py · KNOWN` |

- O servidor é **somente leitura**: só `SELECT` passa (`assert_select`). O servidor **nunca grava no catálogo**.
- A planilha antiga `DadosR-D e DES.xlsx` é ignorada: DES/R-D vêm só do servidor.
- Atualização por planilha: insere só o que falta, nada é apagado, backup automático antes de aplicar (`updater.py`).

## 2. Catálogo
- `CatalogoAMD.xlsx` é a **fonte de verdade**: o que está nela prevalece sobre o banco (política *overwrite*); a posição no catálogo é a ordem das linhas; produto que sai da planilha sai do catálogo (`catalog_position = NULL`), mas não é apagado.
- **[corrigido]** O formato atual da planilha (`Código Produto`, `Descrição Produto`, `Números Referência`, `Veículos`, `Produtos Relacionados`, `Observação`) era reconhecido como *referência cruzada* — o catálogo não era atualizado por ela. Agora é reconhecido como catálogo completo pela presença de «Produtos Relacionados».
- Observação: «Sistema: Gás/Óleo» → `system_type`; «Medida emb.» → nota de embalagem; «MIN: x / MÁX: y» → Lmin/Lmax.
- Números Referência «CÓDIGO (MARCA)»: marca OEM → código OEM; demais → concorrente.
- Pendências automáticas: produto sem Lmin/Lmax, peso ou EAN.
- Brands pelo prefixo: `AMD…` PERFECT · `1BP…` BPROAUTO · só números MOTRIO · base ItensMotorcraft MOTORCRAFT.
- Prefixo `MP-` = item a granel (sem embalagem); é removido para casar com o código do catálogo.

## 3. Desenvolvimento (DES) e Redesenvolvimento (R-D)
- Tipo vem de `SUGESTAO`: qualquer variação de DES → DESENVOLVIMENTO; R-D/RD/Redes… → REDESENVOLVIMENTO (`kinds.py`).
- **Exclusividade:** um código não aparece nos dois; se tem linha R-D, vale só R-D (`normalize_dev`, `rd.py`).
- Universo das telas e metas: LINHA exatamente «AMORTECEDOR» ou «AMORTECEDOR LINHA PESADA»; códigos/descrições COX e KAD ficam fora (`rules.desc_sql`).
- **Item inativado = bloqueado no ERP.** A sincronização lê `ATIVO`/`BLOQ` de `ESTOQUE_ANALISE_REPOSICAO` (tabela `ds_situacao`); `BLOQ = SIM` ou `ATIVO` diferente de «ATIVO» tira o código das listas e contadores de DES/R-D (`rules.ERP_OFF_SQL`). As **metas não mudam**: item recebido e validado continua contando mesmo depois de bloqueado (`goals._meta` usa `desc_sql(erp=False)`). Código fora da view do ERP fica.
- Status do item (várias linhas por aplicação) = o mais avançado do ciclo: PENDENTE COD. PERFECT/PARTNUMBER → PENDENTE CONFIRMAÇÃO → EM COTAÇÃO → PEDIDO CONFIRMADO → FINALIZANDO CIT → ITEM RECEBIDO.
- O servidor só guarda o status atual: o app grava um snapshot por sincronização e registra as **transições** (eventos com data). 1ª sincronização = marco zero.
- Controle de status (Pendente validação, Validação reprovada, Pendente desenho do fornecedor, Pendente compras): detectado pelos sub status; a marcação manual prevalece (`statuses.py`).

## 4. Metas & Validação (`goals.py`, `metas.py`)
- Metas padrão 2026: DESENVOLVIMENTO 125 · REDESENVOLVIMENTO 150 (editáveis; «já realizado antes do rastreio» soma).
- Base «validação» (padrão): conta códigos distintos com `USER_VALID` **exatamente** igual a ITALOC, LINHA amortecedor, por SUGESTAO, no ano da `DATA_APROVACAO`.
- DESENVOLVIMENTO conta só item que chegou a ITEM RECEBIDO no ano **e** validado por ITALOC.
- Base «recebido»: R-D conta a transição PENDENTE CONFIRMAÇÃO → ITEM RECEBIDO no ano, com validação ITALOC.
- **[novo]** A data de recebimento usa também a coluna `DATA_RECEBIDO` do servidor (antes só as transições vistas depois do marco zero).
- **[corrigido]** A lista de eventos da meta mostrava todo item DES recebido como «conta»; agora segue a mesma regra do contador (só se validado).

## 5. Sincronização com o servidor (`data_pipeline.py`) **[novo]**
- **Diária, em horário fixo** (`DEV_SYNC_AT`, padrão 06:30): uma vez por dia; se o app abrir depois do horário, roda ~20 s após abrir. Botão «Sincronizar agora» continua.
- **[etapa 16] Também com o app fechado:** tarefa agendada do Windows «PERFECT Shock Data - sincronizacao diaria» (06:30, usuário logado; se o PC estava desligado, roda assim que possível) executa `sincronizar.bat` → `data_pipeline.py diaria`. Não repete se já houve sincronização OK no dia. Log em `data\sincronizacao_log.txt`.
- **[etapa 16] Uma por vez entre processos:** a tarefa e o app usam a trava `data\sincronizacao.lock`; quem chega depois desiste («já existe uma sincronização em andamento»). Trava com mais de 45 min é considerada de um processo que morreu e é descartada.
- **Só o necessário vem do servidor** (filtro aplicado no próprio SQL Server, `DEV_SYNC_ESCOPO=amortecedor`):
  - DES/R-D: `LINHA LIKE '%AMORTECEDOR%'` (≈2,7 mil linhas em vez de 15 mil);
  - compras: LINHA ou descrição de amortecedor (≈21 mil em vez de 209 mil);
  - embarques: só produtos que aparecem em compras de amortecedor;
  - estoque e garantia: LINHA/FAMÍLIA amortecedor;
  - vendas: **somadas no servidor por mês × SKU × LINHA**, só amortecedor, e **incremental** — depois da 1ª carga (3 anos), só o mês anterior em diante é rebuscado.
- Travas: recusa carga com menos de 50% dos itens/linhas da anterior — exceto quando o filtro mudou (a queda é esperada; fica registrado).
- Tempo: ~8 min → ~1,5 min (1ª carga filtrada) → ~35 s (cargas seguintes).

## 6. Vendas (`curva_abc.py`, `analytics.py`, `conciliacao.py`)
- **[corrigido]** A view usa `DATA_FATUR` e `VALOR_TOTAL_CIPI`/`VALOR_TOTAL_NET`; o app procurava outros nomes → data e valor vazios, e trazia só 300 mil de ~9 milhões de linhas. Além disso a tela chamava uma função inexistente e travava.
- Valor «faturado» = `VALOR_TOTAL_CIPI` (com IPI). O líquido (`VALOR_TOTAL_NET`) é guardado junto. Troque com `DEV_VENDAS_VALOR` se o BI usar outro.
- Curva ABC: agrupa por SKU, ordena por valor; classe A até 80% acumulado, B até 95%, C o resto; só LINHA contendo «AMORTECEDOR».
- Resumo: acumulado do ano vs. mesmo período do ano anterior, evolução mensal, participação por linha e % do faturamento em SKUs do catálogo.
- «Conferir com o BI»: compara o export VENDA_POR_SKU com o servidor (mesmos filtros) e lista SKUs vendidos fora do catálogo.

## 7. Pedidos em Aberto e Lead time (`orders.py`, `leadtime.py`)
- Universo: código começa com `MP-` **e** descrição contém «amortecedor»; em aberto = saldo > 0.
- Fornecedor pelo código EX: EX0002116 = ZS · EX0002110 = E-WIN · EX0008042/EX008042 = XGM · outro = VERIFICAR.
- Lead time (ano vigente): prometido = previsão − emissão; pedido→embarque; embarque→chegada; real; atraso. Meta 180 dias (editável).
- Previsão empurrada: a data prevista de cada linha é gravada a cada sincronização; cada adiamento conta.
- **[novo] Previsão de embarques e chegadas:** as etapas são medidas nos embarques entregues dos últimos 24 meses, por fornecedor:
  produção (emissão → embarque) · mar (embarque → porto) · desembaraço (porto → filial). Cada linha aberta é prevista a partir de onde está:
  no porto → + desembaraço; no mar → ETA do servidor + desembaraço; aguardando embarque → emissão + produção típica (nunca antes de hoje) + mar + desembaraço.
  Mediana = data prevista; p25–p75 = faixa. Fornecedor com < 5 casos usa a base geral. «Vai atrasar» = previsão > promessa + 15 dias.
  Linha sem embarque há mais de 2× o p90 da produção = «Parado — verificar saldo» (fora do calendário).
- **[corrigido]** Embarques: o app não lia `ETA_ATUAL`, `DATA_CHEGADA_FILIAL`, `DATA_CHEGADA_PORTO` nem `STATUS_MICRO`; agora lê. O cálculo de previsão empurrada caiu de ~4 min para <1 s.

## 8. Lados (`sides.py`) **[novo]**
- Escopo padrão: itens do catálogo com LD ou LE separados, ou presentes na planilha Lados (opção «todos os dianteiros/traseiros»).
- Par LD × LE, nesta ordem: planilha Lados → Produtos Relacionados (mesmo eixo, lado oposto) → mesma aplicação do catálogo → mesma aplicação no servidor.
- Traseiro de um dianteiro (e dianteiro de um traseiro), do mais confiável ao menos: Produtos Relacionados → mesma aplicação do catálogo (montadora, modelo e anos que se cruzam) → mesma aplicação no servidor (montadora, veículo, aplicação e anos) → em desenvolvimento (código só no servidor) → provável (mesmo modelo-base).
- Regra de lado: LD casa com LD ou LD/LE; nunca LD × LE. Item inativo só casa com inativo.
- Cada traseiro traz o próprio par; «Conjunto do veículo» = dianteiro + par + traseiro(s) + par (LD/LE único = ×2).

## 9. Amostras, envio, garantia, FOB, desenhos
- Sugestões de compra: só DES/R-D com PENDENTE COMPRAS, sem amostra comprada, fora do catálogo e não ITEM RECEBIDO.
- Envio: Compra (SC) → Chegou ⇒ Pendente projeto → Enviada (com EX do fornecedor) → Finalizada. Na importação de Compra_de_amostra só campos vazios são preenchidos.
- Garantia: do servidor quando há dados; senão planilha (só código, defeito, quantidade; linha «Total» descartada).
- FOB: chave = PartNumber; repetido fica com o menor FOB; menor entre E-WIN/ZS/XGM = «Melhor Preço».
- Desenhos: código e revisão pelo nome do arquivo; cadastros mostram a maior revisão; arquivo idêntico é ignorado.
- Equivalências: só sugestões por similaridade; nada é aprovado automaticamente.
