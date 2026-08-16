/** MapLibre layer definitions for Brazil atlas. */

import type maplibregl from "maplibre-gl";
import {
  CAPITAL_MAX_ZOOM,
  CAPITAL_MIN_ZOOM,
  INTER_LABEL_MAX_ZOOM,
  INTER_LABEL_MIN_ZOOM,
  MUNI_ZOOM,
  REGION_LABEL_MAX_ZOOM,
  UF_LABEL_FADE_IN,
} from "@/lib/map/zoomLadder";

export {
  CAPITAL_MAX_ZOOM,
  CAPITAL_MIN_ZOOM,
  INTER_LABEL_MAX_ZOOM,
  INTER_LABEL_MIN_ZOOM,
  REGION_LABEL_MAX_ZOOM,
  UF_LABEL_FADE_IN,
} from "@/lib/map/zoomLadder";

/**
 * Fonts that actually exist on demotiles.maplibre.org.
 * "Open Sans Bold/Regular" 404 → labels silently vanish.
 */
export const ATLAS_FONT_BOLD = ["Noto Sans Bold"] as const;
export const ATLAS_FONT_REGULAR = ["Noto Sans Regular"] as const;

export function setLayerVisibility(map: maplibregl.Map, id: string, visible: boolean) {
  if (!map.getLayer(id)) return;
  map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
}

