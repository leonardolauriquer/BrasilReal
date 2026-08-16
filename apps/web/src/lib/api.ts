import type {
  Indicator,
  Observation,
  Profile,
  SourceInfo,
  TerritoryItem,
} from "@brasil-real/contracts";

export type { Indicator, Observation, Profile, SourceInfo, TerritoryItem };
export type { GeographyRef } from "@brasil-real/contracts";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export type Provenance = {
  definition?: string;
  source?: SourceInfo | Record<string, unknown>;
  limitations?: string[];
  reference_period?: string;
  status_label?: string;
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
    meta: {
      period_resolved?: boolean | null;
      period_miss?: boolean;
      resolved_period?: string | null;
      [key: string]: unknown;
    };
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

export async function fetchPeriods(indicator: string, refresh = false) {
  const q = refresh ? "?refresh=true" : "";
  return api<{
    indicator: string;
    count: number;
    items: string[];
    latest?: string;
    source?: string;
    cache_hit?: boolean;
  }>(`/v1/indicators/${encodeURIComponent(indicator)}/periods${q}`);
}

export async function fetchMunicipalities(ufCode: string, period?: string) {
  const q = period ? `?period=${encodeURIComponent(period)}` : "";
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
    `/v1/geographies/states/${encodeURIComponent(ufCode)}/municipalities${q}`,
  );
}
