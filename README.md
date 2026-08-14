# Brasil Real

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-20846b?style=flat-square)](.github/workflows)
[![Stack](https://img.shields.io/badge/stack-Next.js%20%2B%20FastAPI%20%2B%20MapLibre-0b3d2e?style=flat-square)](#arquitetura)
[![Dados](https://img.shields.io/badge/dados-s%C3%B3%20fontes%20oficiais-c45c26?style=flat-square)](#camadas-no-mapa)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-555?style=flat-square)](LICENSE)

> **Gêmeo digital exploratório do Brasil** — mapa vivo, números com fonte, simulações hipotéticas auditáveis.  
> **Não é** fonte oficial, parecer jurídico, previsão garantida nem sistema de decisão pública.

<p align="center">
  <a href="#o-que-%C3%A9"><strong>O que é</strong></a> ·
  <a href="#comece-em-5-minutos"><strong>Quickstart</strong></a> ·
  <a href="#camadas-no-mapa"><strong>Camadas</strong></a> ·
  <a href="#arquitetura"><strong>Arquitetura</strong></a> ·
  <a href="#ingest%C3%A3o--fontes-oficiais"><strong>Fontes</strong></a> ·
  <a href="#api"><strong>API</strong></a> ·
  <a href="#roadmap"><strong>Roadmap</strong></a>
</p>

---

## O que é

O **Brasil Real** trata o mapa como produto: você escolhe uma camada oficial, pinta as 27 UFs, clica e abre uma ficha com **definição, órgão, dataset, período e limitações**. Se faltar proveniência, o valor **não aparece** (`fail closed`).

| Isso | Não isso |
|---|---|
| Dados de IBGE, IPEA/DATASUS, MDIC, etc. | Números inventados ou “estimativa de IA” |
| Rótulos `OBSERVADO` / `ESTIMADO` / `SIMULADO` / `SEM DADO` | Misturar simulação com fato |
| Cenário fiscal **hipotético** com manifesto JSON | Parecer jurídico ou motor de decisão pública |
| LLM fora do cálculo de impacto | Chat que “chuta” PIB ou homicídios |

<details>
<summary><strong>Princípios duros</strong> (clique)</summary>

1. **Fonte antes de resposta** — todo número carrega organização + dataset + período.  
2. **Rótulos honestos** — `OBSERVADO`, `ESTIMADO`, `PROJETADO`, `SIMULADO`, `DERIVADO`, `SEM DADO`.  
3. **LLM não calcula impacto** — efeitos numéricos só em motores registrados.  
4. **Lei em texto ≠ lei em código** — catálogo jurídico sem fingir regras executáveis.  
5. **Nunca inventar dados** — sem canal oficial → backlog ou `SEM DADO`.

</details>

---

## Comece em 5 minutos

> Python **3.11–3.13** (recomendado **3.12**). Node 20+.

<table>
<tr>
<td width="50%">

### 1. API

```bash
cd apps/api
py -3.12 -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload --port 8000
```

</td>
<td width="50%">

### 2. Web

```bash
cd apps/web
npm install
npm run dev -- --port 3010
```

Abra **http://localhost:3010**

API docs: **http://localhost:8000/docs**

</td>
</tr>
</table>

No desenvolvimento local, **não** defina `NEXT_PUBLIC_API_URL` — o Next faz proxy same-origin de `/v1/*` (evita CORS).

<details>
<summary><strong>Docker Compose</strong> (web + api + Postgres/PostGIS)</summary>

```bash
cp .env.example .env
docker compose up --build
```

| Serviço | URL |
|---|---|
| Web | http://localhost:3000 |
| API | http://localhost:8000/docs |
| Postgres | `localhost:5432` |

O MVP lê **fixtures** em `data/fixtures`. O Postgres prepara o schema para fases seguintes.

</details>

<details>
<summary><strong>Atualizar dados oficiais (ingestão)</strong></summary>

```bash
cd workers/ingestion
python run.py --source ibge
python run.py --source territory
python run.py --source ipeadata
python run.py --source comex --comex-from 2022
# ou
python run.py --all
```

Snapshots brutos vão para `data/raw/` (gitignored). Fixtures validadas em `data/fixtures/`.

</details>

---

## Camadas no mapa

O seletor agrupa por domínio. Cada camada exige tooltip com definição + fonte.

| Grupo | Camadas | Origem |
|---|---|---|
| **Economia / demografia** | População, PIB | IBGE Agregados |
| **Social** | Pobreza, alfabetização, desocupação | IBGE (ODS / Censo / PNAD) |
| **Agro / comércio** | Export. carnes (SH 02), bovina (0201+0202), soja (1201) | MDIC Comex Stat |
| **Segurança** | Homicídios /100 mil, nº de homicídios | Ipeadata ← SIM/DATASUS |
| **Saúde** | Óbitos de trânsito /100 mil | Ipeadata ← SIM/DATASUS |
| **Ficha (não são camadas)** | Indígenas, quilombolas, área, biomas, costeiro | IBGE |

<details>
<summary><strong>O que ainda NÃO entra no mapa (honestidade)</strong></summary>

| Ideia | Motivo |
|---|---|
| COVID casos/óbitos | APIs do painel MS / OpenDataSUS sem canal estável aberto |
| Processos judiciais | CNJ DataJud exige credencial |
| Milionários / bilionários por UF | Sem agregado oficial; listas privadas ≠ fonte do produto |
| APP (preservação permanente) completa | Sem série oficial limpa por UF pronta para choropleth |
| Consumo de carne | POF — validar granularidade UF vs região |

Regra de produto: **3–5 âncoras por domínio**; resto só com canal oficial + definição.

</details>

---

## Arquitetura

```mermaid
flowchart LR
  subgraph Fontes
    IBGE[IBGE Agregados / Malhas]
    IPEA[Ipeadata / DATASUS]
    MDIC[Comex Stat MDIC]
    STN[SICONFI / Tesouro]
  end

  subgraph Ingestão
    W[workers/ingestion]
    RAW[(data/raw gitignored)]
    FIX[(data/fixtures versionadas)]
  end

  subgraph Runtime
    API[apps/api FastAPI]
    WEB[apps/web Next.js + MapLibre]
  end

  IBGE --> W
  IPEA --> W
  MDIC --> W
  STN --> W
  W --> RAW
  W --> FIX
  FIX --> API
  API --> WEB
```

```text
BrasilReal/
├── apps/
│   ├── web/          # Next.js 15 · MapLibre · ficha flutuante
│   └── api/          # FastAPI · fixtures · motor de cenário
├── workers/ingestion # Conectores oficiais idempotentes
├── data/fixtures/    # Artefatos validados (commitados)
├── data/raw/         # Snapshots brutos (gitignored)
├── docs/             # Visão, ADRs, fontes, roadmap
├── infra/            # Docker / compose auxiliares
└── AGENTS.md         # Regras para agentes de código
```

| Peça | Tecnologia |
|---|---|
| Mapa | MapLibre GL (sem chave proprietária) |
| Front | Next.js (App Router), TypeScript |
| API | FastAPI, Pydantic, pytest |
| Dados | Fixtures JSON + ingestão Python (`urllib`) |
| Cenário | Motor determinístico de rateio hipotético + manifesto |

---

## Ingestão & fontes oficiais

Pipeline: **API/arquivo oficial → snapshot bruto + checksum → fixture validada → API do produto**.

| Domínio | Canal | Status |
|---|---|---|
| População / PIB / social | [IBGE Agregados](https://servicodados.ibge.gov.br/api/docs/agregados) | Automatizado |
| Malha UF / município | [IBGE Malhas](https://servicodados.ibge.gov.br/api/docs/malhas) | Automatizado |
| Homicídios / trânsito | [Ipeadata](http://www.ipeadata.gov.br/) (SIM/DATASUS) | Automatizado |
| Exportações agro | [Comex Stat](https://comexstat.mdic.gov.br/) / [API MDIC](https://api-comexstat.mdic.gov.br/docs) | Automatizado |
| Território / povos | IBGE 9718, 9727, 1301, biomas FTP | Ficha |
| Fiscal (próximo) | [SICONFI](https://apidatalake.tesouro.gov.br/docs/siconfi/) · Tesouro CKAN | Probe / Fase 2 |

Matriz completa, limitações e backlog: **[`docs/data-sources.md`](docs/data-sources.md)**.

<details>
<summary><strong>Comandos de ingestão por fonte</strong></summary>

```bash
cd workers/ingestion
python run.py --source ibge --ibge-pop 2025
python run.py --source territory
python run.py --source ipeadata          # ~2 min (séries grandes)
python run.py --source comex --comex-from 2022
python run.py --source siconfi
python run.py --source tesouro
```

- **Ipeadata:** OData não filtra por UF; o conector baixa a série e seleciona `NIVNOME=Estados`.  
- **Comex:** só anos-civis completos; UF sem operação = `0` declarado; “Não Declarada” fora do mapa.

</details>

---

## API

Prefixo `/v1`. OpenAPI em `/docs`.

| Método | Rota | Uso |
|---|---|---|
| `GET` | `/v1/indicators` | Lista camadas (grupo, unidade, proveniência) |
| `GET` | `/v1/indicators/{id}/periods` | Anos/períodos válidos |
| `GET` | `/v1/observations?indicator=&period=` | Valores por UF |
| `GET` | `/v1/geographies` | 27 UFs |
| `GET` | `/v1/geographies/{code}/profile` | Ficha da UF |
| `GET` | `/v1/geographies/municipalities/{code}/profile` | Ficha municipal (território) |
| `GET` | `/v1/geographies/states/{uf}/municipalities` | Malha + pop. no zoom |
| `POST` | `/v1/scenarios` · `…/run` · `…/manifest` | Cenário hipotético auditável |

Testes:

```bash
cd apps/api
pytest -q
```

---

## UX do mapa (resumo)

- Mapa **full-bleed**; ficha flutuante no clique (não corta o Brasil).  
- Seletor de **camada** + **ano/período** sincronizados.  
- Zoom → municípios da UF selecionada.  
- Todo número da ficha com **InfoTip** (definição + fonte + limitações).  
- Escala “quanto maior, pior” nas taxas de segurança/saúde.

---

## Roadmap

| Fase | Foco |
|---|---|
| **1** ✓ | Fundação: 27 UFs, mapa, proveniência, cenário hipotético |
| **2** | Brasil fiscal observado (SICONFI, transferências União ↔ UF) |
| **3** | Regras federais selecionadas (rules-as-code + vigência) |
| **4** | Municípios + população sintética |
| **5** | Educação, saúde, trabalho, infraestrutura |
| **6** | Agentes / choques (só após calibração) |
| **7** | Cobertura jurídica federativa |

Detalhes: [`docs/roadmap.md`](docs/roadmap.md) · [`docs/implementation-plan.md`](docs/implementation-plan.md)

---

## Documentação técnica

| Doc | Conteúdo |
|---|---|
| [`docs/data-sources.md`](docs/data-sources.md) | Matriz de fontes, ingestão, backlog honesto |
| [`docs/roadmap.md`](docs/roadmap.md) | Fases do produto |
| [`docs/implementation-plan.md`](docs/implementation-plan.md) | Aceite Fase 1 |
| [`docs/adr/`](docs/adr/) | Decisões de arquitetura (stack, LLM boundary…) |
| [`AGENTS.md`](AGENTS.md) | Regras para agentes de código neste repo |

---

## Referências oficiais (entrada)

- [IBGE — API de Agregados](https://servicodados.ibge.gov.br/api/docs/agregados)  
- [IBGE — Localidades](https://servicodados.ibge.gov.br/api/docs/localidades) · [Malhas](https://servicodados.ibge.gov.br/api/docs/malhas)  
- [SIDRA](https://sidra.ibge.gov.br/) (tabelas 6579, 5938, 5877, 9543, 4099, 9718, 9727, 1301…)  
- [Ipeadata](http://www.ipeadata.gov.br/) · séries Atlas da Violência / SIM  
- [Comex Stat (MDIC)](https://comexstat.mdic.gov.br/) · [API ComexStat](https://api-comexstat.mdic.gov.br/docs)  
- [SICONFI — API Tesouro](https://apidatalake.tesouro.gov.br/docs/siconfi/)  
- [Tesouro Transparente — transferências](https://www.tesourotransparente.gov.br/ckan/dataset/api-de-transferencias-constitucionais)  
- [FUNAI — geoprocessamento / terras indígenas](https://www.gov.br/funai/pt-br/atuacao/terras-indigenas/geoprocessamento-e-mapas) *(próximas camadas de área TI)*

---

## Contribuindo

1. Preferir o próximo item da **Fase atual** do roadmap.  
2. Diffs cirúrgicos — sem docs “por precaução”.  
3. Toda nova camada precisa de **definition + source + limitations** antes da UI.  
4. Não commitar `.env`, `scratch/`, `data/raw/`, `*_log.txt`, credenciais.  
5. Rodar `pytest` na API após mudanças de store/ingestão.

---

## Licença

Código sob [MIT](LICENSE).  
Os **dados** pertencem aos órgãos oficiais citados; respeite os termos de cada portal. Este repositório republica agregados para fins educacionais/exploratórios com proveniência explícita.

---

<p align="center">
  <em>Mapa primeiro. Fonte sempre. Simulação nunca disfarçada de fato.</em>
</p>
