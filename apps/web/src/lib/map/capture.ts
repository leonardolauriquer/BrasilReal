let canvasGetter: (() => HTMLCanvasElement | null) | null = null;

export function registerMapCanvas(getter: (() => HTMLCanvasElement | null) | null) {
  canvasGetter = getter;
}

export function getMapCanvas() {
  return canvasGetter?.() ?? null;
}

export type MapPngMeta = {
  layerLabel: string;
  period: string;
  status: string;
  organization?: string;
  url?: string;
};

export function downloadMapPng(meta: MapPngMeta): boolean {
  const mapCanvas = getMapCanvas();
  if (!mapCanvas || mapCanvas.width < 8 || mapCanvas.height < 8) return false;

  const footerPx = Math.max(72, Math.round(mapCanvas.height * 0.08));
  const out = document.createElement("canvas");
  out.width = mapCanvas.width;
  out.height = mapCanvas.height + footerPx;
  const ctx = out.getContext("2d");
  if (!ctx) return false;

  ctx.fillStyle = "#0e1713";
  ctx.fillRect(0, 0, out.width, out.height);
  ctx.drawImage(mapCanvas, 0, 0);

  ctx.fillStyle = "#121c18";
  ctx.fillRect(0, mapCanvas.height, out.width, footerPx);

  const pad = Math.round(footerPx * 0.22);
  const titleSize = Math.max(14, Math.round(footerPx * 0.28));
  ctx.fillStyle = "#eef5f1";
  ctx.font = `600 ${titleSize}px Georgia, serif`;
  ctx.fillText("Brasil Real", pad, mapCanvas.height + pad + titleSize * 0.35);

  const observed = meta.status === "OBSERVADO" || meta.status === "ESTIMADO";
  const line = [
    meta.layerLabel,
    meta.period,
    meta.status,
    meta.organization,
    meta.url,
  ]
    .filter(Boolean)
    .join(" · ");
  const subSize = Math.max(11, Math.round(footerPx * 0.18));
  ctx.fillStyle = observed ? "#7ec8ff" : "#f3c16b";
  ctx.font = `600 ${subSize}px ui-sans-serif, system-ui, sans-serif`;
  ctx.fillText(line, pad, mapCanvas.height + pad + titleSize + subSize * 0.9);

  if (!observed) {
    ctx.fillStyle = "#f3c16b";
    ctx.font = `700 ${Math.max(10, subSize - 1)}px ui-sans-serif, system-ui, sans-serif`;
    ctx.fillText(
      "Não é fato observado — rótulo " + meta.status + ".",
      pad,
      mapCanvas.height + footerPx - pad * 0.45,
    );
  }

  const stamp = new Date().toISOString().slice(0, 10);
  const slug = meta.layerLabel
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 40);
  const a = document.createElement("a");
  a.href = out.toDataURL("image/png");
  a.download = `brasil-real-${slug || "mapa"}-${stamp}.png`;
  a.click();
  return true;
}
