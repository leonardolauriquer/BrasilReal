"use client";

import { LOCALES, LOCALE_META } from "@/lib/i18n/locale";
import { useI18n } from "@/lib/i18n/I18nProvider";

type Props = {
  compact?: boolean;
};

export function LangSwitch({ compact = false }: Props) {
  const { locale, setLocale, t } = useI18n();
  return (
    <div
      className={`lang-switch ${compact ? "is-compact" : ""}`}
      role="group"
      aria-label={t("lang.label")}
    >
      {LOCALES.map((id) => (
        <button
          key={id}
          type="button"
          className={locale === id ? "is-on" : ""}
          aria-pressed={locale === id}
          title={LOCALE_META[id].native}
          onClick={() => setLocale(id)}
        >
          {LOCALE_META[id].short}
        </button>
      ))}
    </div>
  );
}
