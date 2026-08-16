"use client";

import { useEffect, useMemo } from "react";
import { BrandMark } from "@/components/BrandMark";
import { BRAZIL_SILHOUETTE_PATH } from "@/lib/brand";

export type BootStage = {
  id: string;
  label: string;
  done: boolean;
};

type Props = {
  stages: BootStage[];
  error?: string | null;
  exiting?: boolean;
  onExitComplete?: () => void;
};

export function BootScreen({ stages, error, exiting = false, onExitComplete }: Props) {
  const doneCount = stages.filter((s) => s.done).length;
  const progress = stages.length ? doneCount / stages.length : 0;
  const active = stages.find((s) => !s.done)?.label || "Quase pronto";

  const status = useMemo(() => {
    if (error) return "Não foi possível abrir o atlas";
    if (exiting) return "Abrindo o mapa";
    return active;
  }, [active, error, exiting]);

  useEffect(() => {
    if (!exiting || !onExitComplete) return;
    const t = window.setTimeout(onExitComplete, 720);
    return () => window.clearTimeout(t);
  }, [exiting, onExitComplete]);

  return (
    <div
      className={`boot ${exiting ? "boot--out" : ""}`}
      role="status"
      aria-live="polite"
      aria-busy={!exiting && !error}
    >
      <div className="boot-atmosphere" aria-hidden="true">
        <div className="boot-glow boot-glow-a" />
        <div className="boot-glow boot-glow-b" />
        <svg className="boot-silhouette" viewBox="0 0 64 64" fill="none">
          <path className="boot-silhouette-path" d={BRAZIL_SILHOUETTE_PATH} />
        </svg>
      </div>

      <div className="boot-core">
        <BrandMark className="boot-mark" />
        <p className="boot-kicker">Atlas exploratório</p>
        <h1 className="boot-brand">Brasil Real</h1>
        <p className="boot-line">
          Dados oficiais com fonte, período e definição — nada inventado.
        </p>

        <div className="boot-meter" aria-hidden="true">
          <div className="boot-meter-track">
            <div
              className="boot-meter-fill"
              style={{ transform: `scaleX(${Math.max(0.08, progress)})` }}
            />
          </div>
          <span className="boot-meter-pct">{Math.round(progress * 100)}%</span>
        </div>

        <ul className="boot-stages">
          {stages.map((stage) => (
            <li
              key={stage.id}
              className={`boot-stage ${stage.done ? "is-done" : ""} ${
                !stage.done && stages.find((s) => !s.done)?.id === stage.id ? "is-active" : ""
              }`}
            >
              <span className="boot-stage-mark" aria-hidden="true" />
              <span>{stage.label}</span>
            </li>
          ))}
        </ul>

        <p className={`boot-status ${error ? "is-error" : ""}`}>{error || status}</p>
      </div>
    </div>
  );
}
