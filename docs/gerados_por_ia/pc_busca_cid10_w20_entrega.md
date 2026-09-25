The project conventions are clear (pt-BR, Pydantic v2 strict/frozen, rich docstrings, `__all__`, banners). Now I'll create the service in the main backend:
All checks pass — the only failure was a bug in my test script (tuple unpacking), not in the service. Quick final verification of the invalid-limit case and the module demo:
Criado `backend/app/services/busca_cid10.py` (750 linhas), seguindo os padrões do projeto (docstrings pt-BR, Pydantic v2 `strict/frozen`, enums com metadados, `__all__`).

**`CatalogoCID10`** — verificado em execução:
- **Prefixo**: `buscar_por_prefixo("I50")` → Insuficiência cardíaca; aceita "i50", "I50.", "I50.9" (recai para a categoria se a subcategoria não existir na amostra)
- **Descrição com normalização de acentos**: "insuficiencia cardiaca" e "Insuficiência Cardíaca" → mesmo resultado (NFKD + casefold, cacheado)
- **Híbrida** (`buscar`): "asma" → descrição (J45); "j15.9" → prefixo (J15.9); "I" → autocomplete parcial
- **Agrupamento por capítulo**: 18 capítulos com itens (114 códigos, caps. I–XXII, incluindo `U07.1` COVID-19 e `U07.2` Tabagismo com observação de uso nacional SUS)
- **Cache**: `functools.lru_cache` em índices (catálogo ordenado, índices por código) e consultas (256/512 entradas)
- Extras alinhados à APS: espelho **CIAP-2** sugerido nas condições crônicas (I10→K86, E11→T90, J45→R96...) e erro tipado `ConsultaCID10InvalidaError` para consultas/limites inválidos