"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { AtlasFloatCard } from "@/components/AtlasFloatCard";
import { BootScreen } from "@/components/BootScreen";
import { BrandMark } from "@/components/BrandMark";
import { DataDossier } from "@/components/DataDossier";
import { MapControlsBar } from "@/components/MapControlsBar";
import { PwaDock } from "@/components/PwaDock";
import { RankPanel } from "@/components/RankPanel";
import { useAtlasState } from "@/lib/atlas/useAtlasState";
import { getApiUrl } from "@/lib/api";

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

  return (
    <div className="app-shell">
      {a.bootVisible && (
        <BootScreen
          stages={a.bootStages}
          error={a.error && !a.bootReady ? a.error : null}
          exiting={a.bootExiting}
          onExitComplete={() => a.setBootVisible(false)}
        />
      )}

      <div
        className={`atlas ${a.atlasLive ? "atlas--live" : "atlas--booting"}`}
        aria-hidden={!a.atlasLive}
      >
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
          valueUnit={a.activeIndicator?.unit}
          popByIbge={a.popByIbge}
          cardOpen={a.cardOpen}
        />
        <div className="map-veil" aria-hidden="true" />

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
            rows={a.viewObs}
            regionRows={a.regionRows}
            regionMode={a.regionMode}
            selectedCode={a.selected}
            selectedRegionId={a.selectedRegionId}
            layerLabel={a.activeIndicator?.short_name || a.activeIndicator?.name || "Camada"}
            period={a.year}
            periods={a.yearOptions}
            statusLabel={a.rankMode === "delta" ? "DERIVADO" : a.activeIndicator?.status_label}
            higherIsWorse={a.higherIsWorse}
            loading={a.loading}
            onSelect={a.onSelect}
            onSelectRegion={a.onSelectRegion}
            legendLow={a.legendScale.low}
            legendHigh={a.legendScale.high}
            legendNote={a.legendScale.note}
            legendWorse={a.higherIsWorse}
            tip={a.layerTip}
            recorteLabel={a.recorteCaption}
            rankMode={a.rankMode}
            comparePeriod={a.prevPeriod}
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
            controlHint={a.controlHint}
            loading={a.loading}
            onChangeLayer={a.changeLayer}
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
          />

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
          regionMode={a.regionMode}
        />
      </div>

      <PwaDock ready={a.atlasLive} onOfferInstall={setPwaOffer} />
    </div>
  );
}
