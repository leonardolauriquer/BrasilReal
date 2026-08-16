"""MDIC ComexStat — UF export indicators (FOB US$)."""

from __future__ import annotations

COMEX_SPECS: dict[str, dict] = {
    "export_fob": {
        "id": "export_fob",
        "name": "Exportação total (FOB US$)",
        "short_name": "Export. total FOB",
        "unit": "USD",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "agro",
        "group_label": "Agro / comércio exterior",
        "organization": "MDIC — Comex Stat",
        "dataset_page": "https://comexstat.mdic.gov.br/",
        "api_docs": "https://api-comexstat.mdic.gov.br/docs",
        "filters": [],
        "metric": "metricFOB",
        "definition": (
            "Valor FOB (US$) de todas as exportações por UF de origem do produto, "
            "agregado anual via API Comex Stat (MDIC), sem filtro de capítulo SH."
        ),
        "method_notes": (
            "POST /general flow=export, detail=state, sem filtro de capítulo, métrica metricFOB. "
            "UF sem registro no ano recebe 0."
        ),
        "limitations": [
            "Pauta inteira da UF — não é soja nem petróleo isolados.",
            "UF de origem do produto ≠ necessariamente o porto de embarque.",
            "Linhas Comex «Reexportação» e «Não Declarada» não pintam UF.",
        ],
    },
    "export_meat_fob": {
        "id": "export_meat_fob",
        "name": "Exportação de carnes (FOB US$) — capítulo SH 02",
        "short_name": "Export. carnes",
        "unit": "USD",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "agro",
        "group_label": "Agro / comércio exterior",
        "organization": "MDIC — Comex Stat",
        "dataset_page": "https://comexstat.mdic.gov.br/",
        "api_docs": "https://api-comexstat.mdic.gov.br/docs",
        "filters": [{"filter": "chapter", "values": ["02"]}],
        "metric": "metricFOB",
        "definition": (
            "Valor FOB (US$) das exportações classificadas no capítulo 02 do Sistema "
            "Harmonizado (carnes e miudezas comestíveis), por UF de origem do produto, "
            "agregado anual via API Comex Stat (MDIC)."
        ),
        "method_notes": (
            "POST /general flow=export, detail=state, filter chapter=02, métrica metricFOB. "
            "UF sem registro no ano recebe 0 (sem operação declarada naquele recorte)."
        ),
        "limitations": [
            "Capítulo 02 inclui bovino, suíno, aves e outras carnes — não é só boi.",
            "UF de origem do produto ≠ necessariamente local de abate ou fazenda.",
            "Valor em dólar FOB; não é volume em toneladas nem preço interno.",
        ],
    },
    "export_bovine_fob": {
        "id": "export_bovine_fob",
        "name": "Exportação de carne bovina (FOB US$) — SH 0201+0202",
        "short_name": "Export. bovina",
        "unit": "USD",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "agro",
        "group_label": "Agro / comércio exterior",
        "organization": "MDIC — Comex Stat",
        "dataset_page": "https://comexstat.mdic.gov.br/",
        "api_docs": "https://api-comexstat.mdic.gov.br/docs",
        # Two headings fetched and summed per UF
        "filters_multi": [
            [{"filter": "heading", "values": ["0201"]}],
            [{"filter": "heading", "values": ["0202"]}],
        ],
        "metric": "metricFOB",
        "definition": (
            "Valor FOB (US$) das exportações de carne bovina fresca/refrigerada (SH 0201) "
            "e congelada (SH 0202), somadas por UF de origem do produto (Comex Stat / MDIC)."
        ),
        "method_notes": (
            "Duas consultas /general (headings 0201 e 0202), soma do FOB por UF. "
            "Exclui miudezas e outras carnes do capítulo 02."
        ),
        "limitations": [
            "Não inclui miudezas bovinas classificadas em outras posições.",
            "UF de origem do produto ≠ necessariamente UF do rebanho.",
        ],
    },
    "export_soy_fob": {
        "id": "export_soy_fob",
        "name": "Exportação de soja em grão (FOB US$) — SH 1201",
        "short_name": "Export. soja",
        "unit": "USD",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "agro",
        "group_label": "Agro / comércio exterior",
        "organization": "MDIC — Comex Stat",
        "dataset_page": "https://comexstat.mdic.gov.br/",
        "api_docs": "https://api-comexstat.mdic.gov.br/docs",
        "filters": [{"filter": "heading", "values": ["1201"]}],
        "metric": "metricFOB",
        "definition": (
            "Valor FOB (US$) das exportações de soja em grão (posição SH 1201), "
            "por UF de origem do produto, agregado anual (Comex Stat / MDIC)."
        ),
        "method_notes": (
            "POST /general flow=export, detail=state, filter heading=1201, métrica metricFOB."
        ),
        "limitations": [
            "Soja em grão apenas — não inclui farelo (2304) nem óleo (1507).",
            "UF de origem do produto pode diferir do município produtor.",
        ],
    },
    "export_corn_fob": {
        "id": "export_corn_fob",
        "name": "Exportação de milho (FOB US$) — SH 1005",
        "short_name": "Export. milho",
        "unit": "USD",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "agro",
        "group_label": "Agro / comércio exterior",
        "organization": "MDIC — Comex Stat",
        "dataset_page": "https://comexstat.mdic.gov.br/",
        "api_docs": "https://api-comexstat.mdic.gov.br/docs",
        "filters": [{"filter": "heading", "values": ["1005"]}],
        "metric": "metricFOB",
        "definition": (
            "Valor FOB (US$) das exportações de milho (posição SH 1005), "
            "por UF de origem do produto, agregado anual (Comex Stat / MDIC)."
        ),
        "method_notes": (
            "POST /general flow=export, detail=state, filter heading=1005, métrica metricFOB."
        ),
        "limitations": [
            "Milho em grão (SH 1005); não inclui milho doce preparado nem farelos.",
            "UF de origem do produto pode diferir do município produtor.",
        ],
    },
    "export_soy_meal_fob": {
        "id": "export_soy_meal_fob",
        "name": "Exportação de farelo de soja (FOB US$) — SH 2304",
        "short_name": "Export. farelo",
        "unit": "USD",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "agro",
        "group_label": "Agro / comércio exterior",
        "organization": "MDIC — Comex Stat",
        "dataset_page": "https://comexstat.mdic.gov.br/",
        "api_docs": "https://api-comexstat.mdic.gov.br/docs",
        "filters": [{"filter": "heading", "values": ["2304"]}],
        "metric": "metricFOB",
        "definition": (
            "Valor FOB (US$) das exportações de bagaços e outros resíduos da extração "
            "do óleo de soja (posição SH 2304), por UF de origem (Comex Stat / MDIC)."
        ),
        "method_notes": (
            "POST /general flow=export, detail=state, filter heading=2304, métrica metricFOB."
        ),
        "limitations": [
            "Farelo/resíduos (2304), não soja em grão (1201) nem óleo (1507).",
            "UF de origem do produto ≠ necessariamente UF da lavoura.",
        ],
    },
    "export_iron_ore_fob": {
        "id": "export_iron_ore_fob",
        "name": "Exportação de minérios (FOB US$) — capítulo SH 26",
        "short_name": "Export. minérios",
        "unit": "USD",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "agro",
        "group_label": "Agro / comércio exterior",
        "organization": "MDIC — Comex Stat",
        "dataset_page": "https://comexstat.mdic.gov.br/",
        "api_docs": "https://api-comexstat.mdic.gov.br/docs",
        "filters": [{"filter": "chapter", "values": ["26"]}],
        "metric": "metricFOB",
        "definition": (
            "Valor FOB (US$) das exportações classificadas no capítulo 26 do Sistema "
            "Harmonizado (minérios, escórias e cinzas), por UF de origem do produto, "
            "agregado anual via API Comex Stat (MDIC)."
        ),
        "method_notes": (
            "POST /general flow=export, detail=state, filter chapter=26, métrica metricFOB. "
            "UF sem registro no ano recebe 0 (sem operação declarada naquele recorte)."
        ),
        "limitations": [
            "Capítulo 26 inclui minério de ferro e outros minérios — não é só hematita.",
            "UF de origem do produto ≠ necessariamente mina ou porto de embarque.",
            "Valor em dólar FOB; não é volume em toneladas nem cotação interna.",
        ],
    },
    "export_soy_oil_fob": {
        "id": "export_soy_oil_fob",
        "name": "Exportação de óleo de soja (FOB US$) — SH 1507",
        "short_name": "Export. óleo soja",
        "unit": "USD",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "agro",
        "group_label": "Agro / comércio exterior",
        "organization": "MDIC — Comex Stat",
        "dataset_page": "https://comexstat.mdic.gov.br/",
        "api_docs": "https://api-comexstat.mdic.gov.br/docs",
        "filters": [{"filter": "heading", "values": ["1507"]}],
        "metric": "metricFOB",
        "definition": (
            "Valor FOB (US$) das exportações de óleo de soja (posição SH 1507), "
            "por UF de origem do produto, agregado anual (Comex Stat / MDIC)."
        ),
        "method_notes": (
            "POST /general flow=export, detail=state, filter heading=1507, métrica metricFOB."
        ),
        "limitations": [
            "Óleo de soja (1507), não grão (1201) nem farelo (2304).",
            "UF de origem do produto ≠ necessariamente UF da lavoura ou do esmagamento.",
        ],
    },
    "export_petroleum_fob": {
        "id": "export_petroleum_fob",
        "name": "Exportação de combustíveis minerais (FOB US$) — capítulo SH 27",
        "short_name": "Export. combustíveis",
        "unit": "USD",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "annual",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "agro",
        "group_label": "Agro / comércio exterior",
        "organization": "MDIC — Comex Stat",
        "dataset_page": "https://comexstat.mdic.gov.br/",
        "api_docs": "https://api-comexstat.mdic.gov.br/docs",
        "filters": [{"filter": "chapter", "values": ["27"]}],
        "metric": "metricFOB",
        "definition": (
            "Valor FOB (US$) das exportações classificadas no capítulo 27 do Sistema "
            "Harmonizado (combustíveis minerais, óleos minerais e produtos da destilação; "
            "matérias betuminosas; ceras minerais), por UF de origem (Comex Stat / MDIC)."
        ),
        "method_notes": (
            "POST /general flow=export, detail=state, filter chapter=27, métrica metricFOB. "
            "UF sem registro no ano recebe 0 (sem operação declarada naquele recorte)."
        ),
        "limitations": [
            "Capítulo 27 inclui petróleo bruto, derivados, carvão e gases — não é só petróleo cru.",
            "UF de origem do produto ≠ necessariamente UF da produção ou do porto de embarque.",
            "Valor em dólar FOB; não é volume em barris nem cotação interna.",
            "Linhas Comex «Reexportação» e «Não Declarada» não pintam UF; o valor delas é excluído do mapa.",
        ],
    },
}
