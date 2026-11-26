"""Regras das telas (etapa 21): os textos que explicavam cada tela («como é calculado», «o que entra») saíram das telas e ficam aqui, num lugar só,
mostrados em Configurações › Regras das telas. Cada tela leva só um link «Regras da tela» ao lado do título (templates/page.html).
Os números (meta de lead time, mínimo de casos, horizonte…) vêm do código e das Configurações, então o texto acompanha quando eles mudam.
O detalhe técnico, com o arquivo que implementa cada regra, segue em REGRAS_DE_NEGOCIO.md."""


def _ctx():
    import rules, leadtime, estoque
    try: meta = leadtime.meta_dias()
    except Exception: meta = 180
    return {"meta": meta, "meta_m": round(meta / 30), "min_n": leadtime.MIN_N, "hist": leadtime.HIST_MESES, "excesso": estoque.EXCESSO, "horiz": estoque.HORIZONTE,
            "user": rules.valid_user(), "linha": rules.only_desc().title() or "Amortecedor"}


def _des_rd(c, tipo):
    o = ("DESENVOLVIMENTO = item novo em desenvolvimento." if tipo == "des" else "REDESENVOLVIMENTO = item do catálogo com outro fornecedor.")
    marca = ("Marca: o padrão é <b>PERFECT</b>, como no sistema PERFECT (as marcas próprias de clientes — BPROAUTO, MOTORCRAFT, MOTRIO — ficam fora); "
             "«Todas as marcas» e cada marca ficam em «Mais filtros».") if tipo == "des" else "Marca: sem filtro (no servidor a MARCA do redesenvolvimento quase sempre vem vazia); dá para escolher uma em «Mais filtros»."
    return [o + " Tudo vem do servidor SQL (DESENVOLVIMENTO_PRODUTOS), atualizado a cada sincronização.",
            "<b>Chave de linha</b>: a FAMILIA do servidor — Amortecedor (padrão), Amortecedor de moto ou Linha pesada. É o que o sistema PERFECT usa.",
            "<b>Itens</b> = linhas do servidor (cada ID), como o sistema PERFECT conta; a lista agrupa por <b>código</b> (um código pode ter várias aplicações) e mostra os dois números.",
            marca,
            "Abre <b>em andamento</b>: o que ainda não é ITEM RECEBIDO. Os estágios trocam o recorte; «Todos» tira o filtro. Cada estágio mostra os itens e, "
            "quando diferem, os códigos; o quadro de sub status conta dentro do estágio escolhido e clicar num sub status filtra a lista.",
            "«Curtidos» e «Pendente compras» ficam nos atalhos da barra de filtros.",
            "Item <b>bloqueado ou inativo no ERP</b> (ESTOQUE_ANALISE_REPOSICAO) sai das listas e contadores — por isso o número pode ficar um abaixo do sistema PERFECT. As metas não mudam.",
            "<b>Sub status</b>: só o que o servidor manda, por coluna; um valor composto («A / B») conta em cada parte. Validação aprovada, reprovada e pendente qualidade ficam sempre no quadro. "
            "Negociação e vendas" + (" e «Pendente controladoria» (o texto CONTROLADORIA em qualquer status)" if tipo == "des" else "") + " ficam em «Mais filtros».",
            "<b>Curtidos</b> aparecem primeiro; desempate pelo status mais avançado. Nada é marcado à mão.",
            "<b>FOB</b> (só em " + ("PEDIDO CONFIRMADO e FINALIZANDO CIT" if tipo == "des" else "FINALIZANDO CIT e PENDENTE PARTNUMBER FORNECEDOR") + "): em verde o FOB do "
            "fornecedor do item — o FOB_FINAL do servidor (o menor, se varia entre as aplicações); sem ele, o preço desse fornecedor na planilha FOB; «planilha» aparece quando "
            "ela difere do servidor. Em branco, para comparar, o preço na planilha FOB do fornecedor da última compra do código (vigente) ou, sem compra, dos outros fornecedores."]


