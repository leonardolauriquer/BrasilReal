"use client";

import { useEffect, useMemo, useRef } from "react";
import { InfoTip, type ProvenanceFields } from "@/components/InfoTip";
import { comparePeriodKeys, formatPeriodLabel, formatSharePercent, formatValue } from "@/lib/format";
import { compareRankValue, isAdditiveUnit, type RegionRankRow } from "@/lib/map/regions";
import type { Observation } from "@/lib/api";

type Props = {
  rows: Observation[];
  regionRows?: RegionRankRow[];
  /** When true, show macrorregião ranking (zoom afastado). */
  regionMode?: boolean;
  selectedCode?: string | null;
  selectedRegionId?: string | null;
  layerLabel: string;
  period: string;
  periods?: string[];
  statusLabel?: string;
  higherIsWorse?: boolean;
  loading?: boolean;
  onSelect: (ibgeCode: string) => void;
  onSelectRegion?: (row: RegionRankRow) => void;
  legendLow: string;
  legendHigh: string;
  legendNote: string;
  legendWorse?: boolean;
  tip?: ProvenanceFields | null;
  recorteLabel?: string;
  rankMode?: "nivel" | "delta";
  comparePeriod?: string;
  compareCodes?: string[];
  onToggleCompare?: (ibgeCode: string) => void;
};

