"""Editorial lenses — declared equal-weight recipes over official UF layers.

Not IBGE. Not IDHM. Not «melhor estado oficial». The ranking is the recipe.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from common import fixtures_dir, utc_now, write_json
from social_layers import UF_CODES, _estados

INDICATOR_RELS = (
    "ibge/indicators",
    "ipeadata/indicators",
    "comex/indicators",
    "tse/indicators",
    "siconfi/indicators",
    "dieese/indicators",
)


def _checksum(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_latest(indicator_id: str) -> dict[str, Any]:
    root = fixtures_dir()
    if indicator_id == "population":
        path = root / "ibge" / "population_uf_2025.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = []
        for row in payload["records"]:
            records.append(
                {
                    "ibge_code": str(row["ibge_code"]),
                    "uf": row["uf"],
                    "name": row["name"],
                    "value": float(row["population"]),
                }
            )
        return {
            "indicator_id": "population",
            "reference_period": str(payload.get("reference_date") or "2025")[:4],
            "short_name": "População",
            "higher_is_worse": False,
            "records": records,
        }
    for rel in INDICATOR_RELS:
        path = root / rel / f"{indicator_id}_latest.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"lentes: missing latest fixture for {indicator_id}")


def _values(payload: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in payload.get("records") or []:
        code = str(row.get("ibge_code") or "")
        val = row.get("value")
        if code in UF_CODES and isinstance(val, (int, float)):
            out[code] = float(val)
    if set(out) != set(UF_CODES):
        raise RuntimeError(f"{payload.get('indicator_id')}: expected 27 UFs, got {sorted(out)}")
    return out


def _minmax(mapped: dict[str, float], *, invert: bool) -> dict[str, float]:
    vals = list(mapped.values())
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return {code: 50.0 for code in mapped}
    out = {code: 100.0 * (val - lo) / (hi - lo) for code, val in mapped.items()}
    if invert:
        return {code: 100.0 - score for code, score in out.items()}
    return out


def _mean(parts: list[dict[str, float]]) -> dict[str, float]:
    n = len(parts)
    if n < 1:
        raise RuntimeError("lentes: empty mean")
    return {code: sum(p[code] for p in parts) / n for code in UF_CODES}


def _component(indicator_id: str, *, invert: bool | None = None) -> tuple[dict[str, Any], dict[str, float]]:
    payload = _load_latest(indicator_id)
    flag = bool(payload.get("higher_is_worse")) if invert is None else invert
    scaled = _minmax(_values(payload), invert=flag)
    return payload, scaled


def _records(scores: dict[str, float], estados: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for code in sorted(UF_CODES):
        score = round(scores[code], 1)
        if not 0 <= score <= 100:
            raise RuntimeError(f"lentes: score out of range for {code}: {score}")
        meta = estados[code]
        out.append(
            {
                "ibge_code": code,
                "uf": meta["uf"],
                "name": meta["name"],
                "value": score,
            }
        )
    return out


def _write(
    *,
    indicator_id: str,
    name: str,
    short_name: str,
    definition: str,
    limitations: list[str],
    records: list[dict[str, Any]],
    dataset: str,
    higher_is_worse: bool = False,
) -> dict[str, Any]:
    period = "2026-08"
    fixture = {
        "indicator_id": indicator_id,
        "dataset_id": f"brasilreal.{indicator_id}.{period}",
        "title": f"{name} — UFs {period}",
        "short_name": short_name,
        "name": name,
        "status_label": "DERIVADO",
        "evidence_grade": "B",
        "unit": "nota 0-100",
        "higher_is_worse": higher_is_worse,
        "kind": "derived",
        "group": "lentes",
        "group_label": "Lentes (pesos declarados)",
        "frequency": "irregular",
        "reference_period": period,
        "reference_date": period,
        "release_date": None,
        "retrieved_at": utc_now(),
        "definition": definition,
        "source": {
            "organization": "Brasil Real",
            "dataset": dataset,
            "url": "https://brasilreal-atlas.web.app",
        },
        "limitations": limitations,
        "available_periods": [period],
        "checksum_sha256": _checksum(records),
        "records": records,
    }
    out_dir = fixtures_dir() / "lentes" / "indicators"
    out_dir.mkdir(parents=True, exist_ok=True)
    token = period.replace("-", "")
    write_json(out_dir / f"{indicator_id}_{token}.json", fixture)
    write_json(out_dir / f"{indicator_id}_latest.json", fixture)
    return {
        "indicator_id": indicator_id,
        "period": period,
        "n_ufs": len(records),
        "checksum": fixture["checksum_sha256"],
    }


def _cite(payload: dict[str, Any]) -> str:
    name = payload.get("short_name") or payload.get("name") or payload["indicator_id"]
    year = payload.get("reference_period")
    org = ((payload.get("source") or {}).get("organization")) or ""
    return f"{name} ({org} {year})"


COMMON_LIMITATIONS = [
    "Não é ranking oficial, IDHM nem «melhor estado» do IBGE — é receita editorial do Brasil Real.",
    "Pesos iguais entre blocos. Dentro do bloco, média simples das camadas oficiais já no mapa.",
    "Cada camada entra em min–máx 0–100 entre as 27 UFs; «maior é pior» entra invertido (100 − x).",
    "Anos mistos: cada bloco usa o latest da fonte. Não comparar com um único ano censitário.",
    "A cesta DIEESE não entra: é preço da capital, não da UF.",
    "Contagens absolutas (homicídios de mulheres, empregos totais, PIB total, impostos em R$) não entram: enviesam UFs grandes.",
    "Tributária/PIB e RFB não entram: não são carga do empreendedor nem qualidade do serviço.",
]


def materialize_lenses() -> dict[str, Any]:
    estados = _estados()

    income, s_income = _component("household_income_pc")
    labor, s_labor = _component("labor_income")
    poverty, s_poverty = _component("poverty_rate")
    unemp, s_unemp = _component("unemployment_rate")
    informal, s_informal = _component("informality_rate")
    occupy, s_occupy = _component("occupancy_rate")
    part, s_part = _component("participation_rate")
    homicide, s_homicide = _component("homicide_rate")
    traffic, s_traffic = _component("traffic_death_rate")
    physical, s_physical = _component("pns_physical_violence")
    physical_w, s_physical_w = _component("pns_physical_women")
    psych, s_psych = _component("pns_psych_violence")
    sanitation, s_san = _component("sanitation_adequate")
    water, s_water = _component("water_network_share")
    waste, s_waste = _component("waste_collected_share")
    literacy, s_lit = _component("literacy_rate")
    internet, s_net = _component("internet_home_share")
    rcl_pc, s_rcl_pc = _component("rcl_pc")

    live_blocks = [
        _mean([s_income, s_labor, s_poverty]),
        _mean([s_unemp, s_informal, s_occupy]),
        _mean([s_homicide, s_traffic, s_physical, s_psych]),
        _mean([s_san, s_water, s_waste, s_lit, s_net, s_rcl_pc]),
    ]
    live = _records(_mean(live_blocks), estados)

    birth, s_birth = _component("employer_unit_birth_rate")
    survival, s_surv = _component("employer_survival_1y")
    pibpc, s_pib = _component("pib_per_capita")
    wage, s_wage = _component("cempre_avg_wage")
    firms_p = _load_latest("cempre_firms")
    jobs_p = _load_latest("cempre_jobs")
    pop_p = _load_latest("population")
    firms = _values(firms_p)
    jobs = _values(jobs_p)
    pop = _values(pop_p)
    firm_density = {code: 1000.0 * firms[code] / pop[code] for code in UF_CODES}
    job_density = {code: 1000.0 * jobs[code] / pop[code] for code in UF_CODES}
    if any(v <= 0 for v in firm_density.values()) or any(v <= 0 for v in job_density.values()):
        raise RuntimeError("lentes: non-positive firm/job density")
    s_firm_density = _minmax(firm_density, invert=False)
    s_job_density = _minmax(job_density, invert=False)

    venture_blocks = [
        _mean([s_birth, s_surv]),
        _mean([s_pib, s_wage, s_informal, s_occupy, s_part]),
        _mean([s_firm_density, s_job_density]),
    ]
    venture = _records(_mean(venture_blocks), estados)

    live_def = (
        "Nota 0–100 entre as 27 UFs para a pergunta «morar». Quatro blocos com peso igual: "
        f"(1) renda — {_cite(income)}, {_cite(labor)} e {_cite(poverty)} invertida; "
        f"(2) trabalho — {_cite(unemp)} e {_cite(informal)} invertidos, {_cite(occupy)}; "
        f"(3) segurança — {_cite(homicide)}, {_cite(traffic)}, {_cite(physical)} e "
        f"{_cite(psych)}, invertidos; "
        f"(4) serviços e caixa estadual — {_cite(sanitation)}, {_cite(water)}, {_cite(waste)}, "
        f"{_cite(literacy)}, {_cite(internet)} e {_cite(rcl_pc)}. "
        "Dentro do bloco, média dos min–máx. Não é qualidade de vida medida; é essa receita."
    )
    venture_def = (
        "Nota 0–100 entre as 27 UFs para a pergunta «empreender». Três blocos com peso igual: "
        f"(1) dinâmica — {_cite(birth)} e {_cite(survival)}; "
        f"(2) mercado — {_cite(pibpc)}, {_cite(wage)}, {_cite(informal)} invertida, "
        f"{_cite(occupy)} e {_cite(part)}; "
        f"(3) densidade formal — empresas e pessoal ocupado CEMPRE "
        f"({firms_p.get('reference_period')}/{jobs_p.get('reference_period')}) "
        f"÷ população {pop_p.get('reference_period')}, por mil hab. "
        "Exclusive MEI. Contagens absolutas e tributária/PIB não entram. "
        "Não é ambiente de negócios do Banco Mundial."
    )

    wrote = {
        "lens_live": _write(
            indicator_id="lens_live",
            name="Melhor para morar (lente Brasil Real)",
            short_name="Melhor para morar",
            definition=live_def,
            limitations=COMMON_LIMITATIONS
            + ["Trocar um peso muda o 1º lugar — abra as camadas oficiais uma a uma."],
            records=live,
            dataset="Lente morar = 4 blocos iguais sobre camadas oficiais já no mapa",
        ),
        "lens_venture": _write(
            indicator_id="lens_venture",
            name="Melhor para empreender (lente Brasil Real)",
            short_name="Melhor para empreender",
            definition=venture_def,
            limitations=COMMON_LIMITATIONS
            + [
                "Abertura e sobrevivência de empregadoras (não MEI). Sobrevivência é 2021; nascimentos, 2022.",
            ],
            records=venture,
            dataset="Lente empreender = 3 blocos iguais sobre camadas oficiais já no mapa",
        ),
    }

    young_60, s_60 = _component("share_60_plus", invert=False)
    aging_idx, s_aging = _component("aging_index", invert=False)
    depend, s_dep = _component("dependency_ratio", invert=False)
    family_blocks = [
        _mean([s_income, s_poverty]),
        _mean([s_unemp, s_occupy]),
        _mean([s_homicide, s_traffic, s_physical_w]),
        _mean([s_san, s_water, s_waste, s_lit, s_net, s_rcl_pc]),
    ]
    family = _records(_mean(family_blocks), estados)
    aging = _records(_mean([s_60, s_aging, s_dep]), estados)

    family_def = (
        "Nota 0–100 entre as 27 UFs para «criar criança». Quatro blocos iguais: "
        f"(1) renda — {_cite(income)} e {_cite(poverty)} invertida; "
        f"(2) trabalho — {_cite(unemp)} invertida e {_cite(occupy)}; "
        f"(3) segurança — {_cite(homicide)}, {_cite(traffic)} e {_cite(physical_w)}, invertidos; "
        f"(4) serviços e caixa estadual — {_cite(sanitation)}, {_cite(water)}, {_cite(waste)}, "
        f"{_cite(literacy)}, {_cite(internet)} e {_cite(rcl_pc)}. "
        "Homicídios de mulheres (nº) e feminicídio penal não entram. Não é IDEB nem pediatria."
    )
    aging_def = (
        "Nota 0–100 de pressão etária (maior = mais pressão): média min–máx de "
        f"{_cite(young_60)}, {_cite(aging_idx)} e {_cite(depend)}. "
        "Não é «melhor para idoso» nem qualidade do SUS."
    )
    wrote["lens_family"] = _write(
        indicator_id="lens_family",
        name="Melhor para criança (lente Brasil Real)",
        short_name="Melhor para criança",
        definition=family_def,
        limitations=COMMON_LIMITATIONS
        + [
            "PNS 2019 entra só como violência física entre mulheres (autorreferida), não como IDEB.",
            "Homicídios de mulheres em número absoluto não entram (enviesam UFs grandes).",
        ],
        records=family,
        dataset="Lente criança = 4 blocos iguais sobre camadas oficiais já no mapa",
    )
    wrote["lens_aging"] = _write(
        indicator_id="lens_aging",
        name="Pressão etária (lente Brasil Real)",
        short_name="Pressão etária",
        definition=aging_def,
        limitations=COMMON_LIMITATIONS
        + ["Maior nota = mais pressão, não melhor qualidade de vida do idoso."],
        records=aging,
        dataset="Lente pressão etária = 60+, envelhecimento e dependência",
        higher_is_worse=True,
    )
    return wrote
