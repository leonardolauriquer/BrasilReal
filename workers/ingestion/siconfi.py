"""SICONFI / Tesouro Nacional open API probes and snapshots."""

from __future__ import annotations

import hashlib
import json
import math
import time
import unicodedata
from typing import Any, TypedDict

from common import fetch_bytes, fixtures_dir, snapshot_raw, utc_now, write_json

ENTES_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/entes"
RREO_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo"


def snapshot_entes(limit_hint: int = 50) -> dict[str, Any]:
    """Download SICONFI entes catalog (paginated open API)."""
    raw = fetch_bytes(f"{ENTES_URL}?limit={limit_hint}", timeout=120)
    snapshot_raw(
        "siconfi",
        "entes_sample.json",
        raw,
        {"source_url": ENTES_URL, "connector": "siconfi.entes"},
    )
    payload = json.loads(raw.decode("utf-8"))
    items = payload.get("items", [])
    out = {
        "retrieved_at": utc_now(),
        "source_url": ENTES_URL,
        "docs": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        "status_label": "OBSERVADO",
        "count_returned": len(items),
        "has_more": payload.get("hasMore"),
        "sample": items[:10],
        "limitations": [
            "API pública paginada; não é tempo real tick-a-tick.",
            "Contabilidade pública tem defasagem e revisões; separar empenhado/liquidado/pago.",
        ],
    }
    path = fixtures_dir() / "siconfi" / "entes_sample.json"
    write_json(path, out)
    return {"wrote": str(path), "count_returned": len(items), "has_more": out["has_more"]}


def probe_rreo(an_exercicio: int = 2024, nr_periodo: int = 6, id_ente: int = 35) -> dict[str, Any]:
    """Fetch one RREO slice as connectivity/schema probe for Fase 2."""
    url = (
        f"{RREO_URL}?an_exercicio={an_exercicio}&nr_periodo={nr_periodo}"
        f"&co_tipo_demonstrativo=RREO&id_ente={id_ente}"
    )
    try:
        raw = fetch_bytes(url, timeout=120)
    except Exception as exc:  # noqa: BLE001 - probe should not crash runner
        return {"ok": False, "url": url, "error": str(exc)}
    snapshot_raw(
        "siconfi",
        f"rreo_{id_ente}_{an_exercicio}_p{nr_periodo}.json",
        raw,
        {"source_url": url, "connector": "siconfi.rreo.probe"},
    )
    payload = json.loads(raw.decode("utf-8"))
    path = fixtures_dir() / "siconfi" / "rreo_probe.json"
    write_json(
        path,
        {
            "retrieved_at": utc_now(),
            "source_url": url,
            "status_label": "OBSERVADO",
            "count_returned": len(payload.get("items", [])),
            "sample": payload.get("items", [])[:5],
        },
    )
    return {"ok": True, "wrote": str(path), "count_returned": len(payload.get("items", []))}


# --- Fase 2: one honest UF choropleth (RCL from RREO Anexo 14) ---

UF_CODES = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}

RCL_BIMESTRE = 6
RCL_YEARS = (2022, 2023, 2024, 2025)


class RreoLayer(TypedDict):
    indicator_id: str
    anexo: str
    cod_conta: str
    short_name: str
    name: str
    title_prefix: str
    dataset: str
    extra_method: str
    require_positive: bool
    higher_is_worse: bool
    definition: str
    limitations: list[str]


