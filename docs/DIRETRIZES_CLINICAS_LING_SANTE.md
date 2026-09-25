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

## 2.1 Funcionalidades Clínicas que Salvam Tempo Médico e Aumentam Segurança do Paciente

| # | Funcionalidade | Impacto | Justificativa Clínica |
|---|---|---|---|
| 1 | **Prontuário Eletrônico Orientado por Problemas (POO)** — método SOAP | ⭐⭐⭐⭐⭐ | Reduz 40-60% do tempo de documentação; clareza do raciocínio clínico |
| 2 | **AI Scribe (Escrita Clínica Automatizada)** | ⭐⭐⭐⭐⭐ | Salva 10-15 min/consulta em anotações; libera o médico para olhar o paciente |
| 3 | **Receituário Digital com Assinatura Eletrônica** (conforme CFM 2.314/2022 e ICP-Brasil) | ⭐⭐⭐⭐⭐ | Conformidade legal OBRIGATÓRIA — sem isso, sistema não é utilizável legalmente |
| 4 | **Checagem em tempo real de interações medicamentosas + RENAME** | ⭐⭐⭐⭐⭐ | Prevenção de eventos adversos graves; obrigação legal do médico |
| 5 | **Atestado Digital