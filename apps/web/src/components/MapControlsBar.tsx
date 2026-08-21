"use client";

import { GroupedSelect } from "@/components/GroupedSelect";
import { InfoTip, type ProvenanceFields } from "@/components/InfoTip";
import { comparePeriodKeys, formatPeriodLabel } from "@/lib/format";
import { RANKING_PRESET_TIP, RECORTE_TIP, VARIATION_TIP } from "@/lib/legend";
import { RECORTE_OPTIONS, type RecorteId } from "@/lib/map/regions";
import { useI18n } from "@/lib/i18n/I18nProvider";

type Group = {
  key: string;
  label: string;
  items: Array<{ value: string; label: string }>;
};

type Props = {
  layer: string;
  year: string;
  yearOptions: string[];
  indicatorGroups: Group[];
  rankingGroups: Group[];
  layerTip: ProvenanceFields | null;
  yearTip: ProvenanceFields | null;
  controlHint: string;
  loading: boolean;
  onChangeLayer: (id: string) => void;
  onChangeYear: (year: string) => void;
  onFitBrazil: () => void;
  onOpenDossier: () => void;
  showInstallApp?: boolean;
  onInstallApp?: () => void;
  recorte: RecorteId;
  onChangeRecorte: (id: RecorteId) => void;
  rankMode: "nivel" | "delta";
  onChangeRankMode: (mode: "nivel" | "delta") => void;
  canDelta: boolean;
  sheet?: boolean;
  peekLabel?: string;
  onToggleSheet?: () => void;
  onOpenSearch?: () => void;
  onExportPng?: () => void;
  onCopyLink?: () => void;
  simulado?: boolean;
  onToggleSimulado?: () => void;
  colorMode?: "default" | "cb";
  onChangeColorMode?: (mode: "default" | "cb") => void;
};

