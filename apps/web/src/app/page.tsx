"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import { InfoTip, hasProvenance } from "@/components/InfoTip";
import {
  Indicator,
  Observation,
  Profile,
  TerritoryItem,
  fetchIndicators,
  fetchMunicipalities,
  fetchMunicipalityProfile,
  fetchObservations,
  fetchPeriods,
  fetchProfile,
  getApiUrl,
} from "@/lib/api";

const BrazilMap = dynamic(
  () => import("@/components/BrazilMap").then((m) => m.BrazilMap),
  {
    ssr: false,
    loading: () => <div className="map-root" aria-hidden="true" />,
  },
);

const MUNI_ZOOM = 5.6;

function formatValue(obs: Pick<Observation, "value" | "unit"> | { value: number; unit?: string | null }) {
  const unit = obs.unit || "";
  if (unit === "BRL") {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
      maximumFractionDigits: 0,
    }).format(obs.value);
  }
  if (unit === "%" || unit === "hab/km²") {
    return `${new Intl.NumberFormat("pt-BR", {
      maximumFractionDigits: unit === "%" ? 2 : 1,
    }).format(obs.value)}${unit === "%" ? "%" : ` ${unit}`}`;
  }
  if (unit === "por 100 mil hab") {
    return `${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(obs.value)} /100 mil`;
  }
  if (unit === "USD") {
    const abs = Math.abs(obs.value);
    if (abs >= 1e9) {
      return `US$ ${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(obs.value / 1e9)} bi`;
    }
    if (abs >= 1e6) {
      return `US$ ${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(obs.value / 1e6)} mi`;
    }
    return `US$ ${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(obs.value)}`;
  }
  if (unit === "km²") {
    return `${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(obs.value)} km²`;
  }
  return new Intl.NumberFormat("pt-BR").format(obs.value);
}

function formatPeriodLabel(period: string) {
  if (/^\d{6}$/.test(period)) {
    return `${period.slice(0, 4)} · T${Number(period.slice(4))}`;
  }
  return period;
}

function formatTerritoryValue(item: TerritoryItem) {
  if (item.text) return item.text;
  if (item.value == null) return "SEM DADO";
  return formatValue({ value: item.value, unit: item.unit });
}

