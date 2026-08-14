# Metodologia de simulação (MVP)

## Camada usada

**Camada A — contabilidade / regras-as-código**

Motor: `hypothetical_federal_fund_v1`

\[
share_i = w_{pop}\cdot\frac{pop_i}{\sum pop} + w_{need}\cdot\frac{need_i}{\sum need}
\]

\[
amount_i = budget \cdot share_i
\]

Arredondamento bancário em centavos com redistribuição determinística do residual para conservar o orçamento.

## O que NÃO é simulado

Crescimento, votos, saúde, educação, migração, reação comportamental, capacidade estatal.

## Escala de evidência

| Elemento | Grau |
|---|---|
| Conservação orçamentária / shares | A |
| População IBGE 2025 | A (estimativa oficial) |
| Índice de necessidade sintético | D |

## Reprodutibilidade

Mesmo manifesto + seed ⇒ mesmos resultados. O seed está reservado para extensões estocásticas futuras; o motor atual é puramente determinístico.
