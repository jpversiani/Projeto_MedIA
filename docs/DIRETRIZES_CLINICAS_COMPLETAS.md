# PROJETO MEDIA
## Documento Estratégico de Validação Clínica
### Sistema de Clínica em Telessaúde para Atenção Primária à Saúde — PSU/SUS

**Elaborado por:** Ling 3.0 Flash Santé — Diretor Clínico e Arquiteto de Sistemas de Saúde
**Destinatário:** Médico Responsável / Product Owner
**Versão:** 1.0 — Documento de Validação

---

> *"O melhor sistema de saúde digital é aquele que o médico usa sem perceber, porque ele só cuida do paciente."*

---

## SUMÁRIO EXECUTIVO

O PROJETO MEDIA é um sistema clínico de alta performance voltado a um médico de família em regime de **home office**, atendendo via **telessaúde** pacientes do SUS nas regiões de Montes Claros, Vale do Jequitinhonha e entorno de Minas Gerais. O desafio técnico central é triplo: **(1)** presença de conectividade instável, **(2)** perfeição regulatória em receituário, atestados e prescrições digitais, **(3)** integração de Inteligência Artificial Clínica sem perder o juízo médico soberano.

Este documento visa apresentar ao médico uma visão estratégica, estruturada em cinco blocos, permitindo a validação rápida e segura de prioridades, com ênfase em onde a IA gera valor real, onde ela é perigosa, e onde o esforço de desenvolvimento é desperdício puro.

---

# 1. VISÃO GERAL DO CASO DE USO CLÍNICO

## 1.1 Fluxo de Atendimento — Médico de Família em Home Office via Telessaúde

O fluxo completo, do início ao fim, com os pontos críticos de telessaúde marcados:

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO DE ATENDIMENTO MEDIA               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [AGENDAMENTO]                                              │
│   │  ├── Paciente agenda pelo app/WhatsApp/telefone        │
│   │  ├── Fila virtual com priorização (PNU, Gestante,      │
│   │  │   Idoso, Crônicos descompensados)                   │
│   │  └── Lembrete automático + link de acesso              │
│   │                                                         │
│  [CHEGADA/LOGIN]                                            │
│   │  ├── Autenticação com CPF + 2FA                        │
│   │  ├── Teste de conectividade automático                 │
│   │  │   (calibração de qualidade de áudio/vídeo)          │
│   │  ├── Fallback automático: Vídeo → Áudio → Texto       │
│   │  └── Contingência: Atividade offline habilitada       │
│   │                                                         │
│  [CONSULTA MÉDICA]                                          │
│   │  ├── Janela de vídeo com adaptação dinâmica à          │
│   │  │   qualidade de rede (degradação graciosa)           │
│   │  ├── AI Scribe ativo em background (transcrição        │
│   │  │   + estruturação SOAP em tempo real)                │
│   │  ├── Prontuário aberto com histórico do paciente       │
│   │  │   (Problemas Ativos, Medicamentos em uso,           │
│   │  │    Alergias, Últimas consultas, LAM)               │
│   │  ├── Checklist de coleta clínica com IA assistiva      │
│   │  │   (escores automáticos: PA, IMC, Glicemia, etc.)   │
│   │  └── Alertas em tempo real: interações, alergias,      │
│   │       duplicações terapêuticas                         │
│   │                                                         │
│  [ENCERRAMENTO / PLANO TERAPÊUTICO]                        │
│   │  ├── Diagnósticos (CIAP-2 + CID-10 mapeados)           │
│   │  ├── Prescrição digital assinada eletronicamente       │
│   │  ├── Solicitação de exames (laboratório + imagem)      │
│   │  ├── Atestado médico digital (quando aplicável)        │
│   │  ├── Encaminhamento com priorização de vagas           │
│   │  ├── Agendamento de retorno com protocolo              │
│   │  └── Notificação ao paciente em <30s                   │
│   │                                                         │
│  [PÓS-CONSULTA]                                             │
│       ├── Dados sincronizados com SISREG / e-SUS PEC      │
│       ├── Fila de trabalho clínico organizada              │
│       ├── Recalls automáticos (Hipertenso, Diabético,      │
│       │   Gestante, Puericultura, Rastreios)              │
│       └── Métricas de produtividade clínica                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Pontos Críticos do Fluxo em Contexto de Conectividade Instável (Interior de MG):