export function MapControlsBar({
  layer,
  year,
  yearOptions,
  indicatorGroups,
  rankingGroups,
  layerTip,
  yearTip,
  controlHint,
  loading,
  onChangeLayer,
  onChangeYear,
  onFitBrazil,
  onOpenDossier,
  showInstallApp = false,
  onInstallApp,
  recorte,
  onChangeRecorte,
  rankMode,
  onChangeRankMode,
  canDelta,
  sheet = false,
  peekLabel,
  onToggleSheet,
  onOpenSearch,
  onExportPng,
  onCopyLink,
  simulado = false,
  onToggleSimulado,
  colorMode = "default",
  onChangeColorMode,
}: Props) {
  const { t } = useI18n();
  return (
    <>
      {onToggleSheet ? (
        <button
          type="button"
          className="chrome-peek"
          onClick={onToggleSheet}
          aria-expanded={sheet}
        >
          {peekLabel || t("ui.filters")}
        </button>
      ) : null}
      <div className={`map-controls ${sheet ? "is-sheet" : ""}`}>
      {onToggleSheet ? (
        <div className="control-hint control-hint--sheet">
          <button type="button" className="fit-brazil" onClick={onToggleSheet}>
            {t("ui.close")}
          </button>
        </div>
      ) : null}
      {rankingGroups.length ? (
        <div className="control-block control-block--leitura">
          <span>
            {t("ui.reading")} <InfoTip data={RANKING_PRESET_TIP} label={t("ui.readingTip")} />
          </span>
          <GroupedSelect
            aria-label={t("ui.readingAria")}
            value={layer}
            onChange={onChangeLayer}
            placeholder={t("ui.readingPlaceholder")}
            groups={rankingGroups}
          />
        </div>
      ) : null}
      {yearOptions.length > 1 ? (
        <div className="control-block control-block--timeline">
          <span>{t("ui.officialSeries")}</span>
          <PeriodScrubber
            periods={yearOptions}
            value={year}
            disabled={loading || yearOptions.length < 2}
            onChange={onChangeYear}
          />
        </div>
      ) : null}
      <div className="control-block">
        <span>
          {t("ui.layer")} {layerTip ? <InfoTip data={layerTip} label={t("ui.layerTip")} /> : null}
        </span>
        <GroupedSelect
          aria-label={t("ui.layerAria")}
          value={layer}
          onChange={onChangeLayer}
          groups={indicatorGroups}
        />
      </div>
      <div className="control-block">
        <span>
          {t("ui.recorte")} <InfoTip data={RECORTE_TIP} label={t("ui.recorteTip")} />
        </span>
        <GroupedSelect
          aria-label={t("ui.recorteAria")}
          value={recorte}
          onChange={(v) => onChangeRecorte(v as RecorteId)}
          options={RECORTE_OPTIONS.map((o) => {
            const key = `recorte.${o.value}`;
            const translated = t(key);
            return { value: o.value, label: translated === key ? o.label : translated };
          })}
        />
      </div>
      <div className="control-block">
        <span>
          {t("ui.ranking")} <InfoTip data={VARIATION_TIP} label={t("ui.rankTip")} />
        </span>
        <div className="rank-mode" role="group" aria-label={t("ui.rankTip")}>
          <button
            type="button"
            className={rankMode === "nivel" ? "is-on" : ""}
            onClick={() => onChangeRankMode("nivel")}
          >
            {t("ui.level")}
          </button>
          <button
            type="button"
            className={rankMode === "delta" ? "is-on" : ""}
            disabled={!canDelta}
            onClick={() => canDelta && onChangeRankMode("delta")}
          >
            {t("ui.variation")}
          </button>
        </div>
      </div>
      {onChangeColorMode ? (
        <div className="control-block">
          <span>{t("ui.colors")}</span>
          <div className="rank-mode" role="group" aria-label={t("ui.colorsAria")}>
            <button
              type="button"
              className={colorMode === "default" ? "is-on" : ""}
              onClick={() => onChangeColorMode("default")}
            >
              {t("ui.colorDefault")}
            </button>
            <button
              type="button"
              className={colorMode === "cb" ? "is-on" : ""}
              onClick={() => onChangeColorMode("cb")}
            >
              {t("ui.colorCb")}
            </button>
          </div>
        </div>
      ) : null}
      <div className="control-block">
        <span>
          {t("ui.year")} {yearTip ? <InfoTip data={yearTip} label={t("ui.yearTip")} /> : null}
        </span>
        <GroupedSelect
          aria-label={t("ui.yearAria")}
          value={year}
          disabled={!yearOptions.length}
          placeholder={yearOptions.length ? t("ui.period") : "…"}
          onChange={onChangeYear}
          options={yearOptions.map((p) => ({
            value: p,
            label: formatPeriodLabel(p),
          }))}
        />
      </div>
      <div className="control-hint">
        <button type="button" className="fit-brazil" onClick={onFitBrazil}>
          {t("ui.fitBrazil")}
        </button>
        <button type="button" className="dossier-open" onClick={onOpenDossier}>
          {t("ui.dossier")}
        </button>
        {onOpenSearch ? (
          <button type="button" className="dossier-open" onClick={onOpenSearch}>
            {t("ui.search")}
          </button>
        ) : null}
        {onCopyLink ? (
          <button type="button" className="dossier-open" onClick={onCopyLink}>
            {t("ui.copyView")}
          </button>
        ) : null}
        {onExportPng ? (
          <button type="button" className="dossier-open" onClick={onExportPng}>
            PNG
          </button>
        ) : null}
        {onToggleSimulado ? (
          <button
            type="button"
            className={`dossier-open ${simulado ? "is-sim" : ""}`}
            onClick={onToggleSimulado}
          >
            {t("ui.simulado")}
          </button>
        ) : null}
        {showInstallApp && onInstallApp ? (
          <button type="button" className="pwa-open" onClick={onInstallApp}>
            {t("ui.installApp")}
          </button>
        ) : null}
        <span>
          {controlHint}
          {loading ? t("ui.updatingLayer") : ""}
        </span>
      </div>
    </div>
    </>
  );
}

function PeriodScrubber({
  periods,
  value,
  onChange,
  disabled,
}: {
  periods: string[];
  value: string;
  onChange: (year: string) => void;
  disabled?: boolean;
}) {
  const { t } = useI18n();
  const chrono = [...new Set(periods)].sort(comparePeriodKeys);
  const idx = Math.max(0, chrono.indexOf(value));
  const atStart = idx <= 0;
  const atEnd = idx >= chrono.length - 1;
  return (
    <div className="period-scrub">
      <button
        type="button"
        className="period-scrub-step"
        aria-label={t("ui.prevPeriod")}
        disabled={disabled || atStart}
        onClick={() => onChange(chrono[idx - 1])}
      >
        ‹
      </button>
      <input
        type="range"
        className="period-scrub-range"
        min={0}
        max={Math.max(0, chrono.length - 1)}
        step={1}
        value={idx}
        disabled={disabled}
        aria-label={t("ui.scrubAria")}
        onChange={(e) => onChange(chrono[Number(e.target.value)])}
      />
      <button
        type="button"
        className="period-scrub-step"
        aria-label={t("ui.nextPeriod")}
        disabled={disabled || atEnd}
        onClick={() => onChange(chrono[idx + 1])}
      >
        ›
      </button>
      <span className="period-scrub-meta">
        {formatPeriodLabel(chrono[0])} – {formatPeriodLabel(chrono[chrono.length - 1])} ·{" "}
        {t("ui.periodsCount", { n: chrono.length })}
      </span>
    </div>
  );
}
