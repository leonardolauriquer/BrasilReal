/**
 * Shared atlas contracts (web + documented for API parity).
 * Keep fields aligned with FastAPI observation/indicator payloads.
 */

export type SourceInfo = {
  organization: string;
  dataset: string;
  url?: string;
  retrieved_at?: string;
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
  definition: string;
  limitations?: string[];
  short_name?: string;
  label?: string;
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

export type GeographyRef = {
  ibge_code: string;
  uf: string;
  name: string;
  uf_code?: string;
  level?: string;
};

export type Profile = {
  geography: GeographyRef;
  metrics: Observation[];
  territory?: { items: TerritoryItem[] };
  disclaimer: string;
};