| Momento do Fluxo | Risco de Queda | Estratégia de Contingência |
|---|---|---|
| Consulta de vídeo | **ALTO** — interrupção mid-consulta | Fallback automático: vídeo → áudio → texto/chat; AI Scribe continua gravando/transcrevendo localmente |
| Assinatura de prescrição | **ALTO** — assinatura digital requer servidor | Fila offline: prescrição gerada localmente, assinatura pendente → sincroniza quando reestabilizar |
| Busca de histórico no prontuário | **MÉDIO** — cache local (últimas 10 fichas) | Cache inteligente pré-carregado baseado na agenda do dia |
| Geração de atestados | **MÉDIO** | Atestado offline gerado com timestamp, validade assinatura diferida |
| Integração SISREG/e-SUS | **BAIXO** — pós-consulta | Sincronização em batch, retentativas automáticas |

---

## 1.2 Perfil Epidemiológico da APS — A Base de Doenças que o Sistema Deve Suportar

Este é o **DNA clínico** do projeto. O sistema deve ser construído em torno destas 7 áreas primordiais da APS conforme o Ministério da Saúde / e-SUS APS / Financiamento do SUS para Atenção Primária:

### 1.2.1 Hipertensão Arterial Sistêmica (HAS) — 25-30% da carteira

- **Protocolo clínico SUS:** Protocolo Clínico e Diretrizes Terapêuticas de Hipertensão Arterial (BVS/MS)
- **Indicadores-chave que o sistema deve rastrear:**
  - Número de pacientes com HAS registrados
  - % de pacientes com PA aferida no mês/semestre
  - % de pacientes controlados (PA < 140/90 ou meta individualizada)
  - % em terapia farmacológica adequada
- **IA aplicável:**
  - Automação de cálculo de controle de PA (metas, tendência temporal)
  - Sugestão de escalonamento terapêutico conforme protocolo (Dieta/Drogas 1ªLinha → 2ª Linha → 3ª Linha)
  - Alerta de hipotensão postural em idosos
  - Alerta de dupla bloqueação RAAS (IECA + BRA — risco hipercalemia/insuficiência renal)
- **Cards de ágio:** Alerte sobre prescrição combinada vs. monoterapia, visando a taxa de poliprescrição desnecessária em idosos geriátricos (Beers Criteria — Beers 2023)

### 1.2.2 Diabetes Mellitus Tipo 2 (DM2) — 10-15% da carteira

- **Protocolo:** Protocolo Clínico e Diretrizes Terapêuticas de DM2 (BVS/MS)
- **Indicadores-chave:**
  - % com HbA1c realizada nos últimos 6 meses
  - % com HbA1c < 7% (meta geral ADA/Brasil)
  - % com fundoscopia de rastreio (anual)
  - % com cistatinina/eGFR realizados (renal screening)
  - % com examinação de pés (anual)
- **IA aplicável:**
  - Cálculo automático de eGFR (CKD-EPI 2021 ou MDRD — conforme laboratório) a partir de creatinina
  - Predição de risco de hipoglicemia com terapia intensiva
  - Monitoramento glicêmico integrado (glicemia capilar/PAP centralizado)
  - Alerta de interação (Sulfonilureia + Betabloqueador → risco de mascarar hipoglicemia)

### 1.2.3 Pré-Natal (PNU) e Saúde da Mulher — Carteira de Gestantes

