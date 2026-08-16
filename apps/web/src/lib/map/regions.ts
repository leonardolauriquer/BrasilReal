/** IBGE macrorregiões (N/NE/CO/SE/S) — rótulos e agregação honesta no zoom afastado. */

import { formatMapLabel, formatSharePercent } from "@/lib/format";

export type MacroRegionId = "N" | "NE" | "CO" | "SE" | "S";

export type MacroRegion = {
  id: MacroRegionId;
  name: string;
  /** Siglas UF (IBGE). */
  ufs: string[];
};

type LabelFeatureCollection = {
  type: "FeatureCollection";
  features: Array<{
    type: string;
    properties: Record<string, string | number | null>;
    geometry: unknown;
  }>;
};

/** Ordem geográfica estável para ranking/labels. */
export const MACRO_REGIONS: MacroRegion[] = [
  { id: "N", name: "Norte", ufs: ["AC", "AP", "AM", "PA", "RO", "RR", "TO"] },
  {
    id: "NE",
    name: "Nordeste",
    ufs: ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
  },
  { id: "CO", name: "Centro-Oeste", ufs: ["DF", "GO", "MT", "MS"] },
  { id: "SE", name: "Sudeste", ufs: ["ES", "MG", "RJ", "SP"] },
  { id: "S", name: "Sul", ufs: ["PR", "RS", "SC"] },
];

export type RecorteId = "BR" | MacroRegionId | "litoral" | "fronteira";

/** UFs com ≥1 município na lista IBGE Costeiro/Marinho (2019). */
export const COASTAL_UFS = [
  "AL",
  "AP",
  "BA",
  "CE",
  "ES",
  "MA",
  "PA",
  "PB",
  "PE",
  "PI",
  "PR",
  "RJ",
  "RN",
  "RS",
  "SC",
  "SE",
  "SP",
] as const;

/** Estados com fronteira terrestre internacional. */
export const BORDER_UFS = [
  "AC",
  "AM",
  "AP",
  "MS",
  "MT",
  "PA",
  "PR",
  "RO",
  "RR",
  "RS",
  "SC",
] as const;

export const RECORTE_OPTIONS: Array<{ value: RecorteId; label: string }> = [
  { value: "BR", label: "Brasil (27 UFs)" },
  { value: "N", label: "Norte" },
  { value: "NE", label: "Nordeste" },
  { value: "CO", label: "Centro-Oeste" },
  { value: "SE", label: "Sudeste" },
  { value: "S", label: "Sul" },
  { value: "litoral", label: "Litoral" },
  { value: "fronteira", label: "Fronteira" },
];

export function ufsForRecorte(recorte: RecorteId): readonly string[] | null {
  if (recorte === "BR") return null;
  if (recorte === "litoral") return COASTAL_UFS;
  if (recorte === "fronteira") return BORDER_UFS;
  return MACRO_REGIONS.find((r) => r.id === recorte)?.ufs ?? null;
}

export function recorteLabel(recorte: RecorteId): string {
  return RECORTE_OPTIONS.find((o) => o.value === recorte)?.label || recorte;
}

/** 1º lugar = melhor: menor valor se a métrica for «maior é pior». */
export function compareRankValue(a: number, b: number, higherIsWorse: boolean): number {
  return higherIsWorse ? a - b : b - a;
}

const UF_TO_REGION = new Map<string, MacroRegion>();
for (const r of MACRO_REGIONS) {
  for (const uf of r.ufs) UF_TO_REGION.set(uf, r);
}

export function regionForUf(uf: string): MacroRegion | undefined {
  return UF_TO_REGION.get(uf.toUpperCase());
}

/**
 * Soma regional só quando a unidade é aditiva (contagens, valores monetários).
 * Taxas/% não são somadas — entram como média ponderada pela população.
 */
export function isAdditiveUnit(unit?: string): boolean {
  if (!unit) return false;
  const u = unit.trim().toLowerCase();
  if (!u) return false;
  if (u === "anos" || u === "ano") return false;
  if (u === "%" || u === "pp" || u === "p.p.") return false;
  if (u.includes("por 100") || u.startsWith("por ")) return false;
  if (u.includes("salário mínimo") || u.includes("salarios minimos") || u.includes("salários mínimos"))
    return false;
  // Densities and per-capita ratios — not area (km²), which is additive.
  if (u.includes("/") || u.includes("hab/km")) return false;
  if (u.includes("nota")) return false;
  if (u.includes("rcl") || u.includes("razão") || u.includes("razao")) return false;
  if (u.includes("taxa") || u.includes("índice") || u.includes("indice")) return false;
  if (u.includes("percent") || u.includes("%")) return false;
  if (u.includes("densidade")) return false;
  return true;
}

