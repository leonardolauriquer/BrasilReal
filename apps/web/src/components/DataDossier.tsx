"use client";

import { useEffect, useMemo, useState } from "react";
import { BrandMark } from "@/components/BrandMark";
import { BRAZIL_SILHOUETTE_PATH } from "@/lib/brand";
import { fetchObservations, type Indicator, type Observation } from "@/lib/api";
import { gateObservations } from "@/lib/dataGate";
import {
  buildDossierZip,
  citationText,
  downloadBlob,
  type DossierInput,
} from "@/lib/dossier/buildDossier";
import { comparePeriodKeys, formatPeriodLabel } from "@/lib/format";
import { recorteLabel, ufsForRecorte, type RecorteId, type RegionRankRow } from "@/lib/map/regions";

type Props = {
  open: boolean;
  onClose: () => void;
  rows: Observation[];
  indicator: Indicator | null;
  period: string;
  periods: string[];
  recorte: RecorteId;
  rankMode: "nivel" | "delta";
  comparePeriod?: string;
  regionRows?: RegionRankRow[];
  regionMode?: boolean;
};

type Busy = null | "vista" | "serie";

async function loadSeries(
  indicator: string,
  periods: string[],
  recorte: RecorteId,
  onTick: (done: number, total: number) => void,
): Promise<{ rows: Observation[]; omitted: string[] }> {
  const allow = ufsForRecorte(recorte);
  const chrono = [...new Set(periods.filter(Boolean))].sort(comparePeriodKeys);
  const rows: Observation[] = [];
  const omitted: string[] = [];
  let done = 0;
  for (const p of chrono) {
    const data = await fetchObservations(indicator, p);
    const gated = gateObservations(data.items);
    let items = gated.items;
    if (allow) items = items.filter((r) => allow.includes(r.uf));
    if (!items.length) omitted.push(p);
    else rows.push(...items);
    done += 1;
    onTick(done, chrono.length);
  }
  return { rows, omitted };
}

