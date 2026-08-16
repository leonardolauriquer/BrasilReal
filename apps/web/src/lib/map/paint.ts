/** Choropleth paint + Maps-like place/metric properties on GeoJSON features. */

import { formatMapLabel, formatSharePercent } from "@/lib/format";
import { isAdditiveUnit, regionForUf } from "@/lib/map/regions";
export type MunFeatureCollection = {
  type: "FeatureCollection";
  features: Array<{
    type: string;
    properties: Record<string, string | number | null>;
    geometry: unknown;
  }>;
};

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

export function colorScale(t: number, higherIsWorse = false) {
  const x = Math.max(0, Math.min(1, Math.pow(t, 0.85)));
  if (higherIsWorse) {
    const r = Math.round(lerp(210, 176, x));
    const g = Math.round(lerp(230, 78, x));
    const b = Math.round(lerp(220, 58, x));
    return `rgb(${r},${g},${b})`;
  }
  const r = Math.round(lerp(214, 18, x));
  const g = Math.round(lerp(232, 110, x));
  const b = Math.round(lerp(224, 118, x));
  return `rgb(${r},${g},${b})`;
}

function shortPlaceName(name: string, max = 18) {
  const n = name.trim();
  if (n.length <= max) return n;
  return `${n.slice(0, max - 1)}…`;
}

/** Exterior-ring centroid — avoids holes skewing the label into the ocean. */
export function geometryCentroid(geometry: unknown): [number, number] | null {
  if (!geometry || typeof geometry !== "object") return null;
  const g = geometry as { type: string; coordinates: unknown };
  const avg = (ring: unknown): [number, number] | null => {
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
  };

  if (g.type === "Point" && Array.isArray(g.coordinates)) {
    return g.coordinates as [number, number];
  }
  if (g.type === "Polygon" && Array.isArray(g.coordinates)) {
    return avg(g.coordinates[0]);
  }
  if (g.type === "MultiPolygon" && Array.isArray(g.coordinates)) {
    // Largest exterior ring by vertex count ≈ main landmass for label.
    let best: [number, number] | null = null;
    let bestN = -1;
    for (const poly of g.coordinates) {
      if (!Array.isArray(poly) || !poly[0]) continue;
      const ring = poly[0] as unknown[];
      if (ring.length > bestN) {
        bestN = ring.length;
        best = avg(ring);
      }
    }
    return best;
  }
  return null;
}

/** Point FeatureCollection for symbol layers (reliable vs polygon placement). */
export function toLabelPoints(geo: MunFeatureCollection): MunFeatureCollection {
  return {
    type: "FeatureCollection",
    features: geo.features
      .map((f) => {
        const center = geometryCentroid(f.geometry);
        if (!center) return null;
        return {
          type: "Feature",
          properties: { ...f.properties },
          geometry: { type: "Point", coordinates: center },
        };
      })
      .filter(Boolean) as MunFeatureCollection["features"],
  };
}

/**
 * Enrich features for Maps-like labeling:
 * - place_sigla / place_name = geographic identity
 * - metric_text = layer value (secondary)
 * - label_stack_* = single collision-friendly stacked labels
 */
export function paintCollection(
  geo: MunFeatureCollection,
  valueMap: Map<string, number>,
  higherIsWorse: boolean,
  unit?: string,
  mode: "uf" | "mun" = "uf",
) {
  const nums = [...valueMap.values()];
  const min = nums.length ? Math.min(...nums) : 0;
  const max = nums.length ? Math.max(...nums) : 1;
  const span = max - min || 1;
  const total = nums.reduce((a, b) => a + b, 0);
  const showShare = Boolean(total > 0 && isAdditiveUnit(unit));

  const ranked = geo.features
    .map((f, idx) => {
      const code = String(f.properties.ibge_code || f.properties.codarea || "");
      const raw = f.properties.value;
      const hasValue = valueMap.has(code) || typeof raw === "number";
      const value =
        typeof raw === "number"
          ? raw
          : valueMap.has(code)
            ? (valueMap.get(code) as number)
            : Number.NEGATIVE_INFINITY;
      return { idx, code, hasValue, value: hasValue ? value : Number.NEGATIVE_INFINITY };
    })
    .sort((a, b) => b.value - a.value);

  const rankByIdx = new Map<number, number>();
  ranked.forEach((r, order) => rankByIdx.set(r.idx, order));

  return {
    ...geo,
    features: geo.features.map((f, idx) => {
      const code = String(f.properties.ibge_code || f.properties.codarea || "");
      const raw = f.properties.value;
      const hasValue = valueMap.has(code) || typeof raw === "number";
      const value =
        typeof raw === "number"
          ? raw
          : valueMap.has(code)
            ? (valueMap.get(code) as number)
            : min;
      const t = hasValue ? (value - min) / span : 0;
      const uf = String(f.properties.uf || "");
      const fullName = String(f.properties.name || uf || code);
      const placeSigla = mode === "uf" ? uf || fullName.slice(0, 2).toUpperCase() : "";
      const placeName =
        mode === "uf" ? fullName : shortPlaceName(fullName, hasValue ? 16 : 20);
      const labelRank = rankByIdx.get(idx) ?? 999;
      const region = mode === "uf" ? regionForUf(uf) : undefined;

      let metricText = "";
      if (hasValue) {
        const abs = formatMapLabel(value, unit);
        if (showShare) {
          const share = formatSharePercent(value, total);
          metricText = share ? `${abs} · ${share}` : abs;
        } else {
          metricText = abs;
        }
      }

      const compactStack = metricText
        ? `${placeSigla || placeName}\n${metricText}`
        : placeSigla || placeName;
      const fullStack = metricText ? `${placeName}\n${metricText}` : placeName;

      return {
        ...f,
        properties: {
          ...f.properties,
          ibge_code: code,
          fill: hasValue ? colorScale(t, higherIsWorse) : "#c5d4cf",
          value: hasValue ? value : null,
          place_sigla: placeSigla,
          place_name: placeName,
          metric_text: metricText,
          label_rank: labelRank,
          label_stack_compact: compactStack,
          label_stack_full: fullStack,
          label: metricText || placeName,
          region_id: region?.id || "",
          region_name: region?.name || "",
        },
      };
    }),
  };
}
