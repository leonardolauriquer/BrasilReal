"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { setFormatLocale } from "@/lib/format";
import {
  LOCALES,
  LOCALE_META,
  detectLocale,
  persistLocale,
  setActiveLocale,
  type Locale,
} from "@/lib/i18n/locale";
import { MESSAGES } from "@/lib/i18n/messages";

type I18nValue = {
  locale: Locale;
  setLocale: (next: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18nValue | null>(null);

function interpolate(template: string, vars?: Record<string, string | number>) {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, name: string) =>
    vars[name] == null ? `{${name}}` : String(vars[name]),
  );
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("pt");

  useEffect(() => {
    const next = detectLocale();
    setLocaleState(next);
    setActiveLocale(next);
    setFormatLocale(LOCALE_META[next].bcp47);
    persistLocale(next);
  }, []);

  const setLocale = useCallback((next: Locale) => {
    if (!LOCALES.includes(next)) return;
    setLocaleState(next);
    setActiveLocale(next);
    setFormatLocale(LOCALE_META[next].bcp47);
    persistLocale(next);
  }, []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      const table = MESSAGES[locale] || MESSAGES.pt;
      const fallback = MESSAGES.pt[key];
      const raw = table[key] ?? fallback ?? key;
      return interpolate(raw, vars);
    },
    [locale],
  );

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    return {
      locale: "pt" as Locale,
      setLocale: () => undefined,
      t: (key: string, vars?: Record<string, string | number>) =>
        interpolate(MESSAGES.pt[key] ?? key, vars),
    };
  }
  return ctx;
}
