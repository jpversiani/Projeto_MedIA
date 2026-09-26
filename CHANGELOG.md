# 📋 CHANGELOG — Projeto MedIA (Saúde 4.0 / Atenção Primária & Secundária)

Todas as alterações notáveis neste projeto serão documentadas neste arquivo de forma automatizada pelo **HierAgent Cluster Orchestrator** a cada onda de desenvolvimento e release com versionamento semântico (SemVer).

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e adere ao [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/).

---

## [v0.2.0] - 2026-09-26
### 🚀 Marco Fundacional: Multi-Tenancy, SSO Google/Microsoft, 1.501 Pacientes & Trilha LGPD

#### Adicionado (Added)
- **Multi-Tenancy & Gestão Multi-Clínica:**
  - Modelos SQLAlchemy 2.0 (`Usuario`, `VinculoClinica`, `PapelUsuarioEnum`) com permissões granulares por unidade.
  - Alternância contextual dinâmica de clínica ativa via `POST /api/v1/auth/switch-clinic` com reemissão instantânea de JWT.
  - Semente inicial configurada com 2 clínicas ativas: *Consultório Particular MedIA - Montes Claros* (CNES 3180115) e *Centro Integrado de Saúde da Família - Capelinha* (CNES 2199841).
- **Single Sign-On (SSO) & Saúde 4.0:**
  - Provedores federados Google Workspace e Microsoft Entra ID (OAuth 2.0 / OpenID Connect).
  - Autenticação de dois fatores MFA/TOTP (RFC 6238) nativa com SHA-1 HMAC.
  - Gov.br registrado e mantido em backlog técnico.
- **Trilha de Auditoria Criptográfica LGPD / CFM 2.314/2022:**
  - Encadeamento criptográfico imutável `hash_atual = SHA256(hash_anterior + timestamp + dados)` para garantir não-repúdio probatório.
  - Endpoint `GET /api/v1/auth/audit-trail` e modal interativo no Cockpit Clínico com histórico de hashes e IPs.
- **Integração de Interface Landing Page $\leftrightarrow$ Cockpit Clínico:**
  - Modal glassmorphic na Landing Page (`landing.html`) com botões SSO e seletores de teste MVP 1-clique.
  - Topbar do Cockpit (`index.html` & `app.js`) com dropdown de clínica ativa, badge do médico com CRM-MG e botão de acesso à Trilha LGPD.
- **Base Populacional Real (1.501 Cidadãos):**
  - Carga completa de 1.501 pacientes reais de Montes Claros, Capelinha, Turmalina, Diamantina, Bocaiúva e cidades do Norte de MG mantidos no banco SQLite (`backend/esus.db`).
- **Suíte de Testes Automatizados:**
  - 290 testes unitários e de integração com pytest aprovados com 100% de sucesso.
- **Cluster Multi-Agente Distribuído:**
  - Conexão e balanceamento concorrente entre Notebook TUF 16 (Bonsai 27B), PC Zorin GPU (Qwen 3.6 35B), PC Zorin CPU (Qwen 2.5 7B) e agentes Free Tier no OpenRouter (Space Bunny Alpha 1M Contexto, GLM 5.3 Flash, MiMO v2.6 Flash, DeepSeek v4 Flash, Ling Santé, Laguna S e Nemotron 3 Ultra).

---

