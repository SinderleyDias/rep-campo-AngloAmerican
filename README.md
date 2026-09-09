# rep-campo-AngloAmerican

Pipeline único (Databricks Repo) para extrair, limpar, validar e entregar os resultados de laboratório
da API Campo Análises (https://campoanalises.com.br/wst) para **todos os projetos/campanhas Anglo American**
atendidos hoje — atualmente `1233_IC_BA` (Barro Alto) e `1233_IC_CDM`.

Este repositório substitui o modelo anterior de "um repositório por projeto"
([rep-campo-api-databricks](https://github.com/Waterservicestech/rep-campo-api-databricks), só BA):
os 4 notebooks são compartilhados, e o que muda por projeto (pastas do SharePoint, filtro de campanha,
grupos de parâmetros do escopo, webhooks do Teams etc.) vem de `config/projetos.py`.

## Como funciona

Os 4 notebooks em `notebooks/` rodam em sequência, encadeados como tasks de um único Databricks Job
(via `dbutils.jobs.taskValues`, igual ao modelo anterior):

1. `01_extracao_api.ipynb` (task key: `fetch_from_aga_api`) — busca as amostras na API pelo período, filtra pela campanha do projeto, grava na Bronze.
2. `02_limpeza.ipynb` — normaliza datas/matriz, resolve Station via SQL Server + de-para manual do SharePoint, padroniza parâmetro/unidade, grava na Silver (`api_limpo`).
3. `03_validacoes.ipynb` — cruza com o escopo contratado do projeto (SharePoint), valida método/holding time/parâmetro fora do escopo/parâmetro faltante, exporta o Excel consolidado.
4. `04_envio_sharepoint.ipynb` — envia o Excel pro SharePoint do projeto e dispara os cartões do Teams (Power Automate).

### Widget `projeto` — como o fluxo nunca mistura projetos

Cada uma das 4 tasks declara o widget `projeto` (junto com `inicio`/`fim` na task 1) e faz, na primeira
célula útil:

```python
cfg = get_config(projeto)   # config/__init__.py
```

`get_config` falha alto (`ValueError`) se `projeto` vier vazio ou não estiver cadastrado em
`config/projetos.py` — nunca há um valor default silencioso. A partir daí, **todo** caminho de dado
(`/mnt/wst/{projeto}/...`), filtro (API `campanha`, SQL `source_project`), arquivo/pasta do SharePoint e
webhook do Teams vem de `cfg[...]`, nunca de uma string fixa. Isso é o que garante que uma execução do
projeto CDM não pode gravar, ler ou notificar em cima de dados do BA (e vice-versa) — o isolamento é por
config, não por lógica condicional espalhada pelo código.

**Agendamento**: como o Job inteiro roda com um único `projeto` de cada vez, a extração semanal dos dois
projetos precisa de **dois agendamentos (schedules/triggers) separados da mesma definição de Job** — um
fixando `projeto=1233_IC_BA`, outro `projeto=1233_IC_CDM` (mesmos notebooks, parâmetro diferente). Não
rode os dois projetos como tasks paralelas dentro do mesmo Job Run: os `taskValues` (`output_filename`)
são escritos e lidos por chave de task, não por projeto, então dois projetos no mesmo Run correm risco de
uma task ler o `output_filename` errado.

### Segredos

Nada de token/senha/URL de webhook fica em `config/projetos.py` (que é versionado em git) — só nomes de
chave. Os valores reais são resolvidos em runtime por `config/secrets.py`, na mesma ordem que
`sharepoint_connector/auth.py` já usava: variável de ambiente / `.env` primeiro (dev local), Databricks
Secrets depois (produção). Ver `.env.example` para a lista completa de variáveis e o scope/key
equivalente em Databricks Secrets.

## Adicionando um novo projeto

1. Adicionar uma entrada em `PROJETOS` (`config/projetos.py`) com a chave escolhida (ela também nomeia a
   pasta do projeto no data lake, `/mnt/wst/<chave>/...`).
2. Preencher todos os campos: filtro de campanha da API, filtro `source_project` do SQL Server, pastas e
   nomes de arquivo do SharePoint (de-para e escopo), grupos de parâmetros SOLO/ASUB do escopo daquele
   projeto, pasta de entrega e nome de exibição.
3. Cadastrar os segredos do novo projeto (webhooks do Teams) em Databricks Secrets (ou `.env` local).
4. Criar o segundo agendamento do Job com `projeto=<chave nova>`.

Nenhum dos 4 notebooks precisa mudar.

## Reaproveitado do repositório anterior

- `sharepoint_connector/` — cliente Microsoft Graph (OAuth2 client-credentials, download/upload,
  retry) — genérico, sem alterações.
- `suporte/support_functions.py` — helpers PySpark (descoberta de batch, normalização de datas, etc.)
  — genérico, sem alterações.
