# ADR 0002 — Tempo bitemporal

## Status

Aceito (schema preparado; UX ainda mono-período)

## Contexto

Normas e observações revisáveis exigem distinguir vigência de conhecimento do sistema.

## Decisão

Modelar `valid_from/valid_to` (mundo) e `recorded_at` / revisões (sistema) nas tabelas `geography`, `observation` e futuras `legal_version`.

## Consequências

Migrations já antecipam o modelo; o MVP expõe apenas o período 2025-07-01.
