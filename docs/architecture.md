# Arquitetura

## Diagrama lógico

```mermaid
flowchart TD
    A[Fontes oficiais] --> B[Ingestão e proveniência]
    B --> C[Fixtures / armazém bruto]
    B --> D[PostgreSQL e PostGIS]
    C --> E[Motor de cenários]
    D --> E
    E --> G[API FastAPI]
    G --> H[Mapa, linha do tempo e painel]
```

## Limites dos componentes

| Componente | Responsabilidade | Não faz |
|---|---|---|
| `apps/web` | UX, mapa, tabela acessível, export | Cálculo de impacto |
| `apps/api` | Consultas, orquestração, manifesto | Scraping ad hoc em request |
| `workers/ingestion` | Conectores idempotentes | Alterar regras publicadas |
| `services/fund_engine` | Rateio contábil determinístico | Efeitos comportamentais |
| PostgreSQL/PostGIS | Schema durável (próximas fases) | Substituir fixtures no MVP |

## Runtime do MVP

A API sobe em modo `fixtures`: carrega `data/fixtures/ibge/population_uf_2025.json` e o catálogo legal. O Postgres sobe no Compose para validar o caminho de migrations; a leitura pública do MVP não depende dele.