/** Add fill/outline/selection + progressive place/metric symbol layers. */
export function addAtlasLayers(map: maplibregl.Map) {
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
      "line-width": ["interpolate", ["linear"], ["zoom"], 2.6, 0.35, 4.2, 0.7, 6, 1.0],
      "line-opacity": ["interpolate", ["linear"], ["zoom"], 2.6, 0.22, 3.8, 0.4, 6, 0.5],
    },
  });

  // Dissolved IBGE macrorregião outline (stronger regional reading).
  map.addLayer({
    id: "macro-outline",
    type: "line",
    source: "macros",
    paint: {
      "line-color": "#06110d",
      "line-width": ["interpolate", ["linear"], ["zoom"], 2.6, 2.2, 4.0, 2.8, 6.0, 1.6],
      "line-opacity": ["interpolate", ["linear"], ["zoom"], 2.6, 0.85, 4.2, 0.7, 6.5, 0.35],
    },
  });

  // Intermediate regions — soft mesh between macro and UF detail.
  map.addLayer({
    id: "inter-fill",
    type: "fill",
    source: "inter",
    minzoom: INTER_LABEL_MIN_ZOOM,
    maxzoom: INTER_LABEL_MAX_ZOOM,
    paint: {
      "fill-color": "#ffffff",
      "fill-opacity": [
        "case",
        ["boolean", ["feature-state", "hover"], false],
        0.12,
        0.02,
      ],
    },
  });
  map.addLayer({
    id: "inter-outline",
    type: "line",
    source: "inter",
    minzoom: INTER_LABEL_MIN_ZOOM,
    maxzoom: INTER_LABEL_MAX_ZOOM,
    paint: {
      "line-color": "#0e1713",
      "line-width": 0.55,
      "line-opacity": [
        "interpolate",
        ["linear"],
        ["zoom"],
        INTER_LABEL_MIN_ZOOM,
        0.15,
        4.5,
        0.4,
        INTER_LABEL_MAX_ZOOM,
        0.2,
      ],
    },
  });
  map.addLayer({
    id: "inter-selected",
    type: "line",
    source: "inter",
    paint: { "line-color": "#3dcf9a", "line-width": 2.2, "line-opacity": 0.9 },
    filter: ["==", ["get", "ibge_code"], ""],
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
    id: "region-place",
    type: "symbol",
    source: "region-labels",
    maxzoom: REGION_LABEL_MAX_ZOOM,
    layout: {
      "text-field": ["get", "label_stack"],
      "text-font": [...ATLAS_FONT_BOLD],
      "text-size": ["interpolate", ["linear"], ["zoom"], 2.6, 15, 3.4, 17.5, 4.0, 15],
      "text-letter-spacing": 0.06,
      "text-line-height": 1.12,
      "text-transform": "uppercase",
      "text-anchor": "center",
      "text-justify": "center",
      "text-max-width": 10,
      "text-padding": 2,
      "text-allow-overlap": true,
      "text-ignore-placement": true,
      "symbol-placement": "point",
      "symbol-sort-key": ["to-number", ["get", "label_rank"], 99],
    },
    paint: {
      "text-color": "#f7fbf9",
      "text-halo-color": "rgba(8, 14, 12, 0.92)",
      "text-halo-width": 2.1,
      "text-halo-blur": 0.15,
      "text-opacity": [
        "interpolate",
        ["linear"],
        ["zoom"],
        2.6,
        1,
        3.6,
        1,
        REGION_LABEL_MAX_ZOOM,
        0,
      ],
    },
  });

  map.addLayer({
    id: "inter-place",
    type: "symbol",
    source: "inter-labels",
    minzoom: INTER_LABEL_MIN_ZOOM,
    maxzoom: INTER_LABEL_MAX_ZOOM,
    layout: {
      "text-field": ["get", "place_name"],
      "text-font": [...ATLAS_FONT_REGULAR],
      "text-size": ["interpolate", ["linear"], ["zoom"], 3.9, 10, 4.6, 11.5, 5.2, 12.5],
      "text-anchor": "center",
      "text-justify": "center",
      "text-max-width": 8,
      "text-padding": 2,
      "text-allow-overlap": false,
      "symbol-sort-key": ["to-number", ["get", "label_rank"], 999],
    },
    paint: {
      "text-color": "rgba(244, 250, 247, 0.92)",
      "text-halo-color": "rgba(10, 16, 14, 0.82)",
      "text-halo-width": 1.35,
      "text-opacity": [
        "interpolate",
        ["linear"],
        ["zoom"],
        INTER_LABEL_MIN_ZOOM,
        0,
        4.2,
        0.95,
        5.0,
        0.85,
        INTER_LABEL_MAX_ZOOM,
        0,
      ],
    },
    filter: [
      "<=",
      ["to-number", ["get", "label_rank"], 999],
      ["interpolate", ["linear"], ["zoom"], 3.9, 18, 4.4, 40, 4.9, 80, 5.3, 133],
    ],
  });

  map.addLayer({
    id: "uf-place",
    type: "symbol",
    source: "uf-labels",
    minzoom: UF_LABEL_FADE_IN,
    layout: {
      "text-field": [
        "step",
        ["zoom"],
        ["get", "label_stack_compact"],
        4.5,
        ["get", "label_stack_full"],
      ],
      "text-font": [...ATLAS_FONT_BOLD],
      "text-size": ["interpolate", ["linear"], ["zoom"], 3.6, 11, 4.6, 13.5, 6.5, 16],
      "text-letter-spacing": 0.02,
      "text-line-height": 1.15,
      "text-anchor": "center",
      "text-justify": "center",
      "text-max-width": 9,
      "text-padding": 0,
      "text-allow-overlap": true,
      "text-ignore-placement": true,
      "symbol-placement": "point",
      "symbol-sort-key": ["to-number", ["get", "label_rank"], 99],
      "symbol-z-order": "source",
    },
    paint: {
      "text-color": "#f4faf7",
      "text-halo-color": "rgba(10, 16, 14, 0.88)",
      "text-halo-width": 1.75,
      "text-halo-blur": 0.2,
      "text-opacity": [
        "interpolate",
        ["linear"],
        ["zoom"],
        UF_LABEL_FADE_IN,
        0,
        3.95,
        0.55,
        4.5,
        1,
        11,
        1,
      ],
    },
  });

  map.addLayer({
    id: "capital-place",
    type: "symbol",
    source: "capitals",
    minzoom: CAPITAL_MIN_ZOOM,
    maxzoom: CAPITAL_MAX_ZOOM,
    layout: {
      "text-field": ["get", "place_name"],
      "text-font": [...ATLAS_FONT_BOLD],
      "text-size": [
        "interpolate",
        ["linear"],
        ["zoom"],
        CAPITAL_MIN_ZOOM,
        10.5,
        5.5,
        12.5,
        6.4,
        13.5,
      ],
      "text-offset": [0, 1.05],
      "text-anchor": "top",
      "text-allow-overlap": false,
      "text-optional": true,
      "icon-allow-overlap": true,
      "symbol-sort-key": ["to-number", ["get", "label_rank"], 99],
    },
    paint: {
      "text-color": "#dff7ea",
      "text-halo-color": "rgba(8, 14, 12, 0.9)",
      "text-halo-width": 1.5,
      "text-opacity": [
        "interpolate",
        ["linear"],
        ["zoom"],
        CAPITAL_MIN_ZOOM,
        0.15,
        4.35,
        0.95,
        6.2,
        0.85,
        CAPITAL_MAX_ZOOM,
        0,
      ],
    },
  });
  map.addLayer({
    id: "capital-dot",
    type: "circle",
    source: "capitals",
    minzoom: CAPITAL_MIN_ZOOM,
    maxzoom: CAPITAL_MAX_ZOOM,
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 4.4, 2.2, 6, 3.2],
      "circle-color": "#e8fff4",
      "circle-stroke-color": "#0e1713",
      "circle-stroke-width": 1,
      "circle-opacity": 0.9,
    },
  });

  map.addLayer({
    id: "uf-metric",
    type: "symbol",
    source: "uf-labels",
    layout: {
      visibility: "none",
      "text-field": ["get", "metric_text"],
      "text-font": [...ATLAS_FONT_REGULAR],
      "text-size": 10,
    },
    paint: { "text-opacity": 0 },
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
    id: "mun-place",
    type: "symbol",
    source: "mun-labels",
    layout: {
      visibility: "none",
      "text-field": [
        "step",
        ["zoom"],
        ["get", "place_name"],
        7.2,
        ["get", "label_stack_full"],
      ],
      "text-font": [...ATLAS_FONT_BOLD],
      "text-size": ["interpolate", ["linear"], ["zoom"], MUNI_ZOOM, 10.5, 7, 12.5, 9, 14.5],
      "text-line-height": 1.12,
      "text-anchor": "center",
      "text-justify": "center",
      "text-max-width": 8,
      "text-padding": 1,
      "text-allow-overlap": false,
      "text-optional": false,
      "symbol-sort-key": ["to-number", ["get", "label_rank"], 999],
    },
    paint: {
      "text-color": "#f4faf7",
      "text-halo-color": "rgba(10, 16, 14, 0.9)",
      "text-halo-width": 1.55,
    },
    filter: [
      "<=",
      ["to-number", ["get", "label_rank"], 999],
      ["interpolate", ["linear"], ["zoom"], MUNI_ZOOM, 24, 6.2, 55, 7.0, 140, 8.0, 280, 9.0, 600],
    ],
  });

  map.addLayer({
    id: "mun-metric",
    type: "symbol",
    source: "mun-labels",
    layout: { visibility: "none", "text-field": "" },
    paint: { "text-opacity": 0 },
  });

  map.addLayer({
    id: "uf-place-muted",
    type: "symbol",
    source: "uf-labels",
    minzoom: MUNI_ZOOM,
    layout: {
      visibility: "none",
      "text-field": ["get", "place_sigla"],
      "text-font": [...ATLAS_FONT_BOLD],
      "text-size": 12,
      "text-allow-overlap": true,
      "text-ignore-placement": true,
      "text-padding": 0,
    },
    paint: {
      "text-color": "rgba(244, 250, 247, 0.55)",
      "text-halo-color": "rgba(10, 16, 14, 0.55)",
      "text-halo-width": 1.2,
      "text-opacity": 0.85,
    },
  });
}

