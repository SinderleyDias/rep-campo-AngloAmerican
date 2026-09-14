# Incorporação da VSOL como segunda fonte de laboratório

> Documento de planejamento/arquitetura, escrito antes de qualquer implementação.
> Objetivo: registrar as decisões já validadas em conversa, o que ainda está aberto, e servir de
> referência única quando a implementação começar. Nada aqui foi codado ainda.

## 1. Contexto

Hoje o pipeline (`01_extracao_api` → `02_limpeza` → `03_validacoes` → `04_envio_sharepoint`) atende
`1233_IC_BA` e `1233_IC_CDM` com uma única fonte de laboratório: a API Campo Análises.

Um segundo laboratório, **VSOL**, vai passar a atender amostragem tanto de BA quanto de CDM. A API Campo
continua existindo e não é substituída — os dois laboratórios vão coexistir por projeto.

A VSOL entrega resultado de duas formas, com colunas diferentes entre si:

1. **E-mail semanal** — planilha com duas abas relacionadas, `SYS_Sample` e `SYS_SampleAnalysis`.
2. **Download do portal** — planilha única, achatada (uma linha por amostra × parâmetro).

**Decisão de escopo**: o formato do e-mail ainda está sendo validado pelo laboratório e fica **fora do
escopo desta primeira etapa**. Este documento cobre a incorporação da fonte **portal/site**. A seção 13
lista o que falta pro e-mail quando ele voltar a ser prioridade.

### Pasta de pouso no SharePoint (dado bruto da VSOL)

Site `1233_BR_SE_AA_PGRH_GAC_BACKGROUND`, pasta:

```
General/06 - Análise de dados/Suporte Digital/dados_brutos_vsol
```