- **Protocolo:** Pré-natal de baixo/intermediário/alto risco (Guia Prático do Pré-Natal — MS)
- **Indicadores-chave:**
  - Nº de gestantes com ≥6 consultas (meta RNM ≥70%)
  - % com exames: tipagem/uso (Dombrow/Rh), toxoplasmose, anti-HIV, treponêmico, glicemia jejum, urina, UFCS, hemograma
  - % com IMC pré-gestacional
  - % em pré-natal de alto risco com referência adequada
  - Registre o score de Naegele para a data provável do parto (DPP)
- **IA aplicável:**
  - Cálculo automático de DPP (método de Naegele — manual/automático)
  - Detecção de sinais de risco obstétrico (edema, PA, proteinúria, sangramento)
  - Checklist obstétrico automatizado por trimestre (peso do feto, batimentos, liquido amniótico)
  - Alerta de gestante >35 anos ou comendade de gravidez de alto risco (prévia, eclampsia prévia, suspeita preeclâmpsia)

### 1.2.4 Puericultura (Saúde da Criança) — Carteira de 0-5 anos

- **Protocolo:** Cartilha de Puericultura (Série Estimativa)
- **Indicadores-chave:**
  - % de crianças com consultas de rotina (D2, D7, D30, D60, D120, D180, D240, D300 e semestrais)
  - % com esquema vacinal completo (CNV consultada)
  - % com Avaliação do Desenvolvimento (Avaliação do Desenvolvimento, Teste da Mancha / SGP)
  - IMC/IBMS de adultez (referência: CDC 2000, OMS 2006)
- **IA aplicável:**
  - Curvas de crescimento (P/N OMS para altura, peso, perímetro cefálico)
  - Alerta de desnutrição/obesidade infantil (score de puro depercentiles)
  - Score de desenvolvimento motor/social/linguístico automatizado
  - Vacinação automática: vacinas obrigatórias (BCG, OPV, Hepatite B, Penta, VIP, Pneumo 10, Rotavírus, MMR, HPV, Dengue 4ª dose) — com alerta de atrasos

### 1.2.5 Saúde Mental — Carteira de Transtornos Mentais Comuns

- **Protocolo:** Saúde Mental na Atenção Básica (Guia Prático — MS/OPAS)
- **Indicadores-chave:**
  - % de pacientes com transtorno mental com acompanhamento de psicólogo/CRAS
  - Nº de atendimentos com Queixa Psiquiátrica (CAPS) nas últimas 4 semanas
  - Sinais de risco (ISRC — Ideação Suicida)
  - Registro de rastreio com Beck em <3 consultas
- **IA aplicável:**
  - Rastreio automatizado de depressão (PHQ-9 / Beck-II) integrado à consulta
  - Classificação automática de risco (Leve/Modado/Severo com referência)
  - Detecção de palavras-chave em consulta sobre ideação suicida / dano autoinfligido (com alerta imediato + protocolo de segurança do paciente)
  - Suporte à prescrição de psicofármacos com alerta de interações e risco de síndrome serotoninérgica

### 1.2.6 Rastreio Oncológico e Doenças Crônicas NÃO transmissíveis

- **Cancro de Colô Utéris:** Papanicolau (cada 3 anos após 2 mamografias)
- **Cancro de Mama:** Mamografia (a cada 2 anos, 50-69 anos — onde houver infraestrutura de imagem)
- **Cancro de Colo Retal:** FIT (sangramento oculto nas fezes) 45-75 anos (conforme Protocolo de Rastreio MS)
- **Cancro de Pele (Melanoma):** Rastreio clínico com mapeamento corpóreo (fotodermatoscopia)
- **Cancro de Próstata:** PSA (quando indicado — discussão de benefício/risco)
- **Diabetes:** HbA1c, retinografia, nefropatia
- **Has:** PA, ECG, peso, IMC

