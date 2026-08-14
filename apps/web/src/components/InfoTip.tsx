"use client";

import { useId, useState } from "react";

export type ProvenanceFields = {
  definition?: string;
  source?: {
    organization?: string;
    dataset?: string;
    url?: string;
  };
  reference_period?: string;
  status_label?: string;
  limitations?: string[];
};

/** Fail-closed: only render children when definition + source exist. */
export function hasProvenance(p: ProvenanceFields | null | undefined): boolean {
  return Boolean(
    p?.definition &&
      p?.source?.organization &&
      p?.source?.dataset,
  );
}

export function InfoTip({ data, label = "Sobre este dado" }: { data: ProvenanceFields; label?: string }) {
  const id = useId();
  const [open, setOpen] = useState(false);
  if (!hasProvenance(data)) return null;

  return (
    <span className="info-tip">
      <button
        type="button"
        className="info-tip-btn"
        aria-expanded={open}
        aria-controls={id}
        aria-label={label}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setOpen((v) => !v);
        }}
        onBlur={() => setOpen(false)}
      >
        ?
      </button>
      {open && (
        <span className="info-tip-panel" id={id} role="tooltip">
          <strong>O que é</strong>
          <p>{data.definition}</p>
          <strong>De onde veio</strong>
          <p>
            {data.source?.organization} · {data.source?.dataset}
            {data.source?.url ? (
              <>
                {" "}
                ·{" "}
                <a href={data.source.url} target="_blank" rel="noreferrer">
                  fonte
                </a>
              </>
            ) : null}
          </p>
          {data.reference_period ? (
            <>
              <strong>Período</strong>
              <p>{data.reference_period}</p>
            </>
          ) : null}
          {data.status_label ? (
            <>
              <strong>Rótulo</strong>
              <p>{data.status_label}</p>
            </>
          ) : null}
          {data.limitations && data.limitations.length > 0 ? (
            <>
              <strong>Limitações</strong>
              <ul>
                {data.limitations.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </>
          ) : null}
        </span>
      )}
    </span>
  );
}
