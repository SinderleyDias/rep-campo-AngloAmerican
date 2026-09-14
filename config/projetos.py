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

        # Pasta onde o Power Automate pousa o Excel bruto da VSOL (notebook 01_extracao_excel).
        # Mesma pasta pros dois projetos (BA e CDM) -- quem separa o projeto e o proprio
        # conteudo do arquivo (coluna "Proposta Comercial"), nao a pasta. Ver docs/vsol-integracao.md.
        "sharepoint_vsol_bruto_folder": "General/06 - Análise de dados/Suporte Digital/dados_brutos_vsol",

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
        "nome_exibicao": "AA - Investigação Confirmatória (CDM)",
        "campanha_api": "Projeto_1233_IC_CDM",
        # TEMPORARIO: amostras da propriedade CDM que o laboratorio classificou sob
        # a campanha "Projeto_1233_BR_SE_AA" por engano. Ja foi pedida a
        # reclassificacao ao lab -- remover esta chave quando as amostras voltarem
        # como Projeto_1233_IC_CDM. Confirmar o valor EXATO da coluna `campanha` na
        # API antes de rodar (ver df_final.select("campanha").distinct() no nb1).
        "campanhas_api_extra": ["Projeto 1233_BR_SE_AA"],
        "source_project_sql": 'AA Codemin - Investigacao Confirmatoria',
        "sharepoint_depara_folder": ("General/06 - Análise de dados/Suporte Digital/Barro Alto/Investigação Confirmatória/Depara"),
        "depara_filename": "Depara_1233_IC_BA.xlsx",

        # Pasta onde o Power Automate pousa o Excel bruto da VSOL (notebook 01_extracao_excel).
        # Mesma pasta pros dois projetos (BA e CDM) -- quem separa o projeto e o proprio
        # conteudo do arquivo (coluna "Proposta Comercial"), nao a pasta. Ver docs/vsol-integracao.md.
        "sharepoint_vsol_bruto_folder": "General/06 - Análise de dados/Suporte Digital/dados_brutos_vsol",

        "sharepoint_escopo_folder": None, #("General/06 - Análise de dados/Suporte Digital/Barro Alto/Investigação Confirmatória/Escopo Contrato") ,

        "escopo_filename": None,  # TODO
        "escopo_sheet_names": {
            "escopo": "EscopoCampoAnalises",  # TODO: confirmar se o nome da aba é o mesmo
            "solo": "SOLO",
            "asub": "ASUB",
        },

        "grupos_solo": [],  # TODO: colunas de grupo de parâmetro da aba SOLO do escopo CDM
        "grupos_asub": [],  # TODO: idem para ASUB
        "mapa_grupo_asub": {},  # TODO: de-para coluna ASUB -> "Planejamento" do escopo CDM

        "sharepoint_envio_folder": ("General/06 - Análise de dados/Suporte Digital/CODEMIN/Investigação Confirmatória/Edds Semanais"),  
        "link_base_teams": 'https://waterltda.sharepoint.com/sites/1233_BR_SE_AA_PGRH_GAC_BACKGROUND/Documentos%20Compartilhados/Forms/AllItems.aspx?id=%2Fsites%2F1233%5FBR%5FSE%5FAA%5FPGRH%5FGAC%5FBACKGROUND%2FDocumentos%20Compartilhados%2FGeneral%2F06%20%2D%20An%C3%A1lise%20de%20dados%2FSuporte%20Digital%2FCODEMIN%2FInvestiga%C3%A7%C3%A3o%20Confirmat%C3%B3ria%2FEdds%20Semanais&viewid=51929565%2D9b45%2D4604%2D8c4a%2D2709e1fed868&d=w72e083cf0abf4e4eb5fcd64877e4033c&csf=1&ovuser=fea66664%2D4a84%2D4539%2D8269%2Dee79f745a3f4%2Csinderley%2Edias%40waterservicestech%2Ecom&TeamsCID=6983c005%2Df47e%2D47e3%2D9cba%2Dacfb6f461ac1&OR=Teams%2DHL&CT=1785848429880&clickparams=eyJBcHBOYW1lIjoiVGVhbXMtRGVza3RvcCIsIkFwcFZlcnNpb24iOiI0OS8yNjA3MDIxNTcxMSIsIkhhc0ZlZGVyYXRlZFVzZXIiOmZhbHNlfQ%3D%3D&CID=95f02da2%2Da081%2Da000%2D372a%2Dc66a954ee782&cidOR=SPO&FolderCTID=0x012000FAC4A9334C5EFD4CB04E39C937A3EDB5',

        "teams_webhook_resumo_secret": "teams-webhook-resumo-cdm",  # TODO: criar o fluxo no Power Automate
        "teams_webhook_tecnico_secret": "teams-webhook-tecnico-cdm",
    },
}
