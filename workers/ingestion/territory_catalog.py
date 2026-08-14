"""Provenance catalog for territorial attributes (official sources only)."""

from __future__ import annotations

TERRITORY_SPECS: dict[str, dict] = {
    "indigenous_population": {
        "id": "indigenous_population",
        "label": "Pessoas indígenas",
        "section": "povos",
        "unit": "pessoas",
        "status_label": "OBSERVADO",
        "reference_period": "2022",
        "definition": (
            "Número de pessoas que se declararam indígenas no Censo Demográfico 2022 "
            "(quesito de declaração indígena, total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 9718 / variável 350",
            "url": "https://sidra.ibge.gov.br/tabela/9718",
        },
        "limitations": [
            "Não lista etnias nem povos específicos.",
            "Baseado em autodeclaração no Censo; não é cadastro FUNAI.",
        ],
    },
    "indigenous_share": {
        "id": "indigenous_share",
        "label": "Participação indígena na população",
        "section": "povos",
        "unit": "%",
        "status_label": "OBSERVADO",
        "reference_period": "2022",
        "definition": (
            "Percentual de pessoas indígenas no total da população residente "
            "(Censo Demográfico 2022)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 9718 / variável 4727",
            "url": "https://sidra.ibge.gov.br/tabela/9718",
        },
        "limitations": [
            "Comparar apenas com o mesmo recorte censitário.",
        ],
    },
    "quilombola_residents": {
        "id": "quilombola_residents",
        "label": "Moradores quilombolas",
        "section": "povos",
        "unit": "pessoas",
        "status_label": "OBSERVADO",
        "reference_period": "2022",
        "definition": (
            "Moradores quilombolas em domicílios particulares permanentes ocupados "
            "(Censo Demográfico 2022)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 9727 / variável 7097",
            "url": "https://sidra.ibge.gov.br/tabela/9727",
        },
        "limitations": [
            "Autodeclaração no Censo; não substitui cadastros de territórios quilombolas.",
        ],
    },
    "biome_predominant": {
        "id": "biome_predominant",
        "label": "Bioma predominante",
        "section": "territorio",
        "unit": None,
        "status_label": "OBSERVADO",
        "reference_period": "2024",
        "definition": (
            "Bioma de maior área territorial no município, segundo o produto IBGE "
            "“Bioma predominante por Município para fins estatísticos” (2024)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Bioma_Predominante_por_Municipio_2024",
            "url": (
                "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/"
                "biomas/documentos/Bioma_Predominante_por_Municipio_2024.csv"
            ),
        },
        "limitations": [
            "Um município pode ter mais de um bioma; aqui consta só o predominante.",
        ],
    },
    "biomes_present": {
        "id": "biomes_present",
        "label": "Biomas presentes (municípios)",
        "section": "territorio",
        "unit": None,
        "status_label": "DERIVADO",
        "reference_period": "2024",
        "definition": (
            "Lista dos biomas predominantes que aparecem em pelo menos um município "
            "da UF, a partir do produto IBGE 2024 (não é mapa de área por bioma na UF)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Bioma_Predominante_por_Municipio_2024 (rollup UF)",
            "url": (
                "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/"
                "biomas/documentos/Bioma_Predominante_por_Municipio_2024.csv"
            ),
        },
        "limitations": [
            "Agregação por contagem de municípios, não por área do bioma na UF.",
        ],
    },
    "area_km2": {
        "id": "area_km2",
        "label": "Área territorial",
        "section": "territorio",
        "unit": "km²",
        "status_label": "OBSERVADO",
        "reference_period": "2010",
        "definition": (
            "Área total da unidade territorial publicada no agregado IBGE 1301 "
            "(referência 2010)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 1301 / variável 615",
            "url": "https://sidra.ibge.gov.br/tabela/1301",
        },
        "limitations": [
            "Período do agregado é 2010; limites territoriais posteriores podem diferir.",
        ],
    },
    "population_density": {
        "id": "population_density",
        "label": "Densidade demográfica (derivada)",
        "section": "territorio",
        "unit": "hab/km²",
        "status_label": "DERIVADO",
        "reference_period": "misto",
        "definition": (
            "População residente estimada (IBGE agregados 6579) dividida pela área "
            "territorial do agregado 1301 (2010)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "6579 (população) ÷ 1301/615 (área 2010)",
            "url": "https://sidra.ibge.gov.br/tabela/1301",
        },
        "limitations": [
            "Numeros de anos diferentes: população recente ÷ área 2010.",
            "Não usar como densidade oficial do Censo do mesmo ano.",
        ],
    },
    "coastal_marine": {
        "id": "coastal_marine",
        "label": "Município costeiro/marinho",
        "section": "territorio",
        "unit": None,
        "status_label": "OBSERVADO",
        "reference_period": "2019",
        "definition": (
            "Indica se o município consta na lista IBGE de municípios costeiro/marinhos "
            "(produto complementar de biomas / zona costeira)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Lista_Municipio_CosteiroMarinho_250mil",
            "url": (
                "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/"
                "biomas/documentos/Lista_Municipio_CosteiroMarinho_250mil.xls"
            ),
        },
        "limitations": [
            "Classificação geográfica IBGE; não mede extensão de litoral.",
        ],
    },
}