**IA aplicável:**
- Organizador de recalls e agendas de rastreio automatizadas
- Verificação de conformidade com protocolos de rastreio (68/68% conforme protocolo do MS)
- Relatório consolidado de pacientes elegíveis para FIT/Pap/Mamografias/PSA

### 1.2.7 Saúde do Idoso e Doenças Crônicas

- **Índice de Fragilidade (Fried ou SHAD)**
- **Escala de Fragilidade PHC (Questões de Cobre)**
- **Rastreio de Demência (Mini-Exame do Estado Mental — MEEM)**
- **Rastreio de Quedas (Falling Risk — Morse ou Tinetti)**
- **Rastreio de Disfagia (Escala de EAT-10)**
- **AVD/DPAC (Índice de independência das AVD — Índice de Barthel)**

### 1.2.8 Atividade e Saúde Física e Saúde Mental

- **Programa "Bom viver nas comunidades"**
- **Atividade Física no SUS:** Guia de Atividade Física (OMS 2020 — 150 min/semana moderado)

---

# 2. O QUE É ESSENCIAL E DE ALTO IMPACTO — PRIORIDADE MÁXIMA (FASE 1)

## 2. O QUE É ESSENCIAL E DE ALTO IMPACTO (CONTINUAÇÃO)

I need to complete the table of Phase 1 functionalities:
- Receituário digital CFM 2.314/2022 + ICP-Brasil
- Atestado Digital
- Pedidos de Exames
- Prontuário SOAP/CIAP-2/CID-10
- Integração RENAME/Farmácia Popular
- Alertas de Interações

Then:
- Telemedicine resources for low connectivity (WebRTC with graceful degradation, local cache, offline generation with sync queue)
- Legal/ethical compliance: CFM 2.314/2022, LGPD, 20-year record retention, digital informed consent

## 3. AI: where it generates real value vs. waste
- Indispensable: silent clinical copilot, real-time drug interaction checking, cross-allergy alerts, automatic SOAP transcription/structuring, clinical scores (MEWS, Naegele, CKD-EPI, FINDRISC, Framingham)
- NOT to use: autonomous diagnoses without supervision, hallucinations in prescriptions, dehumanized chatbots for SUS patients

## 4. What NOT to build / discard
- Hospital tools (shift schedules, beds, complex TISS billing for private plans)
- Excessive bureaucracy that rigidifies the consultation
- Overloaded screens with dozens of clicks

## 5. Decision Matrix
- Table with 15-20 items: Category, Item, Clinical Rationale, columns for [X] Manter / [ ] Descartar / [ ] Deixar para Fase 2

Let me write this with clinical richness and precision. I should use proper Brazilian medical informatics terminology:

- CFM Resolução 2.314/2022 - regulates telemedicine in Brazil
- ICP-Brasil - Brazilian digital certificate infrastructure (ITI - Instituto Nacional de Tecnologia da Informação)
- CFM 1.829/2007 - digital prescription requirements (actually the prescription with digital signature is regulated by CFM; Lei 14.510/2022 also relevant for digital prescriptions)
- Actually: Resolução CFM 2.314/2022 regulates telemedicine; digital prescription is regulated by CFM norms - Resolução CFM 2.314/2022 allows teleprescription. Lei 14.510/2022 allows digital prescriptions nationally. Portaria... Let me be careful with the exact regulations:
  - Resolução CFM nº 2.314/2022 - telemedicine
  - Lei nº 14.510/2022 - prescrição eletrônica de medicamentos (valid nationwide)
  - Resolução CFM nº 1.638/2002 - digital signature requirements for electronic documents
  - Nota Técnica... 
