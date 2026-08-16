"use client";

import { formatPeriodLabel, formatValue } from "@/lib/format";
import type { Observation } from "@/lib/api";

type Props = {
  rows: Observation[];
  onSelect: (code: string) => void;
  onRemove: (code: string) => void;
};

export function CompareTray({ rows, onSelect, onRemove }: Props) {
  if (rows.length < 2) return null;
  const unit = rows[0]?.unit;
  const same = rows.every((r) => r.indicator === rows[0].indicator && r.reference_period === rows[0].reference_period);
  return (
    <aside className="compare-tray" aria-label="Comparação de UFs">
      <p className="compare-kicker">
        Comparar · mesma camada · {formatPeriodLabel(rows[0].reference_period)} · {rows[0].status_label}
      </p>
      {!same ? (
        <p className="compare-warn">Períodos ou camadas misturados — recarregue a vista.</p>
      ) : null}
      <div className="compare-cols">
        {rows.map((row) => (
          <div key={row.geography_ibge_code} className="compare-col">
            <button type="button" className="compare-open" onClick={() => onSelect(row.geography_ibge_code)}>
              <strong>{row.uf}</strong>
              <em>{row.name}</em>
              <span>{formatValue({ value: row.value, unit: unit || row.unit })}</span>
            </button>
            <button
              type="button"
              className="compare-x"
              aria-label={`Tirar ${row.uf} da comparação`}
              onClick={() => onRemove(row.geography_ibge_code)}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
