"""
Cadastro dos projetos (campanhas) atendidos por este pipeline.

Adicionar um novo projeto = adicionar uma nova entrada neste dicionário — os 4
notebooks não precisam mudar. A chave do dicionário é o valor que vai no widget
`projeto` do Job e também nomeia a pasta do projeto no data lake
(`/mnt/wst/<chave>/...`).

Segredos (token da API Campo, credenciais do SQL Server, URLs de webhook do
Teams) NÃO ficam aqui — isso é config versionada em git. Eles são resolvidos em
tempo de execução via config/secrets.py (Databricks Secrets / .env). Aqui só
guardamos: nomes de chave de segredo, caminhos, filtros e nomes de arquivo.
"""

PROJETOS = {
    "1233_IC_BA": {
        # Nome de exibição usado nos cartões do Teams
        "nome_exibicao": "AA - Investigação Confirmatória (Barro Alto)",

        # Filtro aplicado sobre a coluna `campanha` retornada pela API Campo Análises
        "campanha_api": "Projeto_1233_IC_BA",

        # Filtro aplicado na query JDBC contra a tabela `station` (SQL Server)
        "source_project_sql": "AA Barro Alto - Investigacao Confirmatoria",

        # De-para de Sample Name / Parâmetros (notebook 02)
        "sharepoint_depara_folder": (
            "General/06 - Análise de dados/Suporte Digital/Barro Alto/"
            "Investigação Confirmatória/Depara"
        ),
        "depara_filename": "Depara_1233_IC_BA.xlsx",

        # Escopo contratado / planejamento de amostragem (notebook 03)
        "sharepoint_escopo_folder": (
            "General/06 - Análise de dados/Suporte Digital/Barro Alto/"
            "Investigação Confirmatória/Escopo Contrato"
        ),
        "escopo_filename": "Pontos_IC_BA_SETOR 3 e Posto.xlsx",
        "escopo_sheet_names": {
            "escopo": "EscopoCampoAnalises",
            "solo": "SOLO",
            "asub": "ASUB",
        },

        # Grupos de parâmetros planejados por matriz (colunas da aba SOLO/ASUB
        # do arquivo de escopo acima) — específico da estrutura desse arquivo,
        # revisar ao cadastrar um projeto novo com planilha de escopo diferente
        "grupos_solo": [
            "Metais (CONAMA 420)", "Ions", "pH", "VOC", "SVOC", "TPH Fingerprint", "PCB",
        ],
        "grupos_asub": [
            "Metais Totais", "Metais Dissolvidos", "Ions", "VOC", "SVOC",
            "TPH FP", "Nitrogênio amoniacal", "Nitrato", "Coliformes", "E.coli", "DBO", "DQO",
        ],
        # De-para entre o nome da coluna na aba ASUB e o valor de "Planejamento"
        # usado no EscopoCampoAnalises (nomes não batem 1:1 — ver notebook 03)
        "mapa_grupo_asub": {
            "Metais Totais": "Metais Totais",
            "Metais Dissolvidos": "Metais Dissolvidos",
            "Ions": "Ions",
            "VOC": "VOC",
            "SVOC": "SVOC",
            "TPH FP": "TPH",
            "Nitrogênio amoniacal": "Nitrogênio Amoniacal",
            "Nitrato": "Metais Totais",
            "Coliformes": "Coliformes Totais",
            "E.coli": "Escherichia coli (E. coli)",
            "DBO": "DBO",
            "DQO": "DQO",
        },

        # Entrega final (notebook 04)
        "sharepoint_envio_folder": (
            "General/06 - Análise de dados/Suporte Digital/Barro Alto/"
            "Investigação Confirmatória/Edds Semanais"
        ),
        "link_base_teams": (
            "https://waterltda.sharepoint.com/:f:/r/sites/1233_BR_SE_AA_PGRH_GAC_BACKGROUND/"
            "Documentos%20Compartilhados/General/06%20-%20An%C3%A1lise%20de%20dados/"
            "Suporte%20Digital/Barro%20Alto/Investiga%C3%A7%C3%A3o%20Confirmat%C3%B3ria/"
            "Edds%20Semanais?d=w15161ccaebb94acf8c679a92a92c38c9&csf=1&web=1&e=hNWl3A"
        ),

        # Chaves de segredo (não os valores!) resolvidas via config/secrets.py
        "teams_webhook_resumo_secret": "teams-webhook-resumo-ba",
        "teams_webhook_tecnico_secret": "teams-webhook-tecnico-ba",
    },

    "1233_IC_CDM": {
        # TODO(Sinderley): preencher com os valores reais do projeto CDM antes
        # de agendar o Job para esta campanha. Os campos abaixo são só os
        # nomes das chaves — nenhum notebook vai rodar corretamente pra CDM
        # enquanto isso não for preenchido.
        "nome_exibicao": "AA - Investigação Confirmatória (CDM)",  # TODO: confirmar nome oficial
        "campanha_api": "Projeto_1233_IC_CDM",
        "source_project_sql": None,  # TODO: valor de source_project na tabela `station` p/ CDM

        "sharepoint_depara_folder": None,  # TODO
        "depara_filename": None,  # TODO: ex. "Depara_1233_IC_CDM.xlsx"

        "sharepoint_escopo_folder": None,  # TODO
        "escopo_filename": None,  # TODO
        "escopo_sheet_names": {
            "escopo": "EscopoCampoAnalises",  # TODO: confirmar se o nome da aba é o mesmo
            "solo": "SOLO",
            "asub": "ASUB",
        },

        "grupos_solo": [],  # TODO: colunas de grupo de parâmetro da aba SOLO do escopo CDM
        "grupos_asub": [],  # TODO: idem para ASUB
        "mapa_grupo_asub": {},  # TODO: de-para coluna ASUB -> "Planejamento" do escopo CDM

        "sharepoint_envio_folder": None,  # TODO
        "link_base_teams": None,  # TODO: link da pasta no SharePoint p/ o cartão do Teams

        "teams_webhook_resumo_secret": "teams-webhook-resumo-cdm",  # TODO: criar o fluxo no Power Automate
        "teams_webhook_tecnico_secret": "teams-webhook-tecnico-cdm",
    },
}
