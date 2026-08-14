const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export type SourceInfo = {
  organization: string;
  dataset: string;
  url?: string;
  retrieved_at?: string;
};

export type Provenance = {
  definition?: string;
  source?: SourceInfo | Record<string, unknown>;
  limitations?: string[];
  reference_period?: string;
  status_label?: string;
};

export type Observation = {
  indicator: string;
  geography_ibge_code: string;
  uf: string;
  name: string;
  value: number;
  unit: string;
  reference_period: string;
  release_date?: string | null;
  status_label: string;
  evidence_grade?: string;
  higher_is_worse?: boolean;
  source: SourceInfo | Record<string, unknown>;
  dataset_id: string;
  limitations?: string[];
  short_name?: string;
  definition?: string;
  label?: string;
};

export type Indicator = {
  id: string;
  name: string;
  short_name?: string;
  unit: string;
  status_label: string;
  kind?: string;
  reference_period?: string;
  higher_is_worse?: boolean;
  group?: string;
  group_label?: string;
  definition?: string;
  source?: SourceInfo;
  limitations?: string[];
};

export type TerritoryItem = {
  id: string;
  label: string;
  section: string;
  value?: number | null;
  text?: string | null;
  unit?: string | null;
  status_label: string;
  reference_period: string;
  definition: string;
  source: SourceInfo;
  limitations?: string[];
};

export type Profile = {
  geography: {
    ibge_code: string;
    uf: string;
    name: string;
    uf_code?: string;
    level?: string;
  };
  metrics: Observation[];
  territory?: { items: TerritoryItem[] };
  disclaimer: string;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} falhou: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export function getApiUrl() {
  return API_URL || "(same-origin via Next rewrite)";
}

export async function fetchIndicators() {
  return api<{ count: number; items: Indicator[] }>("/v1/indicators");
}

export async function fetchObservations(indicator: string, period?: string) {
  const q = new URLSearchParams({ indicator });
  if (period) q.set("period", period);
  return api<{
    count: number;
    meta: Record<string, unknown>;
    items: Observation[];
  }>(`/v1/observations?${q.toString()}`);
}

export async function fetchProfile(code: string) {
  return api<Profile>(`/v1/geographies/${encodeURIComponent(code)}/profile`);
}

export async function fetchMunicipalityProfile(code: string) {
  return api<Profile>(
    `/v1/geographies/municipalities/${encodeURIComponent(code)}/profile`,
  );
}

export async function fetchPeriods(indicator: string) {
  return api<{ indicator: string; count: number; items: string[] }>(
    `/v1/indicators/${encodeURIComponent(indicator)}/periods`,
  );
}

export async function fetchMunicipalities(ufCode: string, period = "2025") {
  return api<{
    uf_code: string;
    period: string;
    count: number;
    definition?: string;
    status_label?: string;
    geojson: {
      type: "FeatureCollection";
      features: Array<{
        type: string;
        properties: Record<string, string | number | null>;
        geometry: unknown;
      }>;
    };
    values: Array<{ ibge_code: string; name: string; value: number }>;
    source: SourceInfo & Record<string, string>;
  }>(
    `/v1/geographies/states/${encodeURIComponent(ufCode)}/municipalities?period=${encodeURIComponent(period)}`,
  );
}