def lista():
    """[{slug, titulo, itens: [html]}] na ordem do menu."""
    c = _ctx()
    R = [
        ("dashboard", "Dashboard", [
            "Os cartões de Desenvolvimento e Redesenvolvimento contam os itens em andamento da família Amortecedor, com a mesma regra das telas (marca PERFECT no desenvolvimento).",
            "<b>Pendências por controle de status</b>: itens com cada pendência marcada pelo servidor (um item pode ter mais de uma). Clique numa linha para abrir a lista filtrada.",
            "<b>Funil</b>: códigos distintos por status, do início ao recebimento. Clique num status para abrir a lista."]),
        ("metas", "Metas & Validação", [
            f"Validações: USER_VALID = <b>{c['user']}</b> · LINHA «{c['linha']}» (inclui a linha pesada) · contagem por código distinto · tipo pela SUGESTÃO do servidor (DES / R-D), no ano da data de aprovação.",
            "<b>Redesenvolvimento</b>: entram todas as validações do usuário no ano, inclusive as que estão com validação pendente da qualidade ou reprovada; o item entra na meta do ano quando chegar a ITEM RECEBIDO, mesmo que chegue depois.",
            "Itens em PENDENTE CONFIRMAÇÃO com validação enviada entram na meta sozinhos quando o servidor mostrar ITEM RECEBIDO.",
            "Como as metas contam (validações ou itens recebidos) se escolhe em Configurações › Regras de negócio."]),
        ("pedidos-aberto", "Pedidos em Aberto", [
            "Pedidos de compra de <b>amortecedor</b> com código iniciado em <b>MP-</b> e saldo em aberto. O fornecedor vem do código EX do ERP (EX0002116 = ZS · EX0002110 = E-WIN · EX008042 = XGM); outro código aparece como <b>VERIFICAR</b>.",
            f"<b>Previsão de chegada</b>: cada linha em aberto é prevista a partir de onde ela está hoje, somando as etapas que faltam com o prazo típico (<b>mediana</b>) daquele fornecedor; "
            f"a faixa é <b>p25–p75</b> (metade dos casos históricos cai nela). No mar, usa o <b>ETA do servidor</b>. Fornecedor com menos de <b>{c['min_n']} casos</b> usa a base geral. "
            f"Base: embarques entregues nos últimos {c['hist']} meses.",
            "<b>Parado — verificar saldo</b>: linha sem embarque há mais de 2× o p90 da produção do fornecedor; não entra como «a caminho» no Estoque.",
            "<b>Vai atrasar</b>: previsão mais de 15 dias depois da promessa. <b>Vencida</b>: a previsão já passou (cobrar o fornecedor).",
            "<b>Previsão × realizado</b>: a previsão é fotografada a cada sincronização e comparada com a chegada real. Erro + = chegou depois do previsto; «na faixa» = dentro do p25–p75. Vale a 1ª previsão de cada etapa.",
            f"<b>Lead time</b> (meta {c['meta']} dias = {c['meta_m']} meses, em Configurações): Prometido = previsão − emissão · Pedido→embarque = embarque − emissão · "
            "Embarque→chegada = previsão de chegada − embarque · Real = recebimento − emissão (só entregues) · Atraso = recebimento − previsão. Média e p90 (9 de cada 10 pedidos levam até esse prazo)."]),
        ("vendas", "Vendas (Curva A)", [
            "Faturamento do servidor com IPI (VALOR_TOTAL_CIPI, data de faturamento). Universo padrão = o do BI: LINHA exatamente «AMORTECEDOR»; linha pesada e kit só pelo seletor da tela.",
            "Curva ABC: A até 80% do valor acumulado, B até 95%, o resto C. O resumo mostra o último mês fechado, o mês atual (parcial) e o acumulado do ano com o mesmo período do ano anterior.",
            "Conferência com o BI: o export do BI traz os filtros (ano, mês, LINHA) na linha «Filtros aplicados», e eles são aplicados também aos dados do servidor."]),
        ("garantia", "Garantia", [
            "Só do servidor (ANALITICO_GARANTIA_DEVOLUCAO), FAMILIA AMORTECEDOR ou AMORTECEDOR LINHA PESADA, todos os anos. Valor com IPI.",
            "Padrão da tela: tipos GARANTIA, GARANTIA AUTOMATICA, CRÉDITO GARANTIA e GARANTIA EM DEVOLUÇÃO, sem ocorrência cancelada, no ano atual (data de cadastro). Defeito agrupado sem o prefixo AM-xxx/O-xxx.",
            "<b>Índice por UF</b> = peças em garantia ÷ peças de amortecedor vendidas no estado no mesmo ano. «Mesmo período do ano anterior» = 1/jan até o dia do último cadastro filtrado.",
            "% procedente = peças procedentes ÷ (procedentes + improcedentes). O CNPJ do cliente não é guardado.",
            "<b>Mês a mês</b>: o ano filtrado em azul e o ano anterior em cinza, lado a lado. <b>Pareto de defeitos</b>: defeitos do maior para o menor; a linha vertical "
            "marca onde os defeitos à esquerda somam 80% das peças, e a dica de cada barra mostra o % dela e o acumulado. Clicar numa barra filtra a tela pelo defeito."]),
        ("fob", "FOB (preços de compra)", ["Chave = PartNumber; sem PartNumber, o «Codigo» quando é código PERFECT (AMD…), porque a linha é o próprio item; "
                                           "1BP… sem PartNumber entra pelo item PERFECT relativo do Brands (só quando há um só e ele não tem linha própria).",
                                           "Item em várias linhas: os fornecedores se juntam, cada um com o seu menor preço.",
                                           "<b>FOB = o menor valor</b> entre E-WIN, ZS e XGM, e o «Melhor preço» é o fornecedor desse valor (empate: os dois), em verde — mesmo quando o "
                                           "«Mínimo» da planilha indica outro. Origem e data só quando a planilha indica esse mesmo fornecedor. Sem preço por fornecedor vale o «Mínimo».",
                                           "A lista mostra os produtos do catálogo. A busca acha também os itens da tabela FOB que só existem em DES/R-D, "
                                           "marcados «DES» e/ou «R-D»; códigos da planilha que não são PERFECT nem DES/R-D não aparecem.",
                                           "Reenviar a tabela substitui a anterior."]),
        ("cobertura", "Cobertura de concorrentes", [
            "<b>Catálogo</b>: só itens do catálogo; referência pela regra dos concorrentes (CrossCatalogo; o servidor quando a planilha não tem o item); OEM fora. Curva ABC pelas vendas dos 12 meses fechados (A até 80%, B até 95%).",
            "<b>Desenvolvimento</b>: DES em andamento (sem ITEM RECEBIDO, sem cancelado, não bloqueado, só código AMD). Frota da Fraga pelo veículo e anos da aplicação (o mesmo veículo × ano conta uma vez); sem casamento, COFAP × Fraga e depois a FROTA do servidor. Lançamento = início de produção a partir de 2024.",
            "<b>COFAP</b>: códigos da planilha COFAP × frota sem motos; «Temos · catálogo», «Em desenvolvimento» ou «Não temos» pelo nosso cross; item de montadora nunca conta como «temos».",
            "«Nosso código» corrigido na tela vale sobre o CrossCatalogo e o servidor, e aparece em Anomalias › Cross corrigido para levar à planilha."]),
        ("desenhos", "Desenhos", [
            "Código e revisão pelo nome do arquivo (RED = redesenvolvimento, DES = desenvolvimento); os cadastros mostram a maior revisão; arquivo idêntico é ignorado.",
            "«Sem desenho» = produto do catálogo sem desenho técnico. «Sem projeto» = DESENVOLVIMENTO em andamento fora do catálogo (não bloqueado, sem ITEM RECEBIDO, sem cancelado) sem Projeto PERFECT."]),
        ("envio", "Envio de amostra", ["Compra (SC) → Chegou ⇒ Pendente projeto → Enviada (com o EX do fornecedor) → Finalizada. Na importação da Compra_de_amostra só campos vazios são preenchidos."]),
        ("damping", "Damping force", [
            "Faixa = DRAWING × (1 ± tolerância); se DRAWING for menor que o limite da regra carregada, o mínimo ganha e o máximo perde o ajuste. Ponto aprovado se mín ≤ FOUND ≤ máx.",
            "Ensaio <b>reprovado</b> se algum ponto reprovou; <b>aprovado</b> só se todo ponto com DRAWING foi aprovado; senão <b>incompleto</b>. Os valores da regra em uso aparecem na própria tela."]),
        ("estoque", "Estoque", [
            "Itens do catálogo (CatalogoAMD). Estoque = <b>ESTOQUE_ANALISE_REPOSICAO</b>, total PRIVATE + FECT (PA + MP). «Contar no estoque» (Mais filtros) troca para só PA ou só MP.",
            "Venda média = peças dos <b>12 meses fechados</b> ÷ 12 (o mês atual fica de fora). A caminho = pedidos em aberto, sem os «Parado — verificar saldo».",
            f"Cobertura (meses) = (estoque + a caminho) ÷ venda média. <b>Risco</b> abaixo da meta de lead time ({c['meta_m']} meses) · <b>Excesso</b> acima de {c['excesso']} meses · "
            "<b>Ruptura</b> = vende e está sem estoque · <b>Sem giro</b> = estoque sem venda em 12 meses.",
            f"Projeção mês a mês ({c['horiz']} meses): saldo = estoque + chegadas previstas − venda média. «Falta em» = 1º mês com saldo negativo; «antes de chegar» = tem pedido a caminho, mas falta antes de ele cobrir.",
            "Cada número dos atalhos = linhas da lista ao clicar."]),
        ("brands", "Brands", [
            "Itens agrupados pelo código: <b>AMD…</b> = PERFECT · <b>1BP…</b> = BPROAUTO · <b>somente números</b> = MOTRIO · itens da base ItensMotorcraft (PN Ford e a mesma família de código) = MOTORCRAFT.",
            "Reúne catálogo, desenvolvimento, redesenvolvimento, base de marcas e pedidos de amostra.",
            "<b>Código PERFECT</b>: vem do cross, da base de marcas e das amostras. O lápis da célula vincula manualmente o item PERFECT relativo "
            "(um ou mais códigos AMD… do catálogo ou de DES/R-D; vazio = sem relação); o vínculo vale sobre a base, aparece como «vinculado no app» e tem «Desfazer»."]),
        ("desenvolvimento", "Desenvolvimento", _des_rd(c, "des")),
        ("redesenvolvimento", "Redesenvolvimento", _des_rd(c, "rd") + [
            "<b>Validar itens</b> (etapa 24): sem busca, lista os itens em andamento que o servidor marca «Pendente validação», «Validação reprovada» ou «Pendente desenho do fornecedor», "
            "nessa ordem; com busca, qualquer item em andamento. «Iniciar validação» abre a bancada (a mesma da tela Validação); quem já tem rascunho mostra «Continuar»."]),
        ("validacao", "Validação", [
            "Validação de desenho que gera o F-008: o desenho PERFECT (referência) contra o desenho do fornecedor. Por enquanto só Redesenvolvimento; Desenvolvimento entra depois.",
            "<b>1 · Desenhos</b>: os dois são enviados na hora (PDF, PNG ou JPG; o PDF vale pela 1ª página). No PERFECT, arraste para selecionar: «Apagar seleção» (Delete) pinta de branco e "
            "«Manter só a seleção» apaga o resto; «Desfazer» volta um passo. A versão limpa fica só na validação; o arquivo em Desenhos não muda.",
            "<b>2 · Família</b>: os modelos F-008 de <code>bases_exemplo\\VALIDATION</code> (Cartucho, Convencional, Estrutural, Semi-estrutural, Semi-estrutural interferência). "
            "As medidas são as da coluna B do modelo, na mesma ordem; até 25 linhas, as extras com nome em inglês. Trocar a família guarda os valores das medidas de mesmo nome.",
            "<b>3 · Medidas</b>: «Marcar no desenho» começa pela primeira linha sem número. Em «Só marcar» (padrão), cada clique na cota põe o número e passa para a próxima linha; "
            "Ctrl+Z tira o último; duplo clique num número abre o valor. Em «Marcar e digitar», o clique abre o campo ali mesmo (no PERFECT, «553±3» ou «12.1 +0.15/0» já separa as tolerâncias). "
            "O nome da cota pode ser trocado na tabela (só nesta validação). Roda do mouse aproxima, arrastar (ou a rodinha apertada) move, «Tela cheia» abre o desenho grande; arrastar um número muda o lugar dele. "
            "Cada linha preenchida precisa ser marcada «Conferida».",
            "O fornecedor e o código do fornecedor saem do nome do arquivo do desenho («RED - AMD0128 - ZS - DQ32713 - REV.06»). A coluna PERFECT já vem preenchida (itálico azul) da última "
            "validação do mesmo código, do par ou do catálogo; confira. «Reaproveitar posições» traz os números de uma validação anterior do mesmo código ou do mesmo fornecedor e família. "
            "Na tabela, Enter desce na coluna e colar uma coluna do Excel preenche para baixo.",
            "<b>Itens com lados</b> (LD × LE na planilha Lados): ao concluir um lado, o outro fica pronto — família, medidas, conferência, posições, damping e o desenho PERFECT vigente dele. "
            "Falta enviar o desenho do fornecedor do outro lado e concluir; o botão da mesma decisão fica em destaque. «Espelhar posições» vira os números se o desenho for espelhado.",
            "«Item com mola» (passo 2) acrescenta a medida LMAX2 logo abaixo do LMAX. «Sobrepor» mostra os dois desenhos juntos (PERFECT vermelho, fornecedor azul, coincidência escura); com "
            "2 ou mais linhas marcadas nos dois desenhos, alinha sozinho. Damping: Enter passa para o valor ao lado; colar vários números preenche a linha.",
            "Leitura pelo Claude: desligada por padrão (Configurações › Regras de negócio). Ligada, o Claude (Opus 5.5, pela API, com a chave ANTHROPIC_API_KEY do ~/.perfect_shock_data/.env) "
            "lê os dois desenhos e preenche valor, tolerância e lugar de cada cota; não aprova nada. As imagens dos desenhos saem do PC para a API da Anthropic.",
            "<b>Ap</b> (A/R) é a fórmula do modelo: tolerância «OK» aprova e «N» reprova; roscas (M…), ângulos e textos comparam como texto; números aprovam dentro da tolerância "
            "(fornecedor ≤ PERFECT + Tol.+ e ≥ PERFECT + Tol.−). A Melhoria sugere «CHANGE TO <valor PERFECT>» na linha R e pode ser trocada. Damping: a fórmula do modelo da família — Cartucho: cada velocidade "
            "dentro de ±30/25/15/15/15 % do PERFECT (com ±30 N a menos abaixo de 1000 N); os outros: diferença de até 30/25/15/20/15 %, e sem valor do PERFECT numa velocidade o Ap fica vazio.",
            "<b>4 · Revisão e aprovação</b>: só com todas as linhas conferidas. Aprovar ou Reprovar preenche o modelo da família (Dados, medidas, damping, as duas imagens e o X da conclusão) e grava "
            "«F-008 - Validation Test - Rev.00 - <código> - <fornecedor> - <código do fornecedor> - REV.nn» (nn = revisão da validação) em xlsx e pdf (o pdf pelo Excel do PC) em <code>data\\validacoes</code>. "
            "Só Aprovar sobe o desenho original do fornecedor para Desenhos («RED - … - REV.00», fonte «Validação»), como a revisão vigente.",
            "Aba de damping do F-008: arraste sobre a tabela de damping de cada desenho e use «Manter só a seleção»; sem recorte, vai o desenho inteiro. "
            "Com o Excel no PC, os números das medidas entram como caixas de texto («Medida n») sobre o desenho do fornecedor e podem ser movidos no Excel; sem Excel, são pintados no desenho.",
            "Concluída, a validação não muda mais; «Nova revisão» abre a Rev.01, Rev.02… com tudo da anterior (troque o que mudou), e as anteriores ficam guardadas. "
            "A lixeira exclui a revisão com os arquivos dela (o desenho já enviado para Desenhos fica). O status do item no servidor não muda (o servidor só é lido)."]),
        ("amostras", "Compra de amostras", [
            "<b>Sugestões</b>: itens PERFECT em DESENVOLVIMENTO marcados PENDENTE COMPRAS, sem amostra comprada, fora do catálogo e com status diferente de ITEM RECEBIDO (só Amortecedor). "
            "Redesenvolvimento não tem sugestão: para comprar amostra de um item já desenvolvido, use «+ Nova amostra». Cada referência abre a consulta do menor preço.",
            "<b>Pedidos de amostra</b> por etapa (◀ ▶ muda a etapa); ao chegar em «Chegou», o item entra no Envio de amostra como «Pendente projeto»."]),
        ("pesquisa", "Pesquisa de amortecedores", [
            "Aceita código PERFECT, OEM ou de concorrente (com ou sem ponto/hífen: 16.470 = 16470) ou uma aplicação (ex.: strada 2012 dianteiro). Procura no catálogo e nos itens em DESENVOLVIMENTO e REDESENVOLVIMENTO."]),
        ("produtos", "Produtos e códigos", [
            "Na ordem do catálogo (planilha CatalogoAMD, que prevalece). A busca aceita código PERFECT, OEM ou de concorrente — a linha mostra qual referência casou.",
            "Ficha do item: peso e código de barras do BI03 (Protheus) quando ele tem o item; IPI do servidor. «—» = não consta nas bases."]),
        ("aplicacoes", "Aplicações veiculares", ["Veículos em que cada amortecedor do catálogo é aplicado (um produto pode ter várias aplicações). Clique no código para abrir a ficha."]),
        ("comparacao", "Comparação técnica", ["Escolha de 2 a 4 produtos para comparar os dados lado a lado. As linhas que diferem ficam destacadas; dimensões parecidas não bastam para afirmar intercambialidade."]),
        ("lados", "Lados", ["Amortecedores do catálogo (CatalogoAMD.xlsx). O par LD × LE vem da planilha «Lados - Amortecedores.xlsx»; se ela não cobrir, dos Produtos Relacionados ou da aplicação."]),
        ("anomalias", "Anomalias", [
            "<b>Sugestões de equivalência</b>: a pontuação (0–100%) mede a similaridade dos dados (códigos, aplicação, medidas, sistema). Não comprova intercambialidade e nenhuma sugestão é aprovada automaticamente.",
            "<b>Família</b>: o CatalogoAMD prevalece. Aparecem os produtos com algum certificado Inmetro de família diferente; confira o certificado (ou o catálogo) e corrija na origem.",
            "<b>EAN</b>: EAN do catálogo diferente do que veio na planilha. Nada é sobrescrito: escolha usar o da planilha ou manter o do catálogo.",
            "<b>Peso e EAN</b>: o BI03 (Protheus) prevalece no peso líquido e no código de barras; aparecem os itens em que a planilha CatalogoAMD diz outra coisa.",
            "<b>Pendente cadastro Protheus</b>: DES e R-D em andamento (sem ITEM RECEBIDO, sem cancelado) que ainda não estão no BI03 como amortecedor acabado (PA).",
            "<b>Cross</b>: no catálogo vale o CrossCatalogo.xlsx; em desenvolvimento, o servidor (DESENVOLVIMENTO_CONCORRENTES). Aparecem os itens em que o mesmo concorrente tem referência diferente nas duas fontes.",
            "<b>Repetidos</b>: a mesma referência de um concorrente ligada a vários códigos PERFECT, ou o mesmo código com várias referências do mesmo concorrente.",
            "<b>Corrigido</b>: «nosso código» corrigido na Cobertura de concorrentes; leve a correção para o CrossCatalogo.xlsx."]),
        ("pendencias", "Pendências de dados", [
            "<b>Conflito</b>: o banco e a planilha trazem valores diferentes; o valor do banco foi mantido. Resolva no ERP ou na planilha de origem e marque como resolvida, ou ignore o que não precisa de ação.",
            "<b>Duplicados</b>: mesmo código (OEM, concorrente, EAN…) ligado a mais de um produto PERFECT. Pode ser correto (aplicações em comum) ou erro de cadastro. Nada é unido ou excluído automaticamente."]),
        ("fontes", "Fontes e histórico", ["Prioridade de 1 (maior) a 9: indica qual fonte prevalece quando você analisa um conflito em Pendências. O sistema nunca sobrescreve um valor sozinho."]),
    ]
    return [{"slug": s, "titulo": t, "itens": i} for s, t, i in R]


def slugs():
    return {r["slug"] for r in lista()}
