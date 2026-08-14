# Fontes de dados e automação

## Resposta curta

**Sim, existem APIs públicas oficiais** — e o caminho certo é automatizar ingestão por conectores idempotentes.
**Não:** quase nenhum desses dados é “tempo real” estilo cotação a cada segundo. São séries **periódicas** (diária/mensal/bimestral/anual) com **defasagem** e revisões.

Regra do Brasil Real: preferir API/arquivo oficial → snapshot bruto imutável → fixture validada → API do produto. Se a API falhar, mostrar `SEM DADO` (nunca inventar).

## Matriz de automação

| Domínio | Canal oficial | Periodicidade típica | Tempo real? | Status no repo |
|---|---|---|---|---|
| UFs / municípios | [IBGE Localidades](https://servicodados.ibge.gov.br/api/docs/localidades) | sob demanda | metadados | Automatizado |
| Malha territorial | [IBGE Malhas](https://servicodados.ibge.gov.br/api/docs/malhas) | sob demanda | não | Automatizado |
| População UF | [IBGE Agregados 6579](https://servicodados.ibge.gov.br/api/docs/agregados) | anual | **não** | Automatizado |
| PIB UF | [IBGE Agregados 5938 / var 37](https://servicodados.ibge.gov.br/api/docs/agregados) | anual (defasado) | **não** | Automatizado |
| Pobreza UF | [IBGE 5877 / ODS 1.2.1](https://sidra.ibge.gov.br/tabela/5877) | anual | **não** | Automatizado |
| Alfabetização 15+ | [IBGE 9543 Censo](https://sidra.ibge.gov.br/tabela/9543) | censitária | **não** | Automatizado |
| Desocupação | [IBGE 4099 PNADC](https://sidra.ibge.gov.br/tabela/4099) | trimestral | quase | Automatizado |
| Taxa de homicídios UF | [Ipeadata AVIOL12_THOMIC](http://www.ipeadata.gov.br/ExibeSerie.aspx?serid=AVIOL12_THOMIC) (IPEA/DATASUS) | anual | **não** | Automatizado |
| Nº de homicídios UF | [Ipeadata AVIOL12_HOMIC](http://www.ipeadata.gov.br/ExibeSerie.aspx?serid=AVIOL12_HOMIC) | anual | **não** | Automatizado |
| Óbitos trânsito /100 mil | [Ipeadata AVIOL12_TACIDT](http://www.ipeadata.gov.br/ExibeSerie.aspx?serid=AVIOL12_TACIDT) | anual | **não** | Automatizado |
| Export. carnes (SH 02) | [Comex Stat MDIC](https://comexstat.mdic.gov.br/) API `/general` | anual | **não** | Automatizado |
| Export. bovina (0201+0202) | Comex Stat headings 0201/0202 | anual | **não** | Automatizado |
| Export. soja grão (1201) | Comex Stat heading 1201 | anual | **não** | Automatizado |
| Consumo de carne | IBGE POF | plurianual | **não** | Backlog (poucos anos; checar granularidade UF) |
| Patrimônio / milionários | — | — | — | **SEM CANAL** por UF (listas privadas ≠ oficial) |
| COVID (casos/óbitos) | Painel MS / OpenDataSUS | histórica | **não** | **SEM canal estável** (APIs públicas do painel desativadas / CKAN 401) |
| Processos judiciais | CNJ DataJud | contínua | **não** | **Bloqueado** (API exige credencial; sem chave no produto) |
| Indígenas UF/mun | [IBGE 9718 Censo 2022](https://sidra.ibge.gov.br/tabela/9718) | censitária | **não** | Ficha territorial |
| Quilombolas UF/mun | [IBGE 9727 Censo 2022](https://sidra.ibge.gov.br/tabela/9727) | censitária | **não** | Ficha territorial |
| Área territorial | [IBGE 1301](https://sidra.ibge.gov.br/tabela/1301) | 2010 | **não** | Ficha territorial |
| Bioma predominante | [IBGE FTP biomas 2024](https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/documentos/) | referência 2024 | **não** | Ficha territorial |
| Costeiro/marinho | Lista IBGE CosteiroMarinho | referência lista | **não** | Ficha territorial |
| Detecção ano novo | [FTP Estimativas](https://ftp.ibge.gov.br/Estimativas_de_Populacao/) | anual | não | Automatizado |
| Contas/RREO/MSC | [SICONFI API](https://apidatalake.tesouro.gov.br/docs/siconfi/) | mensal/bimestral | **não** | Probe + snapshot |
| Transferências | [Tesouro CKAN](https://www.tesourotransparente.gov.br/ckan/dataset/api-de-transferencias-constitucionais) | mensal | **não** | Discovery |
| Arrecadação | ReceitaData / dados abertos RFB | mensal | **não** | Fase 2 |
| Séries macro | [BCB Dados Abertos](https://dadosabertos.bcb.gov.br/) | diária/mensal | quase (séries) | Fase 2 |
| Legislação | LexML / Planalto / INLABS | contínua editorial | texto ≠ regra | Catálogo inicial |
| Proposições | Câmara / Senado dados abertos | frequente | tramitação | Fase 3+ |

## Como rodar a ingestão

```bash
cd workers/ingestion
python run.py --all
python run.py --source ibge --ibge-pop 2025
python run.py --source ibge --ibge-pop last
python run.py --source siconfi
python run.py --source tesouro
python run.py --source territory
python run.py --source ipeadata
python run.py --source comex
python run.py --source comex --comex-from 2020
```

### Comércio exterior (Comex Stat)

Ingestão: `python run.py --source comex` → `data/fixtures/comex/indicators/`.

API oficial MDIC (`api-comexstat.mdic.gov.br`). Respeitar rate-limit (429 → retry). UFs sem operação no ano ficam com **0** (declarado), não inventadas.

### Backlog de camadas (pensar antes de shippar)

| Ideia | Canal candidato | Bloqueio |
|---|---|---|
| Consumo de carne / POF | IBGE POF | Poucos anos; validar UF vs região |
| Farelo/óleo soja, milho, minério | Comex Stat | Só falta priorizar NCM/SH |
| Renda / desigualdade | PNAD Contínua IBGE | OK — próximo social |
| Arrecadação / gasto UF | SICONFI / ReceitaData | Roadmap Fase 2 |
| Milionários / bilionários | — | Sem agregado oficial por UF |
| Patrimônio (público) | SICONFI / Balanço | Definir métrica (ativo? dívida?) |
| COVID | — | Sem API estável |
| Processos judiciais | CNJ DataJud | Credencial |

Regra de produto: **3–5 âncoras por domínio** no seletor; resto em busca/catálogo depois. Sem fonte → não entra no mapa.

### Camadas de segurança / saúde (Ipeadata)

Ingestão: `python run.py --source ipeadata` → `data/fixtures/ipeadata/indicators/`.

Séries oficiais republicadas no Ipeadata (origem SIM/DATASUS + Atlas da Violência/IPEA). O OData **não filtra** por UF; o conector baixa a série e seleciona `NIVNOME=Estados`.

**Ainda sem dado no mapa (honestidade):** COVID (APIs do painel covid.saude.gov.br / OpenDataSUS sem endpoint estável aberto) e processos judiciais (CNJ DataJud com autenticação). Até existir canal oficial reproduzível → `SEM DADO`, nunca inventar.

## Ficha territorial + tooltip obrigatório

Na UI, **todo** número/texto da ficha (e camadas do mapa) exige:

1. `definition` — o que é  
2. `source.organization` + `source.dataset` — de onde veio (só órgãos oficiais)  
3. `reference_period` + `status_label`  
4. `limitations[]` quando `DERIVADO` ou cobertura parcial  

Fail closed: sem definition/source, o valor **não é renderizado**.

Ingestão territorial: `python run.py --source territory` → `data/fixtures/territory/`.

### Onda 1 (no produto)

Indígenas, quilombolas, área (2010), bioma predominante / biomas presentes na UF, densidade derivada (população recente ÷ área 2010), município costeiro/marinho.

### Onda 2+ (ainda não)

Temperatura (estação INMET mais próxima), mineração (ANM/CPRM — processos, não inventário), fauna (ocorrências SiBBr — amostra, não censo). Sempre com tooltip de cobertura.

Saídas:

- `data/raw/<fonte>/<timestamp>/` — snapshot bruto + checksum (gitignored)
- `data/fixtures/...` — artefatos consumidos pela API
- `apps/web/public/geo/uf_br.geojson` — malha do mapa (quando IBGE malha roda)

## O que “automatizar ao máximo” significa aqui

1. **Detectar** publicação nova (ex.: pasta `Estimativas_2026` no FTP).
2. **Baixar** via API estruturada (Agregados/SICONFI/CKAN), não scraping frágil.
3. **Validar** invariantes (27 UFs, soma = total Brasil, schema).
4. **Versionar** checksum + `retrieved_at` + dataset card.
5. **Publicar** no runtime só depois da validação.
6. Agendar (cron/GitHub Actions) diário/semanal — sem fingir latência de mercado.

## População 2025 (fonte atual do MVP)

- Canal preferido agora: API Agregados `6579` / variável `9324` / `N3[all]`
- Total reconciliado: **213.421.037**
- Referência típica: `YYYY-07-01`
- Página: https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html
