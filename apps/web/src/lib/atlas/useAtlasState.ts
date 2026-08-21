"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { hasProvenance } from "@/components/InfoTip";
import { groupIndicators, legendScaleFor, rankingPresetsFor } from "@/lib/legend";
import { useI18n } from "@/lib/i18n/I18nProvider";
import {
  buildIntermediateFiche,
  buildMacroFiche,
  buildRegionRanking,
  compareRankValue,
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
  type SimuladoRow,
  fetchIndicators,
  fetchMunicipalities,
  fetchMunicipalityProfile,
  fetchObservationSeries,
  fetchObservations,
  fetchPeriods,
  fetchProfile,
  fetchScenarios,
  runScenario,
  wakeApi,
} from "@/lib/api";
import { parseViewUrl, writeViewUrl, type ColorMode } from "@/lib/atlas/viewUrl";
import { gateObservations } from "@/lib/dataGate";
import { comparePeriodKeys, deltaUnitFor } from "@/lib/format";

const MAX_COMPARE = 3;
const SIM_SOURCE = {
  organization: "Brasil Real (motor hipotético)",
  dataset: "hypothetical_federal_fund_v1",
  url: "https://github.com/leonardolauriquer/BrasilReal",
};

function simRowsToObservations(
  rows: SimuladoRow[],
  disclaimer: string,
): Observation[] {
  return rows.map((row) => ({
    indicator: "simulado_fund",
    geography_ibge_code: row.ibge_code,
    uf: row.uf,
    name: row.name,
    value: Number(row.scenario_amount_brl),
    unit: "BRL",
    reference_period: "hipótese",
    status_label: "SIMULADO",
    source: SIM_SOURCE,
    dataset_id: "hypothetical_federal_fund_v1",
    definition: disclaimer,
    limitations: [
      "Rateio hipotético. Não é transferência, orçamento nem gasto observado.",
      "Conserva o orçamento declarado do cenário; sem efeitos comportamentais.",
    ],
    short_name: "Fundo hipotético",
  }));
}

function matchGeo(rows: Observation[], token: string) {
  const key = token.trim().toUpperCase();
  if (!key) return undefined;
  return rows.find(
    (r) => r.uf === key || r.geography_ibge_code === key || r.name.toUpperCase() === key,
  );
}

const BOOT_MIN_MS = 1200;

export type MuniSelection = {
  ibge_code: string;
  name: string;
  value: number | null;
  uf_code: string;
};