function TerritorySections({ items }: { items: TerritoryItem[] }) {
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

export default function HomePage() {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [layer, setLayer] = useState("population");
  const [year, setYear] = useState<string>("");
  const [periods, setPeriods] = useState<string[]>([]);
  const [obs, setObs] = useState<Observation[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [muniProfile, setMuniProfile] = useState<Profile | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [cardOpen, setCardOpen] = useState(false);
  const [zoom, setZoom] = useState(3.7);
  const [municipalities, setMunicipalities] = useState<Awaited<
    ReturnType<typeof fetchMunicipalities>
  > | null>(null);
  const [muniSelected, setMuniSelected] = useState<{
    ibge_code: string;
    name: string;
    value: number | null;
    uf_code: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMuni, setLoadingMuni] = useState(false);

  useEffect(() => {
    fetchIndicators()
      .then((data) => {
        const real = data.items.filter((i) => i.kind !== "experimental");
        setIndicators(real);
        const pop = real.find((i) => i.id === "population");
        if (pop?.reference_period) {
          setYear(pop.reference_period.slice(0, 4));
        }
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!layer) return;
    fetchPeriods(layer)
      .then((data) => {
        setPeriods(data.items);
        const ref = indicators.find((i) => i.id === layer)?.reference_period || "";
        const preferred = ref.replace(/-.*/, "") || data.items[data.items.length - 1] || "";
        setYear((current) => {
          if (preferred && data.items.includes(preferred)) return preferred;
          const yearPrefix = preferred.slice(0, 4);
          const match = [...data.items]
            .reverse()
            .find((p) => p === yearPrefix || p.startsWith(yearPrefix));
          if (match) return match;
          if (current && data.items.includes(current)) return current;
          return data.items[data.items.length - 1] || "";
        });
      })
      .catch(() => setPeriods([]));
  }, [layer, indicators]);

  useEffect(() => {
    if (!layer || !year || !periods.length) return;
    if (!periods.includes(year)) return;
    setLoading(true);
    fetchObservations(layer, year)
      .then((data) => {
        setObs(data.items);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [layer, year, periods]);

  const showMunicipalities = zoom >= MUNI_ZOOM && Boolean(selected);

  useEffect(() => {
    if (!showMunicipalities || !selected) {
      setMunicipalities(null);
      return;
    }
    const period = year && /^\d{4}/.test(year) ? year.slice(0, 4) : "2025";
    setLoadingMuni(true);
    fetchMunicipalities(selected, period)
      .then((data) => {
        setMunicipalities(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoadingMuni(false));
  }, [showMunicipalities, selected, year]);

  const activeIndicator = useMemo(
    () => indicators.find((i) => i.id === layer) || null,
    [indicators, layer],
  );

  const indicatorGroups = useMemo(() => {
    const order = ["economia", "social", "agro", "seguranca", "saude", "justica"];
    const map = new Map<string, { label: string; items: Indicator[] }>();
    for (const ind of indicators) {
      const key = ind.group || "outros";
      const label = ind.group_label || key;
      if (!map.has(key)) map.set(key, { label, items: [] });
      map.get(key)!.items.push(ind);
    }
    const ranked = [...map.entries()].sort(([a], [b]) => {
      const ia = order.indexOf(a);
      const ib = order.indexOf(b);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });
    return ranked.map(([key, g]) => ({ key, ...g }));
  }, [indicators]);

  const higherIsWorse = Boolean(activeIndicator?.higher_is_worse);

  const selectedObs = useMemo(
    () => obs.find((o) => o.geography_ibge_code === selected) || null,
    [obs, selected],
  );

  const mapValues = useMemo(
    () => obs.map((o) => ({ ibge_code: o.geography_ibge_code, value: o.value })),
    [obs],
  );

  const legendScale = useMemo(() => {
    const unit = activeIndicator?.unit;
    if (higherIsWorse) {
      return { low: "menor taxa", high: "maior taxa", note: "quanto maior, pior o indicador" };
    }
    if (unit === "%") {
      return { low: "menor %", high: "maior %", note: "escala relativa entre UFs no período" };
    }
    if (unit === "BRL") {
      return {
        low: "menor PIB",
        high: "maior PIB",
        note: "absoluto + % do Brasil no rótulo · escuro = maior",
      };
    }
    if (unit === "habitantes") {
      return {
        low: "menos gente",
        high: "mais gente",
        note: "estimativa + % do Brasil no rótulo de cada UF",
      };
    }
    if (unit === "USD") {
      return {
        low: "menor FOB",
        high: "maior FOB",
        note: "exportação US$ FOB · escuro = maior valor",
      };
    }
    if (unit === "por 100 mil hab") {
      return {
        low: "menor taxa",
        high: "maior taxa",
        note: "por 100 mil habitantes · quanto maior, pior",
      };
    }
    if (unit === "homicídios") {
      return {
        low: "menos casos",
        high: "mais casos",
        note: "contagem absoluta · compare UFs pela taxa",
      };
    }
    return { low: "menor", high: "maior", note: "escala relativa entre UFs no período" };
  }, [activeIndicator, higherIsWorse]);

  const layerTip = useMemo(() => {
    if (!activeIndicator || !hasProvenance(activeIndicator)) return null;
    return {
      definition: activeIndicator.definition,
      source: activeIndicator.source,
      reference_period: year || activeIndicator.reference_period,
      status_label: activeIndicator.status_label,
      limitations: activeIndicator.limitations,
    };
  }, [activeIndicator, year]);

  const yearTip = useMemo(() => {
    if (!activeIndicator || !hasProvenance(activeIndicator)) return null;
    return {
      definition: `Período de referência exibido no mapa para a camada “${activeIndicator.short_name || activeIndicator.name}”. O valor colorido corresponde a este período oficial.`,
      source: activeIndicator.source,
      reference_period: year,
      status_label: activeIndicator.status_label,
      limitations: [
        "Trocar o período recarrega observações oficiais da mesma camada.",
        ...(activeIndicator.limitations || []),
      ],
    };
  }, [activeIndicator, year]);

  const onSelect = useCallback((code: string) => {
    setSelected(code);
    setMuniSelected(null);
    setMuniProfile(null);
    setCardOpen(true);
    fetchProfile(code)
      .then(setProfile)
      .catch(() => setProfile(null));
  }, []);

  const onSelectMunicipality = useCallback(
    (m: { ibge_code: string; name: string; value: number | null; uf_code: string }) => {
      setMuniSelected(m);
      setCardOpen(true);
      fetchMunicipalityProfile(m.ibge_code)
        .then(setMuniProfile)
        .catch(() => setMuniProfile(null));
    },
    [],
  );

  const closeCard = () => {
    setCardOpen(false);
    setMuniSelected(null);
    setMuniProfile(null);
  };

  const yearOptions = useMemo(() => {
    if (periods.some((p) => p.length === 6)) {
      return periods.slice(-12).reverse();
    }
    // Séries longas (ex.: homicídios desde ~1980): últimos 25 anos no seletor.
    return [...periods].slice(-25).reverse();
  }, [periods]);

  const muniPopTip = municipalities
    ? {
        definition: municipalities.definition,
        source: municipalities.source,
        reference_period: municipalities.period,
        status_label: municipalities.status_label || "ESTIMADO",
        limitations: [
          "Valor do clique no mapa municipal; demais atributos vêm da ficha territorial.",
        ],
      }
    : null;

  const profileMetricTip = (m: Observation) => ({
    definition: m.definition,
    source: m.source as { organization?: string; dataset?: string; url?: string },
    reference_period: m.reference_period,
    status_label: m.status_label,
    limitations: m.limitations,
  });

  return (
    <div className="app-shell">
      <div className="atlas">
        <BrazilMap
          values={mapValues}
          selectedCode={selected}
          onSelect={onSelect}
          onSelectMunicipality={onSelectMunicipality}
          onZoomChange={setZoom}
          municipalities={municipalities?.geojson || null}
          showMunicipalities={showMunicipalities}
          higherIsWorse={higherIsWorse}
          valueUnit={activeIndicator?.unit}
        />
        <div className="map-veil" aria-hidden="true" />

        <header className="brand-block">
          <h1>Brasil Real</h1>
          <p>O mapa é o produto. Clique para a ficha — dados oficiais com fonte.</p>
        </header>

        <div className="map-controls">
          <label className="control-block">
            <span>
              Camada {layerTip ? <InfoTip data={layerTip} label="Sobre a camada" /> : null}
            </span>
            <select
              value={layer}
              onChange={(e) => {
                setLayer(e.target.value);
                setObs([]);
              }}
            >
              {indicatorGroups.map((group) => (
                <optgroup key={group.key} label={group.label}>
                  {group.items.map((ind) => (
                    <option key={ind.id} value={ind.id}>
                      {ind.short_name || ind.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </label>
          <label className="control-block">
            <span>
              Ano / período {yearTip ? <InfoTip data={yearTip} label="Sobre o período" /> : null}
            </span>
            <select
              value={year}
              onChange={(e) => setYear(e.target.value)}
              disabled={!yearOptions.length}
            >
              {yearOptions.map((p) => (
                <option key={p} value={p}>
                  {formatPeriodLabel(p)}
                </option>
              ))}
            </select>
          </label>
          <div className="control-hint">
            {showMunicipalities
              ? loadingMuni
                ? "Carregando municípios…"
                : `Municípios · ${municipalities?.count || 0}`
              : `Zoom ${zoom.toFixed(1)} · municípios a partir de ${MUNI_ZOOM}`}
            {loading ? " · atualizando camada…" : ""}
          </div>
        </div>

        <div className="legend">
          <div className="legend-title">
            <span>{activeIndicator?.name || "Camada"}</span>
            {layerTip ? <InfoTip data={layerTip} label="Sobre a legenda" /> : null}
          </div>
          <div className={`legend-bar ${higherIsWorse ? "worse" : "observed"}`} />
          <div className="legend-scale">
            <span>{legendScale.low}</span>
            <span>{legendScale.high}</span>
          </div>
          <div className="legend-note">
            {formatPeriodLabel(year || "—")} · {activeIndicator?.status_label || "—"} · IBGE
            <br />
            {legendScale.note}
          </div>
        </div>

        {cardOpen && (selectedObs || muniSelected) && (
          <aside className="float-card" aria-live="polite">
            <div className="float-card-head">
              <div>
                <p className="kicker">
                  {muniSelected ? "Município" : "Unidade da Federação"}
                </p>
                <h2>
                  {muniSelected?.name ||
                    profile?.geography.name ||
                    selectedObs?.name ||
                    "Seleção"}
                </h2>
                <p className="uf-meta">
                  {muniSelected
                    ? `IBGE ${muniSelected.ibge_code} · UF ${muniSelected.uf_code}`
                    : selectedObs
                      ? `${selectedObs.uf} · IBGE ${selectedObs.geography_ibge_code}`
                      : ""}
                </p>
              </div>
              <button type="button" className="close-card" onClick={closeCard} aria-label="Fechar">
                ×
              </button>
            </div>

            {muniSelected ? (
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
              profile?.metrics.find((m) => m.indicator === selectedObs.indicator) &&
              hasProvenance(
                profileMetricTip(
                  profile.metrics.find((m) => m.indicator === selectedObs.indicator)!,
                ),
              ) && (
                <div className="stat-block">
                  <div className="stat-value">
                    {formatValue(selectedObs)}{" "}
                    <InfoTip
                      data={profileMetricTip(
                        profile.metrics.find((m) => m.indicator === selectedObs.indicator)!,
                      )}
                    />
                  </div>
                  <div className="stat-unit">
                    {activeIndicator?.short_name || selectedObs.indicator} ·{" "}
                    {formatPeriodLabel(selectedObs.reference_period)}
                  </div>
                  <span className="status-mark observed">{selectedObs.status_label}</span>
                </div>
              )
            )}

            {muniSelected && muniProfile?.territory?.items && (
              <TerritorySections items={muniProfile.territory.items} />
            )}

            {!muniSelected && profile?.territory?.items && (
              <TerritorySections items={profile.territory.items} />
            )}

            {!muniSelected && profile && (
              <div className="fiche-section">
                <h3 className="section-title">Indicadores</h3>
                <div className="metric-list">
                  {profile.metrics.filter((m) => hasProvenance(profileMetricTip(m))).map((m) => (
                    <div
                      key={m.indicator}
                      className={`metric-row ${layer === m.indicator ? "active" : ""}`}
                    >
                      <button
                        type="button"
                        className="metric-row-main"
                        onClick={() => setLayer(m.indicator)}
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
              {profile?.disclaimer || muniProfile?.disclaimer ||
                "Cada valor exige fonte e definição oficiais no “?”."}
            </p>
          </aside>
        )}

        {error && (
          <div className="map-error" role="alert">
            {error}. API: {getApiUrl()}
          </div>
        )}
      </div>
    </div>
  );
}
