"""TSE — President vote-share indicators by UF / party / turn."""

from __future__ import annotations

# Periods use YYYYTn (e.g. 2022T1). Party indicators only include periods
# where that party had valid presidential votes.

TSE_YEARS = (2018, 2022)

# Always ship these party share layers when data exists.
CORE_PARTY_CODES = ("PT", "PL", "MDB", "PDT", "PSL", "NOVO", "UNIÃO", "REDE")

WINNER_SPEC = {
    "id": "pres_winner_share",
    "name": "Presidente — % do vencedor na UF",
    "short_name": "Pres. % vencedor",
    "unit": "%",
    "status_label": "OBSERVADO",
    "evidence_grade": "A",
    "frequency": "election",
    "higher_is_worse": False,
    "kind": "observed_estimate",
    "group": "eleicoes",
    "group_label": "Eleições",
    "definition": (
        "Percentual dos votos nominais válidos do candidato a presidente mais votado "
        "na UF naquele turno (TSE — votação nominal por município/zona, agregado)."
    ),
    "limitations": [
        "Agregado a partir de votação por município e zona (cargo Presidente).",
        "Não inclui votos em branco/nulo; denominador = soma dos votos nominais válidos.",
        "ZZ (exterior) e VT (em trânsito) excluídos do mapa de UFs.",
    ],
}

MARGIN_SPEC = {
    "id": "pres_margin_pp",
    "name": "Presidente — margem 1º−2º (pontos percentuais)",
    "short_name": "Pres. margem",
    "unit": "pp",
    "status_label": "OBSERVADO",
    "evidence_grade": "A",
    "frequency": "election",
    "higher_is_worse": False,
    "kind": "observed_estimate",
    "group": "eleicoes",
    "group_label": "Eleições",
    "definition": (
        "Diferença, em pontos percentuais, entre o 1º e o 2º colocados a presidente "
        "na UF naquele turno (sobre votos nominais válidos)."
    ),
    "limitations": [
        "Margem local na UF — não é o resultado nacional.",
        "Em 2º turno tipicamente reflete a disputa entre os dois finalistas.",
    ],
}


def party_spec(sg_partido: str) -> dict:
    code = sg_partido.upper()
    slug = (
        code.replace("Ã", "A")
        .replace("Á", "A")
        .replace("Â", "A")
        .replace("À", "A")
        .replace("É", "E")
        .replace("Ê", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ô", "O")
        .replace("Õ", "O")
        .replace("Ú", "U")
        .replace("Ç", "C")
        .replace("Ü", "U")
    )
    slug = "".join(ch if ch.isalnum() else "_" for ch in slug).strip("_").lower()
    return {
        "id": f"pres_party_{slug}",
        "name": f"Presidente — % votos {code}",
        "short_name": f"Pres. %{code}",
        "unit": "%",
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "frequency": "election",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "eleicoes",
        "group_label": "Eleições",
        "party_code": code,
        "definition": (
            f"Percentual dos votos nominais válidos do(s) candidato(s) a presidente "
            f"filiado(s) ao partido {code} na UF e turno (TSE)."
        ),
        "limitations": (
            WINNER_SPEC["limitations"]
            + [
                "Partido do candidato no pleito — coligações/federações podem variar entre anos.",
                "Se o partido não lançou candidato naquele turno, o período pode não existir.",
            ]
        ),
    }


DATASET_PAGE = "https://dadosabertos.tse.jus.br/dataset/resultados-2022"
ORGANIZATION = "TSE — Tribunal Superior Eleitoral"

GOV_WINNER_SPEC = {
    "id": "gov_winner_share",
    "name": "Governador — % do vencedor na UF",
    "short_name": "Gov. % vencedor",
    "unit": "%",
    "status_label": "OBSERVADO",
    "evidence_grade": "A",
    "frequency": "election",
    "higher_is_worse": False,
    "kind": "observed_estimate",
    "group": "eleicoes",
    "group_label": "Eleições",
    "definition": (
        "Percentual dos votos nominais válidos do candidato a governador mais votado "
        "na UF naquele turno (TSE — votação nominal por município/zona, agregado)."
    ),
    "limitations": [
        "Agregado a partir de votação por município e zona (cargo Governador).",
        "Não inclui votos em branco/nulo; denominador = soma dos votos nominais válidos.",
        "Turno só entra se as 27 UFs tiverem votação daquele cargo no arquivo.",
        "ZZ (exterior) e VT (em trânsito) excluídos do mapa de UFs.",
    ],
}

GOV_MARGIN_SPEC = {
    "id": "gov_margin_pp",
    "name": "Governador — margem 1º−2º (pontos percentuais)",
    "short_name": "Gov. margem",
    "unit": "pp",
    "status_label": "OBSERVADO",
    "evidence_grade": "A",
    "frequency": "election",
    "higher_is_worse": False,
    "kind": "observed_estimate",
    "group": "eleicoes",
    "group_label": "Eleições",
    "definition": (
        "Diferença, em pontos percentuais, entre o 1º e o 2º colocados a governador "
        "na UF naquele turno (sobre votos nominais válidos)."
    ),
    "limitations": [
        "Margem local na UF — não é o colégio eleitoral.",
        "Turno só entra se as 27 UFs tiverem votação daquele cargo no arquivo "
        "(2º turno incompleto é omitido, não preenchido com zero).",
    ],
}
