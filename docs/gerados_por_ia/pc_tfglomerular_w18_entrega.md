Corrigindo a equação CKD-EPI 2021 (exponentes aplicados a min/max de Scr/κ) e simplificando validações:
Agora corrijo a validação do CNS (algoritmo oficial módulo 11) e o montagem do plano SOAP:
Preciso corrigir o CNS (o Cartão Nacional de Saúde tem 15 dígitos, não 11) e a tipagem do despacho de medicamentos:
Agora executo um teste de fumaça para validar a equação, estágios, CNS, CPF, ajustes e laudo:
A TFGe está correta (valores consistentes com CKD-EPI 2009/2021). O CNS de teste foi construído com erro de dígito — recalculo e reexecuto:
Tudo validado. Verificação final de compilação e estilo:
`backend/app/services/tfge_renal.py` criado e verificado (Python 3.12, Pydantic v2, textos em pt-BR):

- **CKD-EPI 2021** (`CalculadoraRenal.calcular_tfge`): `142 × min(Scr/κ,1)^α × max(Scr/κ,1)^−1,200 × 0,9938^idade × 1,012 (F)`, sem variável raça; arredondamento Decimal (1 casa).
- **Estágios KDIGO G1–G5** com CID-10 (`N18.1`–`N18.5`) e CIAP-2 `U99` para registro na APS.
- **Ajuste de dose** por estágio: metformina (contraindicada <30, ≤1.000 mg/dia em 30–44), IECA (titulação cautelosa), vancomicina (intervalo estendido/ASC).
- **Alertas de nefrotoxicidade** (informativo/atenção/crítico: AINEs, contraste, acidose láctica, TRS em G5).
- **Laudo SOAP** (`gerar_laudo`) com validação de CNS de 15 dígitos (algoritmo DATASUS módulo 11) e CPF (dígitos verificadores).

Smoke test confirmou: F 40a/Cr 1.0 → 73.0 (G2), M 80a/Cr 2.5 → 25.3 (G4, metformina suspensa + 3 alertas), faixas de estágio, CNS/CPF válidos e rejeição de CNS/CPF inválidos.