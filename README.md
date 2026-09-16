# rep-campo-AngloAmerican

Pipeline único (Databricks Repo) para extrair, limpar, validar e entregar os resultados de laboratório
de **duas fontes** — API da Campo Análises (<https://campoanalises.com.br/wst>) e Excel da VSOL (portal ou
e-mail semanal) — para **todos os projetos/campanhas Anglo American** atendidos hoje — atualmente
`1233_IC_BA` (Barro Alto) e `1233_IC_CDM` (CODEMIN).

Este repositório substitui o modelo anterior de "um repositório por projeto"
([rep-campo-api-databricks](https://github.com/Waterservicestech/rep-campo-api-databricks), só BA):
os notebooks são compartilhados entre projetos e entre as duas fontes de dado, e o que muda (pastas do
SharePoint, filtro de campanha, grupos de parâmetros do escopo, webhooks do Teams etc.) vem de
`config/projetos.py`.

## Duas fontes, dois Jobs

O pipeline roda como **dois Jobs Databricks separados**, um por fonte, encadeados em sequência via
`dbutils.jobs.taskValues` (a task de extração grava `output_filename`, as próximas leem):

**Job Campo** (fonte = API):

1. `01_extracao_api.ipynb` (task key `fetch_from_aga_api`) — busca as amostras na API pelo período
   (widgets `inicio`/`fim`, calculado automaticamente se vazio — domingo a domingo da semana anterior),
   filtra pela campanha do projeto, grava na Bronze.
2. `02_limpeza.ipynb` (widget `fonte=api`, default) — normaliza datas/matriz, resolve Station e
   `quality_code` via SQL Server + de-para manual do SharePoint, padroniza parâmetro/unidade, grava na
   Silver (`api_limpo`).
3. `03_validacoes.ipynb` (widget `fonte=api`) — cruza com o escopo contratado do projeto (SharePoint),
   valida método/holding time/parâmetro fora do escopo/parâmetro faltante, exporta o Excel consolidado.
4. `04_envio_sharepoint.ipynb` (widget `fonte=api`) — envia o Excel pro SharePoint do projeto e dispara
   os cartões do Teams (Power Automate).
5. `05_qaqc.ipynb` — ver seção própria abaixo (roda igual nos dois Jobs).

**Job VSOL** (fonte = Excel, formato SITE ou E-MAIL):

1. `01_extracao_excel.ipynb` (mesma task key `fetch_from_aga_api`) — lê o Excel bruto que o Power
   Automate pousou na pasta do SharePoint (`sharepoint_vsol_bruto_folder`), filtra pela `Proposta
   Comercial` do projeto, grava na Bronze (`BRONZE/vsol/`). Ver "Dois formatos VSOL" abaixo.
2. `02_limpeza.ipynb` (widget `fonte=vsol`) — mesma lógica da Campo (é o mesmo notebook), só muda a
   pasta de leitura/gravação.
3. `03_validacoes.ipynb` (widget `fonte=vsol`).
4. `04_envio_sharepoint.ipynb` (widget `fonte=vsol`).
5. `05_qaqc.ipynb`.

Usar a **mesma task key** (`fetch_from_aga_api`) nas duas extrações é o que permite `02_limpeza`,
`03_validacoes` e `04_envio_sharepoint` serem literalmente o mesmo notebook nos dois Jobs — eles não
sabem (nem precisam saber) se o dado veio da API ou de um Excel da VSOL, só olham pra `fonte` pra decidir
pasta de leitura/gravação.

**Cada Run processa um projeto só** — a extração semanal dos dois projetos (BA e CDM) precisa de **dois
agendamentos separados por Job** (`projeto=1233_IC_BA` e `projeto=1233_IC_CDM`), não de tasks paralelas
no mesmo Run: os `taskValues` são lidos por chave de task, não por projeto, então dois projetos no mesmo
Run correm risco de uma task ler o `output_filename` errado.

### Dois formatos VSOL (SITE e E-MAIL)

A VSOL entrega dado de duas formas, com colunas bem diferentes entre si — detalhamento completo em
`docs/vsol-integracao.md`:

- **SITE** (download do portal): planilha única, achatada (uma linha por amostra × parâmetro).
- **E-MAIL** (semanal): duas abas relacionadas por `Cod Amostra Lab` — `SYS_Sample` (dados da amostra) e
  `SYS_SampleAnalysis` (dados do parâmetro).

O widget `formato` em `01_extracao_excel.ipynb` (`"auto"` / `"site"` / `"email"`) decide qual branch de
leitura roda; em `"auto"` (default), o notebook detecta sozinho pelo nome das abas do arquivo baixado.
Os dois branches convergem pro mesmo schema canônico antes da gravação na Bronze — os notebooks
seguintes não sabem nem precisam saber qual dos dois formatos gerou o dado.

**Pendente do laboratório**: o filtro de campanha do formato E-MAIL depende da coluna `Proposta
Comercial`, que o laboratório ainda não inclui nos arquivos reais enviados (ver `docs/vsol-integracao.md`,
seção 13). Até isso ser resolvido do lado do laboratório, quem for rodar o Job de e-mail em produção
precisa completar essa coluna manualmente no arquivo antes de disparar.

### `05_qaqc.ipynb` — sempre as duas fontes juntas

Roda **depois** do `04_envio_sharepoint`, nos dois Jobs. Não tem widget `fonte` como filtro — ele lê a
execução mais recente de **cada** fonte em `SILVER/api_validado/` (Campo e VSOL, quando existirem) e
junta as duas antes de rodar as checagens, garantindo que o QAQC sempre usa o dado mais atual disponível
de ambas, não importa qual dos dois Jobs disparou a execução. Checagens feitas: Surrogate (faixa
80–120%), Total vs. Dissolvido, DBO vs. DQO, consistência entre espécies de Cromo, Branco (resultado
acima do limite de quantificação) e RPD/Réplica (par de amostra ainda fixo por nome — pendente de
generalização via coluna `parent`, ver comentário no notebook).

## Widgets — dropdown sempre que o valor é um conjunto fechado

Pra evitar erro de digitação ao rodar manualmente no Databricks, todo widget cujos valores válidos já
são conhecidos de antemão é um dropdown, não texto livre:

| Widget     | Notebooks                                                                                                | Valores                                                                                    |
| ---------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `projeto`  | todos os 6                                                                                               | `PROJETOS.keys()` (`config/projetos.py`) — sem manutenção manual ao cadastrar projeto novo |
| `fonte`    | `02_limpeza`, `03_validacoes`, `04_envio_sharepoint` (filtra pasta), `05_qaqc` (só rótulo, não filtra dado) | `"api"` / `"vsol"`                                                                         |
| `formato`  | `01_extracao_excel`                                                                                       | `"auto"` / `"site"` / `"email"`                                                            |

Os únicos widgets que continuam texto livre são os que mudam a cada execução, sem lista fixa possível:
`inicio`/`fim` (datas da janela de coleta, `01_extracao_api`) e `arquivo` (nome do arquivo pousado pelo
Power Automate, `01_extracao_excel` — completa `.xlsx` sozinho se vier sem extensão).

### Widget `projeto` — como o fluxo nunca mistura projetos

Cada notebook, na primeira célula útil, faz:

```python
cfg = get_config(projeto)   # config/__init__.py
```

`get_config` falha alto (`ValueError`) se `projeto` vier vazio ou não estiver cadastrado em
`config/projetos.py` — nunca há um valor default silencioso. A partir daí, **todo** caminho de dado
(`/mnt/wst/{projeto}/...`), filtro (API `campanha`, SQL `source_project`), arquivo/pasta do SharePoint e
webhook do Teams vem de `cfg[...]`, nunca de uma string fixa. Isso é o que garante que uma execução do
projeto CDM não pode gravar, ler ou notificar em cima de dados do BA (e vice-versa) — o isolamento é por
config, não por lógica condicional espalhada pelo código.

## Qualidade de dado — pontos que já foram corrigidos

- **`quality_code`**: não vem mais do campo `codigoQualidade` da API (não confiável) — vem do SQL Server
  (`SYS_Sample.quality_code`), pelo mesmo join que já resolve `codigoHga`/`alternate_name` em
  `02_limpeza.ipynb` ("Mapeamento da Sample Name").
- **Limite de quantificação (LQ)**: parâmetros que chegam com `"-"` (sem LQ aplicável) viram `null`
  explicitamente, em vez de lixo na coluna. E o LQ agora segue a **mesma conversão de unidade** aplicada
  ao resultado (`resultadoCorrigido`) — antes, se o resultado era convertido (ex.: µg/L → mg/L), o LQ
  ficava pra trás na unidade antiga, invalidando qualquer comparação `value` × `quantification_limit`
  (ex.: a checagem de Branco no QAQC).

## Segredos

Nada de token/senha/URL de webhook fica em `config/projetos.py` (que é versionado em git) — só nomes de
chave. Os valores reais são resolvidos em runtime por `config/secrets.py`, na mesma ordem que
`sharepoint_connector/auth.py` já usava: variável de ambiente / `.env` primeiro (dev local), Databricks
Secrets depois (produção). Ver `.env.example` para a lista completa de variáveis e o scope/key
equivalente em Databricks Secrets.

## Adicionando um novo projeto

1. Adicionar uma entrada em `PROJETOS` (`config/projetos.py`) com a chave escolhida (ela também nomeia a
   pasta do projeto no data lake, `/mnt/wst/<chave>/...`, e aparece automaticamente no dropdown `projeto`
   de todos os notebooks).
2. Preencher os campos obrigatórios: `nome_exibicao`, `campanha_api`, `source_project_sql`,
   `sharepoint_depara_folder`/`depara_filename`, `sharepoint_vsol_bruto_folder`,
   `sharepoint_escopo_folder`/`escopo_filename`/`escopo_sheet_names`, `grupos_solo`/`grupos_asub`/
   `mapa_grupo_asub` (grupos de parâmetros planejados por matriz — específico da estrutura da planilha de
   escopo daquele projeto), `sharepoint_envio_folder`, `sharepoint_qaqc_folder`, `link_base_teams`.
3. Cadastrar os segredos do novo projeto (`teams_webhook_resumo_secret`, `teams_webhook_tecnico_secret`)
   em Databricks Secrets (ou `.env` local).
4. Criar os agendamentos dos dois Jobs (Campo e VSOL) com `projeto=<chave nova>`.

Nenhum notebook precisa mudar.

## Log de execução e notificação

Todo notebook mantém uma lista `execucao_steps` (etapa, status, registros lidos/escritos, flags,
observações), persistida em Delta (`{project_path}/execution_log`) ao final da execução via
`persistir_log()`. Esse log alimenta os cartões do Teams (Power Automate) disparados em
`04_envio_sharepoint.ipynb` e serve de histórico de auditoria por projeto — cada linha identifica
`projeto`, `notebook` e `batch_ts`.

## Reaproveitado do repositório anterior

- `sharepoint_connector/` — cliente Microsoft Graph (OAuth2 client-credentials, download/upload,
  retry) — genérico, sem alterações.
- `suporte/support_functions.py` — helpers PySpark (descoberta de batch, normalização de datas, etc.)
  — genérico, sem alterações.

## Para saber mais

`docs/vsol-integracao.md` tem o detalhamento completo da integração VSOL: perfil dos dois formatos de
arquivo, mapeamento coluna a coluna pro schema canônico, decisões de escopo e itens ainda em aberto.
