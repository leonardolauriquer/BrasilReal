"use client";

import { comparePeriodKeys, formatPeriodLabel, formatValue } from "@/lib/format";
import type { Observation } from "@/lib/api";

type Props = {
  rows: Observation[];
  currentPeriod: string;
  onPickPeriod?: (period: string) => void;
};

export function OfficialSparkline({ rows, currentPeriod, onPickPeriod }: Props) {
  const series = [...rows].sort((a, b) => comparePeriodKeys(a.reference_period, b.reference_period));
  if (series.length < 2) return null;

  const values = series.map((r) => r.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const w = 220;
  const h = 52;
  const pad = 4;
  const pts = series.map((row, i) => {
    const x = pad + (i / (series.length - 1)) * (w - pad * 2);
    const y = h - pad - ((row.value - min) / span) * (h - pad * 2);
    return { x, y, row };
  });
  const d = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
  const src = series[0]?.source as { organization?: string } | undefined;
  const last = series[series.length - 1];

  return (
    <div className="spark">
      <p className="spark-kicker">Série oficial desta UF</p>
      <svg viewBox={`0 0 ${w} ${h}`} className="spark-svg" role="img" aria-label="Série oficial">
        <path d={d} fill="none" stroke="currentColor" strokeWidth="1.6" />
        {pts.map((p) => (
          <circle
            key={p.row.reference_period}
            cx={p.x}
            cy={p.y}
            r={p.row.reference_period === currentPeriod ? 3.2 : 2}
            className={p.row.reference_period === currentPeriod ? "is-now" : ""}
          />
        ))}
      </svg>
      <div className="spark-years">
        {series.map((row) => (
          <button
            key={row.reference_period}
            type="button"
            className={row.reference_period === currentPeriod ? "is-on" : ""}
            onClick={() => onPickPeriod?.(row.reference_period)}
          >
            {formatPeriodLabel(row.reference_period)}
          </button>
        ))}
      </div>
      <p className="spark-meta">
        {formatValue(series[0])} → {formatValue(last)} · {src?.organization || "fonte oficial"} ·{" "}
        {series[0].status_label}
      </p>
    </div>
  );
}