### [Onda 1] - Frente 1: Prescrição Digital ICP-Brasil & Validação CFM 2.314/2022 (2026-09-26 07:32:39)
- **Escopo:** `prescricao`
- **Modelos Participantes:** space_bunny_alpha, qwen_3_6_35b, ling_3_0_flash_sante, qwen_2_5_7b_cpu, deepseek_v4_flash
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 1] - Frente 1: Prescrição Digital ICP-Brasil & Validação CFM 2.314/2022 (2026-09-26 07:33:54)
- **Escopo:** `prescricao`
- **Modelos Participantes:** space_bunny_alpha, qwen_3_6_35b, ling_3_0_flash_sante, qwen_2_5_7b_cpu, deepseek_v4_flash
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 2] - Frente 2: Telemedicina WebRTC com Grade PIP & Sinalização Resiliente (2026-09-26 07:34:25)
- **Escopo:** `telemedicina`
- **Modelos Participantes:** bonsai_27b, mimo_2_6_flash, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 3] - Frente 3: Faturamento TISS ANS 4.01.00 & Guias de Consulta/SADT (2026-09-26 07:34:57)
- **Escopo:** `tiss`
- **Modelos Participantes:** space_bunny_alpha, glm_5_3_flash_pc, qwen_2_5_7b_cpu, deepseek_v4_flash
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 4] - Frente 4: Motor Fiscal DMED (Receita Federal) & Gestão Financeira (2026-09-26 07:35:30)
- **Escopo:** `financeiro`
- **Modelos Participantes:** qwen_3_6_35b, glm_5_3_flash_pc, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 5] - Frente 5: Agendamento Multiclínica & Fila Inteligente Manchester (2026-09-26 07:36:01)
- **Escopo:** `agenda`
- **Modelos Participantes:** bonsai_27b, ling_3_0_flash_sante, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 6] - Frente 6: Farmácia, Rename & Checagem Cruzada de Alergias (2026-09-26 07:36:34)
- **Escopo:** `farmacia`
- **Modelos Participantes:** ling_3_0_flash_sante, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 7] - Frente 7: BI Epidemiológico, Rastreamento Ativo & Linhas de Cuidado (2026-09-26 07:37:04)
- **Escopo:** `analytics`
- **Modelos Participantes:** laguna_s_2_1, nemotron_3_ultra, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 8] - Frente 8: PWA, Service Worker & Sincronização Offline-First (2026-09-26 07:37:35)
- **Escopo:** `offline`
- **Modelos Participantes:** bonsai_27b, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 9] - Frente 9: Trilha Criptográfica de Alto Throughput & Stress Test LGPD (2026-09-26 07:38:09)
- **Escopo:** `auditoria`
- **Modelos Participantes:** qwen_3_6_35b, glm_5_3_flash_pc, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 10] - Frente 10: Segurança RBAC/ABAC Avançada & Gestão de Papéis (2026-09-26 07:38:40)
- **Escopo:** `seguranca`
- **Modelos Participantes:** space_bunny_alpha, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 11] - Frente 11: Portal do Cidadão / Agendamento Online & Acolhimento (2026-09-26 07:39:09)
- **Escopo:** `portal_paciente`
- **Modelos Participantes:** bonsai_27b, nemotron_3_ultra, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 12] - Frente 12: Validação E2E, Consolidação e Release Candidate (2026-09-26 07:39:40)
- **Escopo:** `release`
- **Modelos Participantes:** space_bunny_alpha, laguna_s_2_1, glm_5_3_flash_pc, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 1] - Frente 1: Prescrição Digital ICP-Brasil & Validação CFM 2.314/2022 (2026-09-26 07:40:14)
- **Escopo:** `prescricao`
- **Modelos Participantes:** space_bunny_alpha, qwen_3_6_35b, ling_3_0_flash_sante, qwen_2_5_7b_cpu, deepseek_v4_flash
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 2] - Frente 2: Telemedicina WebRTC com Grade PIP & Sinalização Resiliente (2026-09-26 07:40:44)
- **Escopo:** `telemedicina`
- **Modelos Participantes:** bonsai_27b, mimo_2_6_flash, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 3] - Frente 3: Faturamento TISS ANS 4.01.00 & Guias de Consulta/SADT (2026-09-26 07:41:14)
- **Escopo:** `tiss`
- **Modelos Participantes:** space_bunny_alpha, glm_5_3_flash_pc, qwen_2_5_7b_cpu, deepseek_v4_flash
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 1] - Frente 1: Prescrição Digital ICP-Brasil & Validação CFM 2.314/2022 (2026-09-26 07:41:52)
- **Escopo:** `prescricao`
- **Modelos Participantes:** space_bunny_alpha, qwen_3_6_35b, ling_3_0_flash_sante, qwen_2_5_7b_cpu, deepseek_v4_flash
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 2] - Frente 2: Telemedicina WebRTC com Grade PIP & Sinalização Resiliente (2026-09-26 07:42:22)
- **Escopo:** `telemedicina`
- **Modelos Participantes:** bonsai_27b, mimo_2_6_flash, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 3] - Frente 3: Faturamento TISS ANS 4.01.00 & Guias de Consulta/SADT (2026-09-26 07:42:52)
- **Escopo:** `tiss`
- **Modelos Participantes:** space_bunny_alpha, glm_5_3_flash_pc, qwen_2_5_7b_cpu, deepseek_v4_flash
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 4] - Frente 4: Motor Fiscal DMED (Receita Federal) & Gestão Financeira (2026-09-26 07:43:23)
- **Escopo:** `financeiro`
- **Modelos Participantes:** qwen_3_6_35b, glm_5_3_flash_pc, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 5] - Frente 5: Agendamento Multiclínica & Fila Inteligente Manchester (2026-09-26 07:43:52)
- **Escopo:** `agenda`
- **Modelos Participantes:** bonsai_27b, ling_3_0_flash_sante, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 6] - Frente 6: Farmácia, Rename & Checagem Cruzada de Alergias (2026-09-26 07:44:24)
- **Escopo:** `farmacia`
- **Modelos Participantes:** ling_3_0_flash_sante, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 7] - Frente 7: BI Epidemiológico, Rastreamento Ativo & Linhas de Cuidado (2026-09-26 07:44:54)
- **Escopo:** `analytics`
- **Modelos Participantes:** laguna_s_2_1, nemotron_3_ultra, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 8] - Frente 8: PWA, Service Worker & Sincronização Offline-First (2026-09-26 07:45:24)
- **Escopo:** `offline`
- **Modelos Participantes:** bonsai_27b, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 9] - Frente 9: Trilha Criptográfica de Alto Throughput & Stress Test LGPD (2026-09-26 07:45:55)
- **Escopo:** `auditoria`
- **Modelos Participantes:** qwen_3_6_35b, glm_5_3_flash_pc, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 10] - Frente 10: Segurança RBAC/ABAC Avançada & Gestão de Papéis (2026-09-26 07:46:24)
- **Escopo:** `seguranca`
- **Modelos Participantes:** space_bunny_alpha, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 11] - Frente 11: Portal do Cidadão / Agendamento Online & Acolhimento (2026-09-26 07:46:53)
- **Escopo:** `portal_paciente`
- **Modelos Participantes:** bonsai_27b, nemotron_3_ultra, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 12] - Frente 12: Validação E2E, Consolidação e Release Candidate (2026-09-26 07:47:24)
- **Escopo:** `release`
- **Modelos Participantes:** space_bunny_alpha, laguna_s_2_1, glm_5_3_flash_pc, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 1] - Frente 1: Prescrição Digital ICP-Brasil & Validação CFM 2.314/2022 (2026-09-26 07:47:58)
- **Escopo:** `prescricao`
- **Modelos Participantes:** space_bunny_alpha, qwen_3_6_35b, ling_3_0_flash_sante, qwen_2_5_7b_cpu, deepseek_v4_flash
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 2] - Frente 2: Telemedicina WebRTC com Grade PIP & Sinalização Resiliente (2026-09-26 07:48:28)
- **Escopo:** `telemedicina`
- **Modelos Participantes:** bonsai_27b, mimo_2_6_flash, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 3] - Frente 3: Faturamento TISS ANS 4.01.00 & Guias de Consulta/SADT (2026-09-26 07:48:58)
- **Escopo:** `tiss`
- **Modelos Participantes:** space_bunny_alpha, glm_5_3_flash_pc, qwen_2_5_7b_cpu, deepseek_v4_flash
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 4] - Frente 4: Motor Fiscal DMED (Receita Federal) & Gestão Financeira (2026-09-26 07:49:28)
- **Escopo:** `financeiro`
- **Modelos Participantes:** qwen_3_6_35b, glm_5_3_flash_pc, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 5] - Frente 5: Agendamento Multiclínica & Fila Inteligente Manchester (2026-09-26 07:49:58)
- **Escopo:** `agenda`
- **Modelos Participantes:** bonsai_27b, ling_3_0_flash_sante, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 6] - Frente 6: Farmácia, Rename & Checagem Cruzada de Alergias (2026-09-26 07:50:29)
- **Escopo:** `farmacia`
- **Modelos Participantes:** ling_3_0_flash_sante, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 7] - Frente 7: BI Epidemiológico, Rastreamento Ativo & Linhas de Cuidado (2026-09-26 07:50:59)
- **Escopo:** `analytics`
- **Modelos Participantes:** laguna_s_2_1, nemotron_3_ultra, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 8] - Frente 8: PWA, Service Worker & Sincronização Offline-First (2026-09-26 07:51:30)
- **Escopo:** `offline`
- **Modelos Participantes:** bonsai_27b, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 9] - Frente 9: Trilha Criptográfica de Alto Throughput & Stress Test LGPD (2026-09-26 07:52:03)
- **Escopo:** `auditoria`
- **Modelos Participantes:** qwen_3_6_35b, glm_5_3_flash_pc, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 10] - Frente 10: Segurança RBAC/ABAC Avançada & Gestão de Papéis (2026-09-26 07:52:34)
- **Escopo:** `seguranca`
- **Modelos Participantes:** space_bunny_alpha, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 11] - Frente 11: Portal do Cidadão / Agendamento Online & Acolhimento (2026-09-26 07:53:03)
- **Escopo:** `portal_paciente`
- **Modelos Participantes:** bonsai_27b, nemotron_3_ultra, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 12] - Frente 12: Validação E2E, Consolidação e Release Candidate (2026-09-26 07:53:35)
- **Escopo:** `release`
- **Modelos Participantes:** space_bunny_alpha, laguna_s_2_1, glm_5_3_flash_pc, qwen_3_6_35b, qwen_2_5_7b_cpu
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.

### [Onda 1] - Frente 1: Prescrição Digital ICP-Brasil & Validação CFM 2.314/2022 (2026-09-26 07:54:08)
- **Escopo:** `prescricao`
- **Modelos Participantes:** space_bunny_alpha, qwen_3_6_35b, ling_3_0_flash_sante, qwen_2_5_7b_cpu, deepseek_v4_flash
- **Validação Automatizada:** Pytest 290+ testes 100% aprovados.
- **Conformidade:** LGPD Art. 11, CFM 2.314/2022, TISS ANS 4.01.00.
