"""Catalog of UF-level series from Ipeadata (Atlas da Violência / DATASUS via IPEA)."""

from __future__ import annotations

# OData: http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='…')
# NIVNOME 'Estados' → TERCODIGO = código IBGE da UF (2 dígitos).

IPEADATA_SPECS: dict[str, dict] = {
    "homicide_rate": {
        "id": "homicide_rate",
        "sercodigo": "AVIOL12_THOMIC",
        "name": "Taxa de homicídios (por 100 mil habitantes)",
        "short_name": "Homicídios /100 mil",
        "unit": "por 100 mil hab",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "seguranca",
        "group_label": "Segurança",
        "organization": "IPEA / DATASUS",
        "dataset_page": "http://www.ipeadata.gov.br/Default.aspx",
        "serie_page": "http://www.ipeadata.gov.br/ExibeSerie.aspx?serid=AVIOL12_THOMIC",
        "method_notes": (
            "Série Ipeadata AVIOL12_THOMIC — taxa de homicídios por 100 mil habitantes "
            "(Atlas da Violência / IPEA, com base em óbitos SIM/DATASUS). "
            "Nível geográfico: Estados (códigos IBGE)."
        ),
        "limitations": [
            "Classificação CID de causa básica; subnotificação e mudança de codificação podem afetar a série.",
            "Não confundir com mortes violentas intencionais (MVI) do Anuário FBSP — metodologias distintas.",
            "Série anual com defasagem de publicação do SIM.",
        ],
        "definition": (
            "Número de óbitos classificados como homicídio por 100 mil habitantes residentes "
            "na UF, no ano de referência (série Ipeadata AVIOL12_THOMIC / Atlas da Violência)."
        ),
    },
    "homicide_count": {
        "id": "homicide_count",
        "sercodigo": "AVIOL12_HOMIC",
        "name": "Número de homicídios",
        "short_name": "Homicídios (nº)",
        "unit": "homicídios",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "seguranca",
        "group_label": "Segurança",
        "organization": "DATASUS / IPEA",
        "dataset_page": "http://www.ipeadata.gov.br/Default.aspx",
        "serie_page": "http://www.ipeadata.gov.br/ExibeSerie.aspx?serid=AVIOL12_HOMIC",
        "method_notes": (
            "Série Ipeadata AVIOL12_HOMIC — número absoluto de homicídios "
            "(fonte declarada no metadado Ipeadata: DATASUS). Nível: Estados."
        ),
        "limitations": [
            "Contagem absoluta; para comparar UFs use preferencialmente a taxa por 100 mil.",
            "Mesmas limitações de codificação e cobertura do SIM/DATASUS.",
        ],
        "definition": (
            "Número absoluto de óbitos classificados como homicídio na UF no ano "
            "(série Ipeadata AVIOL12_HOMIC, origem DATASUS)."
        ),
    },
    "traffic_death_rate": {
        "id": "traffic_death_rate",
        "sercodigo": "AVIOL12_TACIDT",
        "name": "Taxa de óbitos em acidentes de trânsito (por 100 mil)",
        "short_name": "Trânsito /100 mil",
        "unit": "por 100 mil hab",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "saude",
        "group_label": "Saúde",
        "organization": "IPEA / DATASUS",
        "dataset_page": "http://www.ipeadata.gov.br/Default.aspx",
        "serie_page": "http://www.ipeadata.gov.br/ExibeSerie.aspx?serid=AVIOL12_TACIDT",
        "method_notes": (
            "Série Ipeadata AVIOL12_TACIDT — taxa de vítimas fatais de acidente de trânsito "
            "por 100 mil habitantes (IPEA / SIM-DATASUS). Nível: Estados."
        ),
        "limitations": [
            "Óbitos por causa básica no SIM; pode diferir de estatísticas de trânsito policiais.",
            "Série anual com defasagem típica do SIM.",
        ],
        "definition": (
            "Óbitos de vítimas de acidente de trânsito por 100 mil habitantes na UF "
            "(série Ipeadata AVIOL12_TACIDT)."
        ),
    },
}
