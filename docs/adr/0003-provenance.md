# ADR 0003 — Proveniência primeiro

## Status

Aceito

## Contexto

Números sem fonte destroem a confiança do produto.

## Decisão

Todo indicador exibido carrega `status_label`, fonte, datas e dataset id. Fixtures incluem `checksum_sha256`. Lacunas = `SEM DADO`.

## Consequências

Ingestões futuras devem gerar dataset cards e artifacts imutáveis antes de publicar observações.