export function DataDossier({
  open,
  onClose,
  rows,
  indicator,
  period,
  periods,
  recorte,
  rankMode,
  comparePeriod,
  regionRows = [],
  regionMode = false,
}: Props) {
  const [busy, setBusy] = useState<Busy>(null);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !busy) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  useEffect(() => {
    if (!open) {
      setError(null);
      setProgress("");
      setBusy(null);
      setCopied(false);
    }
  }, [open]);

  const sample = rows[0];
  const src = (sample?.source || indicator?.source || {}) as {
    organization?: string;
    dataset?: string;
    url?: string;
  };
  const status =
    rankMode === "delta" ? "DERIVADO" : sample?.status_label || indicator?.status_label || "";
  const canSeries = Boolean(indicator?.id && periods.length > 1 && rankMode !== "delta");
  const includeRegions = regionMode && regionRows.some((r) => r.value != null);

  const baseInput = useMemo<DossierInput>(
    () => ({
      kind: "vista",
      rows,
      indicator,
      period,
      periods,
      recorte,
      rankMode,
      comparePeriod,
      regionRows,
      includeRegions,
    }),
    [rows, indicator, period, periods, recorte, rankMode, comparePeriod, regionRows, includeRegions],
  );

  const cite = useMemo(() => citationText(baseInput), [baseInput]);

  const run = async (kind: "vista" | "serie") => {
    if (busy) return;
    setError(null);
    setBusy(kind);
    try {
      if (kind === "vista") {
        if (!rows.length) throw new Error("SEM DADO nesta vista — nada para empacotar.");
        setProgress("Montando o dossiê…");
        const pack = await buildDossierZip(baseInput);
        downloadBlob(pack.filename, pack.blob);
      } else {
        if (!indicator?.id) throw new Error("Camada sem identificador.");
        setProgress("Buscando a série oficial…");
        const series = await loadSeries(indicator.id, periods, recorte, (done, total) => {
          setProgress(`Período ${done} de ${total}…`);
        });
        if (!series.rows.length) {
          throw new Error("Série oficial sem observações neste recorte.");
        }
        setProgress("Montando o dossiê…");
        const pack = await buildDossierZip({
          ...baseInput,
          kind: "serie",
          rows: series.rows,
          rankMode: "nivel",
          includeRegions: false,
          omittedPeriods: series.omitted,
        });
        downloadBlob(pack.filename, pack.blob);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao montar o dossiê.");
    } finally {
      setBusy(null);
      setProgress("");
    }
  };

  const copyCite = async () => {
    try {
      await navigator.clipboard.writeText(cite);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setError("Não foi possível copiar. Selecione a citação manualmente.");
    }
  };

  if (!open) return null;

  const name = indicator?.short_name || indicator?.name || sample?.indicator || "Camada";
  const definition = sample?.definition || indicator?.definition || "";

  return (
    <div className="dossier-root">
      <button type="button" className="dossier-veil" aria-label="Fechar dossiê" onClick={() => !busy && onClose()} />
      <aside
        className="dossier"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dossier-title"
      >
        <svg className="dossier-sil" viewBox="0 0 64 64" aria-hidden="true">
          <path d={BRAZIL_SILHOUETTE_PATH} />
        </svg>
        <header className="dossier-head">
          <BrandMark className="dossier-mark" />
          <div>
            <p className="dossier-kicker">Dossiê de dados</p>
            <h2 id="dossier-title">{name}</h2>
          </div>
          <button type="button" className="dossier-close" onClick={onClose} disabled={Boolean(busy)}>
            Fechar
          </button>
        </header>

        <p className="dossier-lede">
          O que o mapa mostra, com órgão, período e limites — para levar, citar e não fingir que a fonte somos nós.
        </p>

        <ul className="dossier-chips">
          <li>{formatPeriodLabel(period || "—")}</li>
          <li>
            {recorteLabel(recorte)} · {rows.length} UFs
          </li>
          {status ? <li className={status === "DERIVADO" ? "is-derived" : ""}>{status}</li> : null}
          {src.organization ? <li>{src.organization}</li> : null}
        </ul>

        {definition ? <p className="dossier-def">{definition}</p> : null}
        <p className="dossier-src">
          {src.dataset ? `${src.organization || "Fonte"} · ${src.dataset}` : src.organization || "Fonte não rotulada"}
          {src.url ? (
            <>
              {" · "}
              <a href={src.url} target="_blank" rel="noreferrer">
                abrir na fonte
              </a>
            </>
          ) : null}
        </p>

        <section className="dossier-pack" aria-label="Conteúdo do pacote">
          <h3>O pacote</h3>
          <ol>
            <li>
              <strong>LEIA-ME.md</strong>
              <span>carta de proveniência, limites e como citar</span>
            </li>
            <li>
              <strong>observacoes.csv</strong>
              <span>uma linha por UF · UTF-8 · ; · decimal com ponto</span>
            </li>
            <li>
              <strong>proveniencia.json</strong>
              <span>o mesmo recorte em contrato máquina</span>
            </li>
            {includeRegions ? (
              <li>
                <strong>agregado-macrorregioes.csv</strong>
                <span>DERIVADO · soma ou média ponderada pela pop.</span>
              </li>
            ) : null}
          </ol>
        </section>

        <div className="dossier-actions">
          <button
            type="button"
            className="dossier-primary"
            disabled={Boolean(busy) || !rows.length}
            onClick={() => void run("vista")}
          >
            {busy === "vista" ? "Montando…" : "Baixar esta vista"}
          </button>
          {canSeries ? (
            <button
              type="button"
              className="dossier-ghost"
              disabled={Boolean(busy)}
              onClick={() => void run("serie")}
            >
              {busy === "serie" ? "Buscando série…" : `Série oficial (${periods.length} períodos)`}
            </button>
          ) : null}
        </div>
        {progress ? <p className="dossier-progress">{progress}</p> : null}
        {error ? <p className="dossier-error">{error}</p> : null}
        {!rows.length ? (
          <p className="dossier-error">SEM DADO nesta vista — o atlas não empacota o vazio.</p>
        ) : null}

        <section className="dossier-cite">
          <div className="dossier-cite-head">
            <h3>Como citar</h3>
            <button type="button" className="dossier-copy" onClick={() => void copyCite()}>
              {copied ? "Copiado" : "Copiar"}
            </button>
          </div>
          <blockquote>{cite}</blockquote>
        </section>
      </aside>
    </div>
  );
}
