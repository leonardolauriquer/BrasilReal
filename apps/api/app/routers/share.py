"""Share cards for crawlers — labels only, no invented numbers."""

from __future__ import annotations

import html
import re
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.store import store

ATLAS_ORIGIN = "https://brasilreal-atlas.web.app"
OG_IMAGE = f"{ATLAS_ORIGIN}/og.png"
SITE_DESCRIPTION = (
    "Atlas exploratório do Brasil com dados oficiais, fonte e período em cada número."
)

RECORTE_LABELS = {
    "BR": "Brasil (27 UFs)",
    "N": "Norte",
    "NE": "Nordeste",
    "CO": "Centro-Oeste",
    "SE": "Sudeste",
    "S": "Sul",
    "litoral": "Litoral",
    "fronteira": "Fronteira",
}
ALLOWED_RECORTE = set(RECORTE_LABELS)
BOT_MARKERS = (
    "facebookexternalhit",
    "facebot",
    "whatsapp",
    "twitterbot",
    "slackbot",
    "linkedinbot",
    "discordbot",
    "telegrambot",
    "pinterest",
    "skypeuripreview",
    "applebot",
    "googlebot",
    "bingbot",
    "embedly",
    "redditbot",
    "iframely",
    "vkshare",
    "notion",
    "preview",
)

_CAMADA_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_PERIOD_RE = re.compile(r"^[0-9][0-9A-Za-z._-]{0,15}$")
_UF_RE = re.compile(r"^[A-Z]{2}$")

router = APIRouter(tags=["share"])


def _is_crawler(request: Request) -> bool:
    ua = (request.headers.get("user-agent") or "").lower()
    if request.query_params.get("format") == "html":
        return True
    return any(marker in ua for marker in BOT_MARKERS)


def _clean_camada(raw: str) -> str:
    token = (raw or "").strip()
    return token if _CAMADA_RE.match(token) else ""


def _clean_period(raw: str) -> str:
    token = (raw or "").strip()
    return token if _PERIOD_RE.match(token) else ""


def _clean_uf(raw: str) -> str:
    token = (raw or "").strip().upper()
    return token if _UF_RE.match(token) else ""


def _clean_recorte(raw: str) -> str:
    token = (raw or "BR").strip()
    return token if token in ALLOWED_RECORTE else "BR"


def _view_query(request: Request) -> dict[str, str]:
    q = request.query_params
    out: dict[str, str] = {}
    camada = _clean_camada(q.get("camada") or "")
    if camada:
        out["camada"] = camada
    ano = _clean_period(q.get("ano") or "")
    if ano:
        out["ano"] = ano
    uf = _clean_uf(q.get("uf") or "")
    if uf:
        out["uf"] = uf
    recorte = _clean_recorte(q.get("recorte") or "BR")
    if recorte != "BR":
        out["recorte"] = recorte
    if (q.get("modo") or "") == "delta":
        out["modo"] = "delta"
    vs_raw = (q.get("vs") or "").strip().upper()
    vs_parts = [p for p in vs_raw.split(",") if _UF_RE.match(p.strip())][:3]
    if vs_parts:
        out["vs"] = ",".join(vs_parts)
    if q.get("sim") == "1":
        out["sim"] = "1"
    if (q.get("cor") or "") == "cb":
        out["cor"] = "cb"
    return out


def _indicator_label(camada: str) -> str:
    if not camada:
        return "População"
    if camada == "population":
        return "População"
    for item in store.list_indicators():
        if item.get("id") == camada:
            return str(item.get("short_name") or item.get("name") or camada)
    return camada


def _uf_label(uf: str) -> str:
    if not uf:
        return ""
    for geo in store.list_geographies():
        if geo.get("uf") == uf:
            return f"{uf} · {geo.get('name') or uf}"
    return uf


def _share_copy(query: dict[str, str]) -> tuple[str, str]:
    camada = query.get("camada") or "population"
    layer = _indicator_label(camada)
    recorte = RECORTE_LABELS.get(query.get("recorte") or "BR", "Brasil (27 UFs)")
    period = query.get("ano") or ""
    uf = _uf_label(query.get("uf") or "")
    bits = [layer]
    if recorte != "Brasil (27 UFs)":
        bits.append(recorte)
    if period:
        bits.append(period)
    if uf:
        bits.append(uf)
    if query.get("modo") == "delta":
        bits.append("variação")
    if query.get("sim") == "1":
        bits.append("SIMULADO")
    title = f"{' · '.join(bits)} | Brasil Real"
    description = (
        f"{SITE_DESCRIPTION} Vista: {layer}"
        f"{', recorte ' + recorte if recorte else ''}"
        f"{', período ' + period if period else ''}. "
        "Os números estão no mapa, com fonte — esta prévia não calcula impacto."
    )
    return title, description


def _atlas_url(query: dict[str, str]) -> str:
    qs = urlencode(query)
    return f"{ATLAS_ORIGIN}/{('?' + qs) if qs else ''}"


def _og_html(title: str, description: str, canonical: str) -> str:
    t = html.escape(title, quote=True)
    d = html.escape(description, quote=True)
    u = html.escape(canonical, quote=True)
    img = html.escape(OG_IMAGE, quote=True)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>{t}</title>
  <meta name="description" content="{d}" />
  <link rel="canonical" href="{u}" />
  <meta property="og:type" content="website" />
  <meta property="og:locale" content="pt_BR" />
  <meta property="og:site_name" content="Brasil Real" />
  <meta property="og:title" content="{t}" />
  <meta property="og:description" content="{d}" />
  <meta property="og:url" content="{u}" />
  <meta property="og:image" content="{img}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{t}" />
  <meta name="twitter:description" content="{d}" />
  <meta name="twitter:image" content="{img}" />
  <meta http-equiv="refresh" content="0;url={u}" />
</head>
<body>
  <p><a href="{u}">{t}</a></p>
</body>
</html>
"""


def share_response(request: Request):
    query = _view_query(request)
    dest = _atlas_url(query)
    if not _is_crawler(request):
        return RedirectResponse(dest, status_code=302)
    title, description = _share_copy(query)
    return HTMLResponse(_og_html(title, description, dest))


@router.get("/s")
@router.get("/s/")
@router.get("/share")
@router.get("/v1/share")
def share(request: Request):
    return share_response(request)
