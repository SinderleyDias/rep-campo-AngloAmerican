"""
Download de arquivos do SharePoint.
"""

import os
import requests
from typing import Optional
from urllib.parse import quote

from .session import create_session
from .auth import get_token


def _get_drive_id() -> str:
    """Carrega DRIVE_ID do .env ou environment."""
    import os
    from dotenv import load_dotenv

    try:
        load_dotenv(override=True)
    except Exception:
        pass

    drive_id = os.getenv("DRIVE_ID")
    if not drive_id:
        try:
            import dbutils
            drive_id = dbutils.secrets.get(scope="sharepoint", key="DRIVE_ID")
        except Exception:
            pass

    if not drive_id:
        raise ValueError("DRIVE_ID não encontrado em .env ou Databricks Secrets")

    return drive_id


def download_file(
    item_id: str,
    local_path: str,
    token: Optional[str] = None,
    chunk_size: int = 1024 * 1024,
) -> dict:
    """
    Faz download de um arquivo do SharePoint para o filesystem local.

    Credenciais carregadas automaticamente de .env ou Databricks Secrets.

    Args:
        item_id: ID do item/arquivo no SharePoint
        local_path: Caminho local onde salvar o arquivo (ex: /tmp/arquivo.xlsx)
        token: Bearer token (opcional — gerado automaticamente se não fornecido)
        chunk_size: Tamanho dos chunks para download (padrão: 1MB)

    Returns:
        Dict com resultado:
            {
                "status": "success" | "error",
                "local_path": caminho onde foi salvo,
                "size_bytes": tamanho baixado,
                "error": mensagem de erro (se houver)
            }

    Example:
        result = download_file(item_id="01ABC123...", local_path="/tmp/arquivo.xlsx")
        if result["status"] == "success":
            print(f"✓ Salvo em {result['local_path']} ({result['size_bytes']} bytes)")
    """

    if not token:
        token = get_token()

    drive_id = _get_drive_id()

    session = create_session()
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = session.get(url, headers=headers, stream=True, timeout=300)
        resp.raise_for_status()

        # Criar diretório se não existir
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)

        # Fazer download em chunks
        total_bytes = 0
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)

        return {
            "status": "success",
            "local_path": local_path,
            "size_bytes": total_bytes,
            "error": None,
        }

    except requests.RequestException as e:
        return {
            "status": "error",
            "local_path": local_path,
            "size_bytes": 0,
            "error": str(e),
        }
    finally:
        session.close()


def download_file_by_name(
    folder_path: str,
    filename: str,
    local_path: str,
    token: Optional[str] = None,
) -> dict:
    """
    Faz download de um arquivo pelo nome a partir de uma pasta específica.

    Útil quando você tem o caminho da pasta mas não o ID do arquivo.
    Credenciais carregadas automaticamente de .env ou Databricks Secrets.

    Args:
        folder_path: Caminho da pasta no SharePoint (ex: "General/Projetos/Dados")
        filename: Nome do arquivo a baixar (ex: "meus_dados.xlsx")
        local_path: Caminho local onde salvar
        token: Bearer token (opcional — gerado automaticamente se não fornecido)

    Returns:
        Dict com resultado (mesma estrutura de download_file)

    Example:
        result = download_file_by_name(
            folder_path="General/Projetos/Dados",
            filename="meus_dados.xlsx",
            local_path="/tmp/meus_dados.xlsx"
        )
    """

    if not token:
        token = get_token()

    drive_id = _get_drive_id()

    session = create_session()
    headers = {"Authorization": f"Bearer {token}"}

    # Construir URL para fazer request by path
    # /drives/{driveId}/root:/{path}:
    path_encoded = quote(f"{folder_path}/{filename}", safe="/")
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{path_encoded}:/content"

    try:
        resp = session.get(url, headers=headers, stream=True, timeout=300)
        resp.raise_for_status()

        # Criar diretório se não existir
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)

        # Fazer download em chunks
        total_bytes = 0
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)

        return {
            "status": "success",
            "local_path": local_path,
            "size_bytes": total_bytes,
            "error": None,
        }

    except requests.RequestException as e:
        return {
            "status": "error",
            "local_path": local_path,
            "size_bytes": 0,
            "error": str(e),
        }
    finally:
        session.close()
