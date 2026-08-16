export const PWA_DISMISS_KEY = "br.pwa.install.dismissedAt";
export const PWA_SNOOZE_MS = 21 * 24 * 60 * 60 * 1000;

export type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

export function isStandaloneDisplay(): boolean {
  if (typeof window === "undefined") return false;
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    window.matchMedia("(display-mode: fullscreen)").matches ||
    Boolean((navigator as Navigator & { standalone?: boolean }).standalone)
  );
}

export function isIosSafari(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent;
  const iOS =
    /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const webkit = /WebKit/i.test(ua);
  const notOther = !/CriOS|FxiOS|EdgiOS|OPiOS|DuckDuckGo/i.test(ua);
  return iOS && webkit && notOther;
}

export function shouldOfferInstall(opts: {
  standalone: boolean;
  canPrompt: boolean;
  iosSafari: boolean;
  dismissedAt: number | null;
  now: number;
}): boolean {
  if (opts.standalone) return false;
  if (!opts.canPrompt && !opts.iosSafari) return false;
  if (opts.dismissedAt != null && opts.now - opts.dismissedAt < PWA_SNOOZE_MS) return false;
  return true;
}

export function readDismissedAt(storage: Pick<Storage, "getItem"> | null): number | null {
  if (!storage) return null;
  const raw = storage.getItem(PWA_DISMISS_KEY);
  if (!raw) return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

export function writeDismissedAt(storage: Pick<Storage, "setItem"> | null, at: number) {
  storage?.setItem(PWA_DISMISS_KEY, String(at));
}
