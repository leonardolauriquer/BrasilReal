"use client";

import { GroupedSelect } from "@/components/GroupedSelect";
import { InfoTip, type ProvenanceFields } from "@/components/InfoTip";
import { comparePeriodKeys, formatPeriodLabel } from "@/lib/format";
import { RANKING_PRESET_TIP, RECORTE_TIP, VARIATION_TIP } from "@/lib/legend";
import { RECORTE_OPTIONS, type RecorteId } from "@/lib/map/regions";

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
  return (
    <>
      {onToggleSheet ? (
        <button
          type="button"
          className="chrome-peek"
          onClick={onToggleSheet}
          aria-expanded={sheet}
        >
          {peekLabel || "Filtros"}
        </button>
      ) : null}
      <div className={`map-controls ${sheet ? "is-sheet" : ""}`}>
      {onToggleSheet ? (
        <div className="control-hint control-hint--sheet">
          <button type="button" className="fit-brazil" onClick={onToggleSheet}>
            Fechar
          </button>
        </div>
      ) : null}
      {rankingGroups.length ? (
        <div className="control-block control-block--leitura">
          <span>
            Leitura <InfoTip data={RANKING_PRESET_TIP} label="O que é esta leitura" />
          </span>
          <GroupedSelect
            aria-label="Leitura — camada oficial ou lente declarada"
            value={layer}
            onChange={onChangeLayer}
            placeholder="Lente ou métrica"
            groups={rankingGroups}
          />
        </div>
      ) : null}
      {yearOptions.length > 1 ? (
        <div className="control-block control-block--timeline">
          <span>Série oficial</span>
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
          Camada {layerTip ? <InfoTip data={layerTip} label="Sobre a camada" /> : null}
        </span>
        <GroupedSelect
          aria-label="Camada do mapa"
          value={layer}
          onChange={onChangeLayer}
          groups={indicatorGroups}
        />
      </div>
      <div className="control-block">
        <span>
          Recorte <InfoTip data={RECORTE_TIP} label="O que é o recorte" />
        </span>
        <GroupedSelect
          aria-label="Recorte do ranking"
          value={recorte}
          onChange={(v) => onChangeRecorte(v as RecorteId)}
          options={RECORTE_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
        />
      </div>
      <div className="control-block">
        <span>
          Ranking <InfoTip data={VARIATION_TIP} label="Nível ou variação" />
        </span>
        <div className="rank-mode" role="group" aria-label="Nível ou variação">
          <button
            type="button"
            className={rankMode === "nivel" ? "is-on" : ""}
            onClick={() => onChangeRankMode("nivel")}
          >
            Nível
          </button>
          <button
            type="button"
            className={rankMode === "delta" ? "is-on" : ""}
            disabled={!canDelta}
            onClick={() => canDelta && onChangeRankMode("delta")}
          >
            Variação
          </button>
        </div>
      </div>
      {onChangeColorMode ? (
        <div className="control-block">
          <span>Cores</span>
          <div className="rank-mode" role="group" aria-label="Escala de cores do mapa">
            <button
              type="button"
              className={colorMode === "default" ? "is-on" : ""}
              onClick={() => onChangeColorMode("default")}
            >
              Padrão
            </button>
            <button
              type="button"
              className={colorMode === "cb" ? "is-on" : ""}
              onClick={() => onChangeColorMode("cb")}
            >
              Daltônico
            </button>
          </div>
        </div>
      ) : null}
      <div className="control-block">
        <span>
          Ano / período {yearTip ? <InfoTip data={yearTip} label="Sobre o período" /> : null}
        </span>
        <GroupedSelect
          aria-label="Ano ou período"
          value={year}
          disabled={!yearOptions.length}
          placeholder={yearOptions.length ? "Período" : "…"}
          onChange={onChangeYear}
          options={yearOptions.map((p) => ({
            value: p,
            label: formatPeriodLabel(p),
          }))}
        />
      </div>
      <div className="control-hint">
        <button type="button" className="fit-brazil" onClick={onFitBrazil}>
          Brasil inteiro
        </button>
        <button type="button" className="dossier-open" onClick={onOpenDossier}>
          Dossiê
        </button>
        {onOpenSearch ? (
          <button type="button" className="dossier-open" onClick={onOpenSearch}>
            Busca
          </button>
        ) : null}
        {onCopyLink ? (
          <button type="button" className="dossier-open" onClick={onCopyLink}>
            Copiar vista
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
            Simulado
          </button>
        ) : null}
        {showInstallApp && onInstallApp ? (
          <button type="button" className="pwa-open" onClick={onInstallApp}>
            Instalar app
          </button>
        ) : null}
        <span>
          {controlHint}
          {loading ? " · atualizando camada…" : ""}
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
  const chrono = [...new Set(periods)].sort(comparePeriodKeys);
  const idx = Math.max(0, chrono.indexOf(value));
  const atStart = idx <= 0;
  const atEnd = idx >= chrono.length - 1;
  return (
    <div className="period-scrub">
      <button
        type="button"
        className="period-scrub-step"
        aria-label="Período anterior"
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
        aria-label="Percorrer períodos da série oficial"
        onChange={(e) => onChange(chrono[Number(e.target.value)])}
      />
      <button
        type="button"
        className="period-scrub-step"
        aria-label="Período seguinte"
        disabled={disabled || atEnd}
        onClick={() => onChange(chrono[idx + 1])}
      >
        ›
      </button>
      <span className="period-scrub-meta">
        {formatPeriodLabel(chrono[0])} – {formatPeriodLabel(chrono[chrono.length - 1])} ·{" "}
        {chrono.length} períodos
      </span>
    </div>
  );
}