/** Densidade já é razão área/pop — média ponderada distorce. */
export function canPopWeightUnit(unit?: string): boolean {
  if (!unit || isAdditiveUnit(unit)) return false;
  const u = unit.trim().toLowerCase();
  if (u.includes("hab/km") || u.includes("densidade")) return false;
  return true;
}

export type RegionAggregateKind = "sum" | "pop_weighted" | "none";

export type RegionRankRow = {
  id: MacroRegionId;
  name: string;
  value: number | null;
  unit?: string;
  /** Códigos IBGE das UFs da região (para enquadrar o mapa). */
  ibge_codes: string[];
  uf_count: number;
  with_data: number;
  aggregate: RegionAggregateKind;
};

function aggregateMacroRegions(
  valueByIbge: Map<string, number>,
  ufMeta: Array<{ ibge_code: string; uf: string }>,
  unit?: string,
  popByIbge?: Map<string, number>,
): RegionRankRow[] {
  const metaByUf = new Map(ufMeta.map((m) => [m.uf.toUpperCase(), m]));
  const additive = isAdditiveUnit(unit);
  const popWeight = canPopWeightUnit(unit);

  return MACRO_REGIONS.map((region) => {
    const codes: string[] = [];
    let sum = 0;
    let withData = 0;
    let wsum = 0;
    let wpop = 0;
    let nWeighted = 0;
    for (const sigla of region.ufs) {
      const meta = metaByUf.get(sigla);
      if (!meta) continue;
      codes.push(meta.ibge_code);
      if (!valueByIbge.has(meta.ibge_code)) continue;
      withData += 1;
      const v = valueByIbge.get(meta.ibge_code) as number;
      sum += v;
      const pop = popByIbge?.get(meta.ibge_code);
      if (typeof pop === "number" && pop > 0) {
        wsum += v * pop;
        wpop += pop;
        nWeighted += 1;
      }
    }
    let value: number | null = null;
    let aggregate: RegionAggregateKind = "none";
    if (additive && withData > 0) {
      value = sum;
      aggregate = "sum";
    } else if (popWeight && withData > 0 && nWeighted === withData && wpop > 0) {
      value = wsum / wpop;
      aggregate = "pop_weighted";
    }
    return {
      id: region.id,
      name: region.name,
      value,
      unit: value != null ? unit : undefined,
      ibge_codes: codes,
      uf_count: region.ufs.length,
      with_data: withData,
      aggregate,
    };
  });
}

export function buildRegionRanking(
  valueByIbge: Map<string, number>,
  ufMeta: Array<{ ibge_code: string; uf: string; unit?: string }>,
  unit?: string,
  higherIsWorse = false,
  popByIbge?: Map<string, number>,
): RegionRankRow[] {
  return aggregateMacroRegions(valueByIbge, ufMeta, unit, popByIbge).sort((a, b) => {
    if (a.value == null && b.value == null) return a.name.localeCompare(b.name, "pt-BR");
    if (a.value == null) return 1;
    if (b.value == null) return -1;
    return compareRankValue(a.value, b.value, higherIsWorse);
  });
}

function ringCentroid(ring: unknown): [number, number] | null {
  if (!Array.isArray(ring) || !ring.length) return null;
  let sx = 0;
  let sy = 0;
  let n = 0;
  for (const c of ring) {
    if (!Array.isArray(c) || typeof c[0] !== "number") continue;
    sx += c[0] as number;
    sy += c[1] as number;
    n += 1;
  }
  return n ? [sx / n, sy / n] : null;
}

function featureCentroid(geometry: unknown): [number, number] | null {
  if (!geometry || typeof geometry !== "object") return null;
  const g = geometry as { type: string; coordinates: unknown };
  if (g.type === "Point" && Array.isArray(g.coordinates)) {
    return g.coordinates as [number, number];
  }
  if (g.type === "Polygon" && Array.isArray(g.coordinates)) {
    return ringCentroid(g.coordinates[0]);
  }
  if (g.type === "MultiPolygon" && Array.isArray(g.coordinates)) {
    let best: [number, number] | null = null;
    let bestN = -1;
    for (const poly of g.coordinates) {
      if (!Array.isArray(poly) || !poly[0]) continue;
      const ring = poly[0] as unknown[];
      if (ring.length > bestN) {
        bestN = ring.length;
        best = ringCentroid(ring);
      }
    }
    return best;
  }
  return null;
}