RREO_LAYERS: tuple[RreoLayer, ...] = (
    {
        "indicator_id": "rcl_rreo",
        "anexo": "RREO-Anexo 14",
        "cod_conta": "ReceitaCorrenteLiquidaDemonstrativoSimplificado",
        "short_name": "RCL (RREO)",
        "name": "Receita Corrente Líquida — RREO (até o 6º bimestre)",
        "title_prefix": "Receita Corrente Líquida (RREO 6º bimestre)",
        "dataset": "RREO Anexo 14 / Receita Corrente Líquida",
        "extra_method": "conta ReceitaCorrenteLiquidaDemonstrativoSimplificado",
        "require_positive": True,
        "higher_is_worse": False,
        "definition": (
            "Receita Corrente Líquida do ente estadual (e DF) no Demonstrativo Simplificado "
            "do RREO (Anexo 14), conta ReceitaCorrenteLiquidaDemonstrativoSimplificado, "
            "coluna «Até o Bimestre», 6º bimestre (acumulado do exercício). "
            "Fonte: API SICONFI / Tesouro Nacional."
        ),
        "limitations": [
            "RCL da LRF — não é PIB, não é transferência recebida isolada, não é caixa.",
            "Valor nominal do exercício; não deflacionado.",
            "A população que o SICONFI devolve no RREO não é usada aqui.",
            "Demonstrativos revisáveis; o 6º bimestre é o acumulado anual publicado naquele recorte.",
        ],
    },
    {
        "indicator_id": "receita_tributaria_rreo",
        "anexo": "RREO-Anexo 01",
        "cod_conta": "ReceitaTributaria",
        "short_name": "Receita tributária",
        "name": "Receita tributária realizada — RREO Anexo 01",
        "title_prefix": "Receita tributária (RREO 6º bimestre)",
        "dataset": "RREO Anexo 01 / Receita tributária realizada",
        "extra_method": "conta ReceitaTributaria (IMPOSTOS, TAXAS E CONTRIBUIÇÕES DE MELHORIA)",
        "require_positive": True,
        "higher_is_worse": False,
        "definition": (
            "Receita tributária realizada do ente estadual (e DF) no Balanço Orçamentário "
            "do RREO (Anexo 01), conta ReceitaTributaria, coluna «Até o Bimestre», 6º bimestre. "
            "Fonte: API SICONFI / Tesouro Nacional."
        ),
        "limitations": [
            "É a receita realizada de impostos, taxas e contribuição de melhoria — não é RCL.",
            "Valor nominal do exercício; não deflacionado.",
            "Não inclui intra-orçamentárias; não é transferência da União.",
        ],
    },
    {
        "indicator_id": "impostos_rreo",
        "anexo": "RREO-Anexo 01",
        "cod_conta": "Impostos",
        "short_name": "Impostos (RREO)",
        "name": "Receita de impostos realizada — RREO Anexo 01",
        "title_prefix": "Impostos (RREO 6º bimestre)",
        "dataset": "RREO Anexo 01 / Impostos",
        "extra_method": "conta Impostos (sem taxas nem contribuição de melhoria)",
        "require_positive": True,
        "higher_is_worse": False,
        "definition": (
            "Receita realizada de impostos do ente estadual (e DF) no Balanço Orçamentário "
            "do RREO (Anexo 01), conta Impostos, coluna «Até o Bimestre», 6º bimestre. "
            "Inclui ICMS, IPVA, ITCMD e demais impostos lançados nessa linha consolidada. "
            "Fonte: API SICONFI / Tesouro Nacional."
        ),
        "limitations": [
            "A API do RREO não publica ICMS/IPVA/ITCMD em linhas separadas com 27 UFs — só o total Impostos.",
            "Não é arrecadação federal da RFB no território nem carga tributária nacional.",
            "Valor nominal do exercício; não deflacionado.",
        ],
    },
    {
        "indicator_id": "transf_uniao_rreo",
        "anexo": "RREO-Anexo 01",
        "cod_conta": "TransferenciasCorrentesDaUniaoEDeSuasEntidades",
        "short_name": "Transf. União (correntes)",
        "name": "Transferências correntes da União — RREO Anexo 01",
        "title_prefix": "Transferências correntes da União (RREO 6º bimestre)",
        "dataset": "RREO Anexo 01 / Transferências correntes da União",
        "extra_method": "conta TransferenciasCorrentesDaUniaoEDeSuasEntidades",
        "require_positive": True,
        "higher_is_worse": False,
        "definition": (
            "Transferências correntes recebidas da União e de suas entidades, realizadas até o "
            "6º bimestre no RREO Anexo 01 (conta TransferenciasCorrentesDaUniaoEDeSuasEntidades). "
            "Inclui FPE e outras correntes da União registradas nessa linha. "
            "Fonte: API SICONFI / Tesouro Nacional."
        ),
        "limitations": [
            "É o que o estado registrou como recebido da União — não o empenho federal isolado.",
            "Não distingue FPE, SUS, FUNDEB ou convênios; a conta é agregada.",
            "Valor nominal do exercício; não deflacionado.",
        ],
    },
    {
        "indicator_id": "despesa_empenhada_rreo",
        "anexo": "RREO-Anexo 14",
        "cod_conta": "DespesasEmpenhadasDemonstrativoSimplificadoBalancoOrcamentario",
        "short_name": "Despesa empenhada",
        "name": "Despesas empenhadas — RREO Anexo 14",
        "title_prefix": "Despesas empenhadas (RREO 6º bimestre)",
        "dataset": "RREO Anexo 14 / Despesas empenhadas (Balanço Orçamentário)",
        "extra_method": "conta DespesasEmpenhadasDemonstrativoSimplificadoBalancoOrcamentario",
        "require_positive": True,
        "higher_is_worse": False,
        "definition": (
            "Despesas empenhadas do ente estadual (e DF) no Demonstrativo Simplificado do RREO "
            "(Anexo 14, recorte do Balanço Orçamentário), coluna «Até o Bimestre», 6º bimestre. "
            "Fonte: API SICONFI / Tesouro Nacional."
        ),
        "limitations": [
            "Empenhado ≠ liquidado ≠ pago. Aqui é só o empenhado acumulado do exercício.",
            "Valor nominal; não deflacionado.",
            "Não é gasto federal territorializado.",
        ],
    },
    {
        "indicator_id": "dcl_rreo",
        "anexo": "RREO-Anexo 06",
        "cod_conta": "DividaConsolidadaLiquida",
        "short_name": "Dívida líquida (DCL)",
        "name": "Dívida Consolidada Líquida — RREO Anexo 06",
        "title_prefix": "Dívida Consolidada Líquida (RREO 6º bimestre)",
        "dataset": "RREO Anexo 06 / Dívida Consolidada Líquida",
        "extra_method": "conta DividaConsolidadaLiquida",
        "require_positive": False,
        "higher_is_worse": True,
        "definition": (
            "Dívida Consolidada Líquida (DCL) do ente estadual (e DF) no RREO Anexo 06, "
            "conta DividaConsolidadaLiquida, coluna «Até o Bimestre» do 6º bimestre "
            "(posição ao fim do exercício naquele recorte). "
            "Fonte: API SICONFI / Tesouro Nacional."
        ),
        "limitations": [
            "Estoque, não fluxo. Pode ser zero ou negativa se as deduções superarem a dívida bruta.",
            "Não é dívida da União nem crédito privado das famílias.",
            "Valor nominal; demonstrativos revisáveis.",
        ],
    },
)


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).casefold().strip()


