/** Chrome insets for MapLibre — keep breakpoints aligned with globals.css. */

export type ChromePadding = {
  top: number;
  right: number;
  bottom: number;
  left: number;
};

export const VIEW = {
  phone: 640,
  tablet: 1100,
  short: 560,
} as const;

export function mapChromePadding(cardOpen = false): ChromePadding {
  if (typeof window === "undefined") {
    return { top: 28, right: 400, bottom: 40, left: 300 };
  }
  const w = window.innerWidth;
  const h = window.innerHeight;
  const compact = h < VIEW.short;
  const phone = w < VIEW.phone;

  if (compact) {
    const sheet = cardOpen ? Math.min(h * 0.58, 280) : Math.min(h * 0.24, 128);
    return { top: 70, right: 10, left: 10, bottom: sheet + 16 };
  }
  if (phone) {
    const sheet = cardOpen ? Math.min(h * 0.62, 520) : Math.min(h * 0.34, 288);
    return { top: 84, right: 12, left: 12, bottom: sheet + 18 };
  }
  if (w < VIEW.tablet) {
    return { top: 24, right: 316, bottom: 28, left: 256 };
  }
  return { top: 28, right: 400, bottom: 40, left: 300 };
}