([link completo](https://waterltda.sharepoint.com/sites/1233_BR_SE_AA_PGRH_GAC_BACKGROUND/Documentos%20Compartilhados/Forms/AllItems.aspx?id=%2Fsites%2F1233%5FBR%5FSE%5FAA%5FPGRH%5FGAC%5FBACKGROUND%2FDocumentos%20Compartilhados%2FGeneral%2F06%20%2D%20An%C3%A1lise%20de%20dados%2FSuporte%20Digital%2Fdados%5Fbrutos%5Fvsol) — Sinderley vai adicionar os arquivos de exemplo/reais aqui.)

**Importante**: essa pasta é **compartilhada entre os dois projetos** (BA e CDM caem no mesmo lugar,
já que é a VSOL quem estrutura a entrega, não o pipeline) — diferente de `sharepoint_depara_folder`,
`sharepoint_escopo_folder` e `sharepoint_envio_folder`, que hoje são valores distintos por entrada em
`config/projetos.py`. Ao cadastrar essa pasta em config, ela provavelmente vai repetir o mesmo valor nas
duas entradas (`1233_IC_BA` e `1233_IC_CDM`) — o que resolve o projeto é o conteúdo do arquivo
(`Proposta Comercial`), não a pasta onde ele está.

## 2. Decisões já fechadas (resumo)

| Decisão | Resposta |
|---|---|
| Repositório novo para a VSOL? | **Não.** Mesmo repo, mesmo padrão config-driven (`config/projetos.py`). |
| A VSOL substitui a Campo? | Não — convivem, cada uma alimentando o mesmo destino final por projeto. |
| Os dois laboratórios amostram a mesma amostra (risco de duplicidade)? | Não, são conjuntos de amostra totalmente disjuntos — não precisa de deduplicação entre fontes. |
| Onde a campanha (BA vs CDM) é resolvida pro arquivo do site? | Coluna `Proposta Comercial` do próprio Excel — confirmado visualmente, valores limpos e únicos por projeto. |
| `source_project` do SQL Server serve pra isso? | **Não** — é de outra fonte/modelo, descartado como sinal de campanha. |
| `codigoHga`/`alternate_name` pra VSOL | Mesmo mecanismo de hoje: parsing do identificador da amostra + join com `station`/`SYS_Sample` do SQL Server pelo nome da amostra. |
| De-para de parâmetro | Mesma planilha de sempre — só ganha linhas novas com os nomes de parâmetro da VSOL. |
| Execução das duas fontes | **Desacoplada** — cada fonte dispara e roda no seu próprio ritmo (freschor do banco é prioridade; não há necessidade de correção por overlap de amostra). |
| Rastreabilidade da fonte (Campo vs VSOL) | Campo `laboratorio` (já existe no schema hoje) + sufixo no nome do arquivo de saída (`export_df_<data>_VSOL.xlsx`). |

## 3. Fontes de dados VSOL

### 3.1 Portal/Site (foco desta etapa)

Planilha única (`Sheet 1`), achatada — uma linha por amostra × parâmetro. Colunas observadas no arquivo
de exemplo:

```
Código da Amostra, Nº Amostra, Proposta Comercial, Identificação, Tipo de Amostra, Empresa Solicitante,
Data de Coleta, Data de Recebimento, Data de Publicação, Parecer, Contratante, Nº Proposta Comercial,
Ponto de Coleta, Previsão de Entrega, Situação da Amostra, Data da Situação Atual, Empresa Faturamento,
Representante, Grupo de Amostras, Identificação da Análise, Resultado da Análise,
Unidade de Medida da Análise
```

Pontos de atenção confirmados no arquivo de exemplo:

- ~~Encoding~~ — **correção**: cheguei a suspeitar de acentuação corrompida (`C�digo`,
  `Identifica��o`) ao inspecionar o arquivo, mas era só um artefato do terminal usado na análise. Byte a
  byte o arquivo já vem correto (`"Código da Amostra"`, `"Identificação"`) — `pandas`/`openpyxl` leem sem
  problema, nenhum tratamento de encoding é necessário.
- **Números com vírgula decimal**: `Resultado da Análise` vem como texto, ex. `"109,39"` — precisa de
  parsing locale-aware antes de virar `resultadoNumerico`.
- **Campanha confiável**: `Proposta Comercial` tem exatamente os valores esperados —
  `Projeto_1233_IC_BA - BARRO ALTO` e `Projeto_1233_IC_CDM_CODEMIN/GO` (confirmado via filtro do Excel,
  screenshot em conversa). Esse é o campo fonte da verdade pra resolver `campanha`.

### 3.2 E-mail (`SYS_Sample` + `SYS_SampleAnalysis`) — adiado

Estrutura observada (dois arquivos relacionados por `Cod Amostra Lab`):

- `SYS_Sample`: `Codigo Ponto`, `Nome Amostra`, `Cod Amostra Lab`, `Data Coleta`, `Amostra Coletada`,
  `Razao Nao Coleta`, `Data Inicio/Fim Amostragem`, `Prof inicio/fim (m)`, `Tipo Qualidade`,
  `Tipo Amostra`, `Matriz Monit`, `Tecnica Coleta`, `Laboratorio`, `Data Envio/Recebimento Lab`,
  `Metodo Entrega`, `Cadeia Cust`, `Responsavel Coleta`, `Comentario`.
- `SYS_SampleAnalysis`: `Cod Amostra Lab`, `Cod Parametro`, `Unidade`, `Resultado Numerico`,
  `Nome Param Original`, `Resultado Original`, `Unidade Original`, `Resultado Textual`, `Qualificador`,
  `Data e Hora Analise`, `Metodo Analise`, `Tipo Analise`, `Fator Diluicao`, `LD`, `LQ`, `Comentario`.

Esse modelo (duas tabelas, amostra + parâmetro) é estruturalmente muito parecido com o schema que a API já
produz — a maior parte das colunas bate quase 1:1. **Mas não tem nenhum campo de campanha/projeto** nas
colunas observadas, e essa é justamente a parte que o laboratório ainda está ajustando. **Não avançar no
desenho dessa fonte até o formato ser confirmado pelo lab** — ideal é pedir que a VSOL inclua uma coluna
de projeto/contrato no próprio export, em vez de tentar inferir via banco (ver seção 13).

## 4. Schema canônico de destino (Bronze)

Esse é o schema que `01_extracao_api` já produz hoje (função `parse_hga_api_json_to_df`,
[01_extracao_api.ipynb](../notebooks/01_extracao_api.ipynb)) e que **toda fonte nova deve convergir para
o mesmo formato**, para que `02_limpeza`/`03_validacoes`/`04_envio_sharepoint` não precisem saber a
origem do dado:

```
codigoHga, idAmostra, nomeAmostra, descricaoAmostra, matriz, dataHoraAmostragem, codigoQualidade,
frequencia, laboratorio, comentario_amostra, parent, dataEnvioLab, dataRecebLab, profInicial, profFinal,
composta, coletada, acreditacao, legislacao, finalidade, campanha, motivoNaoColeta, dataLiberacao,
parametroPadrao, resultadoNumerico, dataHoraAnalise, resultadoTexto, unidadePadrao, qualifier,
limiteDeteccao, limiteQuantificacao, parametroOriginal, resultadoOriginal, unidadeOriginal,
metodoAnalise, comentario_parametro, tipoAnalise, reportavel, qaqcFlag, acreditacaoMetodo,
CC_* (bloco de cadeia de custódia)
```

Mapeamento proposto **SITE → canônico** (a confirmar linha a linha durante a implementação):

| Canônico | Origem no SITE | Observação |
|---|---|---|
| `campanha` | `Proposta Comercial` (parseado) | fonte da verdade — ver seção 3.1 |
| `nomeAmostra` / `descricaoAmostra` | `Identificação` | |
| `matriz` | `Tipo de Amostra` | |
| `dataHoraAmostragem` | `Data de Coleta` | |
| `dataRecebLab` | `Data de Recebimento` | |
| `dataLiberacao` | `Data de Publicação` | |
| `laboratorio` | constante `"VSOL"` | não há coluna de lab no SITE |
| `parametroPadrao` / `parametroOriginal` | `Identificação da Análise` | |
| `resultadoNumerico` / `resultadoOriginal` | `Resultado da Análise` | parsing de vírgula decimal |
| `unidadePadrao` / `unidadeOriginal` | `Unidade de Medida da Análise` | |
| `codigoHga` / `alternate_name` | derivado via join (seção 5/6) | chave = `Identificação` (formato `SDN-83-SO-100826-0,5`) — **não** usar `Ponto de Coleta`, vem 100% vazio no arquivo real (ver seção 14) |
| `qualifier` | derivado da própria `Resultado da Análise` | parsing de prefixo `<`/`>` no texto (ex.: `"< 0,0030"` → `qualifier="<"`, valor `0,0030`) |

### Campos do `api_validado` sem equivalente no SITE — status de cada um

Comparado à lista final que o `03_validacoes` grava (`colunas_finais_1`), estes campos não têm coluna
correspondente no Excel do SITE. Status de cada um (decisão do Sinderley em 2026-09-11):

| Campo final | Situação |
|---|---|
| `laboratory` | **Resolvido** — constante `"VSOL"` para toda linha dessa fonte. |
| `qualifier` | **Resolvido** — derivado por parsing de `Resultado da Análise` (ver tabela acima). |
| `sample_date_sent`, `quality_code`, `frequency`, `result_comment`, `sample_comment` | **Sem ação necessária** — esses campos não são carregados no banco final, então ficam vazios/nulos para linhas VSOL sem problema. |
| `analysis_method`, `AnalysisDate`, `quantification_limit` (LQ) | **Bloqueado — depende do laboratório.** Não dá pra assumir/derivar esses três com segurança (ex.: inferir LQ só a partir do texto `< X` cobriria só os ~85% de resultados qualificados, não os ~15% numéricos — e não teríamos LQ nenhum pra estes). **Ação**: pedir à VSOL que inclua essas 3 colunas no export do SITE. Sem elas, as validações de método e de holding time do `03_validacoes` (que comparam planejado vs. executado) não têm o que comparar pro lado da VSOL. |

## 5. Resolução de campanha (BA vs CDM)

- **SITE**: parsing de `Proposta Comercial` (contém literalmente `Projeto_1233_IC_BA` ou
  `Projeto_1233_IC_CDM`) → mapear pra chave do `config/projetos.py`.
- **`source_project` do SQL Server**: descartado — é outro modelo de dado, não confiável pra essa
  finalidade.
- **E-mail**: em aberto, fora de escopo por ora (seção 13).

## 6. `codigoHga` / `alternate_name` via join com `station`

Mecanismo hoje (`02_limpeza.ipynb`, célula da query SQL):

```sql
select
    s.Name as codigoHga,
    s.alternate_name,
    smp.Name as SampleName
from station s
join SYS_Sample smp
    on s.ID = smp.Station
where source_project = '{cfg["source_project_sql"]}'
```

Pra VSOL, mantém a mesma ideia: casar pelo identificador da amostra (`Identificação`/`Ponto de Coleta`)
contra `SampleName` dessa mesma tabela. Como a campanha do SITE já vem confiável de `Proposta Comercial`
(seção 5), **não é necessário tirar o filtro `where source_project`** aqui — ele pode continuar filtrando
pelo projeto já resolvido, exatamente como a Campo já faz hoje. (A ideia de usar esse join pra descobrir a
campanha em si foi avaliada e descartada — ver seção 5.)

## 7. De-para de parâmetro

Mesma planilha de de-para já usada hoje (`depara_filename` / `sharepoint_depara_folder` em
`config/projetos.py`) — sem estrutura nova. Conforme os nomes de parâmetro da VSOL (`Identificação da
Análise` no SITE) aparecerem sem mapeamento, adicionar as linhas correspondentes nessa mesma planilha.

## 8. Estrutura do Data Lake

Mantém o layout medallion já existente, só espelhando a origem dentro de cada camada:

```
/mnt/wst/<projeto>/
├── BRONZE/
│   ├── api/apiCAMPO_<inicio>_<fim>_<timestamp>/      ← já existe (Campo)
│   └── vsol/vsolSITE_<data_arquivo>_<timestamp>/     ← novo
├── SILVER/
│   ├── api_limpo/                                     ← 02_limpeza (compartilhado)
│   ├── api_validado/<output_filename>/                ← 03_validacoes (compartilhado)
│   ├── resumo_por_estacao/ , resumo_amostra/ , parametro_extra/ , metodo/ , holding/ , ...
│   └── export_continuo/export_df_<data>[_VSOL].xlsx   ← 04_envio_sharepoint (compartilhado)
├── GOLD/
└── execution_log/
```

**Decisão**: a divisão por projeto acontece já na escrita da Bronze — `01_extracao_excel` recebe `projeto`
como widget, filtra pra ele via `Proposta Comercial`, e grava só aquela fatia no `BRONZE/vsol/` daquele
projeto (mesmo princípio que `01_extracao_api` já aplica hoje: busca tudo, filtra por campanha, só então
grava).

**Correção de rota (2026-09-11)**: a primeira tentativa criou um `02_limpeza_vsol.ipynb` separado, cópia
de `02_limpeza.ipynb`. Ao portar célula a célula ficou claro que isso era duplicação desnecessária —
normalização de data, join de Station, de-para de amostra e de parâmetro/unidade são **idênticos**
independente da fonte, porque `01_extracao_excel` já entrega o mesmo schema canônico que a API entrega.
As únicas diferenças reais eram os caminhos de pasta (Bronze/Silver). Solução adotada: **um widget
`fonte`** (`"api"` por padrão, ou `"vsol"`) direto em `02_limpeza.ipynb` e `03_validacoes.ipynb`, só pra
escolher os 2 caminhos que precisam mudar — sem duplicar as ~40 células de lógica que são as mesmas pras
duas fontes. `02_limpeza_vsol.ipynb` foi removido.

Regra geral usada pra decidir o que vira widget/branch e o que não vira: **um tratamento que não faz mal
nenhum rodar em cima do dado da Campo entra direto no notebook compartilhado, sem condicional** — foi o
caso da normalização de matriz, que já ficou case-insensitive nos dois notebooks (cobre `"Água
Subterrânea"` da API e `"Água subterrânea"` do SITE com a mesma linha). Só vira `if fonte == ...` o que
literalmente muda de pasta/caminho. E o que é **genuinamente específico da VSOL** (parsing de
qualificador do resultado, filtro de amostra pendente) fica isolado dentro do `01_extracao_excel.ipynb` —
esse notebook nunca roda pra Campo, então não tem risco de vazar tratamento de uma fonte pra outra.

`02_limpeza.ipynb` grava `SILVER/api_limpo` com `mode("overwrite")` — não é uma tabela cumulativa, é o
"lote em processamento" daquele Run. Como Campo e VSOL rodam desacopladas (podem coincidir no tempo), se
gravassem no mesmo caminho uma execução apagaria o lote da outra. Por isso, com `fonte="vsol"`, o
`02_limpeza.ipynb` grava em `SILVER/api_limpo_vsol` em vez de `api_limpo` — e o `03_validacoes.ipynb`
(mesmo widget `fonte`) lê do caminho correspondente. **Resolvido** — não precisa mais de um
`03_validacoes_vsol.ipynb` dedicado.

**Importante para o Job da Campo**: nenhuma mudança de configuração necessária nele. O widget `fonte`
tem default `"api"` — como o Job da Campo não passa esse parâmetro hoje, ele automaticamente cai no
default e reproduz exatamente o comportamento atual. Só o Job da VSOL precisa passar `fonte=vsol`
explicitamente nas tasks de limpeza/validação.

A garantia de "não perder o dado bruto original" não depende de manter uma cópia não-dividida no lake: o
**Excel original enviado pela VSOL continua intacto no SharePoint**. Convenção: mover o arquivo pra uma
subpasta `processado/<data>/` depois que `01_extracao_excel` concluir com sucesso (nunca apagar) — isso
é o que permite reprocessar do zero se a lógica de resolução de campanha precisar de ajuste depois.

## 9. Notebooks — novo vs reaproveitado

| Notebook | Situação |
|---|---|
| `01_extracao_api.ipynb` | **Inalterado.** Continua só Campo — diferença de fonte real demais pra unificar (HTTP+JSON vs Excel). |
| `01_extracao_excel.ipynb` | **Novo — rascunho pronto** (`notebooks/01_extracao_excel.ipynb`). Lê o Excel do SITE, recebe `projeto`/`arquivo` como widget, filtra via `Proposta Comercial`, filtra pendentes (`Situação == Recebida`), parseia qualificador do resultado, grava Bronze com o schema canônico. Não testado em Databricks real ainda. |
| `02_limpeza.ipynb` | **Editado, não duplicado** — ganhou o widget `fonte` (`"api"`/`"vsol"`) que só escolhe 2 caminhos de pasta (Bronze lida, Silver gravada) e uma pequena melhoria (matriz case-insensitive) que serve pras duas fontes. Toda a lógica de join/de-para/conversão continua uma só, compartilhada. Diff pequeno (~15 linhas) — não testado com dado VSOL real ainda. |
| `03_validacoes.ipynb` | **Editado, não duplicado** — mesmo widget `fonte`, só nas 2 linhas que definiam o caminho de leitura do Silver/Bronze. Resto do notebook (validação de método/holding time/escopo) inalterado. Não testado com dado VSOL real ainda. |
| `04_envio_sharepoint.ipynb` | **Inalterado, nenhuma mudança necessária.** Só varre `SILVER/export_continuo` por `export_df_*.xlsx`, não sabe nem precisa saber a origem. Convenção de nome ganha sufixo de fonte (seção 12), mas isso é só no nome do arquivo escrito por `03_validacoes`, não em código do `04`. |

## 10. Orquestração / Jobs no Databricks

### 10.1 Job "Campo (API)" — inalterado

Continua exatamente como hoje: 1 definição de Job, widgets `projeto`/`inicio`/`fim`, **dois agendamentos
separados** (um fixando `projeto=1233_IC_BA`, outro `projeto=1233_IC_CDM`) — nunca os dois projetos juntos
no mesmo Run. Essa regra já existe hoje no `README.md` do repo por causa de como o `taskValues` funciona
(ver nota abaixo) — e essa regra não muda com a chegada da VSOL, é só reafirmada.

### 10.2 Job "VSOL (Excel)" — novo, mesmo padrão da Campo

Depois de pesar a opção de rodar BA e CDM como duas ramificações paralelas dentro de um único Job Run (o
que exigiria mudar como `02_limpeza`/`03_validacoes`/`04_envio_sharepoint` recebem `output_filename`),
decidimos **não fazer isso** — complexidade desnecessária pra um ganho pequeno. Em vez disso, o Job da
VSOL copia exatamente o modelo que a Campo já usa:

- **1 definição de Job**, com os widgets `projeto` (igual à Campo) **e** `arquivo` (caminho do Excel que
  disparou o run — novo, só existe na VSOL).
- Cada Run processa **um projeto só**, nunca os dois juntos — `01_extracao_excel` recebe `projeto` e
  `arquivo`, lê o Excel indicado, filtra internamente só as linhas daquele projeto (via `Proposta
  Comercial`) e ignora o resto. Isso é o mesmo princípio de hoje: `01_extracao_api` também busca tudo e
  filtra pela campanha do projeto antes de gravar.
- **Gatilho**: quando o Power Automate detecta o arquivo novo na pasta do SharePoint, ele chama o `Run
  Now` da API do Databricks **duas vezes** — uma com `projeto=1233_IC_BA`, outra com
  `projeto=1233_IC_CDM` — sempre passando o mesmo `arquivo`. Não é um file-arrival trigger nativo do
  Databricks (ele não observa bibliotecas do SharePoint diretamente); quem detecta o arquivo e decide
  disparar é o próprio Power Automate.
- Se o arquivo daquela vez só tinha amostra de um dos dois projetos, o outro Run simplesmente processa
  zero registros — idempotente, sem erro, custo desprezível (mesma lógica de "sempre rodar os dois,
  mesmo sem novidade" que já tínhamos decidido, só que agora como dois Runs em vez de duas branches).

**Por que isso resolve o problema do `taskValues` sem tocar em nenhum notebook compartilhado**: cada Run
da VSOL passa a ter a mesma "forma" de um Run da Campo — um projeto só, uma única task de extração por
Run. Como `taskValues` nunca precisa distinguir duas coisas dentro do mesmo Run (só existe uma extração
por vez), o mecanismo de hoje (`taskKey="fetch_from_aga_api"` fixo) continua funcionando sem qualquer
alteração em `02_limpeza.ipynb`, `03_validacoes.ipynb` ou `04_envio_sharepoint.ipynb`.

## 11. Power Automate

Fluxo: gatilho "Quando um arquivo é criado ou modificado" na pasta
`General/06 - Análise de dados/Suporte Digital/dados_brutos_vsol` (site
`1233_BR_SE_AA_PGRH_GAC_BACKGROUND` — ver seção 3) → **duas** ações HTTP chamando
`POST /api/2.1/jobs/run-now` do Databricks (uma pra cada projeto), com o `job_id` do Job "VSOL (Excel)", o
parâmetro `arquivo` = caminho do arquivo que disparou o gatilho (igual nas duas chamadas), e `projeto` =
`1233_IC_BA` numa chamada e `1233_IC_CDM` na outra.

Autenticação dessa chamada (token/PAT do Databricks) deve ser resolvida com o mesmo padrão de segredos já
usado no projeto (`config/secrets.py` para o lado do notebook; do lado do Power Automate, guardar como
conexão segura, não como texto no corpo do flow).

## 12. Convenção de nome de arquivo / rastreabilidade da fonte

- Coluna `laboratorio` (já existe no schema canônico) carrega `"Campo"` ou `"VSOL"` por linha — não
  precisa de coluna nova, só garantir que não é descartada no tratamento.
- Nome do arquivo final exportado ganha sufixo de fonte: `export_df_<data>_VSOL.xlsx` (e, por simetria,
  poderia se tornar `export_df_<data>_CAMPO.xlsx` do lado da API, opcional). Já é compatível com o filtro
  atual do `04_envio_sharepoint.ipynb`, que só exige `startswith("export_df_")` e `endswith(".xlsx")` —
  nenhuma mudança de código necessária aí.

## 13. Itens abertos / próximos passos

1. **E-mail (`SYS_Sample`/`SYS_SampleAnalysis`)** — fora de escopo até o laboratório fechar o formato.
   Quando retomar: preferir pedir à VSOL que inclua uma coluna de projeto/contrato no export, em vez de
   inferir via banco (`source_project` já foi descartado como pouco confiável).
1b. **Pedir à VSOL 3 colunas hoje ausentes no export do SITE**: `analysis_method` (método de análise
   executado), `AnalysisDate` (data/hora da análise, por parâmetro) e o limite de quantificação (LQ).
   Sem elas não dá pra rodar as validações de método/holding time do `03_validacoes` pro lado da VSOL
   (ver seção 4). Isso é bloqueante pra essas duas validações específicas, não pro resto do pipeline.
2. Confirmar, célula a célula, o mapeamento completo SITE → canônico da seção 4 (especialmente os campos
   sem equivalente óbvio: `frequencia`, `acreditacao`, `legislacao`, `finalidade`, `qaqcFlag`,
   `reportavel`, bloco `CC_*`).
3. ~~Testar `02_limpeza.ipynb`~~ — feito o rascunho de `02_limpeza_vsol.ipynb` portando a lógica célula a
   célula (normalização de data/matriz, join de Station, de-para de amostra e parâmetro). Falta testar
   com dado real em Databricks — não rodou ainda em ambiente nenhum.
4. Definir a convenção exata de nome de pasta Bronze da VSOL — já esboçado como `vsolSITE_<timestamp>`
   no rascunho de `01_extracao_excel.ipynb` — e o mecanismo de `processado/<data>/` no SharePoint (mover
   arquivo após sucesso, ainda não implementado no rascunho).
5. Cadastrar a entrada de config necessária em `config/projetos.py` para a fonte VSOL — pasta de pouso já
   conhecida (`General/06 - Análise de dados/Suporte Digital/dados_brutos_vsol`, ver seção 3), falta
   definir a pasta de `processado/` e adicionar os campos nas entradas `1233_IC_BA`/`1233_IC_CDM` já
   existentes (sem criar chave de projeto nova). **Bloqueia rodar `01_extracao_excel.ipynb`** — ele lê
   `cfg["sharepoint_vsol_bruto_folder"]`, que ainda não existe em `config/projetos.py`.
6. ~~Decidir como `03_validacoes.ipynb` vai ler o Silver da VSOL~~ — **resolvido**: widget `fonte`
   adicionado direto em `02_limpeza.ipynb` e `03_validacoes.ipynb` (ver seção 8), sem duplicar notebook.
   Falta só testar com dado real.

## 14. Estudo do arquivo real do SITE (referência)

Perfil feito em cima de `samples-10_09_2026 (1) (1).xlsx` (17.034 linhas, 97 amostras distintas, extraído
em 2026-09-10) — usar como referência ao construir `01_extracao_excel`/`02_limpeza_vsol`, não como
garantia definitiva (validar de novo com um arquivo mais recente antes de codar):

- **Campanha**: `Projeto_1233_IC_BA - BARRO ALTO` (9.092 linhas) e `Projeto_1233_IC_CDM_CODEMIN/GO`
  (7.942 linhas) — confirma a seção 5.
- **Colunas 100% vazias nesse arquivo**: `Parecer`, `Representante`, `Ponto de Coleta`. Não usar nenhuma
  delas como chave ou fonte de dado.
- **`Situação da Amostra`** tem 3 estados: `Publicada` (8.574), `Recebida` (5.914), `A Faturar` (2.546).
  As 5.914 linhas `Recebida` são exatamente as que vêm com `Resultado da Análise` e `Data de Publicação`
  nulos — amostra recebida no lab mas ainda sem resultado. **Filtrar/tratar essas linhas como pendentes**,
  não como erro nem como resultado zerado.
- **Qualificador embutido no resultado**: 9.434 de 11.120 resultados preenchidos (85%) vêm como texto com
  prefixo, ex. `"< 0,0030"`, `"< 0,01"`. É daqui que `qualifier` é derivado (seção 4). Os ~15% restantes
  são numéricos puros (ex. `"109,39"`), decimal com vírgula.
- **`Identificação`** é a chave de amostra: 0 nulos, 97 valores únicos, formato `SDN-83-SO-100826-0,5` —
  é o que se casa contra `SampleName` no join com `station`/`SYS_Sample` (seção 6). Repare que o prefixo
  varia (`SDN-`, `SDI-`) **dentro do mesmo arquivo/mesma campanha** — não usar prefixo como sinal de
  projeto, só `Proposta Comercial` mesmo.
- **226 parâmetros distintos** (`Identificação da Análise`) — dimensiona o esforço de acrescentar linhas
  no de-para universal.
- **Datas**: 100% no formato texto `dd/mm/yyyy hh:mm`, nenhuma variação encontrada nas 17.034 linhas.
- **Duplicidade**: zero linhas duplicadas exatas de (`Código da Amostra`, `Identificação da Análise`)
  dentro do arquivo.
- **Matriz**: só dois valores — `Solo` (16.678 linhas) e `Água subterrânea` (356 linhas).