def _estados() -> dict[str, dict[str, str]]:
    path = fixtures_dir() / "ibge" / "estados_refresh.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, str]] = {}
    for item in data.get("items") or []:
        code = str(item["id"]).zfill(2)
        out[code] = {"ibge_code": code, "uf": item["sigla"], "name": item["nome"]}
    if set(out) != set(UF_CODES):
        raise RuntimeError("siconfi: estados_refresh must cover 27 UFs")
    return out


def _rreo_url(year: int, ibge_code: str) -> str:
    ente = str(int(ibge_code))
    return (
        f"{RREO_URL}?an_exercicio={year}&nr_periodo={RCL_BIMESTRE}"
        f"&co_tipo_demonstrativo=RREO&id_ente={ente}"
    )


def _extract_conta(
    items: list[dict[str, Any]],
    *,
    anexo: str,
    cod_conta: str,
) -> float | None:
    for row in items:
        if str(row.get("cod_conta") or "") != cod_conta:
            continue
        if str(row.get("anexo") or "") != anexo:
            continue
        if _fold(str(row.get("coluna") or "")).startswith("ate o bimestre"):
            raw = row.get("valor")
            if raw in (None, "", "-"):
                return None
            val = float(raw)
            if not math.isfinite(val):
                return None
            return val
    return None


def _acceptable(val: float | None, *, require_positive: bool) -> bool:
    if val is None or not math.isfinite(val):
        return False
    if require_positive and not (val > 0):
        return False
    return True


def _write_rreo_fixture(
    layer: RreoLayer,
    series: dict[str, list[dict[str, Any]]],
    kept_years: list[int],
) -> dict[str, Any]:
    latest = str(max(kept_years))
    records = series[latest]
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    brazil_total = sum(float(r["value"]) for r in records)
    ind = layer["indicator_id"]
    fixture = {
        "indicator_id": ind,
        "dataset_id": f"siconfi.{ind}.{latest}",
        "title": f"{layer['title_prefix']} — UFs {latest}",
        "short_name": layer["short_name"],
        "name": layer["name"],
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "unit": "BRL",
        "higher_is_worse": layer["higher_is_worse"],
        "kind": "observed_estimate",
        "group": "fiscal",
        "group_label": "Fiscal",
        "frequency": "annual",
        "reference_period": latest,
        "reference_date": f"{latest}-12-31",
        "release_date": None,
        "retrieved_at": utc_now(),
        "available_periods": [str(y) for y in kept_years],
        "brazil_total": brazil_total,
        "definition": layer["definition"],
        "source": {
            "organization": "STN — SICONFI / Tesouro Nacional",
            "dataset": layer["dataset"],
            "dataset_page": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
            "url": RREO_URL,
            "method_notes": (
                "GET /ords/siconfi/tt/rreo co_tipo_demonstrativo=RREO nr_periodo=6 "
                f"id_ente=código IBGE da UF. {layer['extra_method']}. Uma linha por exercício."
            ),
        },
        "limitations": layer["limitations"],
        "checksum_sha256": checksum,
        "records": records,
        "series": series,
    }
    out_dir = fixtures_dir() / "siconfi" / "indicators"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / f"{ind}_{latest}.json", fixture)
    write_json(out_dir / f"{ind}_latest.json", fixture)
    return {
        "indicator_id": ind,
        "period": latest,
        "periods": [str(y) for y in kept_years],
        "ufs": 27,
        "brazil_total": brazil_total,
        "checksum": checksum,
    }


