"""
Configuração central por projeto (campanha).

Cada notebook do pipeline recebe um widget `projeto` (ex.: "1233_IC_BA") e usa
get_config(projeto) para carregar todos os valores específicos daquele projeto
(pastas do SharePoint, filtro de campanha na API, filtro na tabela `station`,
grupos de parâmetros do escopo, etc.). Isso é o que garante que uma única
execução do Job nunca "vaza" para a pasta/planilha/webhook de outro projeto:
o resto do código nunca usa uma string literal de projeto, só `cfg[...]`.
"""

from .projetos import PROJETOS


def get_config(projeto: str) -> dict:
    """
    Retorna o dicionário de configuração do projeto solicitado.

    Falha alto (ValueError) se o projeto não estiver cadastrado — propositalmente
    não existe um valor default, pra nunca rodar silenciosamente com a
    configuração errada.
    """
    if not projeto:
        raise ValueError(
            "Widget 'projeto' vazio. Valores válidos: " + ", ".join(sorted(PROJETOS.keys()))
        )
    if projeto not in PROJETOS:
        raise ValueError(
            f"Projeto '{projeto}' não cadastrado em config/projetos.py. "
            f"Valores válidos: {', '.join(sorted(PROJETOS.keys()))}"
        )
    return PROJETOS[projeto]


__all__ = ["PROJETOS", "get_config"]
