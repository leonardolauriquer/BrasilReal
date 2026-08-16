/** Client-side data gate — never paint/rank unlabeled or non-finite values. */

import type { Observation } from "@/lib/api";

export type GateDrop = {
  indicator?: string;
  geography?: string;
  reason: string;
};

export function hasObservationProvenance(row: {
  definition?: string;
  reference_period?: string;
  status_label?: string;
  source?: { organization?: string; dataset?: string } | Record<string, unknown> | null;
}): boolean {
  const src = (row.source || {}) as { organization?: string; dataset?: string };
  return Boolean(
    row.definition &&
      row.reference_period &&
      row.status_label &&
      src.organization &&
      src.dataset,
  );
}

export function gateObservations(rows: Observation[]): {
  items: Observation[];
  dropped: GateDrop[];
} {
  const items: Observation[] = [];
  const dropped: GateDrop[] = [];
  for (const row of rows) {
    if (!hasObservationProvenance(row)) {
      dropped.push({
        indicator: row.indicator,
        geography: row.geography_ibge_code,
        reason: "missing_provenance",
      });
      continue;
    }
    if (!Number.isFinite(row.value)) {
      dropped.push({
        indicator: row.indicator,
        geography: row.geography_ibge_code,
        reason: "non_finite_value",
      });
      continue;
    }
    if (row.unit === "%" && (row.value < 0 || row.value > 100)) {
      dropped.push({
        indicator: row.indicator,
        geography: row.geography_ibge_code,
        reason: "percent_out_of_range",
      });
      continue;
    }
    items.push(row);
  }
  if (
    items.length > 0 &&
    items.every((row) => String(row.geography_ibge_code || "").length === 2)
  ) {
    const codes = new Set(items.map((row) => row.geography_ibge_code));
    if (codes.size !== 27 || items.length !== 27) {
      dropped.push({
        indicator: items[0]?.indicator,
        geography: "*",
        reason: `uf_coverage:${items.length}!=27`,
      });
      return { items: [], dropped };
    }
  }
  return { items, dropped };
}
