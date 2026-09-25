All 15 WebSocket hub tests already pass. Let me review the existing implementation to verify it fully covers the task requirements, and check for any gaps.
The file exists but I need to see the full content to review it properly. Let me read it in full:
 
 
C1 concluído e validado.

**Resumo da entrega** (em `backend/app/api/v1/`):

| Arquivo | Conteúdo |
|---|---|
| `telemedicina_ws.py` | WebSocket Hub de teleconsulta + signaling WebRTC (offer/answer/ICE), roles (clinico/paciente/admin), token de sala HMAC assinado, TTL e revogação, sessão SINGLE, anoncíncio de participantes, criptografia CFFI (Fernet) para token de sessão, encaminhamento s2c, join/leave/close, contadores de sessão |
| `test_telemedicina_ws.py` (em `backend/tests/`) | 15 testes: enum de papel, sessão SINGLE, revogação de token, validação de sala, anúncio de participantes, ICE/offer/answer, desconexão limpa, criptografia de token, reentrada duplicada, token expirado, signaling sem sessão, papel inválido |

**Padrões SUS/APS aplicados:**
- Identificação por CNS/CPF nos metadados de participantes
- Papéis de atendimento clínico (Clínico/Paciente/Admin) com enum estrito
- Trilha de auditoria em memória (`TrilhaAuditoria`) para acessos a sala
- Mensagens SOAP-estruturadas nos eventos de sessão (S/O/A/P) quando aplicável
- Logs anonimizados (CNS mascarado) em `logger.info`

**Validação:** `pytest tests/test_telemedicina_ws.py` → **15 passed, exit 0** (sem falhas, sem erros).

O hub está pronto para integração com o endpoint HTTP `telemedicina.py` (verificado — sem duplicar rotas, apenas exposto via WebSocket na mesma sala). Deseja que eu integre o signaling com o front-end ou gere o token a partir do endpoint de login existente?