/** Capitals of Brazilian states — label anchors at mid zoom. */

export type CapitalPoint = {
  uf: string;
  uf_code: string;
  name: string;
  /** [lng, lat] */
  coordinates: [number, number];
};

/** Official capital cities with approximate coordinates (WGS84). */
export const STATE_CAPITALS: CapitalPoint[] = [
  { uf: "AC", uf_code: "12", name: "Rio Branco", coordinates: [-67.81, -9.97] },
  { uf: "AL", uf_code: "27", name: "Maceió", coordinates: [-35.74, -9.67] },
  { uf: "AP", uf_code: "16", name: "Macapá", coordinates: [-51.07, -0.03] },
  { uf: "AM", uf_code: "13", name: "Manaus", coordinates: [-60.02, -3.12] },
  { uf: "BA", uf_code: "29", name: "Salvador", coordinates: [-38.51, -12.97] },
  { uf: "CE", uf_code: "23", name: "Fortaleza", coordinates: [-38.54, -3.72] },
  { uf: "DF", uf_code: "53", name: "Brasília", coordinates: [-47.93, -15.78] },
  { uf: "ES", uf_code: "32", name: "Vitória", coordinates: [-40.34, -20.32] },
  { uf: "GO", uf_code: "52", name: "Goiânia", coordinates: [-49.25, -16.69] },
  { uf: "MA", uf_code: "21", name: "São Luís", coordinates: [-44.3, -2.53] },
  { uf: "MT", uf_code: "51", name: "Cuiabá", coordinates: [-56.1, -15.6] },
  { uf: "MS", uf_code: "50", name: "Campo Grande", coordinates: [-54.62, -20.47] },
  { uf: "MG", uf_code: "31", name: "Belo Horizonte", coordinates: [-43.94, -19.92] },
  { uf: "PA", uf_code: "15", name: "Belém", coordinates: [-48.5, -1.46] },
  { uf: "PB", uf_code: "25", name: "João Pessoa", coordinates: [-34.86, -7.12] },
  { uf: "PR", uf_code: "41", name: "Curitiba", coordinates: [-49.27, -25.43] },
  { uf: "PE", uf_code: "26", name: "Recife", coordinates: [-34.88, -8.05] },
  { uf: "PI", uf_code: "22", name: "Teresina", coordinates: [-42.8, -5.09] },
  { uf: "RJ", uf_code: "33", name: "Rio de Janeiro", coordinates: [-43.17, -22.91] },
  { uf: "RN", uf_code: "24", name: "Natal", coordinates: [-35.21, -5.79] },
  { uf: "RS", uf_code: "43", name: "Porto Alegre", coordinates: [-51.23, -30.03] },
  { uf: "RO", uf_code: "11", name: "Porto Velho", coordinates: [-63.9, -8.76] },
  { uf: "RR", uf_code: "14", name: "Boa Vista", coordinates: [-60.67, 2.82] },
  { uf: "SC", uf_code: "42", name: "Florianópolis", coordinates: [-48.55, -27.6] },
  { uf: "SP", uf_code: "35", name: "São Paulo", coordinates: [-46.63, -23.55] },
  { uf: "SE", uf_code: "28", name: "Aracaju", coordinates: [-37.07, -10.91] },
  { uf: "TO", uf_code: "17", name: "Palmas", coordinates: [-48.33, -10.18] },
];

export function normalizePlaceName(name: string) {
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

const CAPITAL_NAME_KEYS = new Set(STATE_CAPITALS.map((c) => normalizePlaceName(c.name)));

/** True when name matches a UF capital (e.g. intermediate region "Cuiabá"). */
export function isStateCapitalName(name: string) {
  return CAPITAL_NAME_KEYS.has(normalizePlaceName(name));
}

export function capitalsGeoJSON() {
  return {
    type: "FeatureCollection" as const,
    features: STATE_CAPITALS.map((c, i) => ({
      type: "Feature" as const,
      properties: {
        uf: c.uf,
        uf_code: c.uf_code,
        name: c.name,
        place_name: c.name,
        label_rank: i,
      },
      geometry: { type: "Point" as const, coordinates: c.coordinates },
    })),
  };
}