def fetch_rreo_layers(years: tuple[int, ...] = RCL_YEARS) -> dict[str, Any]:
    """Pull 27-UF RREO 6º bimestre and paint several official choropleths — never invent cells."""
    estados = _estados()
    buckets: dict[str, dict[str, list[dict[str, Any]]]] = {spec["indicator_id"]: {} for spec in RREO_LAYERS}
    kept: dict[str, list[int]] = {spec["indicator_id"]: [] for spec in RREO_LAYERS}

    for year in years:
        year_values: dict[str, dict[str, float]] = {spec["indicator_id"]: {} for spec in RREO_LAYERS}
        year_missing: dict[str, list[str]] = {spec["indicator_id"]: [] for spec in RREO_LAYERS}
        for code in sorted(UF_CODES):
            snap = year == years[-1] and code == "35"
            items = _fetch_rreo_items(year, code, snapshot=snap)
            for spec in RREO_LAYERS:
                ind = spec["indicator_id"]
                val = _extract_conta(items, anexo=spec["anexo"], cod_conta=spec["cod_conta"])
                if not _acceptable(val, require_positive=spec["require_positive"]):
                    year_missing[ind].append(code)
                else:
                    year_values[ind][code] = val  # type: ignore[assignment]
            time.sleep(0.25)
        for spec in RREO_LAYERS:
            ind = spec["indicator_id"]
            values = year_values[ind]
            if year_missing[ind] or set(values) != set(UF_CODES):
                continue
            records = []
            for code in sorted(UF_CODES):
                meta = estados[code]
                records.append(
                    {
                        "ibge_code": code,
                        "uf": meta["uf"],
                        "name": meta["name"],
                        "value": values[code],
                    }
                )
            buckets[ind][str(year)] = records
            kept[ind].append(year)

    written: dict[str, Any] = {}
    missing_layers: list[str] = []
    for spec in RREO_LAYERS:
        ind = spec["indicator_id"]
        if not buckets[ind]:
            missing_layers.append(ind)
            continue
        written[ind] = _write_rreo_fixture(spec, buckets[ind], kept[ind])
    if "rcl_rreo" not in written:
        raise RuntimeError("siconfi rcl_rreo: no year with 27 finite UFs (RCL Anexo 14)")
    if missing_layers:
        written["_skipped"] = missing_layers
    return written


def fetch_rcl_rreo(years: tuple[int, ...] = RCL_YEARS) -> dict[str, Any]:
    result = fetch_rreo_layers(years)
    rcl = result.get("rcl_rreo")
    if not isinstance(rcl, dict):
        raise RuntimeError("siconfi rcl_rreo: fixture missing after RREO pull")
    return rcl


def fetch_fase2() -> dict[str, Any]:
    return {
        "entes": snapshot_entes(limit_hint=50),
        "rreo_probe": probe_rreo(),
        "rreo_layers": fetch_rreo_layers(),
    }


def _fetch_rreo_items(year: int, ibge_code: str, *, snapshot: bool = False) -> list[dict[str, Any]]:
    url = _rreo_url(year, ibge_code)
    raw = fetch_bytes(url, timeout=120)
    if snapshot:
        snapshot_raw(
            "siconfi",
            f"rreo_{ibge_code}_{year}_p{RCL_BIMESTRE}.json",
            raw,
            {"source_url": url, "connector": "siconfi.rreo.rcl"},
        )
    payload = json.loads(raw.decode("utf-8"))
    items = list(payload.get("items") or [])
    offset = int(payload.get("offset") or 0)
    while payload.get("hasMore"):
        offset += int(payload.get("limit") or len(items) or 5000)
        page_url = f"{url}&offset={offset}"
        raw = fetch_bytes(page_url, timeout=120)
        payload = json.loads(raw.decode("utf-8"))
        items.extend(payload.get("items") or [])
    return items

