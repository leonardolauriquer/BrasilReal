# ADR 0001 — Stack inicial

## Status

Aceito

## Contexto

Precisamos de um monorepo auditável para mapa, API, dados e simulação, sem over-engineering.

## Decisão

- Frontend: Next.js + TypeScript + MapLibre
- API: FastAPI + Pydantic
- Dados MVP: fixtures JSON/GeoJSON versionadas
- Banco: PostgreSQL/PostGIS via Compose + Alembic
- Testes: pytest; CI GitHub Actions

## Consequências

MVP funciona offline-first via fixtures; Postgres fica pronto para Fase 2 sem bloquear o caminho crítico.
