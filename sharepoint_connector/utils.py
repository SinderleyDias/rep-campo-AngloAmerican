"""
Utilitários para integração com SharePoint.
"""

import urllib.parse


def parse_sharepoint_url(url: str) -> tuple[str, str]:
    """
    Parse de URL do SharePoint para extrair site e folder path.

    Args:
        url: URL completa da pasta no SharePoint
             (ex: https://waterltda.sharepoint.com/sites/WSTTeam/Documentos%20Compartilhados/...)

    Returns:
        (site_in_graph_format, folder_path_relative_to_library)

        site: Formato Graph (hostname:/sites/siteName)
              ex: waterltda.sharepoint.com:/sites/WSTTeam

        folder_path: Caminho relativo à raiz da biblioteca
                    ex: "General/Projetos/Dados"

    Raises:
        ValueError: Se URL estiver malformada ou sem parâmetro 'id'

    Example:
        url = "https://waterltda.sharepoint.com/sites/WSTTeam/Documentos%20..."
        site, folder = parse_sharepoint_url(url)
        # site = "waterltda.sharepoint.com:/sites/WSTTeam"
        # folder = "General/Projetos/Dados"
    """

    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    query_params = urllib.parse.parse_qs(parsed.query)

    # Extrair site name
    path_parts = parsed.path.strip("/").split("/")
    try:
        sites_idx = path_parts.index("sites")
        site_name = path_parts[sites_idx + 1]
    except (ValueError, IndexError):
        raise ValueError("Could not parse site name from URL (expected /sites/<siteName>/)")

    site = f"{hostname}:/sites/{site_name}"

    # Extrair folder path do query parameter 'id'
    raw_id = query_params.get("id", [None])[0]
    if not raw_id:
        raise ValueError("URL está incompleta — falta parâmetro 'id=...' (query string)")

    folder_path = urllib.parse.unquote(raw_id)

    # Remover prefixo /sites/<siteName>/
    prefix = f"/sites/{site_name}/"
    if folder_path.startswith(prefix):
        folder_path = folder_path[len(prefix):]

    # Remover nome da biblioteca (primeiro segmento)
    # ex: "Documentos Compartilhados/General/Projetos" → "General/Projetos"
    parts = folder_path.split("/", 1)
    if len(parts) > 1:
        folder_path = parts[1]
    else:
        folder_path = ""

    return site, folder_path
