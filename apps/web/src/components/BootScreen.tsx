"use client";

import { useEffect, useMemo } from "react";
import { BrandMark } from "@/components/BrandMark";
import { LangSwitch } from "@/components/LangSwitch";
import { BRAZIL_SILHOUETTE_PATH } from "@/lib/brand";
import { useI18n } from "@/lib/i18n/I18nProvider";

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
  onRetry?: () => void;
};

export function BootScreen({
  stages,
  error,
  exiting = false,
  onExitComplete,
  onRetry,
}: Props) {
  const doneCount = stages.filter((s) => s.done).length;
  const progress = stages.length ? doneCount / stages.length : 0;
  const { t } = useI18n();
  const active = stages.find((s) => !s.done)?.label || t("boot.almost");

  const status = useMemo(() => {
    if (error) return t("boot.fail");
    if (exiting) return t("boot.opening");
    return active;
  }, [active, error, exiting, t]);

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
        <LangSwitch compact />
        <p className="boot-kicker">{t("boot.kicker")}</p>
        <h1 className="boot-brand">Brasil Real</h1>
        <p className="boot-line">{t("boot.line")}</p>

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
        {error && onRetry ? (
          <button type="button" className="boot-retry" onClick={onRetry}>
            {t("boot.retry")}
          </button>
        ) : null}
      </div>
    </div>
  );
}
