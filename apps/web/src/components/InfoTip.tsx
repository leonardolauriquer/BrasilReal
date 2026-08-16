"use client";

import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

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
  return Boolean(p?.definition && p?.source?.organization && p?.source?.dataset);
}

const VIEW_PAD = 10;

export function InfoTip({ data, label = "Sobre este dado" }: { data: ProvenanceFields; label?: string }) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0, width: 280, maxHeight: 320 });
  const [ready, setReady] = useState(false);
  const btnRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const place = useCallback(() => {
    const btn = btnRef.current;
    if (!btn) return;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const width = Math.min(300, vw - VIEW_PAD * 2);
    const br = btn.getBoundingClientRect();
    let left = br.left;
    if (left + width > vw - VIEW_PAD) left = vw - VIEW_PAD - width;
    if (left < VIEW_PAD) left = VIEW_PAD;

    const spaceBelow = vh - br.bottom - VIEW_PAD;
    const spaceAbove = br.top - VIEW_PAD;
    const panelH = panelRef.current?.scrollHeight ?? 240;
    const flipUp = spaceBelow < Math.min(panelH, 220) && spaceAbove > spaceBelow;
    const maxHeight = Math.max(160, flipUp ? spaceAbove : spaceBelow);
    const shownH = Math.min(panelH, maxHeight);
    const top = flipUp
      ? Math.max(VIEW_PAD, br.top - 8 - shownH)
      : Math.min(br.bottom + 8, vh - VIEW_PAD - 80);

    setCoords({ top, left, width, maxHeight });
    setReady(true);
  }, []);

  useLayoutEffect(() => {
    if (!open) {
      setReady(false);
      return;
    }
    place();
    const id = requestAnimationFrame(() => place());
    return () => cancelAnimationFrame(id);
  }, [open, place, data]);

  useEffect(() => {
    if (!open) return;
    const onWin = () => place();
    window.addEventListener("resize", onWin);
    window.addEventListener("scroll", onWin, true);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    const onPointer = (e: PointerEvent) => {
      const t = e.target as Node;
      if (btnRef.current?.contains(t) || panelRef.current?.contains(t)) return;
      setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      window.removeEventListener("resize", onWin);
      window.removeEventListener("scroll", onWin, true);
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [open, place]);

  if (!hasProvenance(data)) return null;

  const panel =
    open && typeof document !== "undefined"
      ? createPortal(
          <div
            ref={panelRef}
            id={id}
            role="dialog"
            aria-label={label}
            className="info-tip-panel"
            style={{
              top: coords.top,
              left: coords.left,
              width: coords.width,
              maxHeight: coords.maxHeight,
              visibility: ready ? "visible" : "hidden",
            }}
          >
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
          </div>,
          document.body,
        )
      : null;

  return (
    <span className="info-tip">
      <button
        ref={btnRef}
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
      >
        ?
      </button>
      {panel}
    </span>
  );
}
