"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { hasProvenance } from "@/components/InfoTip";
import { groupIndicators, legendScaleFor, rankingPresetsFor } from "@/lib/legend";
import {
  buildIntermediateFiche,
  buildMacroFiche,
  buildRegionRanking,
  isAdditiveUnit,
  recorteLabel,
  ufsForRecorte,
  type RecorteId,
  type RegionFiche,
  type RegionRankRow,
} from "@/lib/map/regions";
import {
  isRegionRankMode,
  shouldShowMunicipalities,
  ZOOM,
} from "@/lib/map/zoomLadder";
import {
  type Indicator,
  type Observation,
  type Profile,
  fetchIndicators,
  fetchMunicipalities,
  fetchMunicipalityProfile,
  fetchObservations,
  fetchPeriods,
  fetchProfile,
} from "@/lib/api";
import { gateObservations } from "@/lib/dataGate";
import { comparePeriodKeys, deltaUnitFor } from "@/lib/format";

const BOOT_MIN_MS = 1200;

export type MuniSelection = {
  ibge_code: string;
  name: string;
  value: number | null;
  uf_code: string;
};

export function useAtlasState() {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [layer, setLayer] = useState("population");
  const [year, setYear] = useState("");
  const [periods, setPeriods] = useState<string[]>([]);
  const [obs, setObs] = useState<Observation[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [muniProfile, setMuniProfile] = useState<Profile | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [focusCodes, setFocusCodes] = useState<string[] | null>(null);
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);
  const [selectedInter, setSelectedInter] = useState<string | null>(null);
  const [regionFiche, setRegionFiche] = useState<RegionFiche | null>(null);
  const [fitBrazilToken, setFitBrazilToken] = useState(0);
  const [cardOpen, setCardOpen] = useState(false);
  const [zoom, setZoom] = useState<number>(ZOOM.start);
  const [municipalities, setMunicipalities] = useState<Awaited<
    ReturnType<typeof fetchMunicipalities>
  > | null>(null);
  const [muniSelected, setMuniSelected] = useState<MuniSelection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMuni, setLoadingMuni] = useState(false);
  const [recorte, setRecorte] = useState<RecorteId>("BR");
  const [rankMode, setRankMode] = useState<"nivel" | "delta">("nivel");
  const [prevObs, setPrevObs] = useState<Observation[]>([]);
  const [popByIbge, setPopByIbge] = useState<Map<string, number>>(() => new Map());

  const [bootCatalog, setBootCatalog] = useState(false);
  const [bootPeriods, setBootPeriods] = useState(false);
  const [bootObs, setBootObs] = useState(false);
  const [bootMap, setBootMap] = useState(false);
  const [bootExiting, setBootExiting] = useState(false);
  const [bootVisible, setBootVisible] = useState(true);
  const bootStartedRef = useRef(
    typeof performance !== "undefined" ? performance.now() : Date.now(),
  );
  const initialLayerRef = useRef(true);
  const loadingDepthRef = useRef(0);
  const periodsSeq = useRef(0);
  const obsSeq = useRef(0);
  const prevSeq = useRef(0);
  const profileSeq = useRef(0);
  const muniSeq = useRef(0);
  const muniProfileSeq = useRef(0);

  const beginLoading = () => {
    loadingDepthRef.current += 1;
    setLoading(true);
  };
  const endLoading = () => {
    loadingDepthRef.current = Math.max(0, loadingDepthRef.current - 1);
    if (loadingDepthRef.current === 0) setLoading(false);
  };

  useEffect(() => {
    let cancelled = false;
    fetchIndicators()
      .then((data) => {
        if (cancelled) return;
        setIndicators(data.items.filter((i) => i.kind !== "experimental"));
        setBootCatalog(true);
      })
      .catch((err: Error) => {
        if (cancelled) return;
        setError(err.message);
        setBootCatalog(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchObservations("population")
      .then((data) => {
        if (cancelled) return;
        const next = new Map<string, number>();
        for (const row of gateObservations(data.items).items) {
          next.set(row.geography_ibge_code, row.value);
        }
        setPopByIbge(next);
      })
      .catch(() => {
        if (!cancelled) setPopByIbge(new Map());
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!layer) return;
    const seq = ++periodsSeq.current;
    setPeriods([]);
    setYear("");
    setObs([]);
    if (initialLayerRef.current) setBootPeriods(false);
    beginLoading();
    fetchPeriods(layer)
      .then((data) => {
        if (seq !== periodsSeq.current) return;
        const items = data.items || [];
        setPeriods(items);
        const latest = data.latest || items[items.length - 1] || "";
        setYear(latest);
        setBootPeriods(true);
        if (!latest) {
          setError((prev) => prev || "Nenhum período oficial para esta camada.");
        }
      })
      .catch((err: Error) => {
        if (seq !== periodsSeq.current) return;
        setPeriods([]);
        setYear("");
        setBootPeriods(true);
        setError(err.message);
      })
      .finally(() => {
        if (seq === periodsSeq.current) endLoading();
      });
  }, [layer]);

  useEffect(() => {
    if (!layer || !year || !periods.length) return;
    if (!periods.includes(year)) return;
    const seq = ++obsSeq.current;
    beginLoading();
    fetchObservations(layer, year)
      .then((data) => {
        if (seq !== obsSeq.current) return;
        const gated = gateObservations(data.items);
        setObs(gated.items);
        setBootObs(true);
        const integrity = data.meta?.integrity as
          | {
              dropped_count?: number;
              population_reconcile_ok?: boolean | null;
              pib_reconcile_ok?: boolean | null;
              coverage_ok?: boolean | null;
            }
          | undefined;
        if (data.meta?.period_miss) {
          setError(`Período ${year} sem observações oficiais para esta camada.`);
        } else if (integrity?.population_reconcile_ok === false) {
          setError("População inconsistente com o total Brasil — camada bloqueada.");
        } else if (integrity?.pib_reconcile_ok === false) {
          setError("PIB inconsistente com o total Brasil — camada bloqueada.");
        } else if (integrity?.coverage_ok === false) {
          setError("Camada incompleta (≠ 27 UFs) — mapa bloqueado.");
        } else if (gated.dropped.length && !gated.items.length) {
          setError("Observações sem proveniência completa foram bloqueadas.");
        } else {
          setError(null);
        }
      })
      .catch((err: Error) => {
        if (seq !== obsSeq.current) return;
        setBootObs(true);
        setError(err.message);
      })
      .finally(() => {
        if (seq === obsSeq.current) {
          endLoading();
          initialLayerRef.current = false;
        }
      });
  }, [layer, year, periods]);

  const chronoOfficial = useMemo(
    () => [...periods].sort(comparePeriodKeys),
    [periods],
  );
  const prevPeriod = useMemo(() => {
    const i = chronoOfficial.indexOf(year);
    return i > 0 ? chronoOfficial[i - 1] : "";
  }, [chronoOfficial, year]);
  const canDelta = Boolean(prevPeriod);

  useEffect(() => {
    if (!canDelta && rankMode === "delta") setRankMode("nivel");
  }, [canDelta, rankMode]);

  useEffect(() => {
    if (rankMode !== "delta" || !layer || !prevPeriod) {
      setPrevObs([]);
      return;
    }
    const seq = ++prevSeq.current;
    beginLoading();
    fetchObservations(layer, prevPeriod)
      .then((data) => {
        if (seq !== prevSeq.current) return;
        setPrevObs(gateObservations(data.items).items);
      })
      .catch((err: Error) => {
        if (seq !== prevSeq.current) return;
        setPrevObs([]);
        setError(err.message);
      })
      .finally(() => {
        if (seq === prevSeq.current) endLoading();
      });
  }, [rankMode, layer, prevPeriod]);

  const showMunicipalities = shouldShowMunicipalities(zoom, selected, layer);

  useEffect(() => {
    if (!showMunicipalities || !selected) {
      setMunicipalities(null);
      return;
    }
    const seq = ++muniSeq.current;
    const period = year && /^\d{4}/.test(year) ? year.slice(0, 4) : undefined;
    setLoadingMuni(true);
    fetchMunicipalities(selected, period)
      .then((data) => {
        if (seq !== muniSeq.current) return;
        setMunicipalities(data);
        setError(null);
      })
      .catch((err: Error) => {
        if (seq !== muniSeq.current) return;
        setError(err.message);
      })
      .finally(() => {
        if (seq === muniSeq.current) setLoadingMuni(false);
      });
  }, [showMunicipalities, selected, year]);

  const bootStages = useMemo(
    () => [
      { id: "catalog", label: "Catálogo de camadas", done: bootCatalog },
      { id: "periods", label: "Período oficial mais recente", done: bootPeriods },
      { id: "obs", label: "Observações por UF", done: bootObs },
      { id: "map", label: "Malha e rótulos do mapa", done: bootMap },
    ],
    [bootCatalog, bootPeriods, bootObs, bootMap],
  );

  const bootReady = bootCatalog && bootPeriods && bootObs && bootMap;

  useEffect(() => {
    if (!bootReady || bootExiting || !bootVisible) return;
    const now = typeof performance !== "undefined" ? performance.now() : Date.now();
    const wait = Math.max(0, BOOT_MIN_MS - (now - bootStartedRef.current));
    const t = window.setTimeout(() => setBootExiting(true), wait);
    return () => window.clearTimeout(t);
  }, [bootReady, bootExiting, bootVisible]);

  const onMapReady = useCallback(() => setBootMap(true), []);

  const activeIndicator = useMemo(
    () => indicators.find((i) => i.id === layer) || null,
    [indicators, layer],
  );

  const indicatorGroups = useMemo(() => groupIndicators(indicators), [indicators]);
  const rankingGroups = useMemo(() => rankingPresetsFor(indicators), [indicators]);
  const higherIsWorse = Boolean(activeIndicator?.higher_is_worse);

  const viewObs = useMemo(() => {
    let rows = obs;
    if (rankMode === "delta" && prevPeriod && prevObs.length) {
      const prevBy = new Map(prevObs.map((r) => [r.geography_ibge_code, r]));
      const next: Observation[] = [];
      for (const row of obs) {
        const prev = prevBy.get(row.geography_ibge_code);
        if (!prev) continue;
        next.push({
          ...row,
          value: row.value - prev.value,
          unit: deltaUnitFor(row.unit),
          status_label: "DERIVADO",
          definition: `Variação entre os períodos oficiais ${year} e ${prevPeriod} da mesma camada. ${row.definition || ""}`.trim(),
          limitations: [
            "Delta local: valor atual − valor do período oficial anterior. A fonte não publica este ranking.",
            "Valor nominal; não deflacionado.",
            ...(row.limitations || []),
          ],
        });
      }
      rows = next;
    }
    const allow = ufsForRecorte(recorte);
    if (allow) rows = rows.filter((r) => allow.includes(r.uf));
    return rows;
  }, [obs, rankMode, prevObs, prevPeriod, year, recorte]);

  const selectedObs = useMemo(
    () => viewObs.find((o) => o.geography_ibge_code === selected) || null,
    [viewObs, selected],
  );

  const mapValues = useMemo(
    () => viewObs.map((o) => ({ ibge_code: o.geography_ibge_code, value: o.value })),
    [viewObs],
  );

  const regionMode = isRegionRankMode(zoom, showMunicipalities);

  const regionRows = useMemo(() => {
    const valueByIbge = new Map(viewObs.map((o) => [o.geography_ibge_code, o.value]));
    return buildRegionRanking(
      valueByIbge,
      viewObs.map((o) => ({
        ibge_code: o.geography_ibge_code,
        uf: o.uf,
        unit: o.unit,
      })),
      viewObs[0]?.unit || activeIndicator?.unit,
      higherIsWorse,
      popByIbge,
    );
  }, [viewObs, activeIndicator?.unit, higherIsWorse, popByIbge]);

  const legendScale = useMemo(() => {
    if (rankMode === "delta") {
      return {
        low: higherIsWorse ? "maior queda (melhor)" : "maior queda",
        high: higherIsWorse ? "maior alta (pior)" : "maior alta",
        note: "variação vs período oficial anterior · não deflacionada · não somar",
      };
    }
    return legendScaleFor(activeIndicator, higherIsWorse);
  }, [activeIndicator, higherIsWorse, rankMode]);

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
        periods.length > 1
          ? `Série oficial com ${periods.length} períodos; o mapa mostra só o selecionado.`
          : "Esta camada tem um único período oficial na fonte (não há série anual aqui).",
        "Trocar o período recarrega observações oficiais da mesma camada.",
        ...(activeIndicator.limitations || []),
      ],
    };
  }, [activeIndicator, periods.length, year]);

  const onSelect = useCallback((code: string) => {
    const seq = ++profileSeq.current;
    setSelected(code);
    setFocusCodes(null);
    setSelectedRegionId(null);
    setSelectedInter(null);
    setRegionFiche(null);
    setMuniSelected(null);
    setMuniProfile(null);
    setCardOpen(true);
    fetchProfile(code)
      .then((p) => {
        if (seq !== profileSeq.current) return;
        setProfile(p);
      })
      .catch(() => {
        if (seq !== profileSeq.current) return;
        setProfile(null);
      });
  }, []);

  const onSelectRegion = useCallback(
    (row: RegionRankRow) => {
      setSelectedRegionId(row.id);
      setFocusCodes(row.ibge_codes);
      setSelected(null);
      setSelectedInter(null);
      setMuniSelected(null);
      setMuniProfile(null);
      setProfile(null);
      setRegionFiche(
        buildMacroFiche(row, {
          layerLabel: activeIndicator?.short_name || activeIndicator?.name || "Camada",
          period: year,
          unit: activeIndicator?.unit,
          definition: activeIndicator?.definition,
          source_org: activeIndicator?.source?.organization,
          status_label: "DERIVADO",
        }),
      );
      setCardOpen(true);
    },
    [activeIndicator, year],
  );

  const onSelectIntermediate = useCallback(
    (m: { ibge_code: string; name: string; uf: string; uf_code: string }) => {
      setSelectedInter(m.ibge_code);
      setSelected(null);
      setSelectedRegionId(null);
      setFocusCodes(null);
      setMuniSelected(null);
      setMuniProfile(null);
      setProfile(null);
      setRegionFiche(
        buildIntermediateFiche({
          id: m.ibge_code,
          name: m.name,
          uf: m.uf,
          uf_code: m.uf_code,
          layerLabel: activeIndicator?.short_name || activeIndicator?.name || "Camada",
          period: year,
        }),
      );
      setCardOpen(true);
    },
    [activeIndicator, year],
  );

  const onSelectMunicipality = useCallback((m: MuniSelection) => {
    const seq = ++muniProfileSeq.current;
    setMuniSelected(m);
    setRegionFiche(null);
    setSelectedInter(null);
    setCardOpen(true);
    fetchMunicipalityProfile(m.ibge_code)
      .then((p) => {
        if (seq !== muniProfileSeq.current) return;
        setMuniProfile(p);
      })
      .catch(() => {
        if (seq !== muniProfileSeq.current) return;
        setMuniProfile(null);
      });
  }, []);

  const closeCard = useCallback(() => {
    setCardOpen(false);
    setMuniSelected(null);
    setMuniProfile(null);
    setRegionFiche(null);
    setSelectedInter(null);
    setSelected(null);
    setSelectedRegionId(null);
    setFocusCodes(null);
    setProfile(null);
  }, []);

  const fitBrazil = useCallback(() => {
    setFitBrazilToken((n) => n + 1);
    setFocusCodes(null);
    setSelectedRegionId(null);
    setSelectedInter(null);
    setSelected(null);
    setRegionFiche(null);
    setCardOpen(false);
    setMuniSelected(null);
    setMuniProfile(null);
    setProfile(null);
  }, []);

  const changeLayer = useCallback((id: string) => {
    setLayer(id);
    setObs([]);
    setPrevObs([]);
    setRankMode("nivel");
  }, []);

  const yearOptions = useMemo(() => {
    const chrono = [...periods].sort(comparePeriodKeys);
    if (periods.some((p) => /^\d{4}T[12]$/.test(p))) return [...chrono].reverse();
    if (periods.some((p) => p.length === 6)) return chrono.slice(-16).reverse();
    return [...chrono].reverse();
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

  const selectedObsTip = useMemo(() => {
    if (!selectedObs) return null;
    const src =
      (selectedObs.source as { organization?: string; dataset?: string; url?: string }) ||
      activeIndicator?.source;
    return {
      definition: selectedObs.definition || activeIndicator?.definition,
      source: src,
      reference_period: selectedObs.reference_period,
      status_label: selectedObs.status_label,
      limitations: selectedObs.limitations || activeIndicator?.limitations,
    };
  }, [selectedObs, activeIndicator]);

  const controlHint = useMemo(() => {
    const z = zoom.toFixed(1);
    const additive = isAdditiveUnit(activeIndicator?.unit);
    if (layer === "population") {
      if (showMunicipalities) {
        if (loadingMuni) return "Carregando municípios…";
        return `Municípios · ${municipalities?.count || 0} · nomes densificam com o zoom`;
      }
      if (zoom >= ZOOM.municipality && !selected) {
        return `Zoom ${z} · selecione uma UF para municípios`;
      }
      if (regionMode) return `Zoom ${z} · macrorregião → intermediária → UF → município`;
      return `Zoom ${z} · intermediária/UF/capitais · município ≥${ZOOM.municipality}`;
    }
    if (recorte !== "BR") {
      return `Zoom ${z} · recorte ${recorteLabel(recorte)} · ${rankMode === "delta" ? "variação" : "nível"}`;
    }
    if (rankMode === "delta") {
      return `Zoom ${z} · variação vs período oficial anterior`;
    }
    if (regionMode) {
      return `Zoom ${z} · macrorregiões${additive ? " · soma aditiva" : " · média ponderada pela pop."}`;
    }
    if (periods.length > 1) {
      return `Zoom ${z} · linha do tempo da mesma métrica · ${periods.length} períodos oficiais`;
    }
    return `Zoom ${z} · intermediária + UF + capitais · municípios só em População`;
  }, [
    activeIndicator?.unit,
    layer,
    loadingMuni,
    municipalities?.count,
    periods.length,
    rankMode,
    recorte,
    regionMode,
    selected,
    showMunicipalities,
    zoom,
  ]);

  return {
    // data
    indicators,
    layer,
    year,
    periods,
    obs,
    profile,
    muniProfile,
    selected,
    focusCodes,
    selectedRegionId,
    selectedInter,
    regionFiche,
    fitBrazilToken,
    cardOpen,
    zoom,
    municipalities,
    muniSelected,
    error,
    loading,
    loadingMuni,
    // derived
    recorte,
    rankMode,
    canDelta,
    prevPeriod,
    recorteCaption: recorteLabel(recorte),
    viewObs,
    popByIbge,
    showMunicipalities,
    regionMode,
    regionRows,
    mapValues,
    activeIndicator,
    indicatorGroups,
    rankingGroups,
    higherIsWorse,
    selectedObs,
    legendScale,
    layerTip,
    yearTip,
    yearOptions,
    muniPopTip,
    selectedObsTip,
    controlHint,
    bootStages,
    bootReady,
    bootExiting,
    bootVisible,
    atlasLive: !bootVisible,
    // actions
    setYear,
    setRecorte,
    setRankMode,
    setZoom,
    setBootVisible,
    changeLayer,
    onMapReady,
    onSelect,
    onSelectRegion,
    onSelectIntermediate,
    onSelectMunicipality,
    closeCard,
    fitBrazil,
  };
}