- CIAP-2 - Classificação Internacional de Atenção Primária (CIAP-2 / ICPC-2) - used in e-SUS APS
- CID-10 (and CID-11 now, but CID-10 still widely used in Brazil)
- e-SUS APS / PEC (Prontuário Eletrônico do Cidadão) - the Ministry of Health system
- RENAME - Relação Nacional de Medicamentos Essenciais
- Farmácia Popular do Brasil - program with co-payment; CMED regulation
- RNDS - Rede Nacional de Dados em Saúde (now DADOS - Departamento de Informação e Saúde Digital... actually RNDS became part of DNIT... no. RNDS - Rede Nacional de Dados em Saúde, managed by DATASUS; there's now the "DADOS" (Departamento de Informação e Saúde Digital). I'll mention RNDS/DADOS carefully.
- LGPD - Lei Geral de Proteção de Dados (Lei 13.709/2018), sensitive health data (Art. 5, II; Art. 11)
- Guarda de prontuário: CFM says 20 years (Resolução CFM 1.638/2002 and Código de Ética Médica - CEM Art. 87 - physicians must keep records for 20 years from last appointment; actually CEM 2019 Art. 87: "Manter prontuário..." - 20 years per Resolução CFM 1.821/2007 which approves the Código de Processo Ético... The 20-year rule comes from CFM. For SUS establishments, Portaria... there's also the requirement of 20 years. I'll state 20 anos conforme CFM.
- SOAP - Subjective, Objective, Assessment, Plan (Problem-oriented record by Weed)
- MEWS - Modified Early Warning Score
- Naegele - obstetric dating (DP - DUM + 7 - 3 + 1 year adjustment)
- CKD-EPI - Chronic Kidney Disease Epidemiology Collaboration (eGFR)
- FINDRISC - Finnish Diabetes Risk Score
- Framingham - cardiovascular risk score
- Also could mention: ASCVD, SCORE2, but stick to what they asked
- WebRTC - Web Real-Time Communication
- ICP-Brasil A1/A3 certificates - A1 (software, 1 year) vs A3 (token/card)
- e-SUS APS, PEC
- SISAB - Sistema de Informação em Saúde para a Atenção Básica
- e-Gestor AB
- RNDS
- TeleSUS / Telessaúde Brasil (NUTES/UFPB) - teleconsultation
- PNMC... no.
- Interações medicamentosas: bases como Micromedex, UpToDate, ANVISA's bulas, or Brazilian bases (e.g., "Interações medicamentosas" from ANVISA; also the "Consulta de Interações" via... I can mention validated databases)
- Beers Criteria / STOPP-START for polypharmacy in elderly
- Lista de medicamentos de notificação/controle especial (Portaria 344/98 ANVISA; RDC 471/2021 for prescriptions of controlled substances; Receita de Controle Especial em 2 vias; SNGPC)
- Actually for digital prescriptions of controlled drugs: RDC 471/2021 allows electronic prescription for controlled (A1-A4, B1-B2) via systems certified... The "Receita Digital" for controlled medications requires specific systems. I can mention this briefly.
- RENAME 2022 (Relação Nacional de Medicamentos Essenciais)
- Farmácia Popular: CMED, categories (hipertensão, diabetes, anticoncepcionais...), "Aqui tem Farmácia Popular"
- CIAP-2 codes: e.g., A01 dor generalizada, K29 hipertensão, T90 diabetes, etc. I can give examples.
- CID-10: I10, E11, J44, etc.
- LGPD: Art. 11 (sensitive data), Art. 46 (security), ANPD (Autoridade Nacional de Proteção de Dados)
- Consentimento informado digital
- Teleconsulta requirements per CFM 2.314/2022: identification, consent, record in prontuário, possibility of presential referral, etc.
- "Degradation graciosa" - WebRTC → audio-only → chat → async
- Cache local: IndexedDB/Service Workers (PWA), fila de sincronização (outbox pattern), assinatura em fila (queue for ICP-Brasil signing when connectivity returns)
- Conflict resolution for sync (last-write-wins vs. merge; operational transforms) - keep it clinical not too technical, but I'm the informatics specialist too.

For section 3, AI:
Value:
- Copiloto clínico silencioso (ambient scribe) - transcribes and structures SOAP, reduces burnout (physicians spend ~2h on EHR per 1h of consultation - studies show)
- Checagem em tempo real: interações (e.g., contraindicated: claritromicina + sinvastatina → rabdomiólise; AAS + varfarina; IECA + espironolactona + AINE → nefrotoxicidade tripla whammy)
- Alergias cruzadas: penicilina → cefalosporinas (desensitization considerations, cross-reactivity ~1-2% with side chain similarity), sulfa, AINEs, contraste iodado vs. frutos do mar (myth but relevant)
- Escores: MEWS (early warning), Naegele (gestational age), CKD-EPI 2021 (eGFR without race), FINDRISC, Framingham (10-year CV risk)
- Also: triagem de mensagens assíncronas, sugestão de condutas baseadas em PCDT (Protocolos da Atenção Básica) e linhas de cuidado
- IA para apoio à regulação/estratificação (estratificação de risco da lista de espera)

Not to use / dangerous:
- Diagnóstico autônomo sem supervisão (CFM 2.314/2022 requires physician responsibility; AI cannot replace)
- Alucinações em prescrições: dose errada, medicamento inexistente, apresentação errada - must have guardrails: only prescribe from RENAME/formulário terapêutico local, hard validation
- Chatbots desumanizados para SUS patients: health literacy, elderly, low digital literacy; equity concerns
- IA generativa livre (ChatGPT público) com dados de pacientes - LGPD violation
- Predição sem validação local (bias em dados de populações diferentes)

Section 4 - discard:
- Gestão hospitalar: leitos, escalas de plantão, centro cirúrgico
- Faturamento TISS complexo (RN 465/2021 ANS) - for SUS APS the billing is SISAB/e-Gestor, not TISS
- Módulos de estoque complexos de farmácia central (leave to Fase 2 maybe - actually e-SUS has e-Farmácia... keep simple)
- Burocracia: campos obrigatórios excessivos, duplicação de digitação (e-SUS + sistema próprio), "checklist" que engessa
- Telas com dezenas de cliques: regra dos 3 cliques
- Gamificação, marketing, CRM de pacientes (private practice stuff)
- IA de última geração sem caso de uso claro
- App do paciente completo (agendamento, chat) - maybe Fase 2
- BI avançado - Fase 2
- Integração com laboratórios privados - Fase 2

Section 5 - Decision matrix (15-20 items):
Categories: Prescrição, Prontuário, Telemedicina, IA, Integrações, Segurança/LGPD, UX, Gestão
Items with rationale. Format: table with columns: Nº, Categoria, Item, Racional Clínico, [X] Manter, [ ] Descartar, [ ] Fase 2

Let me draft ~18 items:
1. Prescrição - Receituário com assinatura digital ICP-Brasil (A3 token) e validação CFM - Manter
2. Prescrição - Receita de controle especial eletrônica (RDC 471/2021) - Fase 2 (complex; but high value... maybe Fase 2 due to certification requirements)
3. Prescrição - Integração RENAME + Farmácia Popular (marcador "Aqui tem Farmácia Popular") - Manter
4. Prescrição - Alertas de interação gravidade maior/moderada com base validada - Manter
5. Prontuário - SOAP estruturado com CIAP-2 + CID-10 - Manter
6. Prontuário - Transcrição IA (ambient scribe) com revisão obrigatória - Manter (Fase 1? They said AI copilot is indispensable - Manter)
7. Prontuário - Histórico automático de problemas ativos/medicamentos em uso - Manter
8. Telemedicina - WebRTC vídeo com degradação para áudio/chat - Manter
9. Telemedicina - Modo offline com fila de sincronização e assinatura diferida - Manter
10. Telemedicina - Sala de espera virtual com verificação de identidade e consentimento digital - Manter
11. IA - Cálculo automático de escores (MEWS, CKD-EPI, FINDRISC, Framingham, Naegele) - Manter
12. IA - Sugestão diagnóstica autônoma sem revisão - Descartar
13. IA - Chatbot de triagem sem supervisão médica - Descartar (or Fase 2 with supervision)
14. Gestão - Faturamento TISS de planos privados - Descartar
15. Gestão - Gestão de leitos/escalas hospitalares - Descartar
16. Gestão - Painel de indicadores e-SUS/SISAB (produtividade, cobertura) - Manter (essential for APS management) - or Fase 2? Basic dashboard is important. Manter (simple version).
17. UX - Regra dos 3 cliques / atalhos de teclado - Manter
18. Segurança - LGPD: criptografia, trilha de auditoria, consentimento - Manter
19. Integração - Envio RNDS/DADOS - Fase 2 (complex)
20. Integração - Interoperabilidade HL7 FHIR - Fase 2
21. Agendamento - Agenda simples com teleconsulta - Manter
22. Exames - Pedido de exames com dicionário SUS (SIGTAP) - Manter

That's about 20. Good.

Formatting considerations: The user wants a structured document with headers, tables. This is a professional document request, so rich markdown formatting is appropriate. Should be in Portuguese (Brazil). Length: this is a detailed technical document request - it should be comprehensive but not bloated. The user explicitly asked for "rigor, objetividade e riqueza clínica" - rigor, objectivity, clinical richness. So I should be thorough. Tables are explicitly requested for section 2 (continuation of table) and section 5.

Let me make sure section 2 continues the table format (they said "Conclua a tabela de funcionalidades da Fase 1"). Since I don't have the previous table, I'll present the remaining functionalities in table format with columns like: Funcionalidade | Especificação Técnica/Clinical | Impacto/Justificativa.

Let me write the content:

### Section 2 continuation

Table of Phase 1 functionalities:

| # | Funcionalidade | Especificação Clínico-Técnica | Impacto na APS |
|---|---|---|---|
| 2.1 | Receituário digital (CFM 2.314/2022 + Lei 14.510/2022) | Assinatura com certificado ICP-Brasil (padrão A3/token ou A1), QR Code de validação, PDF/A com marca d'água, numeração sequencial, identificação completa do prescritor (CRM, RQE, CPF) | Elimina receita manuscrita ilegível; permite teleprescrição; validação pública pelo paciente/farmácia |
| 2.2 | Atestado digital | Modelo com CID (opcional ao paciente - LGPD), assinatura digital, formato aceito por RH/INSS | ... |
| 2.3 | Pedidos de exames | Dicionário SIGTAP + laboratório local; campos de preparo; justificativa clínica | ... |
| 2.4 | Prontuário SOAP + CIAP-2 + CID-10 | S-O-A-P com CIAP-2 como eixo episdêmico (episódio de cuidado), CID-10 para faturamento/referência | ... |
| 2.5 | Integração RENAME/Farmácia Popular | Base local sincronizável; flag "consta na Farmácia Popular" (grupos: hipertensão, diabetes...) | ... |
| 2.6 | Alertas de interações | Motor com base validada; gravidade (contraindicada/maior/moderada); duplicidade terapêutica; alergias | ... |

Then subsection on low connectivity telemedicine:
- Arquitetura offline-first: PWA com Service Worker, IndexedDB
- WebRTC: vídeo → áudio → chat → assíncrono (degradação graciosa); TURN/STUN; bitrate adaptativo (Simulcast); fallback
- Cache local: prontuário do paciente agendado pré-carregado no dia
- Fila de sincronização (outbox): receitas/atestados gerados offline ficam pendentes de assinatura; assinatura em lote quando conectividade retorna; timestamp confiável
- Cuidado: receita só é válida após assinatura — comunicar ao paciente que o documento será enviado após assinatura (transparência)
- Métricas: funcionar em 3G/512 kbps; latência