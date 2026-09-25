O serviço já existe no sandbox (variante rotulada "C18") e os 62 testes passam. Vou alinhar o rótulo à tarefa **C2**, reforçar a conformidade documentada e fechar lacunas de teste.
Entrega concluída em `sandboxes/Coder-OpenCode-PC-GLM/`.

**`backend/app/services/receita_digital.py`** (C2 — SUS/APS):
- `serializar_canonico` — JSON determinístico (chaves ordenadas, NFC, datas em UTC, metadados de integridade excluídos).
- `gerar_hash_prescricao` — SHA-256 canônico hex de 64 caracteres (identidade do QR Code).
- `AssinadorReceitaDigital.assinar/verificar` — HMAC-SHA256 com chave derivada da unidade (`chave_id` público), comparação em tempo constante; detecta adulteração de dosagem, medicamento, quantidade, CNS/CPF, CID-10, CIAP-2, hash ou algoritmo.
- `verificar_dispensacao` — baixa farmacêutica conferida contra a receita assinada (dispensação fracionada permitida, excedente rejeitado).
- `validar_documento_emitido` — chave explícita ou `MEDIA_CHAVE_INTEGRIDADE` (ausência gera `RuntimeError`).

**`backend/tests/test_receita_digital.py`**: 65 testes (`python -m pytest` → **65 passed**), incluindo round-trip JSON do documento assinado e detecção de dosagem adulterada no transporte.