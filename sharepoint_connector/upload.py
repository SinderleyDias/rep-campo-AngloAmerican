"""
Upload de arquivos para o SharePoint.
"""

import os
import requests
from urllib.parse import quote
from typing import Optional

from .session import create_session
from .auth import get_token


def _get_drive_id() -> str:
    """Carrega DRIVE_ID do .env ou environment."""
    from dotenv import load_dotenv

    try:
        load_dotenv(override=True)
    except Exception:
        pass

    drive_id = os.getenv("DRIVE_ID")
    if not drive_id:
        try:
            from .utils import get_dbutils
            dbutils = get_dbutils()
            if dbutils is not None:
                drive_id = dbutils.secrets.get(scope="sharepoint", key="DRIVE_ID")
        except Exception:
            pass

    if not drive_id:
        raise ValueError("DRIVE_ID não encontrado em .env ou Databricks Secrets")

    return drive_id


def upload_file(
    folder_path: str,
    local_path: str,
    filename: Optional[str] = None,
    token: Optional[str] = None,
) -> dict:
    """
    Faz upload de um arquivo local para o SharePoint.

    Credenciais carregadas automaticamente de .env ou Databricks Secrets.

    Args:
        folder_path: Caminho da pasta de destino no SharePoint (ex: "General/Projetos/Dados")
        local_path: Caminho local do arquivo (ex: /tmp/arquivo.xlsx ou dbfs:/mnt/arquivo.xlsx)
        filename: Nome do arquivo no SharePoint (padrão: nome do arquivo local)
        token: Bearer token (opcional — gerado automaticamente se não fornecido)

    Returns:
        Dict com resultado:
            {
                "status": "success" | "error",
                "filename": nome do arquivo no SharePoint,
                "web_url": URL públco do arquivo (se sucesso),
                "size_bytes": tamanho do arquivo,
                "error": mensagem de erro (se houver)
            }

    Example:
        result = upload_file(
            folder_path="General/Projetos/Dados",
            local_path="/tmp/resultado.xlsx",
            filename="resultado_2026_07_15.xlsx"
        )
        if result["status"] == "success":
            print(f"✓ Enviado para: {result['web_url']}")
    """

    if not token:
        token = get_token()

    drive_id = _get_drive_id()

    # Converter caminho DBFS para local se necessário
    if local_path.startswith("dbfs:/"):
        local_path = "/dbfs" + local_path[len("dbfs:"):]

    # Validar arquivo local
    if not os.path.isfile(local_path):
        return {
            "status": "error",
            "filename": filename or os.path.basename(local_path),
            "web_url": None,
            "size_bytes": 0,
            "error": f"Arquivo não encontrado: {local_path}",
        }

    # Determinar nome do arquivo no SharePoint
    target_filename = filename or os.path.basename(local_path)

    session = create_session()
    headers = {"Authorization": f"Bearer {token}"}

    # Construir URL
    # /drives/{driveId}/root:/{folder_path}/{filename}:/content
    path_encoded = quote(f"{folder_path}/{target_filename}", safe="/")
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{path_encoded}:/content"

    try:
        # Ler arquivo
        with open(local_path, "rb") as f:
            file_content = f.read()

        size_bytes = len(file_content)

        # Upload
        resp = session.put(url, data=file_content, headers=headers, timeout=300)
        resp.raise_for_status()

        response_data = resp.json()
        web_url = response_data.get("webUrl", "")

        return {
            "status": "success",
            "filename": target_filename,
            "web_url": web_url,
            "size_bytes": size_bytes,
            "error": None,
        }

    except requests.RequestException as e:
        return {
            "status": "error",
            "filename": target_filename,
            "web_url": None,
            "size_bytes": 0,
            "error": str(e),
        }
    finally:
        session.close()
