"use client";

import { useI18n } from "@/lib/i18n/I18nProvider";

type Props = {
  title: string;
  disclaimer: string;
  onExit: () => void;
};

export function SimuladoBanner({ title, disclaimer, onExit }: Props) {
  const { t } = useI18n();
  return (
    <div className="sim-banner" role="status">
      <div>
        <p className="sim-kicker">{t("sim.kicker")}</p>
        <p className="sim-title">{title || t("sim.fund")}</p>
        <p className="sim-text">{disclaimer}</p>
      </div>
      <button type="button" onClick={onExit}>
        {t("sim.exit")}
      </button>
    </div>
  );
}