/** Pontos de rótulo: centroide médio das UFs da região (+ métrica agregada). */
export function buildRegionLabelPoints(
  ufGeo: LabelFeatureCollection,
  valueMap: Map<string, number>,
  unit?: string,
  popByIbge?: Map<string, number>,
): LabelFeatureCollection {
  const byUf = new Map<string, LabelFeatureCollection["features"][number]>();
  const ufMeta: Array<{ ibge_code: string; uf: string }> = [];
  for (const f of ufGeo.features) {
    const uf = String(f.properties.uf || "").toUpperCase();
    const code = String(f.properties.ibge_code || "");
    if (uf) byUf.set(uf, f);
    if (uf && code) ufMeta.push({ ibge_code: code, uf });
  }
  const stats = aggregateMacroRegions(valueMap, ufMeta, unit, popByIbge);
  const statById = new Map(stats.map((s) => [s.id, s]));
  const shareTotal = stats.reduce(
    (sum, s) => (s.aggregate === "sum" && s.value != null ? sum + s.value : sum),
    0,
  );

  const features: LabelFeatureCollection["features"] = [];
  for (const region of MACRO_REGIONS) {
    let sx = 0;
    let sy = 0;
    let n = 0;
    for (const sigla of region.ufs) {
      const f = byUf.get(sigla);
      if (!f) continue;
      const c = featureCentroid(f.geometry);
      if (!c) continue;
      sx += c[0];
      sy += c[1];
      n += 1;
    }
    if (!n) continue;

    const row = statById.get(region.id);
    let metricText = "";
    if (row?.value != null && row.unit) {
      const abs = formatMapLabel(row.value, row.unit);
      if (row.aggregate === "sum" && shareTotal > 0) {
        const share = formatSharePercent(row.value, shareTotal);
        metricText = share ? `${abs} · ${share}` : abs;
      } else {
        metricText = abs;
      }
    }

    const stack = metricText ? `${region.name}\n${metricText}` : region.name;
    features.push({
      type: "Feature",
      properties: {
        region_id: region.id,
        place_name: region.name,
        metric_text: metricText,
        label_stack: stack,
        label_rank: MACRO_REGIONS.findIndex((r) => r.id === region.id),
      },
      geometry: { type: "Point", coordinates: [sx / n, sy / n] },
    });
  }

  return { type: "FeatureCollection", features };
}

export type RegionFiche = {
  level: "macro" | "intermediate";
  id: string;
  name: string;
  uf?: string;
  uf_code?: string;
  ibge_codes: string[];
  layerLabel: string;
  period: string;
  value: number | null;
  unit?: string;
  with_data: number;
  total_parts: number;
  method: string;
  disclaimer: string;
  status_label: string;
  definition?: string;
  source_org?: string;
};

export function buildMacroFiche(
  row: RegionRankRow,
  opts: {
    layerLabel: string;
    period: string;
    unit?: string;
    definition?: string;
    source_org?: string;
    status_label?: string;
  },
): RegionFiche {
  const method =
    row.aggregate === "sum"
      ? `Soma das ${row.with_data} UFs com dado nesta camada (de ${row.uf_count}).`
      : row.aggregate === "pop_weighted"
        ? `Média ponderada pela população (projeção IBGE mais recente) das ${row.with_data} UFs com dado (de ${row.uf_count}). Não é publicação IBGE da macrorregião.`
        : "Taxas deste tipo (ex.: densidade) não agregamos no recorte regional — veja cada UF.";
  return {
    level: "macro",
    id: row.id,
    name: row.name,
    ibge_codes: row.ibge_codes,
    layerLabel: opts.layerLabel,
    period: opts.period,
    value: row.value,
    unit: row.unit,
    with_data: row.with_data,
    total_parts: row.uf_count,
    method,
    disclaimer:
      "Agregado exploratório a partir de observações oficiais por UF. Não é publicação IBGE da macrorregião.",
    status_label: opts.status_label || "DERIVADO",
    definition: opts.definition,
    source_org: opts.source_org,
  };
}

export function buildIntermediateFiche(props: {
  id: string;
  name: string;
  uf?: string;
  uf_code?: string;
  layerLabel: string;
  period: string;
}): RegionFiche {
  return {
    level: "intermediate",
    id: props.id,
    name: props.name,
    uf: props.uf,
    uf_code: props.uf_code,
    ibge_codes: props.uf_code ? [props.uf_code] : [],
    layerLabel: props.layerLabel,
    period: props.period,
    value: null,
    with_data: 0,
    total_parts: 0,
    method:
      "Região intermediária IBGE (divisão oficial). A camada atual é publicada por UF/município — sem recorte intermediário aqui.",
    disclaimer:
      "Rótulo e malha oficiais IBGE. Não inventamos valor da camada neste nível geográfico.",
    status_label: "MALHA",
  };
}
