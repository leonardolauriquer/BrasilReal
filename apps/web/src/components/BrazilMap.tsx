"use client";

import { useEffect, useMemo, useRef } from "react";
import maplibregl, { GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { addAtlasLayers, setMunicipalityMode } from "@/lib/map/layers";
import {
  paintCollection,
  toLabelPoints,
  type MunFeatureCollection,
} from "@/lib/map/paint";
import { buildRegionLabelPoints } from "@/lib/map/regions";
import { capitalsGeoJSON, isStateCapitalName } from "@/lib/map/capitals";
import { isIntermediateClickBand, ZOOM } from "@/lib/map/zoomLadder";
import { mapChromePadding } from "@/lib/map/chrome";
import { useI18n } from "@/lib/i18n/I18nProvider";
import { registerMapCanvas } from "@/lib/map/capture";
import { formatMapLabel } from "@/lib/format";

export type MapValue = {
  ibge_code: string;
  value: number;
  label?: string;
};

export { formatMapLabel };

/** Continental Brazil + a bit of ocean — “Brasil inteiro”. */
export const BRAZIL_BOUNDS: [[number, number], [number, number]] = [
  [-74.2, -34.2],
  [-28.5, 5.6],
];

type Props = {
  values: MapValue[];
  selectedCode?: string | null;
  selectedInterCode?: string | null;
  /** Fit map to these UF IBGE codes (e.g. macrorregião). */
  focusCodes?: string[] | null;
  /** Increment to reframe Brasil inteiro. */
  fitBrazilToken?: number;
  onSelect: (code: string) => void;
  onSelectMunicipality?: (payload: {
    ibge_code: string;
    name: string;
    value: number | null;
    uf_code: string;
  }) => void;
  onSelectIntermediate?: (payload: {
    ibge_code: string;
    name: string;
    uf: string;
    uf_code: string;
  }) => void;
  onZoomChange?: (zoom: number) => void;
  onReady?: () => void;
  municipalities?: MunFeatureCollection | null;
  showMunicipalities?: boolean;
  higherIsWorse?: boolean;
  colorMode?: "default" | "cb";
  valueUnit?: string;
  /** População por código IBGE (UF) para média ponderada / rótulos regionais. */
  popByIbge?: Map<string, number>;
  cardOpen?: boolean;
  compareCodes?: string[];
};

function collectBounds(
  features: MunFeatureCollection["features"],
): maplibregl.LngLatBounds | null {
  const bounds = new maplibregl.LngLatBounds();
  const walk = (coords: unknown): void => {
    if (!Array.isArray(coords)) return;
    if (typeof coords[0] === "number") bounds.extend(coords as [number, number]);
    else coords.forEach(walk);
  };
  for (const feature of features) {
    if (!feature.geometry) continue;
    const geom = feature.geometry as { type: string; coordinates: unknown };
    walk(geom.coordinates);
  }
  return bounds.isEmpty() ? null : bounds;
}

/**
 * Intermediate labels omit UF capitals — same name is owned by capital-place
 * (avoids "Cuiabá" / "Porto Velho" doubling).
 */
function enrichInterLabels(geo: MunFeatureCollection): MunFeatureCollection {
  const withoutCapitals = geo.features.filter(
    (f) => !isStateCapitalName(String(f.properties.name || "")),
  );
  const ranked = [...withoutCapitals].sort((a, b) =>
    String(a.properties.name || "").localeCompare(String(b.properties.name || ""), "pt-BR"),
  );
  const rankByCode = new Map<string, number>();
  ranked.forEach((f, i) => rankByCode.set(String(f.properties.ibge_code), i));

  return toLabelPoints({
    ...geo,
    features: withoutCapitals.map((f) => ({
      ...f,
      properties: {
        ...f.properties,
        place_name: String(f.properties.name || f.properties.ibge_code || ""),
        label_rank: rankByCode.get(String(f.properties.ibge_code)) ?? 999,
      },
    })),
  });
}

export function BrazilMap({
  values,
  selectedCode,
  selectedInterCode = null,
  focusCodes = null,
  fitBrazilToken = 0,
  onSelect,
  onSelectMunicipality,
  onSelectIntermediate,
  onZoomChange,
  onReady,
  municipalities = null,
  showMunicipalities = false,
  higherIsWorse = false,
  colorMode = "default",
  valueUnit,
  popByIbge,
  cardOpen = false,
  compareCodes = [],
}: Props) {
  const { t, locale } = useI18n();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const geoCacheRef = useRef<MunFeatureCollection | null>(null);
  const interCacheRef = useRef<MunFeatureCollection | null>(null);
  const readyOnceRef = useRef(false);
  const focusKeyRef = useRef<string>("");
  const fitBrazilSeenRef = useRef(0);
  const hoverInterRef = useRef<string | null>(null);
  const cardOpenRef = useRef(cardOpen);
  const onSelectRef = useRef(onSelect);
  const onMunRef = useRef(onSelectMunicipality);
  const onInterRef = useRef(onSelectIntermediate);
  const onZoomRef = useRef(onZoomChange);
  const onReadyRef = useRef(onReady);
  onSelectRef.current = onSelect;
  onMunRef.current = onSelectMunicipality;
  onInterRef.current = onSelectIntermediate;
  onZoomRef.current = onZoomChange;
  onReadyRef.current = onReady;
  cardOpenRef.current = cardOpen;

  const valueMap = useMemo(() => {
    const m = new Map<string, number>();
    for (const v of values) m.set(v.ibge_code, v.value);
    return m;
  }, [values]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      preserveDrawingBuffer: true,
      style: {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: {},
        layers: [
          {
            id: "background",
            type: "background",
            paint: { "background-color": "#7f9b94" },
          },
        ],
      },
      center: [-52.2, -14.5],
      zoom: ZOOM.start,
      minZoom: ZOOM.min,
      maxZoom: ZOOM.max,
      attributionControl: { compact: true },
    });

    const applyChromePadding = () => {
      map.setPadding(mapChromePadding(cardOpenRef.current));
    };
    applyChromePadding();
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

    const resize = () => {
      applyChromePadding();
      (map as unknown as { resize: () => void }).resize();
    };
    window.addEventListener("resize", resize);
    const ro =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => map.resize())
        : null;
    if (containerRef.current && ro) ro.observe(containerRef.current);

    map.on("load", async () => {
      map.resize();
      try {
        const [geo, macros, inter] = await Promise.all([
          fetch("/geo/uf_br.geojson").then((r) => {
            if (!r.ok) throw new Error(`uf geo ${r.status}`);
            return r.json();
          }),
          fetch("/geo/macro_br.geojson").then((r) => {
            if (!r.ok) throw new Error(`macro geo ${r.status}`);
            return r.json();
          }),
          fetch("/geo/inter_br.geojson").then((r) => {
            if (!r.ok) throw new Error(`inter geo ${r.status}`);
            return r.json();
          }),
        ]);
        geoCacheRef.current = geo;
        interCacheRef.current = inter;

        map.addSource("ufs", { type: "geojson", data: geo });
        map.addSource("macros", { type: "geojson", data: macros });
        map.addSource("inter", {
          type: "geojson",
          data: inter,
          promoteId: "ibge_code",
        });
        map.addSource("uf-labels", {
          type: "geojson",
          data: { type: "FeatureCollection", features: [] },
        });
        map.addSource("region-labels", {
          type: "geojson",
          data: { type: "FeatureCollection", features: [] },
        });
        map.addSource("inter-labels", {
          type: "geojson",
          data: enrichInterLabels(inter),
        });
        map.addSource("capitals", { type: "geojson", data: capitalsGeoJSON() });
        map.addSource("mun", {
          type: "geojson",
          data: { type: "FeatureCollection", features: [] },
        });
        map.addSource("mun-labels", {
          type: "geojson",
          data: { type: "FeatureCollection", features: [] },
        });

        addAtlasLayers(map);
      } catch (err) {
        console.error("Brasil Real: falha ao carregar malhas", err);
        // Still unlock boot — chrome can show error from parent if needed.
        if (!readyOnceRef.current) {
          readyOnceRef.current = true;
          onReadyRef.current?.();
        }
        return;
      }

      map.on("click", "uf-fill", (e) => {
        if (map.getLayoutProperty("mun-fill", "visibility") === "visible") return;
        // Intermediate clicks are owned by inter-fill only (avoids double fire).
        if (isIntermediateClickBand(map.getZoom())) return;
        const code = e.features?.[0]?.properties?.ibge_code;
        if (code) onSelectRef.current(String(code));
      });
      map.on("click", "inter-fill", (e) => {
        if (!isIntermediateClickBand(map.getZoom())) return;
        const p = e.features?.[0]?.properties;
        if (!p?.ibge_code) return;
        onInterRef.current?.({
          ibge_code: String(p.ibge_code),
          name: String(p.name || p.ibge_code),
          uf: String(p.uf || ""),
          uf_code: String(p.uf_code || ""),
        });
      });
      map.on("click", "mun-fill", (e) => {
        const f = e.features?.[0]?.properties;
        if (!f) return;
        const raw = f.value;
        let value: number | null = null;
        if (typeof raw === "number" && Number.isFinite(raw)) value = raw;
        else if (raw != null && raw !== "") {
          const n = Number(raw);
          if (Number.isFinite(n)) value = n;
        }
        onMunRef.current?.({
          ibge_code: String(f.ibge_code),
          name: String(f.name || f.ibge_code),
          value,
          uf_code: String(f.uf_code || ""),
        });
      });

      const setCursor = (on: boolean) => {
        map.getCanvas().style.cursor = on ? "pointer" : "";
      };
      map.on("mouseenter", "uf-fill", () => setCursor(true));
      map.on("mouseleave", "uf-fill", () => setCursor(false));
      map.on("mouseenter", "inter-fill", () => setCursor(true));
      map.on("mouseleave", "inter-fill", () => {
        setCursor(false);
        if (hoverInterRef.current != null) {
          map.setFeatureState(
            { source: "inter", id: hoverInterRef.current },
            { hover: false },
          );
          hoverInterRef.current = null;
        }
      });
      map.on("mousemove", "inter-fill", (e) => {
        const f = e.features?.[0];
        const id = f?.id != null ? String(f.id) : f?.properties?.ibge_code;
        if (id == null) return;
        if (hoverInterRef.current === String(id)) return;
        if (hoverInterRef.current != null) {
          map.setFeatureState(
            { source: "inter", id: hoverInterRef.current },
            { hover: false },
          );
        }
        hoverInterRef.current = String(id);
        map.setFeatureState({ source: "inter", id: String(id) }, { hover: true });
      });
      map.on("mouseenter", "mun-fill", () => setCursor(true));
      map.on("mouseleave", "mun-fill", () => setCursor(false));
      map.on("zoom", () => onZoomRef.current?.(map.getZoom()));
      map.fire("br:source-ready");
      onZoomRef.current?.(map.getZoom());
      requestAnimationFrame(() => map.resize());
      // Unlock boot even before choropleth values arrive.
      map.once("idle", () => {
        if (readyOnceRef.current) return;
        readyOnceRef.current = true;
        onReadyRef.current?.();
      });
    });

    mapRef.current = map;
    registerMapCanvas(() => map.getCanvas());
    return () => {
      window.removeEventListener("resize", resize);
      ro?.disconnect();
      registerMapCanvas(null);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.setPadding(mapChromePadding(cardOpen));
  }, [cardOpen]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const paint = () => {
      const source = map.getSource("ufs") as GeoJSONSource | undefined;
      const labels = map.getSource("uf-labels") as GeoJSONSource | undefined;
      const regions = map.getSource("region-labels") as GeoJSONSource | undefined;
      if (!source || !geoCacheRef.current) return;
      const painted = paintCollection(
        geoCacheRef.current,
        valueMap,
        higherIsWorse,
        valueUnit,
        "uf",
        colorMode,
      );
      source.setData(painted);
      labels?.setData(toLabelPoints(painted));
      regions?.setData(buildRegionLabelPoints(painted, valueMap, valueUnit, popByIbge));
      if (map.getLayer("uf-fill")) {
        map.setPaintProperty("uf-fill", "fill-color", ["get", "fill"]);
      }
    };
    void paint();
    map.on("br:source-ready", paint);
    return () => {
      map.off("br:source-ready", paint);
    };
  }, [valueMap, higherIsWorse, valueUnit, popByIbge, colorMode, locale]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("uf-selected")) return;
    const codes = [...new Set([selectedCode, ...compareCodes].filter((c): c is string => Boolean(c)))];
    const filter =
      codes.length === 0
        ? ["==", ["get", "ibge_code"], ""]
        : codes.length === 1
          ? ["==", ["get", "ibge_code"], codes[0]]
          : ["in", ["get", "ibge_code"], ["literal", codes]];
    map.setFilter("uf-selected", filter as never);
    map.setFilter("uf-selected-outer", filter as never);
  }, [selectedCode, compareCodes]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("inter-selected")) return;
    map.setFilter("inter-selected", ["==", ["get", "ibge_code"], selectedInterCode || ""]);
  }, [selectedInterCode]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getSource("mun")) return;
    const munSource = map.getSource("mun") as GeoJSONSource;
    const visible = Boolean(showMunicipalities && municipalities?.features?.length);
    const munLabels = map.getSource("mun-labels") as GeoJSONSource | undefined;
    if (visible && municipalities) {
      const munValues = new Map<string, number>();
      for (const f of municipalities.features) {
        const code = String(f.properties.ibge_code || "");
        const val = f.properties.value;
        if (code && typeof val === "number") munValues.set(code, val);
      }
      const painted = paintCollection(
        municipalities,
        munValues,
        false,
        "habitantes",
        "mun",
        colorMode,
      );
      munSource.setData(painted);
      munLabels?.setData(toLabelPoints(painted));
      setMunicipalityMode(map, true);
    } else {
      munSource.setData({ type: "FeatureCollection", features: [] });
      munLabels?.setData({ type: "FeatureCollection", features: [] });
      setMunicipalityMode(map, false);
    }
  }, [municipalities, showMunicipalities, colorMode, locale]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedCode || !geoCacheRef.current) return;
    if (focusCodes?.length) return;
    const feature = geoCacheRef.current.features.find(
      (f) => String(f.properties.ibge_code) === selectedCode,
    );
    if (!feature) return;
    const bounds = collectBounds([feature]);
    if (!bounds) return;
    map.fitBounds(bounds, {
      maxZoom: 6.2,
      duration: 900,
    });
  }, [selectedCode, focusCodes]);

  useEffect(() => {
    const map = mapRef.current;
    if (!focusCodes?.length) {
      focusKeyRef.current = "";
      return;
    }
    if (!map || !geoCacheRef.current) return;
    const key = focusCodes.slice().sort().join(",");
    if (key === focusKeyRef.current) return;
    focusKeyRef.current = key;
    const set = new Set(focusCodes);
    const feats = geoCacheRef.current.features.filter((f) =>
      set.has(String(f.properties.ibge_code)),
    );
    const bounds = collectBounds(feats);
    if (!bounds) return;
    map.fitBounds(bounds, {
      maxZoom: 5.2,
      duration: 1000,
    });
  }, [focusCodes]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !fitBrazilToken || fitBrazilToken === fitBrazilSeenRef.current) return;
    fitBrazilSeenRef.current = fitBrazilToken;
    map.fitBounds(BRAZIL_BOUNDS, {
      duration: 900,
      maxZoom: 3.5,
    });
  }, [fitBrazilToken]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedInterCode || !interCacheRef.current) return;
    const feature = interCacheRef.current.features.find(
      (f) => String(f.properties.ibge_code) === selectedInterCode,
    );
    if (!feature) return;
    const bounds = collectBounds([feature]);
    if (!bounds) return;
    map.fitBounds(bounds, {
      maxZoom: 6.4,
      duration: 900,
    });
  }, [selectedInterCode]);

  return (
    <div className="map-root" ref={containerRef} role="img" aria-label={t("map.aria")} />
  );
}
