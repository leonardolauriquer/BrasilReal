"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Indicator, Observation } from "@/lib/api";

type Hit =
  | { kind: "layer"; id: string; label: string; hint: string }
  | { kind: "uf"; id: string; label: string; hint: string };

function fold(s: string) {
  return s
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

type Props = {
  open: boolean;
  indicators: Indicator[];
  ufs: Observation[];
  onClose: () => void;
  onPickLayer: (id: string) => void;
  onPickUf: (ibge: string) => void;
};

export function AtlasSearch({ open, indicators, ufs, onClose, onPickLayer, onPickUf }: Props) {
  const [q, setQ] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    setQ("");
    const t = window.setTimeout(() => inputRef.current?.focus(), 20);
    return () => window.clearTimeout(t);
  }, [open]);

  const hits = useMemo(() => {
    const needle = fold(q.trim());
    if (!needle) {
      return [
        ...indicators.slice(0, 6).map((ind) => ({
          kind: "layer" as const,
          id: ind.id,
          label: ind.short_name || ind.name,
          hint: "camada",
        })),
        ...ufs.slice(0, 6).map((row) => ({
          kind: "uf" as const,
          id: row.geography_ibge_code,
          label: `${row.uf} · ${row.name}`,
          hint: "UF",
        })),
      ];
    }
    const layers: Hit[] = indicators
      .filter((ind) =>
        [ind.id, ind.name, ind.short_name || ""].some((v) => fold(v).includes(needle)),
      )
      .slice(0, 8)
      .map((ind) => ({
        kind: "layer",
        id: ind.id,
        label: ind.short_name || ind.name,
        hint: ind.group_label || "camada",
      }));
    const places: Hit[] = ufs
      .filter((row) => [row.uf, row.name, row.geography_ibge_code].some((v) => fold(v).includes(needle)))
      .slice(0, 8)
      .map((row) => ({
        kind: "uf",
        id: row.geography_ibge_code,
        label: `${row.uf} · ${row.name}`,
        hint: "UF",
      }));
    return [...layers, ...places];
  }, [indicators, q, ufs]);

  if (!open) return null;

  return (
    <div className="search-root" role="dialog" aria-label="Buscar camada ou UF">
      <button type="button" className="search-veil" onClick={onClose} aria-label="Fechar busca" />
      <div className="search-panel">
        <input
          ref={inputRef}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Gini, RCL, Roraima…"
          aria-label="Buscar"
        />
        <p className="search-hint">/ ou Ctrl+K · Esc fecha</p>
        <ul>
          {hits.length ? (
            hits.map((hit) => (
              <li key={`${hit.kind}-${hit.id}`}>
                <button
                  type="button"
                  onClick={() => {
                    if (hit.kind === "layer") onPickLayer(hit.id);
                    else onPickUf(hit.id);
                    onClose();
                  }}
                >
                  <strong>{hit.label}</strong>
                  <em>{hit.hint}</em>
                </button>
              </li>
            ))
          ) : (
            <li className="search-empty">Nada com essa busca</li>
          )}
        </ul>
      </div>
    </div>
  );
}
