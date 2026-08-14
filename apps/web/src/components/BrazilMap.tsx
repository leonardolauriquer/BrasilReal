"use client";

import { useEffect, useMemo, useRef } from "react";
import maplibregl, { GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export type MapValue = {
  ibge_code: string;
  value: number;
  label?: string;
};

type MunFeatureCollection = {
  type: "FeatureCollection";
  features: Array<{
    type: string;
    properties: Record<string, string | number | null>;
    geometry: unknown;
  }>;
};

type Props = {
  values: MapValue[];
  selectedCode?: string | null;
  onSelect: (code: string) => void;
  onSelectMunicipality?: (payload: {
    ibge_code: string;
    name: string;
    value: number | null;
    uf_code: string;
  }) => void;
  onZoomChange?: (zoom: number) => void;
  municipalities?: MunFeatureCollection | null;
  showMunicipalities?: boolean;
  higherIsWorse?: boolean;
  /** Unit of the active layer — drives in-map labels (% , BRL, etc.). */
  valueUnit?: string;
};

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function colorScale(t: number, higherIsWorse = false) {
  const x = Math.max(0, Math.min(1, Math.pow(t, 0.85)));
  if (higherIsWorse) {
    // Low (better) → cool mist; high (worse) → warm alert
    const r = Math.round(lerp(210, 176, x));
    const g = Math.round(lerp(230, 78, x));
    const b = Math.round(lerp(220, 58, x));
    return `rgb(${r},${g},${b})`;
  }
  // Low → pale mist; high → deep teal (more = stronger signal)
  const r = Math.round(lerp(214, 18, x));
  const g = Math.round(lerp(232, 110, x));
  const b = Math.round(lerp(224, 118, x));
  return `rgb(${r},${g},${b})`;
}

export function formatMapLabel(value: number, unit?: string): string {
  if (!Number.isFinite(value)) return "—";
  if (unit === "%") {
    return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
  }
  if (unit === "BRL") {
    const abs = Math.abs(value);
    if (abs >= 1e12) {
      return `R$ ${(value / 1e12).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} tri`;
    }
    if (abs >= 1e9) {
      return `R$ ${(value / 1e9).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} bi`;
    }
    if (abs >= 1e6) {
      return `R$ ${(value / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 0 })} mi`;
    }
    return `R$ ${value.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}`;
  }
  if (unit === "USD") {
    const abs = Math.abs(value);
    if (abs >= 1e9) {
      return `US$ ${(value / 1e9).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} bi`;
    }
    if (abs >= 1e6) {
      return `US$ ${(value / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 0 })} mi`;
    }
    return `US$ ${value.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}`;
  }
  if (unit === "por 100 mil hab") {
    return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}/100k`;
  }
  if (unit === "homicídios") {
    if (Math.abs(value) >= 1e3) {
      return `${(value / 1e3).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mil`;
    }
  }
  if (unit === "habitantes" || unit === "pessoas") {
    if (Math.abs(value) >= 1e6) {
      return `${(value / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mi`;
    }
    if (Math.abs(value) >= 1e3) {
      return `${(value / 1e3).toLocaleString("pt-BR", { maximumFractionDigits: 0 })} mil`;
    }
  }
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

function paintCollection(
  geo: MunFeatureCollection,
  valueMap: Map<string, number>,
  higherIsWorse: boolean,
  unit?: string,
) {
  const nums = [...valueMap.values()];
  const min = nums.length ? Math.min(...nums) : 0;
  const max = nums.length ? Math.max(...nums) : 1;
  const span = max - min || 1;
  const total = nums.reduce((a, b) => a + b, 0);
  const showShare = Boolean(
    total > 0 && unit && unit !== "%" && unit !== "por 100 mil hab" && !unit?.startsWith("por "),
  );

  return {
    ...geo,
    features: geo.features.map((f) => {
      const code = String(f.properties.ibge_code || f.properties.codarea || "");
      const raw = f.properties.value;
      const hasValue = valueMap.has(code) || typeof raw === "number";
      const value =
        typeof raw === "number"
          ? raw
          : valueMap.has(code)
            ? (valueMap.get(code) as number)
            : min;
      const t = hasValue ? (value - min) / span : 0;
      const uf = String(f.properties.uf || "");
      const nameShort = uf || String(f.properties.name || "").slice(0, 12);
      let label = "SEM DADO";
      let labelStack = nameShort;
      let labelCompact = nameShort;
      if (hasValue) {
        if (unit === "%") {
          label = formatMapLabel(value, unit);
          labelStack = `${nameShort}\n${label}`;
          labelCompact = `${nameShort}\n${label}`;
        } else if (showShare) {
          const share = (value / total) * 100;
          label = formatMapLabel(value, unit);
          const shareTxt = `${share.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
          labelStack = `${nameShort}\n${label}\n${shareTxt}`;
          labelCompact = `${nameShort}\n${shareTxt}`;
        } else {
          label = formatMapLabel(value, unit);
          labelStack = `${nameShort}\n${label}`;
          labelCompact = labelStack;
        }
      }
      return {
        ...f,
        properties: {
          ...f.properties,
          ibge_code: code,
          fill: hasValue ? colorScale(t, higherIsWorse) : "#c5d4cf",
          value: hasValue ? value : null,
          label,
          label_stack: labelStack,
          label_compact: labelCompact,
        },
      };
    }),
  };
}

