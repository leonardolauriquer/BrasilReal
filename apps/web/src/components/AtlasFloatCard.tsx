"use client";

import { InfoTip, hasProvenance, type ProvenanceFields } from "@/components/InfoTip";
import { OfficialSparkline } from "@/components/OfficialSparkline";
import { TerritorySections } from "@/components/TerritorySections";
import { formatPeriodLabel, formatValue } from "@/lib/format";
import type { RegionFiche } from "@/lib/map/regions";
import type { Indicator, Observation, Profile } from "@/lib/api";
import type { MuniSelection } from "@/lib/atlas/useAtlasState";

type Props = {
  layer: string;
  onChangeLayer: (id: string) => void;
  onClose: () => void;
  onSelectUf: (code: string) => void;
  regionFiche: RegionFiche | null;
  muniSelected: MuniSelection | null;
  selectedObs: Observation | null;
  profile: Profile | null;
  muniProfile: Profile | null;
  activeIndicator: Indicator | null;
  muniPopTip: ProvenanceFields | null;
  selectedObsTip: ProvenanceFields | null;
  series?: Observation[];
  onPickPeriod?: (period: string) => void;
};

function profileMetricTip(m: Observation): ProvenanceFields {
  return {
    definition: m.definition,
    source: m.source as ProvenanceFields["source"],
    reference_period: m.reference_period,
    status_label: m.status_label,
    limitations: m.limitations,
  };
}

export function AtlasFloatCard({
  layer,
  onChangeLayer,
  onClose,
  onSelectUf,
  regionFiche,
  muniSelected,
  selectedObs,
  profile,
  muniProfile,
  activeIndicator,
  muniPopTip,
  selectedObsTip,
  series = [],
  onPickPeriod,
}: Props) {
  if (!selectedObs && !muniSelected && !regionFiche) return null;

  const kicker = muniSelected
    ? "Município"
    : regionFiche?.level === "macro"
      ? "Macrorregião IBGE"
      : regionFiche?.level === "intermediate"
        ? "Região intermediária IBGE"
        : "Unidade da Federação";

  const title =
    muniSelected?.name ||
    regionFiche?.name ||
    profile?.geography.name ||
    selectedObs?.name ||
    "Seleção";

  const meta = muniSelected
    ? `IBGE ${muniSelected.ibge_code} · UF ${muniSelected.uf_code}`
    : regionFiche?.level === "macro"
      ? `${regionFiche.id} · ${regionFiche.with_data}/${regionFiche.total_parts} UFs com dado`
      : regionFiche?.level === "intermediate"
        ? `IBGE ${regionFiche.id}${regionFiche.uf ? ` · UF ${regionFiche.uf}` : ""}`
        : selectedObs
          ? `${selectedObs.uf} · IBGE ${selectedObs.geography_ibge_code}`
          : "";

  return (
    <aside className="float-card" aria-live="polite">
      <div className="float-card-head">
        <div>
          <p className="kicker">{kicker}</p>
          <h2>{title}</h2>
          <p className="uf-meta">{meta}</p>
        </div>
        <button type="button" className="close-card" onClick={onClose} aria-label="Fechar">
          ×
        </button>
      </div>

      {regionFiche ? (
        <div className="stat-block">
          <div className="stat-value">
            {regionFiche.value != null && regionFiche.unit
              ? formatValue({ value: regionFiche.value, unit: regionFiche.unit })
              : "SEM AGREGADO"}
          </div>
          <div className="stat-unit">
            {regionFiche.layerLabel} · {formatPeriodLabel(regionFiche.period || "—")}
          </div>
          <span className="status-mark observed">{regionFiche.status_label}</span>
          <p className="region-method">{regionFiche.method}</p>
          {regionFiche.definition ? <p className="region-def">{regionFiche.definition}</p> : null}
          {regionFiche.source_org ? (
            <p className="region-source">Fonte das UFs: {regionFiche.source_org}</p>
          ) : null}
          <p className="region-disclaimer">{regionFiche.disclaimer}</p>
          {regionFiche.level === "intermediate" && regionFiche.uf_code ? (
            <button
              type="button"
              className="region-open-uf"
              onClick={() => onSelectUf(regionFiche.uf_code!)}
            >
              Abrir ficha da UF {regionFiche.uf || regionFiche.uf_code}
            </button>
          ) : null}
        </div>
      ) : muniSelected ? (
        hasProvenance(muniPopTip) ? (
          <div className="stat-block">
            <div className="stat-value">
              {muniSelected.value == null
                ? "SEM DADO"
                : formatValue({ value: muniSelected.value, unit: "habitantes" })}{" "}
              <InfoTip data={muniPopTip!} />
            </div>
            <div className="stat-unit">população estimada · município</div>
            <span className="status-mark observed">ESTIMADO</span>
          </div>
        ) : null
      ) : (
        selectedObs &&
        hasProvenance(selectedObsTip) && (
          <div className="stat-block">
            <div className="stat-value">
              {formatValue(selectedObs)} <InfoTip data={selectedObsTip!} />
            </div>
            <div className="stat-unit">
              {activeIndicator?.short_name || selectedObs.indicator} ·{" "}
              {formatPeriodLabel(selectedObs.reference_period)}
            </div>
            <span className={`status-mark ${selectedObs.status_label === "SIMULADO" ? "simulado" : "observed"}`}>
              {selectedObs.status_label}
            </span>
          </div>
        )
      )}

      {!regionFiche && !muniSelected && series.length > 1 && selectedObs ? (
        <OfficialSparkline
          rows={series}
          currentPeriod={selectedObs.reference_period}
          onPickPeriod={onPickPeriod}
        />
      ) : null}

      {!regionFiche && muniSelected && muniProfile?.territory?.items && (
        <TerritorySections items={muniProfile.territory.items} />
      )}

      {!regionFiche && !muniSelected && profile?.territory?.items && (
        <TerritorySections items={profile.territory.items} />
      )}

      {!regionFiche && !muniSelected && profile && (
        <div className="fiche-section">
          <h3 className="section-title">Indicadores</h3>
          <div className="metric-list">
            {profile.metrics
              .filter((m) => hasProvenance(profileMetricTip(m)))
              .map((m) => (
                <div
                  key={m.indicator}
                  className={`metric-row ${layer === m.indicator ? "active" : ""}`}
                >
                  <button
                    type="button"
                    className="metric-row-main"
                    onClick={() => onChangeLayer(m.indicator)}
                  >
                    <span>
                      <strong>{m.short_name || m.indicator}</strong>
                      <em>
                        {formatPeriodLabel(m.reference_period)} · {m.status_label}
                      </em>
                    </span>
                    <strong>{formatValue(m)}</strong>
                  </button>
                  <InfoTip data={profileMetricTip(m)} />
                </div>
              ))}
          </div>
        </div>
      )}

      <p className="note">
        {profile?.disclaimer ||
          muniProfile?.disclaimer ||
          "Cada valor exige fonte e definição oficiais no “?”."}
      </p>
    </aside>
  );
}
