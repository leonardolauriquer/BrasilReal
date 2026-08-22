export type Locale = "pt" | "en" | "es";

export const LOCALES: Locale[] = ["pt", "en", "es"];

export const LOCALE_META: Record<
  Locale,
  { bcp47: string; short: string; native: string }
> = {
  pt: { bcp47: "pt-BR", short: "PTBR", native: "Português" },
  en: { bcp47: "en", short: "ENG", native: "English" },
  es: { bcp47: "es", short: "ESP", native: "Español" },
};

const STORAGE_KEY = "br-lang";

let active: Locale = "pt";

export function getLocale(): Locale {
  return active;
}

export function setActiveLocale(next: Locale) {
  active = next;
}

export function parseLocale(raw: string | null | undefined): Locale | null {
  if (!raw) return null;
  const token = raw.trim().toLowerCase().replace("_", "-");
  if (token === "pt" || token === "pt-br" || token === "pt-pt") return "pt";
  if (token === "en" || token.startsWith("en-")) return "en";
  if (token === "es" || token.startsWith("es-")) return "es";
  return null;
}

export function detectLocale(): Locale {
  if (typeof window !== "undefined") {
    const fromUrl = parseLocale(new URLSearchParams(window.location.search).get("lang"));
    if (fromUrl) return fromUrl;
    try {
      const stored = parseLocale(window.localStorage.getItem(STORAGE_KEY));
      if (stored) return stored;
    } catch {
      /* ignore */
    }
    const nav = parseLocale(window.navigator.language);
    if (nav) return nav;
  }
  return "pt";
}

export function persistLocale(locale: Locale) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    /* ignore */
  }
  const url = new URL(window.location.href);
  if (locale === "pt") url.searchParams.delete("lang");
  else url.searchParams.set("lang", locale);
  const next = `${url.pathname}${url.search}${url.hash}`;
  const cur = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (next !== cur) window.history.replaceState(window.history.state, "", next);
  document.documentElement.lang = LOCALE_META[locale].bcp47;
}