# Metric definitions for existing UF indicators (tooltips on fiche)
METRIC_DEFINITIONS: dict[str, dict] = {
    "population": {
        "definition": (
            "Estimativa da população residente na Unidade da Federação, "
            "publicada pelo IBGE (agregado 6579)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 6579 / variável 9324",
            "url": "https://sidra.ibge.gov.br/tabela/6579",
        },
        "limitations": [
            "Estimativa anual; não é contagem censitária do mesmo ano.",
        ],
    },
    "pib": {
        "definition": (
            "Produto Interno Bruto a preços correntes da UF (contas regionais IBGE)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 5938 / variável 37",
            "url": "https://sidra.ibge.gov.br/tabela/5938",
        },
        "limitations": [
            "Série anual com defasagem típica de publicação.",
        ],
    },
    "poverty_rate": {
        "definition": (
            "Proporção da população abaixo da linha de pobreza nacional do IBGE "
            "(indicador ODS 1.2.1)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 5877 / variável 9948",
            "url": "https://sidra.ibge.gov.br/tabela/5877",
        },
        "limitations": [
            "Não confundir com linhas do Banco Mundial.",
        ],
    },
    "literacy_rate": {
        "definition": (
            "Taxa de alfabetização da população de 15 anos ou mais (Censo Demográfico)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 9543 / variável 2513",
            "url": "https://sidra.ibge.gov.br/tabela/9543",
        },
        "limitations": [
            "Alfabetização ≠ qualidade da educação nem IDEB.",
        ],
    },
    "unemployment_rate": {
        "definition": (
            "Taxa de desocupação das pessoas de 14 anos ou mais (PNAD Contínua)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 4099 / variável 4099",
            "url": "https://sidra.ibge.gov.br/tabela/4099",
        },
        "limitations": [
            "Taxa trimestral; sujeita a sazonalidade.",
        ],
    },
    "homicide_rate": {
        "definition": (
            "Número de óbitos classificados como homicídio por 100 mil habitantes "
            "residentes na UF (série Ipeadata AVIOL12_THOMIC / Atlas da Violência)."
        ),
        "source": {
            "organization": "IPEA / DATASUS",
            "dataset": "Ipeadata AVIOL12_THOMIC",
            "url": "http://www.ipeadata.gov.br/ExibeSerie.aspx?serid=AVIOL12_THOMIC",
        },
        "limitations": [
            "Não confundir com MVI do Anuário FBSP — metodologias distintas.",
            "Subnotificação e mudança de codificação CID no SIM podem afetar a série.",
        ],
    },
    "homicide_count": {
        "definition": (
            "Número absoluto de óbitos classificados como homicídio na UF "
            "(série Ipeadata AVIOL12_HOMIC, origem DATASUS)."
        ),
        "source": {
            "organization": "DATASUS / IPEA",
            "dataset": "Ipeadata AVIOL12_HOMIC",
            "url": "http://www.ipeadata.gov.br/ExibeSerie.aspx?serid=AVIOL12_HOMIC",
        },
        "limitations": [
            "Para comparar UFs, preferir a taxa por 100 mil habitantes.",
        ],
    },
    "traffic_death_rate": {
        "definition": (
            "Óbitos de vítimas de acidente de trânsito por 100 mil habitantes na UF "
            "(série Ipeadata AVIOL12_TACIDT)."
        ),
        "source": {
            "organization": "IPEA / DATASUS",
            "dataset": "Ipeadata AVIOL12_TACIDT",
            "url": "http://www.ipeadata.gov.br/ExibeSerie.aspx?serid=AVIOL12_TACIDT",
        },
        "limitations": [
            "Pode diferir de estatísticas policiais de trânsito.",
        ],
    },
    "export_meat_fob": {
        "definition": (
            "Valor FOB (US$) das exportações do capítulo SH 02 (carnes e miudezas), "
            "por UF de origem do produto (Comex Stat / MDIC)."
        ),
        "source": {
            "organization": "MDIC — Comex Stat",
            "dataset": "API Comex Stat / chapter 02",
            "url": "https://comexstat.mdic.gov.br/",
        },
        "limitations": [
            "Inclui bovino, suíno, aves e outras carnes.",
        ],
    },
    "export_bovine_fob": {
        "definition": (
            "Valor FOB (US$) de carne bovina SH 0201+0202 por UF de origem (Comex Stat / MDIC)."
        ),
        "source": {
            "organization": "MDIC — Comex Stat",
            "dataset": "API Comex Stat / headings 0201+0202",
            "url": "https://comexstat.mdic.gov.br/",
        },
        "limitations": [
            "Não inclui miudezas bovinas em outras posições SH.",
        ],
    },
    "export_soy_fob": {
        "definition": (
            "Valor FOB (US$) de soja em grão (SH 1201) por UF de origem (Comex Stat / MDIC)."
        ),
        "source": {
            "organization": "MDIC — Comex Stat",
            "dataset": "API Comex Stat / heading 1201",
            "url": "https://comexstat.mdic.gov.br/",
        },
        "limitations": [
            "Não inclui farelo nem óleo de soja.",
        ],
    },
}
