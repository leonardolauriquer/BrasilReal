"use client";

import { formatPeriodLabel, formatValue } from "@/lib/format";
import type { Observation } from "@/lib/api";
import { useI18n } from "@/lib/i18n/I18nProvider";

type Props = {
  rows: Observation[];
  onSelect: (code: string) => void;
  onRemove: (code: string) => void;
};

export function CompareTray({ rows, onSelect, onRemove }: Props) {
  const { t } = useI18n();
  if (rows.length < 2) return null;
  const unit = rows[0]?.unit;
  const same = rows.every((r) => r.indicator === rows[0].indicator && r.reference_period === rows[0].reference_period);
  return (
    <aside className="compare-tray" aria-label={t("compare.aria")}>
      <p className="compare-kicker">
        {t("compare.kicker", {
          period: formatPeriodLabel(rows[0].reference_period),
          status: rows[0].status_label,
        })}
      </p>
      {!same ? (
        <p className="compare-warn">{t("compare.mixed")}</p>
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
              aria-label={t("compare.remove", { uf: row.uf })}
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
