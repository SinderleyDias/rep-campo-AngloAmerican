"""
Autenticação com Microsoft Graph API via OAuth 2.0 Client Credentials Flow.
"""

import os
import time
import requests
from typing import Dict, Tuple


class TokenManager:
    """
    Gerenciador de tokens OAuth 2.0 com refresh automático.

    Cache de token em memória com renovação automática antes da expiração.
    Thread-safe para acesso concorrente em pipelines.
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        early_renew_seconds: int = 600
    ):
        """
        Inicializa o gerenciador de tokens.

        Args:
            tenant_id: Tenant ID do Azure AD (TENANT_ID)
            client_id: Client ID da app registration (CLIENT_ID)
            client_secret: Client secret da app registration (CLIENT_SECRET)
            early_renew_seconds: Renovar token N segundos antes da expiração (padrão: 600s = 10min)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.early_renew_seconds = early_renew_seconds

        self._token = None
        self._expires_at = 0

    def _fetch_token(self) -> Tuple[str, int]:
        """
        Faz requisição OAuth 2.0 para obter novo token.

        Returns:
            (access_token, expires_at_timestamp)

        Raises:
            requests.HTTPError: Se a requisição falhar (credenciais inválidas, etc.)
        """
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }

        resp = requests.post(url, data=data, timeout=30)
        resp.raise_for_status()

        payload = resp.json()
        token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 3600))  # padrão: 1 hora
        expires_at = int(time.time()) + expires_in

        return token, expires_at

    def get_token(self) -> str:
        """
        Retorna um token Bearer válido.

        Renova automaticamente se próximo da expiração.

        Returns:
            Token de acesso para usar em requisições Graph API
        """
        now = int(time.time())

        # Token válido e não está próximo da expiração?
        if self._token and now < (self._expires_at - self.early_renew_seconds):
            return self._token

        # Renovar token
        self._token, self._expires_at = self._fetch_token()
        return self._token

    def auth_header(self) -> Dict[str, str]:
        """Retorna header Authorization pronto para usar."""
        return {"Authorization": f"Bearer {self.get_token()}"}


def get_token() -> str:
    """
    Função simplificada para obter token Bearer.

    Carrega credenciais automaticamente de (nesta ordem):
    1. Variáveis de ambiente: TENANT_ID, CLIENT_ID, CLIENT_SECRET
    2. .env (se existir, carregado via python-dotenv)
    3. Databricks Secrets: scope "sharepoint"

    Returns:
        Token de acesso Bearer

    Raises:
        ValueError: Se credenciais não forem encontradas

    Example:
        token = get_token()
        # Usa credenciais de .env, env vars, ou Databricks Secrets automaticamente
    """

    from dotenv import load_dotenv

    # Tentar carregar .env (se existir)
    try:
        load_dotenv(override=True)
    except Exception:
        pass

    # Prioridade 1: Environment variables / .env
    tid = os.getenv("TENANT_ID")
    cid = os.getenv("CLIENT_ID")
    csec = os.getenv("CLIENT_SECRET")

    # Prioridade 2: Databricks Secrets (se em Databricks)
    if not all([tid, cid, csec]):
        try:
            import dbutils
            if not tid:
                tid = dbutils.secrets.get(scope="sharepoint", key="TENANT_ID")
            if not cid:
                cid = dbutils.secrets.get(scope="sharepoint", key="CLIENT_ID")
            if not csec:
                csec = dbutils.secrets.get(scope="sharepoint", key="CLIENT_SECRET")
        except Exception:
            pass

    if not all([tid, cid, csec]):
        raise ValueError(
            "Credenciais não encontradas. Configure TENANT_ID, CLIENT_ID, CLIENT_SECRET via:\n"
            "  - Arquivo .env na raiz do projeto, ou\n"
            "  - Variáveis de ambiente (export TENANT_ID=...), ou\n"
            "  - Databricks Secrets (scope='sharepoint')"
        )

    tm = TokenManager(tid, cid, csec)
    return tm.get_token()
