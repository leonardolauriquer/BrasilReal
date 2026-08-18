"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { AtlasFloatCard } from "@/components/AtlasFloatCard";
import { AtlasSearch } from "@/components/AtlasSearch";
import { BootScreen } from "@/components/BootScreen";
import { BrandMark } from "@/components/BrandMark";
import { CompareTray } from "@/components/CompareTray";
import { DataDossier } from "@/components/DataDossier";
import { MapControlsBar } from "@/components/MapControlsBar";
import { PwaDock } from "@/components/PwaDock";
import { RankPanel } from "@/components/RankPanel";
import { SimuladoBanner } from "@/components/SimuladoBanner";
import { useAtlasState } from "@/lib/atlas/useAtlasState";
import { copyViewUrl, isTypingTarget } from "@/lib/atlas/viewUrl";
import { getApiUrl } from "@/lib/api";
import { LENS_SHORTCUTS } from "@/lib/legend";
import { downloadMapPng } from "@/lib/map/capture";
import { formatPeriodLabel } from "@/lib/format";

const BrazilMap = dynamic(
  () => import("@/components/BrazilMap").then((m) => m.BrazilMap),
  {
    ssr: false,
    loading: () => <div className="map-root" aria-hidden="true" />,
  },
);

export default function HomePage() {
  const a = useAtlasState();
  const [dossierOpen, setDossierOpen] = useState(false);
  const [pwaOffer, setPwaOffer] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const layerLabel = a.simulado
    ? a.simTitle || "Fundo hipotético"
    : a.activeIndicator?.short_name || a.activeIndicator?.name || "Camada";

  useEffect(() => {
    const bits = [layerLabel];
    if (a.recorteCaption && a.recorteCaption !== "Brasil (27 UFs)") bits.push(a.recorteCaption);
    if (a.year) bits.push(formatPeriodLabel(a.year));
    if (a.selectedObs?.uf) bits.push(a.selectedObs.uf);
    document.title = `${bits.join(" · ")} | Brasil Real`;
    return () => {
      document.title = "Brasil Real";
    };
  }, [a.recorteCaption, a.selectedObs?.uf, a.year, layerLabel]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (isTypingTarget(e.target) && e.key !== "Escape") return;
      if (e.key === "Escape") {
        if (searchOpen) {
          setSearchOpen(false);
          return;
        }
        if (filtersOpen) {
          setFiltersOpen(false);
          return;
        }
        if (dossierOpen) {
          setDossierOpen(false);
          return;
        }
        if (a.cardOpen) a.closeCard();
        return;
      }
      if ((e.key === "/" && !e.ctrlKey && !e.metaKey) || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k")) {
        e.preventDefault();
        setSearchOpen(true);
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        a.selectAdjacent(1);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        a.selectAdjacent(-1);
        return;
      }
      if (e.key >= "1" && e.key <= "4" && !e.altKey && !e.ctrlKey && !e.metaKey) {
        const lens = LENS_SHORTCUTS[Number(e.key) - 1];
        if (lens) a.changeLayer(lens);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [a, dossierOpen, filtersOpen, searchOpen]);

  const shareView = async () => {
    const ok = await copyViewUrl();
    setCopied(ok);
    window.setTimeout(() => setCopied(false), 1800);
  };

  const exportPng = () => {
    downloadMapPng({
      layerLabel,
      period: a.simulado ? "hipótese" : formatPeriodLabel(a.year || "—"),
      status: a.simulado ? "SIMULADO" : a.rankMode === "delta" ? "DERIVADO" : a.activeIndicator?.status_label || "—",
      organization: a.simulado
        ? "Brasil Real (motor hipotético)"
        : a.activeIndicator?.source?.organization,
      url: typeof window !== "undefined" ? window.location.href : undefined,
    });
  };

  const atlasClass = [
    "atlas",
    a.atlasLive ? "atlas--live" : "atlas--booting",
    a.colorMode === "cb" ? "atlas--cb" : "",
    filtersOpen ? "atlas--filters" : "",
    a.simulado ? "atlas--simulado" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="app-shell">
      {a.bootVisible && (
        <BootScreen
          stages={a.bootStages}
          error={a.error && (!a.bootReady || a.bootFailed) ? a.error : null}
          exiting={a.bootExiting}
          onExitComplete={() => a.setBootVisible(false)}
          onRetry={a.retryBoot}
        />
      )}

      <div className={atlasClass} aria-hidden={!a.atlasLive}>
        <BrazilMap
          values={a.mapValues}
          selectedCode={a.selected}
          selectedInterCode={a.selectedInter}
          focusCodes={a.focusCodes}
          fitBrazilToken={a.fitBrazilToken}
          onSelect={a.onSelect}
          onSelectMunicipality={a.onSelectMunicipality}
          onSelectIntermediate={a.onSelectIntermediate}
          onZoomChange={a.setZoom}
          onReady={a.onMapReady}
          municipalities={a.municipalities?.geojson || null}
          showMunicipalities={a.showMunicipalities}
          higherIsWorse={a.higherIsWorse}
          colorMode={a.colorMode}
          valueUnit={a.simulado ? "BRL" : a.activeIndicator?.unit}
          popByIbge={a.popByIbge}
          cardOpen={a.cardOpen}
          compareCodes={a.compareCodes}
        />
        <div className="map-veil" aria-hidden="true" />

        {a.simulado ? (
          <SimuladoBanner
            title={a.simTitle}
            disclaimer={a.simDisclaimer}
            onExit={() => a.toggleSimulado(false)}
          />
        ) : null}

        <div className="left-rail">
          <header className="brand-block">
            <div className="brand-lockup">
              <BrandMark className="brand-mark" />
              <h1>Brasil Real</h1>
            </div>
            <p>
              {a.regionMode
                ? "Zoom afastado: macrorregiões IBGE. Clique uma região para ficha + aproximar."
                : "Mapa + ranking com fonte. Clique UF, região intermediária ou capital no zoom médio."}
            </p>
          </header>

          <RankPanel
            rows={a.displayObs}
            regionRows={a.regionRows}
            regionMode={a.regionMode && !a.simulado}
            selectedCode={a.selected}
            selectedRegionId={a.selectedRegionId}
            layerLabel={layerLabel}
            period={a.simulado ? "hipótese" : a.year}
            periods={a.simulado ? [] : a.yearOptions}
            statusLabel={a.simulado ? "SIMULADO" : a.rankMode === "delta" ? "DERIVADO" : a.activeIndicator?.status_label}
            higherIsWorse={a.higherIsWorse}
            loading={a.loading}
            onSelect={a.onSelect}
            onSelectRegion={a.onSelectRegion}
            legendLow={a.legendScale.low}
            legendHigh={a.legendScale.high}
            legendNote={a.legendScale.note}
            legendWorse={a.higherIsWorse}
            tip={a.simulado
              ? {
                  definition: a.simDisclaimer,
                  source: {
                    organization: "Brasil Real (motor hipotético)",
                    dataset: "hypothetical_federal_fund_v1",
                  },
                  reference_period: "hipótese",
                  status_label: "SIMULADO",
                  limitations: ["Não é transferência, orçamento nem gasto observado."],
                }
              : a.layerTip}
            recorteLabel={a.recorteCaption}
            rankMode={a.rankMode}
            comparePeriod={a.prevPeriod}
            compareCodes={a.compareCodes}
            onToggleCompare={a.toggleCompare}
          />
        </div>

        <div className="right-rail">
          <MapControlsBar
            layer={a.layer}
            year={a.year}
            yearOptions={a.yearOptions}
            indicatorGroups={a.indicatorGroups.map((g) => ({
              key: g.key,
              label: g.label,
              items: g.items.map((ind) => ({
                value: ind.id,
                label: ind.short_name || ind.name,
              })),
            }))}
            rankingGroups={a.rankingGroups}
            layerTip={a.layerTip}
            yearTip={a.yearTip}
            controlHint={copied ? "Link da vista copiado." : a.controlHint}
            loading={a.loading}
            onChangeLayer={(id) => {
              a.changeLayer(id);
              setFiltersOpen(false);
            }}
            onChangeYear={a.setYear}
            onFitBrazil={a.fitBrazil}
            onOpenDossier={() => setDossierOpen(true)}
            showInstallApp={pwaOffer}
            onInstallApp={() => window.dispatchEvent(new Event("br:pwa-install"))}
            recorte={a.recorte}
            onChangeRecorte={a.setRecorte}
            rankMode={a.rankMode}
            onChangeRankMode={a.setRankMode}
            canDelta={a.canDelta}
            sheet={filtersOpen}
            peekLabel={`${layerLabel} · ${a.simulado ? "SIMULADO" : formatPeriodLabel(a.year || "…")} · Filtros`}
            onToggleSheet={() => setFiltersOpen((v) => !v)}
            onOpenSearch={() => setSearchOpen(true)}
            onExportPng={exportPng}
            onCopyLink={() => void shareView()}
            simulado={a.simulado}
            onToggleSimulado={() => a.toggleSimulado(!a.simulado)}
            colorMode={a.colorMode}
            onChangeColorMode={a.setColorMode}
          />

          <CompareTray rows={a.compareObs} onSelect={a.onSelect} onRemove={a.toggleCompare} />

          {a.cardOpen && (
            <AtlasFloatCard
              layer={a.layer}
              onChangeLayer={a.changeLayer}
              onClose={a.closeCard}
              onSelectUf={a.onSelect}
              regionFiche={a.regionFiche}
              muniSelected={a.muniSelected}
              selectedObs={a.selectedObs}
              profile={a.profile}
              muniProfile={a.muniProfile}
              activeIndicator={a.activeIndicator}
              muniPopTip={a.muniPopTip}
              selectedObsTip={a.selectedObsTip}
              series={a.simulado ? [] : a.series}
              onPickPeriod={a.setYear}
            />
          )}
        </div>

        {a.atlasLive && a.error && (
          <div className="map-error" role="alert">
            {a.error}. API: {getApiUrl()}
          </div>
        )}

        <DataDossier
          open={dossierOpen}
          onClose={() => setDossierOpen(false)}
          rows={a.viewObs}
          indicator={a.activeIndicator}
          period={a.year}
          periods={a.yearOptions}
          recorte={a.recorte}
          rankMode={a.rankMode}
          comparePeriod={a.prevPeriod}
          regionRows={a.regionRows}
          regionMode={Boolean(a.regionMode && !a.simulado)}
        />

        <AtlasSearch
          open={searchOpen}
          indicators={a.indicators}
          ufs={a.displayObs}
          onClose={() => setSearchOpen(false)}
          onPickLayer={a.changeLayer}
          onPickUf={a.onSelect}
        />
      </div>

      <PwaDock ready={a.atlasLive} onOfferInstall={setPwaOffer} />
    </div>
  );
}
