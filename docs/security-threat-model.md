# Modelo de ameaças (inicial)

## Ativos

- Integridade de fixtures e checksums
- Regras/cenários publicados
- Disponibilidade de compute (simulações/IA futuras)
- Credenciais de banco

## Ameaças prioritárias (MVP)

1. Injeção de dados falsos em fixtures sem checksum/review
2. Confundir saída simulada com dado oficial na UX
3. Path traversal / ZIP bomb em ingestões futuras
4. Prompt injection quando o copiloto existir
5. Denial of wallet em runs/IA

## Controles já presentes

- Fixtures com checksum e dataset cards
- Disclaimer de cenário hipotético na API e UI
- Sem execução de LLM no caminho crítico
- `.env.example` sem segredos reais; `.env` ignorado
- Dependências pinadas na API

## Controles planejados

OIDC + RBAC, aprovação em duas etapas para regras, rate limits, CSP, SBOM/SLSA, quarentena de artefatos.
