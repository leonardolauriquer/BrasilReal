import { SITE_URL } from "@/lib/brand";
import { RECORTE_OPTIONS, type RecorteId } from "@/lib/map/regions";

export type RankMode = "nivel" | "delta";
export type ColorMode = "default" | "cb";

export type AtlasView = {
  camada: string;
  ano: string;
  uf: string;
  recorte: RecorteId;
  modo: RankMode;
  vs: string[];
  sim: boolean;
  cor: ColorMode;
};

const RECORTE_SET = new Set(RECORTE_OPTIONS.map((o) => o.value));

function readSearch(search?: string) {
  if (search != null) return new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  if (typeof window === "undefined") return new URLSearchParams();
  return new URLSearchParams(window.location.search);
}

function parseVs(raw: string | null): string[] {
  if (!raw) return [];
  const seen = new Set<string>();
  const out: string[] = [];
  for (const part of raw.split(",")) {
    const token = part.trim().toUpperCase();
    if (!token || seen.has(token) || out.length >= 3) continue;
    seen.add(token);
    out.push(token);
  }
  return out;
}

export function parseViewUrl(search?: string): AtlasView {
  const q = readSearch(search);
  const recorteRaw = q.get("recorte") || "BR";
  const modoRaw = q.get("modo");
  return {
    camada: (q.get("camada") || "").trim(),
    ano: (q.get("ano") || "").trim(),
    uf: (q.get("uf") || "").trim().toUpperCase(),
    recorte: RECORTE_SET.has(recorteRaw as RecorteId) ? (recorteRaw as RecorteId) : "BR",
    modo: modoRaw === "delta" ? "delta" : "nivel",
    vs: parseVs(q.get("vs")),
    sim: q.get("sim") === "1",
    cor: q.get("cor") === "cb" ? "cb" : "default",
  };
}

export function viewSearchParams(view: AtlasView): URLSearchParams {
  const q = new URLSearchParams();
  if (view.camada && view.camada !== "population") q.set("camada", view.camada);
  if (view.ano) q.set("ano", view.ano);
  if (view.uf) q.set("uf", view.uf);
  if (view.recorte && view.recorte !== "BR") q.set("recorte", view.recorte);
  if (view.modo === "delta") q.set("modo", "delta");
  if (view.vs.length) q.set("vs", view.vs.join(","));
  if (view.sim) q.set("sim", "1");
  if (view.cor === "cb") q.set("cor", "cb");
  if (typeof window !== "undefined") {
    const lang = new URLSearchParams(window.location.search).get("lang");
    if (lang) q.set("lang", lang);
  }
  return q;
}

export function atlasHref(view: AtlasView, origin = SITE_URL): string {
  const qs = viewSearchParams(view).toString();
  return `${origin}/${qs ? `?${qs}` : ""}`;
}

/** Hosting rewrite `/s` → API HTML (crawlers) or 302 to the atlas (humans). */
export function shareHref(view: AtlasView, origin?: string): string {
  const base =
    origin ||
    (typeof window !== "undefined" ? window.location.origin : SITE_URL);
  const qs = viewSearchParams(view).toString();
  return `${base}/s${qs ? `?${qs}` : ""}`;
}

export function writeViewUrl(view: AtlasView) {
  if (typeof window === "undefined") return;
  const q = viewSearchParams(view);
  const lang = new URLSearchParams(window.location.search).get("lang");
  if (lang) q.set("lang", lang);
  const qs = q.toString();
  const next = `${window.location.pathname}${qs ? `?${qs}` : ""}${window.location.hash}`;
  const cur = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (next !== cur) window.history.replaceState(window.history.state, "", next);
}

export async function copyViewUrl(view?: AtlasView): Promise<boolean> {
  if (typeof window === "undefined") return false;
  const href = view ? shareHref(view) : shareHref(parseViewUrl());
  try {
    await navigator.clipboard.writeText(href);
    return true;
  } catch {
    return false;
  }
}

export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (target.isContentEditable) return true;
  return Boolean(target.closest("[role=dialog], [role=listbox], .gselect-panel"));
}
