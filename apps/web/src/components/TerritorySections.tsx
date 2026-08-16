"use client";

import { InfoTip, hasProvenance } from "@/components/InfoTip";
import { formatPeriodLabel, formatValue } from "@/lib/format";
import type { TerritoryItem } from "@/lib/api";

function formatTerritoryValue(item: TerritoryItem) {
  if (item.text) return item.text;
  if (item.value == null) return "SEM DADO";
  return formatValue({ value: item.value, unit: item.unit });
}

export function TerritorySections({ items }: { items: TerritoryItem[] }) {
  const povos = items.filter((i) => i.section === "povos" && hasProvenance(i));
  const territorio = items.filter((i) => i.section === "territorio" && hasProvenance(i));
  const blocks = [
    { title: "Povos", rows: povos },
    { title: "Território", rows: territorio },
  ].filter((b) => b.rows.length);

  if (!blocks.length) return null;

  return (
    <>
      {blocks.map((block) => (
        <div key={block.title} className="fiche-section">
          <h3 className="section-title">{block.title}</h3>
          <div className="metric-list">
            {block.rows.map((item) => (
              <div key={item.id} className="metric-row static">
                <div className="metric-row-main">
                  <span>
                    <strong>{item.label}</strong>
                    <em>
                      {formatPeriodLabel(item.reference_period)} · {item.status_label}
                    </em>
                  </span>
                  <strong>{formatTerritoryValue(item)}</strong>
                </div>
                <InfoTip data={item} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </>
  );
}
