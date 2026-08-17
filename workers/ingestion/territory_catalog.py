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
    "export_corn_fob": {
        "definition": (
            "Valor FOB (US$) das exportações de milho (SH 1005) por UF de origem (Comex Stat / MDIC)."
        ),
        "source": {
            "organization": "MDIC — Comex Stat",
            "dataset": "API Comex Stat / heading 1005",
            "url": "https://comexstat.mdic.gov.br/",
        },
        "limitations": [
            "Não inclui milho doce preparado nem farelos.",
        ],
    },
    "export_soy_meal_fob": {
        "definition": (
            "Valor FOB (US$) de farelo/resíduos de soja (SH 2304) por UF de origem (Comex Stat / MDIC)."
        ),
        "source": {
            "organization": "MDIC — Comex Stat",
            "dataset": "API Comex Stat / heading 2304",
            "url": "https://comexstat.mdic.gov.br/",
        },
        "limitations": [
            "Não inclui soja em grão (1201) nem óleo (1507).",
        ],
    },
    "export_iron_ore_fob": {
        "definition": (
            "Valor FOB (US$) das exportações do capítulo SH 26 (minérios, escórias e cinzas), "
            "por UF de origem (Comex Stat / MDIC)."
        ),
        "source": {
            "organization": "MDIC — Comex Stat",
            "dataset": "API Comex Stat / chapter 26",
            "url": "https://comexstat.mdic.gov.br/",
        },
        "limitations": [
            "Capítulo 26 inclui ferro e outros minérios.",
        ],
    },
    "export_soy_oil_fob": {
        "definition": (
            "Valor FOB (US$) de óleo de soja (SH 1507) por UF de origem (Comex Stat / MDIC)."
        ),
        "source": {
            "organization": "MDIC — Comex Stat",
            "dataset": "API Comex Stat / heading 1507",
            "url": "https://comexstat.mdic.gov.br/",
        },
        "limitations": [
            "Não inclui soja em grão (1201) nem farelo (2304).",
        ],
    },
    "export_petroleum_fob": {
        "definition": (
            "Valor FOB (US$) das exportações do capítulo SH 27 (combustíveis minerais, "
            "óleos minerais e produtos da destilação) por UF de origem (Comex Stat / MDIC)."
        ),
        "source": {
            "organization": "MDIC — Comex Stat",
            "dataset": "API Comex Stat / chapter 27",
            "url": "https://comexstat.mdic.gov.br/",
        },
        "limitations": [
            "Capítulo 27 inclui petróleo, derivados, carvão e gases — não é só petróleo cru.",
        ],
    },
    "area_km2": {
        "definition": "Área total da unidade territorial publicada no agregado IBGE 1301 (referência 2010).",
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
            "Números de anos diferentes: população recente ÷ área 2010.",
            "Não usar como densidade oficial do Censo do mesmo ano.",
        ],
    },
    "indigenous_population": {
        "definition": (
            "Número de pessoas que se declararam indígenas no Censo Demográfico 2022."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 9718 / variável 350",
            "url": "https://sidra.ibge.gov.br/tabela/9718",
        },
        "limitations": [
            "Autodeclaração no Censo; não é cadastro FUNAI.",
        ],
    },
    "indigenous_share": {
        "definition": (
            "Percentual de pessoas indígenas no total da população residente (Censo 2022)."
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
        "definition": (
            "Moradores quilombolas em domicílios particulares permanentes ocupados (Censo 2022)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 9727 / variável 7097",
            "url": "https://sidra.ibge.gov.br/tabela/9727",
        },
        "limitations": [
            "IBGE publica '-' para AC e RR neste recorte; interpretado como 0.",
        ],
    },
    "pib_per_capita": {
        "definition": (
            "PIB a preços correntes (IBGE 5938/37) dividido pela população residente estimada "
            "(IBGE 6579) — razão local, rótulo DERIVADO."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "5938/37 ÷ 6579",
            "url": "https://sidra.ibge.gov.br/tabela/5938",
        },
        "limitations": [
            "A tabela 5938 não publica PIB per capita; não usar como renda domiciliar.",
        ],
    },
    "pib_share": {
        "definition": (
            "PIB da UF dividido pelo PIB do Brasil na mesma publicação de contas regionais (IBGE 5938/37)."
        ),
        "source": {
            "organization": "Brasil Real",
            "dataset": "PIB UF ÷ PIB Brasil",
            "url": "https://sidra.ibge.gov.br/tabela/5938",
        },
        "limitations": [
            "Participação nominal; UFs grandes dominam.",
        ],
    },
    "sanitation_adequate": {
        "definition": (
            "Percentual de domicílios com esgotamento na categoria IBGE «Rede geral, rede "
            "pluvial ou fossa ligada à rede» (SIDRA 6805, Censo 2022)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 6805 / 46290÷46292",
            "url": "https://sidra.ibge.gov.br/tabela/6805",
        },
        "limitations": [
            "Razão de duas contagens oficiais da mesma tabela (DERIVADO).",
        ],
    },
    "water_network_share": {
        "definition": (
            "Percentual de domicílios cuja forma principal de abastecimento é a rede geral "
            "(SIDRA 6803, Censo 2022)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 6803 / 1000381 / 72144",
            "url": "https://sidra.ibge.gov.br/tabela/6803",
        },
        "limitations": [
            "Não mede qualidade nem continuidade do serviço.",
        ],
    },
    "waste_collected_share": {
        "definition": (
            "Percentual de domicílios com destino do lixo na categoria IBGE «Coletado» "
            "(SIDRA 6892, Censo 2022)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 6892 / 1000381 / 2520",
            "url": "https://sidra.ibge.gov.br/tabela/6892",
        },
        "limitations": [
            "Não mede destinação final (aterro/lixão).",
        ],
    },
    "pns_tobacco_smokers": {
        "definition": (
            "Percentual de pessoas de 18 anos ou mais fumantes atuais de tabaco (PNS 2019)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 4173 / var 4163",
            "url": "https://sidra.ibge.gov.br/tabela/4173",
        },
        "limitations": [
            "Retrato amostral de 2019; não atualizar para anos seguintes.",
        ],
    },
    "pns_diabetes": {
        "definition": (
            "Percentual de pessoas de 18 anos ou mais que referem diagnóstico médico de diabetes "
            "(PNS 2019)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 4487 / var 4465",
            "url": "https://sidra.ibge.gov.br/tabela/4487",
        },
        "limitations": [
            "Autoreferido; retrato de 2019.",
        ],
    },
    "pns_health_plan": {
        "definition": (
            "Percentual de pessoas com plano de saúde médico (PNS 2019, SIDRA 7570)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 7570 / var 10908",
            "url": "https://sidra.ibge.gov.br/tabela/7570",
        },
        "limitations": [
            "Retrato amostral de 2019; plano médico, não odontológico isolado.",
        ],
    },
    "pns_violence": {
        "definition": (
            "Percentual de pessoas de 18 anos ou mais que sofreram violência nos últimos "
            "12 meses (PNS 2019)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 8022 / var 11396",
            "url": "https://sidra.ibge.gov.br/tabela/8022",
        },
        "limitations": [
            "Autorreferido; não confundir com homicídios do SIM.",
        ],
    },
    "pns_physical_violence": {
        "definition": (
            "Percentual de pessoas de 18 anos ou mais que sofreram violência física "
            "nos últimos 12 meses (PNS 2019, SIDRA 8058)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 8058 / var 11458",
            "url": "https://sidra.ibge.gov.br/tabela/8058",
        },
        "limitations": [
            "Autorreferida; não é BO de assalto nem homicídio.",
        ],
    },
    "pns_physical_women": {
        "definition": (
            "Percentual de mulheres de 18 anos ou mais que sofreram violência física "
            "nos últimos 12 meses (PNS 2019, SIDRA 8058, sexo feminino)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 8058 / sexo feminino",
            "url": "https://sidra.ibge.gov.br/tabela/8058",
        },
        "limitations": [
            "Não é feminicídio nem homicídio de mulheres do SIM.",
        ],
    },
    "pns_psych_violence": {
        "definition": (
            "Percentual de pessoas de 18 anos ou mais que sofreram violência psicológica "
            "nos últimos 12 meses (PNS 2019, SIDRA 8049)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 8049 / var 11445",
            "url": "https://sidra.ibge.gov.br/tabela/8049",
        },
        "limitations": [
            "Autorreferida; retrato de 2019.",
        ],
    },
    "pns_sexual_lifetime": {
        "definition": (
            "Percentual de pessoas de 18 anos ou mais que sofreram violência sexual "
            "alguma vez na vida (PNS 2019, SIDRA 8076)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 8076 / var 11482",
            "url": "https://sidra.ibge.gov.br/tabela/8076",
        },
        "limitations": [
            "Prevalência na vida — não é incidência em 12 meses.",
        ],
    },
    "female_homicide_count": {
        "definition": (
            "Número absoluto de óbitos de pessoas do sexo feminino classificados como "
            "homicídio (Ipeadata AVIOL12_HOMICF / SIM-DATASUS)."
        ),
        "source": {
            "organization": "DATASUS / IPEA",
            "dataset": "Ipeadata AVIOL12_HOMICF",
            "url": "http://www.ipeadata.gov.br/ExibeSerie.aspx?serid=AVIOL12_HOMICF",
        },
        "limitations": [
            "Não é feminicídio da Lei 13.104; o SIM não publica essa categoria penal.",
            "Contagem absoluta; comparar UFs com cautela.",
        ],
    },
    "pns_alcohol": {
        "definition": (
            "Percentual de pessoas de 18 anos ou mais que costumam consumir bebida alcoólica "
            "uma vez ou mais por mês (PNS 2019)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 4394 / var 4277",
            "url": "https://sidra.ibge.gov.br/tabela/4394",
        },
        "limitations": [
            "Retrato amostral de 2019; frequência, não volume em doses.",
        ],
    },
    "pns_hypertension": {
        "definition": (
            "Percentual de pessoas de 18 anos ou mais que referem diagnóstico médico de "
            "hipertensão arterial (PNS 2019)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 4418 / var 4399",
            "url": "https://sidra.ibge.gov.br/tabela/4418",
        },
        "limitations": [
            "Autoreferido; retrato de 2019.",
        ],
    },
    "gini_household": {
        "definition": (
            "Índice de Gini do rendimento domiciliar per capita, a preços médios do ano "
            "(PNAD Contínua anual, SIDRA 7435)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 7435 / var 10681",
            "url": "https://sidra.ibge.gov.br/tabela/7435",
        },
        "limitations": [
            "0 = igualdade; tende a 1 com maior desigualdade. Não é IDHM.",
        ],
    },
    "household_income_pc": {
        "definition": (
            "Rendimento médio mensal real domiciliar per capita, a preços médios do ano, "
            "classe Total (PNAD Contínua, SIDRA 7532)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 7532 / var 10824 / Total",
            "url": "https://sidra.ibge.gov.br/tabela/7532",
        },
        "limitations": [
            "Média, não mediana; não confundir com PIB per capita.",
        ],
    },
    "aging_index": {
        "definition": (
            "Índice de envelhecimento da população residente (Censo 2022, SIDRA 9515 / "
            "variável 10612): 65 anos ou mais por 100 pessoas de 0 a 14 anos."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9515 / var 10612",
            "url": "https://sidra.ibge.gov.br/tabela/9515",
        },
        "limitations": [
            "Não é esperança de vida; o recorte IBGE usa 65+, não 60+.",
        ],
    },
    "median_age": {
        "definition": "Idade mediana da população residente (Censo 2022, SIDRA 9515 / variável 10613).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9515 / var 10613",
            "url": "https://sidra.ibge.gov.br/tabela/9515",
        },
        "limitations": [
            "Mediana censitária de 2022; não é média etária.",
        ],
    },
    "share_0_14": {
        "definition": (
            "Percentual de 0 a 14 anos na população residente (Censo 2022, SIDRA 9514): "
            "soma dos grupos oficiais 0–4, 5–9 e 10–14 ÷ total."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9514 / var 93 / 93070+93084+93085 ÷ 100362",
            "url": "https://sidra.ibge.gov.br/tabela/9514",
        },
        "limitations": [
            "Razão local de grupos oficiais (DERIVADO); não é índice de juventude.",
        ],
    },
    "share_60_plus": {
        "definition": (
            "Percentual de 60 anos ou mais na população residente (Censo 2022, SIDRA 9514): "
            "soma dos grupos oficiais a partir de 60 anos ÷ total."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9514 / var 93 / 60+ ÷ 100362",
            "url": "https://sidra.ibge.gov.br/tabela/9514",
        },
        "limitations": [
            "Corte 60+ (Estatuto do Idoso); o índice de envelhecimento IBGE usa 65+.",
        ],
    },
    "share_gen_alpha": {
        "definition": (
            "Percentual de 0 a 9 anos (Censo 2022, SIDRA 9514). Apelido Alpha = nascidos "
            "aproximadamente em 2013–2022 — não é classificação IBGE."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9514 / var 93 / 0–9 ÷ total",
            "url": "https://sidra.ibge.gov.br/tabela/9514",
        },
        "limitations": [
            "DERIVADO: soma de grupos oficiais de 5 anos. IBGE não publica gerações.",
        ],
    },
    "share_gen_z": {
        "definition": (
            "Percentual de 10 a 24 anos (Censo 2022, SIDRA 9514). Apelido Geração Z = nascidos "
            "aproximadamente em 1998–2012 — não é classificação IBGE."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9514 / var 93 / 10–24 ÷ total",
            "url": "https://sidra.ibge.gov.br/tabela/9514",
        },
        "limitations": [
            "DERIVADO: soma de grupos oficiais de 5 anos. IBGE não publica gerações.",
        ],
    },
    "share_gen_y": {
        "definition": (
            "Percentual de 25 a 39 anos (Censo 2022, SIDRA 9514). Apelido millennial = nascidos "
            "aproximadamente em 1983–1997 — não é classificação IBGE."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9514 / var 93 / 25–39 ÷ total",
            "url": "https://sidra.ibge.gov.br/tabela/9514",
        },
        "limitations": [
            "DERIVADO: soma de grupos oficiais de 5 anos. IBGE não publica gerações.",
        ],
    },
    "share_gen_x": {
        "definition": (
            "Percentual de 40 a 59 anos (Censo 2022, SIDRA 9514). Apelido Geração X = nascidos "
            "aproximadamente em 1963–1982 — não é classificação IBGE."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9514 / var 93 / 40–59 ÷ total",
            "url": "https://sidra.ibge.gov.br/tabela/9514",
        },
        "limitations": [
            "DERIVADO: soma de grupos oficiais de 5 anos. IBGE não publica gerações.",
        ],
    },
    "share_gen_boomer": {
        "definition": (
            "Percentual de 60 a 79 anos (Censo 2022, SIDRA 9514). Apelido baby boom = nascidos "
            "aproximadamente em 1943–1962 — não é classificação IBGE."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9514 / var 93 / 60–79 ÷ total",
            "url": "https://sidra.ibge.gov.br/tabela/9514",
        },
        "limitations": [
            "DERIVADO: soma de grupos oficiais de 5 anos. IBGE não publica gerações.",
        ],
    },
    "share_gen_silent": {
        "definition": (
            "Percentual de 80 anos ou mais (Censo 2022, SIDRA 9514). Gerações anteriores ao "
            "baby boom (nascidos até ~1942)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9514 / var 93 / 80+ ÷ total",
            "url": "https://sidra.ibge.gov.br/tabela/9514",
        },
        "limitations": [
            "DERIVADO: soma de grupos oficiais de 5 anos. IBGE não publica gerações.",
        ],
    },
    "crude_birth_rate": {
        "definition": (
            "Nascidos vivos (Registro Civil SIDRA 2609) por mil habitantes (estimativa IBGE "
            "6579 do mesmo ano)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 2609/217 ÷ 6579",
            "url": "https://sidra.ibge.gov.br/tabela/2609",
        },
        "limitations": [
            "Taxa bruta, não fecundidade total nem padronizada por idade.",
        ],
    },
    "crude_death_rate": {
        "definition": (
            "Óbitos registrados (Registro Civil SIDRA 2682) por mil habitantes (estimativa "
            "IBGE 6579 do mesmo ano)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 2682/223 ÷ 6579",
            "url": "https://sidra.ibge.gov.br/tabela/2682",
        },
        "limitations": [
            "Taxa bruta: UFs mais velhas tendem a mortalidade maior. Não é TMI nem esperança de vida.",
        ],
    },
    "internet_home_share": {
        "definition": (
            "Percentual de domicílios com conexão à internet (Censo 2022, amostra SIDRA 9936)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9936 / var 1000381 / Sim",
            "url": "https://sidra.ibge.gov.br/tabela/9936",
        },
        "limitations": [
            "Amostra, não universo; existência de conexão, não qualidade.",
        ],
    },
    "urban_share": {
        "definition": "Percentual da população residente em situação urbana (Censo 2022, SIDRA 9923).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9923 / var 1000093 / Urbana",
            "url": "https://sidra.ibge.gov.br/tabela/9923",
        },
        "limitations": [
            "Situação do domicílio; não é densidade.",
        ],
    },
    "race_branca_share": {
        "definition": "Percentual autodeclarado branco (Censo 2022, SIDRA 9605).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9605 / branca",
            "url": "https://sidra.ibge.gov.br/tabela/9605",
        },
        "limitations": ["Autodeclaração; não é índice de diversidade."],
    },
    "race_preta_share": {
        "definition": "Percentual autodeclarado preto (Censo 2022, SIDRA 9605).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9605 / preta",
            "url": "https://sidra.ibge.gov.br/tabela/9605",
        },
        "limitations": ["Autodeclaração; distinta de parda."],
    },
    "race_parda_share": {
        "definition": "Percentual autodeclarado pardo (Censo 2022, SIDRA 9605).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9605 / parda",
            "url": "https://sidra.ibge.gov.br/tabela/9605",
        },
        "limitations": ["Autodeclaração; distinta de preta."],
    },
    "informality_rate": {
        "definition": (
            "Taxa de informalidade dos ocupados de 14 anos ou mais (PNAD Contínua, SIDRA 4708)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 4708 / var 12466",
            "url": "https://sidra.ibge.gov.br/tabela/4708",
        },
        "limitations": [
            "Não confundir com desocupação.",
        ],
    },
    "occupancy_rate": {
        "definition": (
            "Nível da ocupação das pessoas de 14 anos ou mais (PNADC, SIDRA 4093 / var 4097)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 4093 / var 4097",
            "url": "https://sidra.ibge.gov.br/tabela/4093",
        },
        "limitations": [
            "Ocupados / população 14+ — não é o complemento da desocupação.",
        ],
    },
    "participation_rate": {
        "definition": (
            "Taxa de participação na força de trabalho das pessoas de 14 anos ou mais "
            "(PNADC, SIDRA 4093 / var 4096)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 4093 / var 4096",
            "url": "https://sidra.ibge.gov.br/tabela/4093",
        },
        "limitations": [
            "Força de trabalho / população 14+.",
        ],
    },
    "higher_education_share": {
        "definition": (
            "Percentual de pessoas de 14 anos ou mais com ensino superior completo (PNAD Contínua, SIDRA 7128)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 7128 / var 4104 / 99713",
            "url": "https://sidra.ibge.gov.br/tabela/7128",
        },
        "limitations": [
            "Base 14 anos ou mais, não só adultos 25+.",
        ],
    },
    "sex_ratio": {
        "definition": "Razão de sexo: homens por 100 mulheres (Censo 2022, SIDRA 9515).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9515 / var 8845",
            "url": "https://sidra.ibge.gov.br/tabela/9515",
        },
        "limitations": ["Não é índice de equidade de gênero."],
    },
    "labor_income": {
        "definition": (
            "Rendimento médio mensal real do trabalho dos ocupados de 14 anos ou mais (PNAD Contínua, SIDRA 6469)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 6469 / var 5935",
            "url": "https://sidra.ibge.gov.br/tabela/6469",
        },
        "limitations": [
            "Não é renda domiciliar per capita nem PIB per capita.",
        ],
    },
    "dependency_ratio": {
        "definition": (
            "Dependentes (0–14 + 60+) por 100 pessoas de 15–59 anos (Censo 2022, SIDRA 9514)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9514 / (0–14 + 60+) ÷ 15–59",
            "url": "https://sidra.ibge.gov.br/tabela/9514",
        },
        "limitations": [
            "DERIVADO; corte 60+ e 15–59, não o índice IBGE 15–64 / 65+.",
        ],
    },
    "cempre_avg_wage": {
        "definition": "Salário médio mensal em reais das unidades locais formais (CEMPRE, SIDRA 9509).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9509 / var 10143",
            "url": "https://sidra.ibge.gov.br/tabela/9509",
        },
        "limitations": [
            "Cadastro formal exclusive MEI; não é PNADC nem salário mínimo legal.",
        ],
    },
    "cempre_wage_in_sm": {
        "definition": "Salário médio formal em salários mínimos (CEMPRE, SIDRA 9509 / var 1606).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9509 / var 1606",
            "url": "https://sidra.ibge.gov.br/tabela/9509",
        },
        "limitations": [
            "Múltiplo oficial do IBGE no ano do cadastro, não o SM vigente da data do mapa.",
        ],
    },
    "cempre_firms": {
        "definition": "Número de empresas e organizações atuantes (CEMPRE, SIDRA 9509 / var 367).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9509 / var 367",
            "url": "https://sidra.ibge.gov.br/tabela/9509",
        },
        "limitations": [
            "Cadastro formal exclusive MEI; não é abertura de empresas.",
        ],
    },
    "cempre_jobs": {
        "definition": "Pessoal ocupado total nas unidades locais formais (CEMPRE, SIDRA 9509 / var 707).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9509 / var 707",
            "url": "https://sidra.ibge.gov.br/tabela/9509",
        },
        "limitations": [
            "Estoque formal exclusive MEI; não é PNADC.",
        ],
    },
    "rented_share": {
        "definition": (
            "Percentual de domicílios particulares ocupados alugados (Censo 2022, SIDRA 9930)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9930 / Alugado",
            "url": "https://sidra.ibge.gov.br/tabela/9930",
        },
        "limitations": [
            "Não é valor do aluguel; o SIDRA 2022 não publica média em reais por UF.",
        ],
    },
    "owned_paying_share": {
        "definition": "Percentual de domicílios próprios ainda pagando (Censo 2022, SIDRA 9930).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9930 / ainda pagando",
            "url": "https://sidra.ibge.gov.br/tabela/9930",
        },
        "limitations": ["Não é valor da prestação."],
    },
    "owned_paid_share": {
        "definition": "Percentual de domicílios próprios já pagos, herdados ou ganhos (Censo 2022, SIDRA 9930).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9930 / já pago",
            "url": "https://sidra.ibge.gov.br/tabela/9930",
        },
        "limitations": ["Inclui herdado/ganho."],
    },
    "employer_unit_births": {
        "definition": "Nascimentos de unidades locais empregadoras (SIDRA 9925, exclusive MEI).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9925 / nascimento",
            "url": "https://sidra.ibge.gov.br/tabela/9925",
        },
        "limitations": [
            "Contagem; SIDRA não publica morte por UF («-»).",
        ],
    },
    "employer_unit_birth_rate": {
        "definition": "Taxa de nascimento: nascimentos ÷ unidades locais empregadoras ativas (SIDRA 9925).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9925 / 73120÷73119",
            "url": "https://sidra.ibge.gov.br/tabela/9925",
        },
        "limitations": [
            "DERIVADO das duas células oficiais; exclusive MEI.",
        ],
    },
    "employer_survival_1y": {
        "definition": "Taxa de 1 ano de sobrevivência das unidades locais empregadoras (SIDRA 9950).",
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9950 / var 13235",
            "url": "https://sidra.ibge.gov.br/tabela/9950",
        },
        "limitations": ["Exclusive MEI; recorte SIDRA, não 5 anos (publicado como «...»)."],
    },
    "basket_capital": {
        "definition": "Custo da cesta básica de alimentos na capital da UF (DIEESE/Conab, Tabela 1).",
        "source": {
            "organization": "DIEESE / Conab",
            "dataset": "PNCBA — Tabela 1",
            "url": "https://www.dieese.org.br/analisecestabasica/",
        },
        "limitations": [
            "É o preço da CAPITAL, não o custo de vida da UF.",
        ],
    },
    "basket_share_sm": {
        "definition": "Cesta da capital como % do salário mínimo líquido (DIEESE/Conab).",
        "source": {
            "organization": "DIEESE / Conab",
            "dataset": "PNCBA — Tabela 1",
            "url": "https://www.dieese.org.br/analisecestabasica/",
        },
        "limitations": [
            "Capital, não UF; mínimo líquido nacional (7,5% de Previdência).",
        ],
    },
    "rcl_rreo": {
        "definition": (
            "Receita Corrente Líquida do ente estadual no RREO Anexo 14 "
            "(Até o Bimestre, 6º bimestre)."
        ),
        "source": {
            "organization": "STN — SICONFI",
            "dataset": "RREO Anexo 14 / RCL",
            "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        },
        "limitations": [
            "RCL da LRF; valor nominal; não é PIB nem transferência isolada.",
        ],
    },
    "impostos_rreo": {
        "definition": (
            "Receita realizada de impostos do ente estadual no RREO Anexo 01 "
            "(conta Impostos, até o 6º bimestre). Linha consolidada: a API não separa ICMS/IPVA."
        ),
        "source": {
            "organization": "STN — SICONFI",
            "dataset": "RREO Anexo 01 / Impostos",
            "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        },
        "limitations": [
            "Não é arrecadação da RFB no território; ICMS isolado não cobre 27 UFs nesta API.",
        ],
    },
    "gov_winner_share": {
        "definition": (
            "Percentual dos votos nominais válidos do candidato a governador mais votado "
            "na UF naquele turno."
        ),
        "source": {
            "organization": "TSE",
            "dataset": "votacao_candidato_munzona (Governador)",
            "url": "https://dadosabertos.tse.jus.br/",
        },
        "limitations": [
            "Turno omitido se não houver as 27 UFs no arquivo.",
        ],
    },
    "gov_margin_pp": {
        "definition": (
            "Diferença, em pontos percentuais, entre 1º e 2º colocados a governador na UF."
        ),
        "source": {
            "organization": "TSE",
            "dataset": "votacao_candidato_munzona (Governador)",
            "url": "https://dadosabertos.tse.jus.br/",
        },
        "limitations": [
            "Turno omitido se não houver as 27 UFs no arquivo.",
        ],
    },
    "lens_live": {
        "definition": (
            "Nota 0–100 entre as 27 UFs para «morar»: 4 blocos iguais "
            "(renda incl. pobreza invertida, trabalho com ocupação, segurança SIM+PNS, "
            "serviços + RCL/hab). Min–máx de camadas oficiais. Não é IDHM."
        ),
        "source": {
            "organization": "Brasil Real",
            "dataset": "Lente morar — pesos iguais declarados",
            "url": "https://brasilreal-atlas.web.app",
        },
        "limitations": [
            "Receita editorial; anos mistos; cesta da capital não entra.",
            "Contagens absolutas e tributária/PIB não entram nas lentes.",
        ],
    },
    "lens_venture": {
        "definition": (
            "Nota 0–100 entre as 27 UFs para «empreender»: 3 blocos iguais "
            "(dinâmica de empregadoras, mercado formal com ocupação/participação, "
            "densidade de empresas e empregos formais por mil hab.). "
            "Não é ranking de ambiente de negócios."
        ),
        "source": {
            "organization": "Brasil Real",
            "dataset": "Lente empreender — pesos iguais declarados",
            "url": "https://brasilreal-atlas.web.app",
        },
        "limitations": [
            "Exclusive MEI; sobrevivência 2021 e nascimentos 2022; não é IDHM.",
        ],
    },
    "lens_family": {
        "definition": (
            "Nota 0–100 para «criar criança»: renda, trabalho, segurança "
            "(homicídio, trânsito e violência física PNS entre mulheres) e serviços/RCL. "
            "Não é IDEB nem feminicídio penal."
        ),
        "source": {
            "organization": "Brasil Real",
            "dataset": "Lente criança — pesos iguais declarados",
            "url": "https://brasilreal-atlas.web.app",
        },
        "limitations": [
            "Receita editorial; anos mistos; cesta da capital não entra.",
            "PNS 2019 só como violência física entre mulheres; homicídios de mulheres (nº) ficam de fora.",
        ],
    },
    "lens_aging": {
        "definition": (
            "Nota 0–100 de pressão etária (maior = mais pressão): 60+, índice de "
            "envelhecimento e razão de dependência. Não é qualidade de vida do idoso."
        ),
        "source": {
            "organization": "Brasil Real",
            "dataset": "Lente pressão etária — pesos iguais declarados",
            "url": "https://brasilreal-atlas.web.app",
        },
        "limitations": [
            "Receita editorial; anos mistos; não é IDHM.",
        ],
    },
    "rcl_pc": {
        "definition": "RCL do RREO dividida pela população IBGE 2025.",
        "source": {
            "organization": "Brasil Real",
            "dataset": "RCL ÷ população",
            "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        },
        "limitations": ["Razão local; não é renda."],
    },
    "trib_pc": {
        "definition": "Receita tributária do RREO dividida pela população IBGE 2025.",
        "source": {
            "organization": "Brasil Real",
            "dataset": "Tributária ÷ população",
            "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        },
        "limitations": [
            "Ente estadual; não é RFB. Denominador 2025 em toda a série.",
        ],
    },
    "trib_pib_share": {
        "definition": "Receita tributária estadual do RREO dividida pelo PIB da UF no mesmo ano.",
        "source": {
            "organization": "Brasil Real",
            "dataset": "Tributária RREO ÷ PIB IBGE",
            "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        },
        "limitations": [
            "Não é carga tributária da RFB; só o ano em que RREO e contas regionais coincidem.",
        ],
    },
    "trib_share_rcl": {
        "definition": "Receita tributária realizada como percentual da RCL no mesmo exercício RREO.",
        "source": {
            "organization": "Brasil Real",
            "dataset": "Tributária ÷ RCL",
            "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        },
        "limitations": ["Anexos diferentes do mesmo RREO; não é qualidade da gestão."],
    },
    "dcl_rcl": {
        "definition": "DCL dividida pela RCL no mesmo exercício RREO. Pode ser negativa.",
        "source": {
            "organization": "Brasil Real",
            "dataset": "DCL ÷ RCL",
            "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        },
        "limitations": ["Não aplica sozinha o limite da LRF."],
    },
    "export_fob": {
        "definition": "Valor FOB total das exportações da UF (Comex Stat), sem filtro de capítulo.",
        "source": {
            "organization": "MDIC — Comex Stat",
            "dataset": "FOB total / estado",
            "url": "https://comexstat.mdic.gov.br/",
        },
        "limitations": ["Não Declarada não pinta UF."],
    },
    "export_fob_pc": {
        "definition": "Exportação FOB total da UF dividida pela população IBGE 2025.",
        "source": {
            "organization": "Brasil Real",
            "dataset": "FOB total ÷ população",
            "url": "https://api-comexstat.mdic.gov.br/docs",
        },
        "limitations": ["Denominador 2025; dólar nominal."],
    },
}
