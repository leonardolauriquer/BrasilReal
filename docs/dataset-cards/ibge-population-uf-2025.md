# Dataset card — IBGE Estimativas População UF 2025

- **ID:** `ibge.estimativas_populacao.uf.2025`
- **Organização:** IBGE
- **Cobertura:** 27 UFs + total Brasil
- **Referência:** 2025-07-01
- **Publicação:** 2025-08-28
- **Unidade:** habitantes
- **Rótulo:** ESTIMADO
- **Arquivo:** `data/fixtures/ibge/population_uf_2025.json`
- **Artefato oficial:** PDF DOU/FTP IBGE Estimativas 2025
- **Transformações:** digitação da tabela UF; inclusão de `exploratory_need_index` sintético separado (não oficial)
- **Testes:** soma UF = 213.421.037; count = 27
- **Limitações:** estimativa ≠ censo; nota IBGE sobre PR/SC (±67 vs projeção)
