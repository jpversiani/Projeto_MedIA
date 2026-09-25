The target file already exists in the main project. Let me examine it and a similar service to understand conventions.
The working sandbox is empty, but the main project already contains a `tfge_renal.py`. Let me check its git status and whether testsexist.
A versão no projeto principal não está rastreada e contém um bug no validador de CNS. Vou verificar o validador de CNS canônico do projeto antes de escrever o arquivo sandbox.
Agora vou verificar o `__init__.py` do projeto principal dos services para convenções de exportação, e então criar o arquivo no sandbox.
Estrutura confirmada. Agora vou criar o arquivo no sandbox com o validador de CNS corrigido (algoritmo DATASUS canônico), o mapeamento CID-10 alinhado ao SUS (N18.3 para G3a/G3b) e o código CIAP-2 correto (U13 — insuficiência renal).
Now let me verify the implementation with a validation script using the project's venv.
My test expectations were wrong, not the implementation — I misapplied the min/max terms (Scr 1.0 > κ=0.9 for males triggers the >κ exponent) and misread KDIGO boundaries (29.0 → G4, 15.3 → G4). Let me re-verify with correct reference values and boundary tests.
All calculations verified against an independent reference implementation. Now checking lint/typecheck tooling.
No linter configured. Final compile check:
Criado: `backend/app/services/tfge_renal.py` (556 linhas), com a classe `CalculadoraRenal` validada por testes.

**Implementação:**
- **TFGe CKD-EPI 2021** (Inker et al., NEJM 2021, sem raça): `142 × min(Scr/κ,1)^α × max(Scr/κ,1)^-1,2 × 0,9938^idade × 1,012 (F)` — verificada contra implementação de referência independente em 10 casos, erro < 0,05 mL/min/1,73 m²
- **Estágios KDIGO** G1→G5 com fronteiras testadas (90/60/45/30/15), CID-10 SUS (N18.1–N18.5, N18.3 para G3a/G3b) e CIAP-2 **U13** (insuficiência renal)
- **Ajuste de dose**: metformina (bloqueada <30; máx 1.000 mg/dia em 30-44), IECA (titulação + monitorar K⁺/creatinina), vancomicina (intervalos e ASC por estágio)
- **Alertas de nefrotoxicidade**: informativo/atenção/crítico (AINEs, contraste, aminoglicosídeos; metformina suspensa em G4/G5)
- **Laudo SOAP** com identificação por **CNS** (algoritmo DATASUS oficial: pesos 15→1, soma múltipla de 11, prefixos 1/2/7/8/9) e CPF (módulo 11)
- Pydantic v2 (`frozen`, validadores), `StrEnum`, tipagem estrita, tudo em pt-BR

**Correções sobre a versão pré-existente não versionada no projeto principal:** validador de CNS estava com algoritmo errado (rejeitava CNS válidos não terminados em 0 e não aceitava prefixo 2); CID-10 usava N18.30/N18.31 (códigos ICD-10-CM dos EUA, não da CID-10 SUS); CIAP-2 usava U99 (código inexistente).