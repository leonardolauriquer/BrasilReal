# ADR 0004 — Separação LLM × motor numérico

## Status

Aceito

## Contexto

LLMs inventam com fluência. Impactos fiscais precisam ser testáveis.

## Decisão

Efeitos numéricos só via motores registrados (camada A agora). O sistema permanece funcional sem LLM. Qualquer copiloto futuro usa RAG com citação e tools read-only.

## Consequências

O fundo hipotético do MVP é determinístico e coberto por testes de invariantes.
