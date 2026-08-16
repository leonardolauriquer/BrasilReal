import { SITE_URL } from "@/lib/brand";
import { formatPeriodLabel } from "@/lib/format";
import type { Indicator, Observation, SourceInfo } from "@/lib/api";
import type { RecorteId, RegionRankRow } from "@/lib/map/regions";
import { recorteLabel } from "@/lib/map/regions";
import { utf8, utf8Bom, zipStore } from "@/lib/dossier/zipStore";

export type DossierKind = "vista" | "serie";

export type DossierInput = {
  kind: DossierKind;
  rows: Observation[];
  indicator: Indicator | null;
  period: string;
  periods: string[];
  recorte: RecorteId;
  rankMode: "nivel" | "delta";
  comparePeriod?: string;
  regionRows?: RegionRankRow[];
  includeRegions?: boolean;
  omittedPeriods?: string[];
  generatedAt?: Date;
};

function sourceOf(row?: Observation, indicator?: Indicator | null): SourceInfo {
  const raw = (row?.source || indicator?.source || {}) as SourceInfo;
  return {
    organization: raw.organization || "",
    dataset: raw.dataset || "",
    url: raw.url,
    retrieved_at: raw.retrieved_at,
  };
}

function csvCell(value: string | number | null | undefined): string {
  if (value == null) return "";
  const s = String(value);
  if (/[;"\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function csvLine(cells: Array<string | number | null | undefined>): string {
  return cells.map(csvCell).join(";");
}

export function slugPart(value: string): string {
  const s = value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
  return s.slice(0, 48) || "camada";
}

export function dossierFilename(input: DossierInput): string {
  const layer = slugPart(input.indicator?.id || input.rows[0]?.indicator || "camada");
  const recorte = input.recorte === "BR" ? "27ufs" : slugPart(input.recorte);
  const period =
    input.kind === "serie"
      ? "serie"
      : slugPart(input.period || "periodo");
  const delta = input.kind === "vista" && input.rankMode === "delta" ? "_variacao" : "";
  return `BrasilReal_${layer}_${period}_${recorte}${delta}.zip`;
}

function observationsCsv(rows: Observation[]): string {
  const header = csvLine([
    "codigo_ibge",
    "uf",
    "nome",
    "valor",
    "unidade",
    "periodo_ref",
    "status_label",
    "orgao",
    "dataset",
    "url",
    "dataset_id",
    "indicador",
  ]);
  const body = [...rows]
    .sort((a, b) => a.uf.localeCompare(b.uf, "pt-BR"))
    .map((row) => {
      const src = sourceOf(row);
      return csvLine([
        row.geography_ibge_code,
        row.uf,
        row.name,
        row.value,
        row.unit,
        row.reference_period,
        row.status_label,
        src.organization,
        src.dataset,
        src.url || "",
        row.dataset_id,
        row.indicator,
      ]);
    });
  return [header, ...body].join("\r\n") + "\r\n";
}

function regionsCsv(rows: RegionRankRow[]): string {
  const header = csvLine([
    "macro_id",
    "nome",
    "valor",
    "unidade",
    "agregacao",
    "ufs_com_dado",
    "ufs_total",
    "status_label",
  ]);
  const body = rows.map((row) =>
    csvLine([
      row.id,
      row.name,
      row.value,
      row.unit || "",
      row.aggregate,
      row.with_data,
      row.uf_count,
      "DERIVADO",
    ]),
  );
  return [header, ...body].join("\r\n") + "\r\n";
}

function uniqueLimitations(input: DossierInput): string[] {
  const out: string[] = [];
  const push = (item?: string) => {
    const t = (item || "").trim();
    if (t && !out.includes(t)) out.push(t);
  };
  for (const row of input.rows) {
    for (const lim of row.limitations || []) push(lim);
  }
  for (const lim of input.indicator?.limitations || []) push(lim);
  if (input.kind === "vista" && input.rankMode === "delta" && input.comparePeriod) {
    push(
      `Vista em variação: valor = período ${input.period} − período ${input.comparePeriod} da mesma série oficial. A fonte não publica este ranking.`,
    );
  }
  if (input.includeRegions) {
    push(
      "Arquivo agregado-macrorregioes.csv é DERIVADO (soma aditiva ou média ponderada pela população). Não é publicação IBGE da macrorregião.",
    );
  }
  if (input.omittedPeriods?.length) {
    push(
      `Períodos oficiais omitidos deste pacote (SEM DADO / cobertura ≠ 27): ${input.omittedPeriods.join(", ")}.`,
    );
  }
  return out;
}

export function citationText(input: DossierInput): string {
  const sample = input.rows[0];
  const src = sourceOf(sample, input.indicator);
  const name =
    input.indicator?.short_name ||
    input.indicator?.name ||
    sample?.short_name ||
    sample?.indicator ||
    "camada";
  const year = (input.generatedAt || new Date()).getFullYear();
  const period =
    input.kind === "serie"
      ? `série ${input.periods.map(formatPeriodLabel).filter(Boolean).join(" / ") || "oficial"}`
      : formatPeriodLabel(input.period || sample?.reference_period || "—");
  const org = src.organization ? ` Com base em ${src.organization}.` : "";
  const url = src.url ? ` Fonte original: ${src.url}` : "";
  return `Brasil Real (${year}). «${name}», ${period}, recorte ${recorteLabel(input.recorte)}. Atlas exploratório. ${SITE_URL}.${org}${url}`;
}

function readme(input: DossierInput, sha?: string): string {
  const sample = input.rows[0];
  const src = sourceOf(sample, input.indicator);
  const name = input.indicator?.name || sample?.indicator || "Camada";
  const short = input.indicator?.short_name || name;
  const definition = sample?.definition || input.indicator?.definition || "";
  const status =
    input.kind === "vista" && input.rankMode === "delta"
      ? "DERIVADO"
      : sample?.status_label || input.indicator?.status_label || "";
  const when = (input.generatedAt || new Date()).toISOString();
  const limitations = uniqueLimitations(input);
  const files = [
    "- `LEIA-ME.md` — esta carta (o que é, de onde veio, o que não é).",
    "- `observacoes.csv` — uma linha por UF; UTF-8; separado por ponto e vírgula; decimal com ponto.",
    "- `proveniencia.json` — o mesmo pacote em contrato máquina (fonte, período, limites).",
  ];
  if (input.includeRegions) {
    files.push(
      "- `agregado-macrorregioes.csv` — DERIVADO a partir das UFs (não republicar como fato IBGE da região).",
    );
  }

  const lines: string[] = [
    `# Brasil Real — dossiê de dados`,
    ``,
    `Este arquivo **não substitui a fonte oficial**. É um recorte auditável do atlas`,
    `[Brasil Real](${SITE_URL}): os mesmos números que o mapa mostra, com órgão, dataset,`,
    `período e rótulo em cada linha.`,
    ``,
    `A estatística continua sendo do órgão citado. O Brasil Real não inventa valor,`,
    `não calcula impacto e não reivindica autoria do dado oficial — só a curadoria`,
    `(cobertura 27 UFs ou vazio, proveniência obrigatória, rótulo OBSERVADO / DERIVADO / SEM DADO).`,
    ``,
    `## O que você está baixando`,
    ``,
    `| | |`,
    `|---|---|`,
    `| Camada | ${short} (\`${sample?.indicator || input.indicator?.id || ""}\`) |`,
    `| Pacote | ${input.kind === "serie" ? "Série oficial da camada" : "Vista do mapa"} |`,
    `| Período | ${
      input.kind === "serie"
        ? input.periods.map(formatPeriodLabel).join(", ")
        : formatPeriodLabel(input.period)
    } |`,
    `| Recorte | ${recorteLabel(input.recorte)} · ${input.rows.length} linha(s) |`,
    `| Unidade | ${sample?.unit || input.indicator?.unit || "—"} |`,
    `| Status | ${status} |`,
    `| Gerado em | ${when} |`,
  ];
  if (sha) lines.push(`| SHA-256 (observacoes.csv) | \`${sha}\` |`);
  lines.push(
    ``,
    `## De onde veio`,
    ``,
    `- Órgão: **${src.organization || "—"}**`,
    `- Dataset: ${src.dataset || "—"}`,
    src.url ? `- URL: ${src.url}` : "- URL: (não informada neste recorte)",
  );
  if (src.retrieved_at) lines.push(`- Consultado em: ${src.retrieved_at}`);
  lines.push(
    ``,
    `## O que o número significa`,
    ``,
    definition ||
      "(definição ausente — não deveria acontecer; o atlas bloqueia número sem definição.)",
    ``,
    `## Limites — leia antes do gráfico`,
    ``,
    ...(limitations.length
      ? limitations.map((item) => `- ${item}`)
      : ["- Sem limitações adicionais declaradas nesta camada."]),
    ``,
    `## Como não usar`,
    ``,
    `- Não apresente lente, variação ou agregado regional (status DERIVADO) como publicação do órgão.`,
    `- Não some taxas, densidades nem notas 0–100.`,
    `- Não misture períodos distintos sem dizer isso no gráfico.`,
    `- Cite **o órgão original**. O Brasil Real é o atlas; a fonte é o SIDRA, o SICONFI, o Comex, o TSE…`,
    ``,
    `## Como citar`,
    ``,
    citationText(input),
    ``,
    `## Arquivos`,
    ``,
    ...files,
    ``,
    `CSV: Excel brasileiro → Dados → De texto/CSV → delimitador **ponto e vírgula**, decimal **ponto**.`,
    `Python: \`pandas.read_csv("observacoes.csv", sep=";")\`.`,
    ``,
  );
  return lines.join("\n");
}

export function proveniencia(input: DossierInput, sha?: string) {
  const sample = input.rows[0];
  const src = sourceOf(sample, input.indicator);
  return {
    product: "Brasil Real",
    url: SITE_URL,
    packaging: "dossie-v1",
    generated_at: (input.generatedAt || new Date()).toISOString(),
    kind: input.kind,
    observations_sha256: sha || null,
    view: {
      indicator: sample?.indicator || input.indicator?.id || "",
      name: input.indicator?.name || "",
      short_name: input.indicator?.short_name || sample?.short_name || "",
      period: input.kind === "serie" ? input.periods : input.period,
      recorte: input.recorte,
      recorte_label: recorteLabel(input.recorte),
      rank_mode: input.kind === "vista" ? input.rankMode : "nivel",
      compare_period:
        input.kind === "vista" && input.rankMode === "delta" ? input.comparePeriod || null : null,
      unit: sample?.unit || input.indicator?.unit || "",
      status_label:
        input.kind === "vista" && input.rankMode === "delta"
          ? "DERIVADO"
          : sample?.status_label || input.indicator?.status_label || "",
      higher_is_worse: Boolean(input.indicator?.higher_is_worse),
      row_count: input.rows.length,
    },
    source: src,
    definition: sample?.definition || input.indicator?.definition || "",
    limitations: uniqueLimitations(input),
    citation: citationText(input),
    license_note:
      "A estatística pertence ao órgão citado. O Brasil Real publica só a curadoria auditável, sem reivindicar autoria dos números oficiais.",
  };
}

async function sha256Hex(data: Uint8Array): Promise<string | undefined> {
  if (typeof crypto === "undefined" || !crypto.subtle) return undefined;
  const buf = await crypto.subtle.digest("SHA-256", data as BufferSource);
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export async function buildDossierZip(input: DossierInput): Promise<{ blob: Blob; filename: string }> {
  const stamped = input.generatedAt || new Date();
  const csv = observationsCsv(input.rows);
  const csvBytes = utf8Bom(csv);
  const sha = await sha256Hex(csvBytes);
  const meta = proveniencia(input, sha);
  const files = [
    { name: "LEIA-ME.md", body: utf8(readme(input, sha)) },
    { name: "observacoes.csv", body: csvBytes },
    { name: "proveniencia.json", body: utf8(`${JSON.stringify(meta, null, 2)}\n`) },
  ];
  if (input.includeRegions && input.regionRows?.length) {
    files.push({
      name: "agregado-macrorregioes.csv",
      body: utf8Bom(regionsCsv(input.regionRows)),
    });
  }
  return {
    blob: zipStore(files, stamped),
    filename: dossierFilename(input),
  };
}

export function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 4000);
}
