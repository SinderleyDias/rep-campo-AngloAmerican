"""
Módulo consolidado para integração com SharePoint via Microsoft Graph API.

Carrega credenciais automaticamente de .env ou Databricks Secrets.
Específico para a biblioteca "Documentos Compartilhados" em waterltda.sharepoint.com.

Funcionalidades:
- Autenticação OAuth 2.0 (Client Credentials Flow) — automática
- Download de arquivos do SharePoint
- Upload de arquivos para o SharePoint
- Retry automático com exponential backoff
- Configuração via .env ou variáveis de ambiente

Uso básico:
    from sharepoint_connector import download_file_by_name, upload_file

    # Download (credenciais carregadas automaticamente)
    download_file_by_name(
        folder_path="General/Projetos/Dados",
        filename="meus_dados.xlsx",
        local_path="/tmp/meus_dados.xlsx"
    )

    # Upload
    upload_file(
        folder_path="General/Projetos/Resultados",
        local_path="/tmp/resultado.xlsx",
        filename="resultado_2026_07_15.xlsx"
    )

Configuração:
    Criar .env na raiz do projeto com:
        TENANT_ID=...
        CLIENT_ID=...
        CLIENT_SECRET=...
        DRIVE_ID=...
        MNT_ROOT="/mnt/wst"

    Mudar para outro ambiente? Basta trocar o .env.
"""

from .auth import get_token
from .download import download_file, download_file_by_name
from .upload import upload_file
from .utils import parse_sharepoint_url, get_dbutils

__all__ = [
    "get_token",
    "download_file",
    "download_file_by_name",
    "upload_file",
    "parse_sharepoint_url",
    "get_dbutils",
]