export function BrazilMap({
  values,
  selectedCode,
  onSelect,
  onSelectMunicipality,
  onZoomChange,
  municipalities = null,
  showMunicipalities = false,
  higherIsWorse = false,
  valueUnit,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const geoCacheRef = useRef<MunFeatureCollection | null>(null);
  const onSelectRef = useRef(onSelect);
  const onMunRef = useRef(onSelectMunicipality);
  const onZoomRef = useRef(onZoomChange);
  onSelectRef.current = onSelect;
  onMunRef.current = onSelectMunicipality;
  onZoomRef.current = onZoomChange;

  const valueMap = useMemo(() => {
    const m = new Map<string, number>();
    for (const v of values) m.set(v.ibge_code, v.value);
    return m;
  }, [values]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
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
      center: [-52.2, -15.2],
      zoom: 3.7,
      minZoom: 3.2,
      maxZoom: 10,
      attributionControl: { compact: true },
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

    const resize = () => map.resize();
    window.addEventListener("resize", resize);
    const ro =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => map.resize())
        : null;
    if (containerRef.current && ro) ro.observe(containerRef.current);

    map.on("load", async () => {
      map.resize();
      const geo = await fetch("/geo/uf_br.geojson").then((r) => r.json());
      geoCacheRef.current = geo;
      map.addSource("ufs", { type: "geojson", data: geo });
      map.addSource("mun", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      map.addLayer({
        id: "uf-fill",
        type: "fill",
        source: "ufs",
        paint: { "fill-color": "#c5d4cf", "fill-opacity": 0.96 },
      });
      map.addLayer({
        id: "uf-outline",
        type: "line",
        source: "ufs",
        paint: {
          "line-color": "#0e1713",
          "line-width": 0.8,
          "line-opacity": 0.45,
        },
      });
      map.addLayer({
        id: "uf-selected-outer",
        type: "line",
        source: "ufs",
        paint: { "line-color": "#3dcf9a", "line-width": 5, "line-opacity": 0.45 },
        filter: ["==", ["get", "ibge_code"], ""],
      });
      map.addLayer({
        id: "uf-selected",
        type: "line",
        source: "ufs",
        paint: { "line-color": "#eef5f1", "line-width": 2.4, "line-opacity": 0.95 },
        filter: ["==", ["get", "ibge_code"], ""],
      });
      map.addLayer({
        id: "uf-label",
        type: "symbol",
        source: "ufs",
        layout: {
          "text-field": [
            "step",
            ["zoom"],
            ["get", "label_compact"],
            4.8,
            ["get", "label_stack"],
          ],
          "text-font": ["Open Sans Bold", "Open Sans Regular"],
          "text-size": [
            "interpolate",
            ["linear"],
            ["zoom"],
            3.2,
            9,
            4.5,
            11,
            6,
            13,
          ],
          "text-line-height": 1.05,
          "text-anchor": "center",
          "text-allow-overlap": false,
          "text-ignore-placement": false,
          "text-padding": 4,
          "text-max-width": 7,
          "symbol-sort-key": ["-", ["to-number", ["get", "value"], 0]],
        },
        paint: {
          "text-color": "#0e1713",
          "text-halo-color": "rgba(238, 245, 241, 0.92)",
          "text-halo-width": 1.15,
          "text-halo-blur": 0.2,
        },
      });

      map.addLayer({
        id: "mun-fill",
        type: "fill",
        source: "mun",
        layout: { visibility: "none" },
        paint: { "fill-color": ["get", "fill"], "fill-opacity": 0.92 },
      });
      map.addLayer({
        id: "mun-outline",
        type: "line",
        source: "mun",
        layout: { visibility: "none" },
        paint: {
          "line-color": "#0e1713",
          "line-width": 0.35,
          "line-opacity": 0.35,
        },
      });
      map.addLayer({
        id: "mun-label",
        type: "symbol",
        source: "mun",
        layout: {
          visibility: "none",
          "text-field": ["get", "label"],
          "text-font": ["Open Sans Regular", "Open Sans Bold"],
          "text-size": ["interpolate", ["linear"], ["zoom"], 5.5, 8, 8, 11],
          "text-allow-overlap": false,
          "text-padding": 1,
        },
        paint: {
          "text-color": "#0e1713",
          "text-halo-color": "rgba(238, 245, 241, 0.85)",
          "text-halo-width": 1.1,
        },
      });

      map.on("click", "uf-fill", (e) => {
        if (map.getLayoutProperty("mun-fill", "visibility") === "visible") return;
        const code = e.features?.[0]?.properties?.ibge_code;
        if (code) onSelectRef.current(String(code));
      });
      map.on("click", "mun-fill", (e) => {
        const f = e.features?.[0]?.properties;
        if (!f) return;
        onMunRef.current?.({
          ibge_code: String(f.ibge_code),
          name: String(f.name || f.ibge_code),
          value: typeof f.value === "number" ? f.value : Number(f.value) || null,
          uf_code: String(f.uf_code || ""),
        });
      });
      map.on("mouseenter", "uf-fill", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "uf-fill", () => {
        map.getCanvas().style.cursor = "";
      });
      map.on("mouseenter", "mun-fill", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "mun-fill", () => {
        map.getCanvas().style.cursor = "";
      });
      map.on("zoom", () => onZoomRef.current?.(map.getZoom()));
      map.fire("br:source-ready");
      onZoomRef.current?.(map.getZoom());
      requestAnimationFrame(() => map.resize());
    });

    mapRef.current = map;
    return () => {
      window.removeEventListener("resize", resize);
      ro?.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const paint = () => {
      const source = map.getSource("ufs") as GeoJSONSource | undefined;
      if (!source || !geoCacheRef.current) return;
      source.setData(
        paintCollection(geoCacheRef.current, valueMap, higherIsWorse, valueUnit),
      );
      if (map.getLayer("uf-fill")) {
        map.setPaintProperty("uf-fill", "fill-color", ["get", "fill"]);
      }
    };
    void paint();
    map.on("br:source-ready", paint);
    return () => {
      map.off("br:source-ready", paint);
    };
  }, [valueMap, higherIsWorse, valueUnit]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("uf-selected")) return;
    const filter = ["==", ["get", "ibge_code"], selectedCode || ""];
    map.setFilter("uf-selected", filter);
    map.setFilter("uf-selected-outer", filter);
  }, [selectedCode]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getSource("mun")) return;
    const munSource = map.getSource("mun") as GeoJSONSource;
    const visible = Boolean(showMunicipalities && municipalities?.features?.length);
    if (visible && municipalities) {
      const munValues = new Map<string, number>();
      for (const f of municipalities.features) {
        const code = String(f.properties.ibge_code || "");
        const val = f.properties.value;
        if (code && typeof val === "number") munValues.set(code, val);
      }
      munSource.setData(
        paintCollection(municipalities, munValues, false, "habitantes"),
      );
      map.setLayoutProperty("mun-fill", "visibility", "visible");
      map.setLayoutProperty("mun-outline", "visibility", "visible");
      map.setLayoutProperty("mun-label", "visibility", "visible");
      map.setLayoutProperty("uf-label", "visibility", "none");
      map.setPaintProperty("uf-fill", "fill-opacity", 0.14);
      map.setPaintProperty("uf-outline", "line-opacity", 0.75);
      map.setPaintProperty("uf-outline", "line-width", 1.4);
    } else {
      munSource.setData({ type: "FeatureCollection", features: [] });
      map.setLayoutProperty("mun-fill", "visibility", "none");
      map.setLayoutProperty("mun-outline", "visibility", "none");
      if (map.getLayer("mun-label")) {
        map.setLayoutProperty("mun-label", "visibility", "none");
      }
      if (map.getLayer("uf-label")) {
        map.setLayoutProperty("uf-label", "visibility", "visible");
      }
      map.setPaintProperty("uf-fill", "fill-opacity", 0.97);
      map.setPaintProperty("uf-outline", "line-opacity", 0.45);
      map.setPaintProperty("uf-outline", "line-width", 0.8);
    }
  }, [municipalities, showMunicipalities]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedCode || !geoCacheRef.current) return;
    const feature = geoCacheRef.current.features.find(
      (f) => String(f.properties.ibge_code) === selectedCode,
    );
    if (!feature || !feature.geometry) return;
    const bounds = new maplibregl.LngLatBounds();
    const geom = feature.geometry as { type: string; coordinates: any };
    const walk = (coords: any): void => {
      if (typeof coords[0] === "number") bounds.extend(coords as [number, number]);
      else coords.forEach(walk);
    };
    walk(geom.coordinates);
    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, {
        padding: { top: 72, bottom: 72, left: 72, right: 360 },
        maxZoom: 6.2,
        duration: 900,
      });
    }
  }, [selectedCode]);

  return (
    <div className="map-root" ref={containerRef} role="img" aria-label="Mapa do Brasil" />
  );
}