export function useAtlasState() {
  const { t } = useI18n();
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
  const [urlReady, setUrlReady] = useState(false);
  const [compareCodes, setCompareCodes] = useState<string[]>([]);
  const [simulado, setSimulado] = useState(false);
  const [simRows, setSimRows] = useState<Observation[]>([]);
  const [simDisclaimer, setSimDisclaimer] = useState("");
  const [simTitle, setSimTitle] = useState("");
  const [series, setSeries] = useState<Observation[]>([]);
  const [colorMode, setColorMode] = useState<ColorMode>("default");
  const [bootNonce, setBootNonce] = useState(0);
  const pendingYearRef = useRef<string>("");
  const pendingUfRef = useRef<string>("");
  const pendingVsRef = useRef<string[]>([]);

  const [bootApi, setBootApi] = useState(false);
  const [bootCatalog, setBootCatalog] = useState(false);
  const [bootPeriods, setBootPeriods] = useState(false);
  const [bootObs, setBootObs] = useState(false);
  const [bootMap, setBootMap] = useState(false);
  const [bootExiting, setBootExiting] = useState(false);
  const [bootVisible, setBootVisible] = useState(true);
  const [bootFailed, setBootFailed] = useState(false);
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
    const view = parseViewUrl();
    pendingYearRef.current = view.ano;
    pendingUfRef.current = view.uf;
    pendingVsRef.current = view.vs;
    if (view.camada) setLayer(view.camada);
    if (view.recorte) setRecorte(view.recorte);
    if (view.modo === "delta") setRankMode("delta");
    if (view.sim) setSimulado(true);
    if (view.cor === "cb") setColorMode("cb");
    setUrlReady(true);
  }, []);

  useEffect(() => {
    if (!urlReady) return;
    let cancelled = false;
    const ctrl = new AbortController();
    setBootApi(false);
    setBootCatalog(false);
    setBootFailed(false);
    wakeApi(ctrl.signal)
      .then(() => {
        if (cancelled) return;
        setBootApi(true);
        return fetchIndicators();
      })
      .then((data) => {
        if (cancelled || !data) return;
        setIndicators(data.items.filter((i) => i.kind !== "experimental"));
        setBootCatalog(true);
      })
      .catch((err: Error) => {
        if (cancelled || err.name === "AbortError") return;
        setBootApi(true);
        setBootCatalog(true);
        setBootFailed(true);
        setError(
          err.message.includes("API") || err.message.includes("cold") || err.message.includes("acordar")
            ? `${err.message} O primeiro acesso após inatividade pode demorar.`
            : err.message,
        );
      });
    return () => {
      cancelled = true;
      ctrl.abort();
    };
  }, [urlReady, bootNonce]);

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
    if (!urlReady || !layer) return;
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
        const want = pendingYearRef.current;
        pendingYearRef.current = "";
        setYear(want && items.includes(want) ? want : latest);
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
  }, [layer, urlReady, bootNonce]);

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
  }, [layer, year, periods, bootNonce]);

  useEffect(() => {
    if (!urlReady || !indicators.length) return;
    if (layer && !indicators.some((i) => i.id === layer)) setLayer("population");
  }, [indicators, layer, urlReady]);

  useEffect(() => {
    if (!selected || !layer || simulado) {
      setSeries([]);
      return;
    }
    let cancelled = false;
    fetchObservationSeries(layer, selected)
      .then((data) => {
        if (cancelled) return;
        setSeries(gateObservations(data.items).items);
      })
      .catch(() => {
        if (!cancelled) setSeries([]);
      });
    return () => {
      cancelled = true;
    };
  }, [selected, layer, simulado]);

  useEffect(() => {
    if (!simulado) {
      setSimRows([]);
      setSimDisclaimer("");
      setSimTitle("");
      return;
    }
    let cancelled = false;
    fetchScenarios()
      .then((data) => {
        if (cancelled) return undefined;
        const scenario =
          data.items.find((s) => s.id === "scn_baseline_fund_demo") || data.items[0];
        if (!scenario) throw new Error("Nenhum cenário hipotético na API.");
        setSimTitle(scenario.title);
        setSimDisclaimer(scenario.disclaimer || "");
        return runScenario(scenario.id, 42);
      })
      .then((run) => {
        if (cancelled || !run) return;
        setSimDisclaimer(run.disclaimer || "");
        setSimRows(
          gateObservations(simRowsToObservations(run.comparison || [], run.disclaimer)).items,
        );
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [simulado]);

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

  const showMunicipalities = !simulado && shouldShowMunicipalities(zoom, selected, layer);

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
      { id: "api", label: t("boot.api"), done: bootApi },
      { id: "catalog", label: t("boot.catalog"), done: bootCatalog },
      { id: "periods", label: t("boot.periods"), done: bootPeriods },
      { id: "obs", label: t("boot.obs"), done: bootObs },
      { id: "map", label: t("boot.map"), done: bootMap },
    ],
    [bootApi, bootCatalog, bootPeriods, bootObs, bootMap, t],
  );

  const bootReady = bootApi && bootCatalog && bootPeriods && bootObs && bootMap;

  useEffect(() => {
    if (!bootReady || bootExiting || !bootVisible || bootFailed) return;
    const now = typeof performance !== "undefined" ? performance.now() : Date.now();
    const wait = Math.max(0, BOOT_MIN_MS - (now - bootStartedRef.current));
    const t = window.setTimeout(() => setBootExiting(true), wait);
    return () => window.clearTimeout(t);
  }, [bootReady, bootExiting, bootVisible, bootFailed]);

  const onMapReady = useCallback(() => setBootMap(true), []);

  const retryBoot = useCallback(() => {
    setError(null);
    setBootFailed(false);
    setBootExiting(false);
    setBootVisible(true);
    setBootApi(false);
    setBootCatalog(false);
    setBootPeriods(false);
    setBootObs(false);
    bootStartedRef.current = typeof performance !== "undefined" ? performance.now() : Date.now();
    setBootNonce((n) => n + 1);
  }, []);

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

  const displayObs = useMemo(
    () => (simulado && simRows.length ? simRows : viewObs),
    [simulado, simRows, viewObs],
  );

  const selectedObs = useMemo(
    () => displayObs.find((o) => o.geography_ibge_code === selected) || null,
    [displayObs, selected],
  );

  const mapValues = useMemo(
    () => displayObs.map((o) => ({ ibge_code: o.geography_ibge_code, value: o.value })),
    [displayObs],
  );

  const rankedCodes = useMemo(
    () =>
      [...displayObs]
        .sort((a, b) => compareRankValue(a.value, b.value, simulado ? false : higherIsWorse))
        .map((r) => r.geography_ibge_code),
    [displayObs, higherIsWorse, simulado],
  );

  const compareObs = useMemo(
    () => compareCodes.map((code) => displayObs.find((r) => r.geography_ibge_code === code)).filter(Boolean) as Observation[],
    [compareCodes, displayObs],
  );

  const regionMode = isRegionRankMode(zoom, showMunicipalities);

  const regionRows = useMemo(() => {
    const valueByIbge = new Map(displayObs.map((o) => [o.geography_ibge_code, o.value]));
    return buildRegionRanking(
      valueByIbge,
      displayObs.map((o) => ({
        ibge_code: o.geography_ibge_code,
        uf: o.uf,
        unit: o.unit,
      })),
      displayObs[0]?.unit || activeIndicator?.unit,
      higherIsWorse && !simulado,
      popByIbge,
    );
  }, [displayObs, activeIndicator?.unit, higherIsWorse, popByIbge, simulado]);

  const legendScale = useMemo(() => {
    if (simulado) {
      return {
        low: "menor alocação hipotética",
        high: "maior alocação hipotética",
        note: "SIMULADO · não é gasto observado · orçamento do cenário conservado",
      };
    }
    if (rankMode === "delta") {
      return {
        low: higherIsWorse ? "maior queda (melhor)" : "maior queda",
        high: higherIsWorse ? "maior alta (pior)" : "maior alta",
        note: "variação vs período oficial anterior · não deflacionada · não somar",
      };
    }
    return legendScaleFor(activeIndicator, higherIsWorse);
  }, [activeIndicator, higherIsWorse, rankMode, simulado]);

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
    if (simulado) setSimulado(false);
  }, [simulado]);

  const toggleCompare = useCallback((code: string) => {
    setCompareCodes((prev) => {
      if (prev.includes(code)) return prev.filter((c) => c !== code);
      if (prev.length >= MAX_COMPARE) return [...prev.slice(1), code];
      return [...prev, code];
    });
  }, []);

  const selectAdjacent = useCallback(
    (dir: 1 | -1) => {
      if (!rankedCodes.length) return;
      const i = selected ? rankedCodes.indexOf(selected) : -1;
      const next =
        i < 0
          ? rankedCodes[dir === 1 ? 0 : rankedCodes.length - 1]
          : rankedCodes[(i + dir + rankedCodes.length) % rankedCodes.length];
      if (next) onSelect(next);
    },
    [onSelect, rankedCodes, selected],
  );

  const toggleSimulado = useCallback((on: boolean) => {
    setSimulado(on);
    if (on) setRankMode("nivel");
  }, []);

  useEffect(() => {
    if (!obs.length) return;
    const ufToken = pendingUfRef.current;
    const vsTokens = pendingVsRef.current;
    if (ufToken) {
      pendingUfRef.current = "";
      const hit = matchGeo(obs, ufToken);
      if (hit) onSelect(hit.geography_ibge_code);
    }
    if (vsTokens.length) {
      pendingVsRef.current = [];
      const codes = vsTokens
        .map((t) => matchGeo(obs, t)?.geography_ibge_code)
        .filter((c): c is string => Boolean(c))
        .slice(0, MAX_COMPARE);
      if (codes.length) setCompareCodes(codes);
    }
  }, [obs, onSelect]);

  useEffect(() => {
    if (!urlReady || !year) return;
    const geoPool = simulado && simRows.length ? simRows : obs;
    const uf =
      geoPool.find((r) => r.geography_ibge_code === selected)?.uf || selectedObs?.uf || "";
    const vs = compareCodes
      .map((code) => geoPool.find((r) => r.geography_ibge_code === code)?.uf)
      .filter((s): s is string => Boolean(s));
    writeViewUrl({
      camada: layer,
      ano: year,
      uf,
      recorte,
      modo: rankMode,
      vs,
      sim: simulado,
      cor: colorMode,
    });
  }, [
    colorMode,
    compareCodes,
    layer,
    obs,
    rankMode,
    recorte,
    selected,
    selectedObs?.uf,
    simRows,
    simulado,
    urlReady,
    year,
  ]);

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
        if (loadingMuni) return t("hint.loadingMuni");
        return t("hint.muniReady", { n: municipalities?.count || 0 });
      }
      if (zoom >= ZOOM.municipality && !selected) {
        return t("hint.pickUf", { z });
      }
      if (regionMode) return t("hint.ladderPop", { z });
      return t("hint.popDefault", { z, min: ZOOM.municipality });
    }
    if (recorte !== "BR") {
      return t("hint.recorte", {
        z,
        recorte: t(`recorte.${recorte}`),
        mode: rankMode === "delta" ? t("ui.variation") : t("ui.level"),
      });
    }
    if (rankMode === "delta") {
      return t("hint.delta", { z });
    }
    if (regionMode) {
      return additive ? t("hint.regionSum", { z }) : t("hint.regionAvg", { z });
    }
    if (periods.length > 1) {
      return t("hint.timeline", { z, n: periods.length });
    }
    return t("hint.default", { z });
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
    t,
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
    canDelta: canDelta && !simulado,
    prevPeriod,
    recorteCaption: t(`recorte.${recorte}`),
    viewObs,
    displayObs,
    compareCodes,
    compareObs,
    series,
    simulado,
    simTitle,
    simDisclaimer,
    popByIbge,
    showMunicipalities,
    regionMode,
    regionRows,
    mapValues,
    activeIndicator,
    indicatorGroups,
    rankingGroups,
    higherIsWorse: simulado ? false : higherIsWorse,
    selectedObs,
    legendScale,
    layerTip,
    yearTip,
    yearOptions,
    muniPopTip,
    selectedObsTip,
    controlHint,
    colorMode,
    bootStages,
    bootReady,
    bootExiting,
    bootVisible,
    bootFailed,
    atlasLive: !bootVisible,
    // actions
    setYear,
    setRecorte,
    setRankMode,
    setColorMode,
    setZoom,
    setBootVisible,
    retryBoot,
    changeLayer,
    onMapReady,
    onSelect,
    onSelectRegion,
    onSelectIntermediate,
    onSelectMunicipality,
    closeCard,
    fitBrazil,
    toggleCompare,
    selectAdjacent,
    toggleSimulado,
  };
}
