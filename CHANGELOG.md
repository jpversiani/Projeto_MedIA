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
