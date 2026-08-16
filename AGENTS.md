# AGENTS.md — Brasil Real

## Missão

Construir um gêmeo digital exploratório do Brasil, auditável e honesto. Nunca inventar dados. Nunca apresentar simulação como fato observado.

## Antes de expandir escopo

1. Ler `docs/implementation-plan.md` e o roadmap.
2. Preferir o próximo item da Fase atual.
3. Manter diffs cirúrgicos; não gerar docs extras “por precaução”.

## Regras duras

- Fonte, data e rótulo em todo número.
- Integridade fail-closed: `validate_fixtures` + `MANIFEST.json` + contratos TS/Python no CI; gate de proveniência/cobertura 27 nas observations; soma população/PIB = totais oficiais; ingestão recusa fixture inválida; canary pós-deploy.
- LLM não calcula impacto.
- Sem dados pessoais.
- Não commitar segredos nem lixo de agent (`scratch/`, `*_log.txt`).
