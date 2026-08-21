"use client";

import { useEffect, useMemo, useRef } from "react";
import { InfoTip, type ProvenanceFields } from "@/components/InfoTip";
import { comparePeriodKeys, formatPeriodLabel, formatSharePercent, formatValue, medianNumbers } from "@/lib/format";
import { compareRankValue, isAdditiveUnit, type RegionRankRow } from "@/lib/map/regions";
import type { Observation } from "@/lib/api";
import { useI18n } from "@/lib/i18n/I18nProvider";

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
  const { t } = useI18n();
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
  const median = medianNumbers(valuePool);
  const barShare = (value: number) => {
    const raw = higherIsWorse ? (max - value) / span : (value - min) / span;
    return Math.max(6, raw * 100);
  };
  const medianMark = median != null ? barShare(median) : null;
  const medianUnit = regionMode
    ? rankedRegions.find((r) => r.unit)?.unit
    : ranked[0]?.unit;
  const medianLabel =
    median != null && medianUnit
      ? formatValue({ value: median, unit: medianUnit })
      : median != null
        ? median.toLocaleString("pt-BR")
        : null;

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
    <aside className="rank-rail" aria-label={regionMode ? t("rank.ariaRegions") : t("rank.ariaUfs")}>
      <div className="rank-head">
        <div>
          <p className="rank-kicker">
            {regionMode
              ? t("rank.regions")
              : recorteLabel && recorteLabel !== t("recorte.BR")
                ? t("rank.ufsRecorte", { n: ranked.length, recorte: recorteLabel })
                : t("rank.ufs")}
          </p>
          <h2 className="rank-title">
            {layerLabel}
            {rankTip ? (
              <InfoTip data={rankTip} label={t("rank.tip")} />
            ) : null}
          </h2>
          <p className="rank-meta">
            {rankMode === "delta" && comparePeriod
              ? `${formatPeriodLabel(period || "—")} vs ${formatPeriodLabel(comparePeriod)}`
              : formatPeriodLabel(period || "—")}
            {rankMode === "delta" ? ` · ${t("rank.variation")}` : ""}
            {statusLabel ? ` · ${statusLabel}` : ""}
            {seriesNote ? ` · ${seriesNote}` : ""}
            {regionMode ? ` · ${t("rank.ibgeMacro")}` : ""}
            {showUfShare || showRegionShare ? ` · ${t("rank.shareRecorte")}` : ""}
            {regionWeighted ? ` · ${t("rank.weightedPop")}` : ""}
            {medianLabel ? ` · ${t("rank.median", { value: medianLabel })}` : ""}
          </p>
        </div>
        <p className="rank-order">
          {regionMode
            ? t("rank.zoomForUf")
            : higherIsWorse
              ? t("rank.betterLow")
              : t("rank.betterHigh")}
          {onToggleCompare ? t("rank.pinHint") : ""}
        </p>
      </div>

      <div className="rank-list" ref={listRef} role="list">
        {regionMode ? (
          loading && !regionRows.length ? (
            <p className="rank-empty">{t("rank.updating")}</p>
          ) : !regionRows.length ? (
            <p className="rank-empty">{t("rank.empty")}</p>
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
                    {medianMark != null ? (
                      <i className="rank-median" style={{ left: `${medianMark}%` }} />
                    ) : null}
                  </span>
                </button>
              );
            })
          )
        ) : loading && !ranked.length ? (
          <p className="rank-empty">{t("rank.updating")}</p>
        ) : !ranked.length ? (
          <p className="rank-empty">{t("rank.empty")}</p>
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
                    {medianMark != null ? (
                      <i className="rank-median" style={{ left: `${medianMark}%` }} />
                    ) : null}
                  </span>
                </button>
                {onToggleCompare ? (
                  <button
                    type="button"
                    className={`rank-pin ${compared ? "is-on" : ""}`}
                    aria-pressed={compared}
                    aria-label={compared ? t("rank.pinOn", { uf: row.uf }) : t("rank.pinOff", { uf: row.uf })}
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
        <div
          className={`legend-bar ${legendWorse ? "worse" : "observed"}`}
        />
        <div className="legend-scale">
          <span>{legendLow}</span>
          <span>{legendHigh}</span>
        </div>
        <p className="rank-legend-note">
          {regionWeighted
            ? t("rank.legendWeighted", { note: legendNote })
            : showUfShare
              ? t("rank.legendUfShare", { note: legendNote })
              : showRegionShare
                ? t("rank.legendRegionShare", { note: legendNote })
                : legendNote}
          {medianLabel
            ? t("rank.legendMedian", {
                who: regionMode ? t("rank.whoRegions") : t("rank.whoUfs"),
                value: medianLabel,
              })
            : ""}
        </p>
      </div>
    </aside>
  );
}