const UF_OUTLINE_OPACITY: unknown = [
  "interpolate",
  ["linear"],
  ["zoom"],
  2.6,
  0.22,
  3.8,
  0.4,
  6,
  0.5,
];
const UF_OUTLINE_WIDTH: unknown = [
  "interpolate",
  ["linear"],
  ["zoom"],
  2.6,
  0.35,
  4.2,
  0.7,
  6,
  1.0,
];

export function setMunicipalityMode(map: maplibregl.Map, enabled: boolean) {
  if (enabled) {
    setLayerVisibility(map, "mun-fill", true);
    setLayerVisibility(map, "mun-outline", true);
    setLayerVisibility(map, "mun-place", true);
    setLayerVisibility(map, "mun-metric", false);
    setLayerVisibility(map, "uf-place", false);
    setLayerVisibility(map, "uf-metric", false);
    setLayerVisibility(map, "uf-place-muted", true);
    setLayerVisibility(map, "region-place", false);
    setLayerVisibility(map, "inter-place", false);
    setLayerVisibility(map, "inter-fill", false);
    setLayerVisibility(map, "inter-outline", false);
    setLayerVisibility(map, "capital-place", false);
    setLayerVisibility(map, "capital-dot", false);
    map.setPaintProperty("uf-fill", "fill-opacity", 0.12);
    map.setPaintProperty("uf-outline", "line-opacity", 0.8);
    map.setPaintProperty("uf-outline", "line-width", 1.5);
  } else {
    setLayerVisibility(map, "mun-fill", false);
    setLayerVisibility(map, "mun-outline", false);
    setLayerVisibility(map, "mun-place", false);
    setLayerVisibility(map, "mun-metric", false);
    setLayerVisibility(map, "uf-place", true);
    setLayerVisibility(map, "uf-metric", false);
    setLayerVisibility(map, "uf-place-muted", false);
    setLayerVisibility(map, "region-place", true);
    setLayerVisibility(map, "inter-place", true);
    setLayerVisibility(map, "inter-fill", true);
    setLayerVisibility(map, "inter-outline", true);
    setLayerVisibility(map, "capital-place", true);
    setLayerVisibility(map, "capital-dot", true);
    map.setPaintProperty("uf-fill", "fill-opacity", 0.97);
    map.setPaintProperty("uf-outline", "line-opacity", UF_OUTLINE_OPACITY);
    map.setPaintProperty("uf-outline", "line-width", UF_OUTLINE_WIDTH);
  }
}
