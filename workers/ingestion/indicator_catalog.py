"""Catalog of UF-level official social/economic indicators (IBGE Agregados)."""

from __future__ import annotations

# Each entry produces data/fixtures/ibge/indicators/<id>_latest.json
INDICATOR_SPECS: dict[str, dict] = {
    "poverty_rate": {
        "id": "poverty_rate",
        "name": "Proporção abaixo da linha de pobreza nacional",
        "short_name": "Pobreza",
        "aggregate_id": 5877,
        "variable_id": 9948,
        "unit": "%",
        "status_label": "ESTIMADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "social",
        "group_label": "Social",
        "classificacao": None,
        "dataset_page": "https://sidra.ibge.gov.br/tabela/5877",
        "method_notes": (
            "IBGE ODS 1.2.1 / Agregados 5877, variável 9948, localidades N3. "
            "Linha de pobreza nacional do IBGE — não confundir com linhas do Banco Mundial."
        ),
        "limitations": [
            "Definição depende da linha nacional vigente no ano de referência.",
            "Não é tempo real; série anual com defasagem de publicação.",
        ],
    },
    "literacy_rate": {
        "id": "literacy_rate",
        "name": "Taxa de alfabetização (15 anos ou mais)",
        "short_name": "Alfabetização",
        "aggregate_id": 9543,
        "variable_id": 2513,
        "unit": "%",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "census",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "social",
        "group_label": "Social",
        # Sexo Total | Cor/raça Total | Idade Total
        "classificacao": "2[6794]|86[95251]|287[100362]",
        "dataset_page": "https://sidra.ibge.gov.br/tabela/9543",
        "method_notes": (
            "Censo Demográfico via Agregados 9543/variável 2513, totais. "
            "Alfabetização ≠ qualidade da educação nem IDEB."
        ),
        "limitations": [
            "Atualização censitária (décadas); não use como proxy de escolaridade média.",
            "Taxa alta pode coexistir com baixa proficiência leitora.",
        ],
    },
    "unemployment_rate": {
        "id": "unemployment_rate",
        "name": "Taxa de desocupação (14 anos ou mais)",
        "short_name": "Desocupação",
        "aggregate_id": 4099,
        "variable_id": 4099,
        "unit": "%",
        "status_label": "ESTIMADO",
        "evidence_grade": "A",
        "frequency": "quarterly",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "social",
        "group_label": "Social",
        "classificacao": None,
        "dataset_page": "https://sidra.ibge.gov.br/tabela/4099",
        "method_notes": (
            "PNAD Contínua / Agregados 4099, variável 4099, N3. "
            "Período trimestral no formato AAAATT (ex.: 202602 = 2026 T2)."
        ),
        "limitations": [
            "Taxa trimestral sujeita a sazonalidade e coeficiente de variação.",
            "Desocupação ≠ informalidade nem desalento (há outras taxas na mesma tabela).",
        ],
    },
}
