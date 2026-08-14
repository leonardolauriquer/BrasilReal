"""MDIC ComexStat — UF export indicators (FOB US$)."""

from __future__ import annotations

COMEX_SPECS: dict[str, dict] = {
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
}
