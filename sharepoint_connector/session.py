"""
Sessão HTTP com retry automático e exponential backoff.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session(
    retries: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: tuple = (429, 500, 502, 503, 504),
    timeout: int = 30,
) -> requests.Session:
    """
    Cria uma sessão requests com retry automático.

    Args:
        retries: Número máximo de tentativas (padrão: 3)
        backoff_factor: Fator de exponential backoff (padrão: 0.3)
                       delay = backoff_factor * (2 ** (retry_num - 1))
        status_forcelist: Códigos HTTP que trigam retry (padrão: 429, 5xx)
        timeout: Timeout em segundos (padrão: 30)

    Returns:
        requests.Session configurada com retry automático

    Example:
        session = create_session()
        resp = session.get("https://graph.microsoft.com/v1.0/...", timeout=30)
    """

    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST", "PUT", "DELETE"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session
