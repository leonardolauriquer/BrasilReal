/**
 * Single source of truth for atlas zoom bands.
 * macro → intermediate → UF/capital → municipality
 */
export const ZOOM = {
  min: 2.6,
  max: 11,
  /** Initial camera. */
  start: 3.35,
  /** Ranking + macro labels dominate below this. */
  regionRankMax: 3.85,
  regionLabelMax: 4.15,
  ufLabelFadeIn: 3.55,
  interLabelMin: 3.85,
  interLabelMax: 5.35,
  capitalMin: 3.95,
  capitalMax: 6.55,
  /** Population choropleth municipalities. */
  municipality: 5.6,
} as const;

/** @deprecated prefer ZOOM.* — kept as aliases used by layers. */
export const REGION_LABEL_MAX_ZOOM = ZOOM.regionLabelMax;
export const INTER_LABEL_MIN_ZOOM = ZOOM.interLabelMin;
export const INTER_LABEL_MAX_ZOOM = ZOOM.interLabelMax;
export const UF_LABEL_FADE_IN = ZOOM.ufLabelFadeIn;
export const CAPITAL_MIN_ZOOM = ZOOM.capitalMin;
export const CAPITAL_MAX_ZOOM = ZOOM.capitalMax;
export const MUNI_ZOOM = ZOOM.municipality;
export const REGION_RANK_MAX_ZOOM = ZOOM.regionRankMax;

export function isRegionRankMode(zoom: number, showMunicipalities: boolean) {
  return zoom < ZOOM.regionRankMax && !showMunicipalities;
}

export function isIntermediateClickBand(zoom: number) {
  return zoom >= ZOOM.interLabelMin && zoom < ZOOM.interLabelMax;
}

export function shouldShowMunicipalities(
  zoom: number,
  selectedUf: string | null | undefined,
  layerId: string,
) {
  return zoom >= ZOOM.municipality && Boolean(selectedUf) && layerId === "population";
}