export function RankPanel({
  rows,
  regionRows = [],
  regionMode = false,
  selectedCode,
  selectedRegionId,
  layerLabel,
  period,
  periods = [],
  statusLabel,
  higherIsWorse = false,
  loading = false,
  onSelect,
  onSelectRegion,
  legendLow,
  legendHigh,
  legendNote,
  legendWorse = false,
  tip = null,
  recorteLabel,
  rankMode = "nivel",
  comparePeriod,
  compareCodes = [],
  onToggleCompare,
}: Props) {
  const listRef = useRef<HTMLDivElement>(null);

  const ranked = useMemo(() => {
    return [...rows].sort((a, b) => compareRankValue(a.value, b.value, higherIsWorse));
  }, [rows, higherIsWorse]);

  const rankedRegions = useMemo(() => {
    return [...regionRows].sort((a, b) => {
      if (a.value == null && b.value == null) return a.name.localeCompare(b.name, "pt-BR");
      if (a.value == null) return 1;
      if (b.value == null) return -1;
      return compareRankValue(a.value, b.value, higherIsWorse);
    });
  }, [regionRows, higherIsWorse]);

  const chrono = useMemo(
    () => [...new Set(periods.filter(Boolean))].sort(comparePeriodKeys),
    [periods],
  );
  const seriesNote =
    chrono.length > 1
      ? `série ${formatPeriodLabel(chrono[0])}–${formatPeriodLabel(chrono[chrono.length - 1])}`
      : "";

  const ufTotal = useMemo(
    () => ranked.reduce((sum, row) => sum + row.value, 0),
    [ranked],
  );
  const regionTotal = useMemo(
    () =>
      regionRows.reduce(
        (sum, row) => (row.aggregate === "sum" && row.value != null ? sum + row.value : sum),
        0,
      ),
    [regionRows],
  );

  const showUfShare = Boolean(
    !regionMode &&
      rankMode !== "delta" &&
      ranked.length &&
      isAdditiveUnit(ranked[0]?.unit) &&
      ufTotal > 0,
  );
  const showRegionShare = Boolean(
    regionMode &&
      rankMode !== "delta" &&
      regionRows.some((r) => r.aggregate === "sum") &&
      regionTotal > 0,
  );
  const regionWeighted = regionMode && regionRows.some((r) => r.aggregate === "pop_weighted");

  const valuePool = regionMode
    ? rankedRegions.map((r) => r.value).filter((v): v is number => v != null)
    : ranked.map((r) => r.value);
  const max = valuePool.length ? Math.max(...valuePool) : 0;
  const min = valuePool.length ? Math.min(...valuePool) : 0;
  const span = max - min || 1;
  const barShare = (value: number) => {
    const raw = higherIsWorse ? (max - value) / span : (value - min) / span;
    return Math.max(6, raw * 100);
  };

  const rankTip = useMemo<ProvenanceFields | null>(() => {
    if (!tip) return null;
    if (!regionMode) return tip;
    const additive = regionRows.some((r) => r.aggregate === "sum");
    const weighted = regionRows.some((r) => r.aggregate === "pop_weighted");
    return {
      ...tip,
      definition: [
        tip.definition,
        "Neste ranking, as 27 UFs entram nas 5 macrorregiões oficiais do IBGE (Norte, Nordeste, Centro-Oeste, Sudeste e Sul).",
        additive
          ? "O valor de cada região é a soma dos valores oficiais das UFs — não é um recálculo da fonte."
          : weighted
            ? "O valor de cada região é a média ponderada pela população (projeção IBGE mais recente) das UFs — DERIVADO, não publicação regional da fonte."
            : "Por ser densidade ou razão de área, não agregamos a região: só a cobertura de UFs com dado.",
      ]
        .filter(Boolean)
        .join(" "),
      limitations: [
        "Malha N/NE/CO/SE/S = classificação geográfica IBGE, não um indicador novo.",
        ...(additive
          ? ["% do ranking = participação no total das macrorregiões (somas aditivas)."]
          : []),
        ...(weighted
          ? ["Média ponderada pela população; não confundir com % do total do Brasil."]
          : []),
        ...(tip.limitations || []),
      ],
    };
  }, [tip, regionMode, regionRows]);

  useEffect(() => {
    if (!listRef.current) return;
    if (regionMode && selectedRegionId) {
      listRef.current
        .querySelector<HTMLElement>(`[data-region="${selectedRegionId}"]`)
        ?.scrollIntoView({ block: "nearest", behavior: "smooth" });
      return;
    }
    if (!selectedCode) return;
    listRef.current
      .querySelector<HTMLElement>(`[data-code="${selectedCode}"]`)
      ?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selectedCode, selectedRegionId, ranked, regionMode, regionRows]);

  return (
    <aside className="rank-rail" aria-label={regionMode ? "Ranking por região" : "Ranking por UF"}>
      <div className="rank-head">
        <div>
          <p className="rank-kicker">
            {regionMode
              ? "Ranking · macrorregiões"
              : recorteLabel && recorteLabel !== "Brasil (27 UFs)"
                ? `Ranking · ${ranked.length} UFs · ${recorteLabel}`
                : "Ranking · UFs"}
          </p>
          <h2 className="rank-title">
            {layerLabel}
            {rankTip ? (
              <InfoTip data={rankTip} label="O que é este ranking e de onde veio" />
            ) : null}
          </h2>
          <p className="rank-meta">
            {rankMode === "delta" && comparePeriod
              ? `${formatPeriodLabel(period || "—")} vs ${formatPeriodLabel(comparePeriod)}`
              : formatPeriodLabel(period || "—")}
            {rankMode === "delta" ? " · variação" : ""}
            {statusLabel ? ` · ${statusLabel}` : ""}
            {seriesNote ? ` · ${seriesNote}` : ""}
            {regionMode ? " · IBGE N/NE/CO/SE/S" : ""}
            {showUfShare || showRegionShare ? " · % do recorte" : ""}
            {regionWeighted ? " · média ponderada pop." : ""}
          </p>
        </div>
        <p className="rank-order">
          {regionMode
            ? "aproxime o zoom para UFs"
            : higherIsWorse
              ? "melhor no topo · menor valor"
              : "melhor no topo · maior valor"}
          {onToggleCompare ? " · pin compara até 3" : ""}
        </p>
      </div>

      <div className="rank-list" ref={listRef} role="list">
        {regionMode ? (
          loading && !regionRows.length ? (
            <p className="rank-empty">Atualizando camada…</p>
          ) : !regionRows.length ? (
            <p className="rank-empty">SEM DADO para este filtro</p>
          ) : (
            rankedRegions.map((row, idx) => {
              const active = row.id === selectedRegionId;
              const share =
                showRegionShare && row.value != null
                  ? formatSharePercent(row.value, regionTotal)
                  : null;
              return (
                <button
                  key={row.id}
                  type="button"
                  role="listitem"
                  data-region={row.id}
                  className={`rank-row ${active ? "is-active" : ""}`}
                  onClick={() => onSelectRegion?.(row)}
                >
                  <span className="rank-pos">{idx + 1}</span>
                  <span className="rank-place">
                    <strong>{row.id}</strong>
                    <em>{row.name}</em>
                  </span>
                  <span className="rank-value">
                    <strong>
                      {row.value != null && row.unit
                        ? formatValue({ value: row.value, unit: row.unit })
                        : `${row.with_data}/${row.uf_count} UFs`}
                    </strong>
                    {share ? <em>{share}</em> : regionWeighted && row.with_data ? <em>{row.with_data}/{row.uf_count} UFs</em> : null}
                  </span>
                  <span className="rank-bar" aria-hidden="true">
                    <span
                      style={{
                        width: `${row.value != null ? barShare(row.value) : 8}%`,
                      }}
                    />
                  </span>
                </button>
              );
            })
          )
        ) : loading && !ranked.length ? (
          <p className="rank-empty">Atualizando camada…</p>
        ) : !ranked.length ? (
          <p className="rank-empty">SEM DADO para este filtro</p>
        ) : (
          ranked.map((row, idx) => {
            const active = row.geography_ibge_code === selectedCode;
            const compared = compareCodes.includes(row.geography_ibge_code);
            const share = showUfShare ? formatSharePercent(row.value, ufTotal) : null;
            return (
              <div
                key={row.geography_ibge_code}
                className={`rank-row-wrap ${active ? "is-active" : ""} ${compared ? "is-compared" : ""}`}
              >
                <button
                  type="button"
                  role="listitem"
                  data-code={row.geography_ibge_code}
                  className={`rank-row ${active ? "is-active" : ""}`}
                  onClick={() => onSelect(row.geography_ibge_code)}
                >
                  <span className="rank-pos">{idx + 1}</span>
                  <span className="rank-place">
                    <strong>{row.uf}</strong>
                    <em>{row.name}</em>
                  </span>
                  <span className="rank-value">
                    <strong>{formatValue({ value: row.value, unit: row.unit })}</strong>
                    {share ? <em>{share}</em> : null}
                  </span>
                  <span className="rank-bar" aria-hidden="true">
                    <span style={{ width: `${barShare(row.value)}%` }} />
                  </span>
                </button>
                {onToggleCompare ? (
                  <button
                    type="button"
                    className={`rank-pin ${compared ? "is-on" : ""}`}
                    aria-pressed={compared}
                    aria-label={compared ? `Tirar ${row.uf} da comparação` : `Comparar ${row.uf}`}
                    onClick={() => onToggleCompare(row.geography_ibge_code)}
                  >
                    {compared ? "●" : "○"}
                  </button>
                ) : null}
              </div>
            );
          })
        )}
      </div>

      <div className="rank-legend">
        <div className={`legend-bar ${legendWorse ? "worse" : "observed"}`} />
        <div className="legend-scale">
          <span>{legendLow}</span>
          <span>{legendHigh}</span>
        </div>
        <p className="rank-legend-note">
          {regionWeighted
            ? `${legendNote} · valor = média ponderada pela população (DERIVADO)`
            : showUfShare
              ? `${legendNote} · % = participação no total das UFs listadas`
              : showRegionShare
                ? `${legendNote} · % = participação no total das macrorregiões (somas aditivas)`
                : legendNote}
        </p>
      </div>
    </aside>
  );
}
