"""
Resolução de segredos em runtime — nunca hardcoded em notebook nem em .py versionado.

Mesma prioridade usada em sharepoint_connector/auth.py:
    1. Variáveis de ambiente / .env (dev local)
    2. Databricks Secrets (produção)

Esses segredos são compartilhados entre projetos (mesma API, mesmo SQL Server,
mesmo tenant do Power Automate) — o que muda por projeto é só QUAL webhook do
Teams usar, e isso é resolvido pela chave de segredo (`teams_webhook_*_secret`)
cadastrada em config/projetos.py, não pelo valor em si.
"""

import os


def _load_dotenv():
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except Exception:
        pass


def _get_dbutils():
    """
    Retorna `dbutils` quando rodando no Databricks, senão None.

    `import dbutils` NÃO funciona de dentro de um módulo `.py` no Databricks
    (dbutils só existe no namespace do notebook). Resolve pelas vias suportadas:
    helper do runtime (DBR 13+), SparkSession ativa (clássico, funciona em Jobs)
    e por fim o global do notebook via IPython.
    """
    try:
        from databricks.sdk.runtime import dbutils as _db
        return _db
    except Exception:
        pass
    try:
        from pyspark.sql import SparkSession
        from pyspark.dbutils import DBUtils
        _spark = SparkSession.getActiveSession()
        if _spark is not None:
            return DBUtils(_spark)
    except Exception:
        pass
    try:
        import IPython
        _ip = IPython.get_ipython()
        if _ip is not None and "dbutils" in _ip.user_ns:
            return _ip.user_ns["dbutils"]
    except Exception:
        pass
    return None


def _get(env_key: str, secrets_scope: str, secrets_key: str) -> str:
    _load_dotenv()

    value = os.getenv(env_key)
    if value:
        return value

    _dbutils = _get_dbutils()
    if _dbutils is not None:
        try:
            value = _dbutils.secrets.get(scope=secrets_scope, key=secrets_key)
            if value:
                return value
        except Exception:
            pass

    raise ValueError(
        f"Segredo não encontrado: configure a variável de ambiente '{env_key}' "
        f"(.env) ou o Databricks Secret scope='{secrets_scope}' key='{secrets_key}'."
    )


def get_campo_api_token() -> str:
    """Bearer token da API Campo Análises (https://campoanalises.com.br/wst)."""
    return _get("CAMPO_API_TOKEN", "campo-api", "TOKEN")


def get_sql_credentials() -> dict:
    """
    Credenciais JDBC do SQL Server (tabela `station`/`SYS_Sample`), compartilhadas
    entre todos os projetos — só o filtro `source_project` muda por projeto.
    """
    return {
        "host": _get("SQLSERVER_HOST", "sqlserver", "HOST"),
        "port": _get("SQLSERVER_PORT", "sqlserver", "PORT"),
        "database": _get("SQLSERVER_DATABASE", "sqlserver", "DATABASE"),
        "user": _get("SQLSERVER_USER", "sqlserver", "USER"),
        "password": _get("SQLSERVER_PASSWORD", "sqlserver", "PASSWORD"),
    }


def get_teams_webhook_url(secret_key: str) -> str:
    """
    Resolve a URL do webhook do Power Automate a partir da chave de segredo
    cadastrada em config/projetos.py (ex.: "teams-webhook-resumo-ba").

    Convenção do nome da variável de ambiente local: a chave em maiúsculas,
    com "-" trocado por "_" (ex.: TEAMS_WEBHOOK_RESUMO_BA).
    """
    env_key = secret_key.upper().replace("-", "_")
    return _get(env_key, "teams-webhooks", secret_key)
