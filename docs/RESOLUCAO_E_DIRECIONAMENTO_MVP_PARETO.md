# 🎯 Resolução Estrutural e Direcionamento do MVP MedIA (Curva de Pareto)

> **Documento Oficial de Certificação Técnica e Operação dos Agentes**  
> **Data:** 25 de setembro de 2026  
> **Escopo:** Projeto_MedIA (`/home/jpversiani/Projeto_MedIA`) & Orquestrador HierAgent (`/home/jpversiani/projeto de multiplos agentes`)  
> **Status:** Suíte 100% verde (236 testes aprovados), Git limpo e sincronizado, Modelo de Negócio realinhado para Atendimento Particular e Convênios (TISS/DMED).

---

## 1. Certificação da Resolução do "Relatório: Código no Local Errado"

Todos os pontos levantados na auditoria anterior foram integralmente sanados e validados:

| Item Auditado | Situação Anterior | Resolução Implementada | Status |
|---|---|---|:---:|
| **1. Suíte de Testes Quebrada** | 239 erros de importação/conftest | Imports corrigidos, fixture mock ajustada, zero erros. | ✅ **236 PASS / 0 FAIL** |
| **2. Testes Dispersos e Duplicados** | 3 locais (`backend/app/tests`, `tests/`, `backend/tests`) | Unificação total em `backend/tests/`. Duplicatas eliminadas. | ✅ **Resolvido** |
| **3. Árvore Morta na Raiz** | `app/` paralelo na raiz sombreando pacotes | Diretório `app/` completamente removido da raiz. | ✅ **Resolvido** |
| **4. Debris e Nomes JSON** | Arquivos corrompidos de JSON na raiz | Removidos da raiz e do rastreamento Git. | ✅ **Resolvido** |
| **5. Arquivo ASCII em Router** | `analytics.py` continha árvore ASCII em vez de código | Documento movido para `docs/ARQUITETURA_ANALYTICS_ASCII.txt`; router FastAPI limpo criado. | ✅ **Resolvido** |
| **6. Divergência `farmacia.py`** | Acoplado a modelos hipotéticos | Integrado com os modelos reais canônicos `app.models.farmacia.Receita`. | ✅ **Resolvido** |
| **7. Divergência `fai_serializer.py`** | Imports inválidos (`validator_as_str`, `SIASAB`) | Reescreveu-se com schemas Pydantic v2 estritos e tipados. | ✅ **Resolvido** |
| **8. Proteção das Maratonas** | Scripts escrevendo código sem validação | Implementado `sanitize_target_path` + validação sintática AST (`ast.parse`) em `continuous_marathon_8h.py`. | ✅ **Resolvido** |

---

## 2. Realinhamento de Negócio: Foco no MedIA Particular & Convênios

Em conformidade com a decisão estratégica do produto:
1. **Atendimento Particular & Convênios de Saúde Suplementar**:
   - **TISS ANS 4.01**: Módulo de geração de guias de Consulta e SP/SADT (`backend/app/services/tiss_generator.py`).
   - **DMED / Recibo Fiscal**: Emissão de recibos dedutíveis de IRPF com hash de integridade eletrônica (`backend/app/api/v1/convenios.py`).
2. **Saúde da Família / Atenção Primária**:
   - Abordagem focada em cuidado longitudinal, acolhimento, método clínico centrado na pessoa e codificação dupla CIAP-2 + CID-10.
3. **Descarte de Itens Fora do Escopo**:
   - Sem dependência obrigatória de envio para SISAB/e-SUS APS público.
   - Eliminação de complexidades de IoT físico (estetos/otoscópios bluetooth).
   - Eliminação de telas labirinto de 50 abas: foco no **Cockpit Clínico Unificado**.

---

## 3. Curva de Pareto: O Que Entrega 80% do Valor do MVP com 20% do Esforço?

Para disponibilizar um MVP funcional e comercializável com máxima agilidade, o desenvolvimento é focado em 4 blocos essenciais:

```
                              [ CURVA DE PARETO — MVP MedIA ]
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │ 1. COCKPIT CLÍNICO UNIFICADO (Telemedicina WebRTC + Prontuário SOAP + Copiloto IA)    │ -> 40% do valor
  │ 2. RECEITUÁRIO DIGITAL & ATESTADOS (Assinatura, PDF/HTML imprimível e QR Code)        │ -> 20% do valor
  │ 3. FATURAMENTO (Guias TISS ANS para Convênios + Recibos DMED para Particulares)      │ -> 15% do valor
  │ 4. SALA VIRTUAL & AGENDAMENTO SIMPLES (Link direto para paciente sem barreiras)      │ -> 10% do valor
  └────────────────────────────────────────────────────────────────────────────────────────┘
                       = 85% do valor percebido pelo médico e paciente
```

---

## 4. Matriz de Atribuição Estratégica dos Agentes

Cada modelo foi alocado estritamente na função onde possui superioridade técnica comprovada:

### 🩺 1. Ling 3.0 Flash Santé (`Researcher-Clinical-Copilot`)
- **Potencialidade**: Especialização em terminologia médica, raciocínio clínico de Atenção Primária (APS), CIAP-2 e CID-10.
- **Missão Foco**:
  - Refinar o **Copiloto Clínico de Diagnóstico Diferencial** (`backend/app/services/copiloto_clinico.py`).
  - Alimentar a base de sugestões clínicas de conduta e interações medicamentosas frequentes na Atenção Primária.
  - Regra de ouro: atuar como assistente ágil de segunda opinião — sem telas labirínticas.

### ⚡ 2. MiMO V2.6 Flash (`Coder-FastAPI-Integrator`)
- **Potencialidade**: Modelo gratuito, extremamente rápido, excelente para contratos de API REST, Pydantic v2 e roteamento FastAPI.
- **Missão Foco**:
  - Implementar os endpoints do **Cockpit Clínico Unificado** conectando vídeo, prontuário e sugestões em um único payload.
  - Validação de schemas Pydantic v2 para emissão de atestados, pedidos de exames e relatórios médicos.
  - Rápida integração entre o front-end e os serviços de backend.

### 🧠 3. DeepSeek V4 Flash 0731 (`Tester-Logic-Auditor`)
- **Potencialidade**: Campeão em raciocínio lógico formal, geração de testes de estresse e validação de regras de faturamento/glosas.
- **Missão Foco**:
  - Expandir a suíte de testes de estresse em `backend/tests/` mantendo cobertura de 100%.
  - Validar algoritmos de regras TISS (cálculo de honorários, validação de carteira de convênio, regras de faturamento).
  - Testar robustez do cache local anti-perda (resiliência a oscilações de internet).

### 💾 4. Qwen 3.6 35B A3B (`DB-Persistence-Specialist` — Local PC RTX 4060)
- **Potencialidade**: Modelo local com GPU dedicada, zero custo de token, ótimo para operações relacionais SQLAlchemy 2.0.
- **Missão Foco**:
  - Criar e otimizar queries e migrações no banco SQLite/Postgres.
  - Aprimorar o histórico longitudinal do prontuário do paciente (`backend/app/repositories/`).
  - Gerenciar repositórios de agendamentos, operadoras e planos de saúde com performance e tipagem estrita.

### 🖥️ 5. NVIDIA Nemotron 3 Ultra (550B) (`UX-Nemotron-Architect` — OpenRouter)
- **Potencialidade**: Colosso de 550 bilhões de parâmetros, domina orquestração de layouts complexos, prompts difíceis e design centrado no médico com redução drástica de carga cognitiva.
- **Missão Foco**:
  - Projetar a arquitetura visual e design system do **Cockpit Clínico Unificado** (`backend/app/static/cockpit_clinico.html`).
  - Desenvolver layouts ergonômicos e sem telas labirínticas para atendimento particular e telemedicina.
  - Otimizar componentes interativos para o médico atender com poucos cliques (SOAP instantâneo, badges semafóricos de risco e emissão de guias TISS/DMED).

### 🎨 6. Bonsai 27B (`UI-Component-Specialist` — Local Notebook RTX 5060)
- **Potencialidade**: Modelo local, excelente para geração rápida de componentes HTML5, Tailwind CSS, widgets interativos leves e scripts JS cliente.
- **Missão Foco**:
  - Implementar os scripts do cliente WebRTC (`js/webrtc_manager.js`) e sincronização de dados locais.
  - Implementar o template elegante da Receita Digital / Atestado com QR Code para impressão e envio por WhatsApp/Email.

### 📊 7. GLM 5.3 Flash (`Architect-Compliance-Lead`)
- **Potencialidade**: Visão de arquitetura de sistemas, geração de XML complexo e conformidade com normas regulatórias.
- **Missão Foco**:
  - Validar a conformidade das guias TISS contra as tabelas oficiais TUSS da ANS.
  - Estruturar a emissão de relatórios financeiros e exportação em lote para as operadoras de saúde suplementar.

---

## 5. Regras Operacionais Inegociáveis para os Agentes

1. **Destino Canônico**: Arquivos de código só podem ser gravados em `backend/app/` e arquivos de teste exclusivamente em `backend/tests/`.
2. **Validação de Sintaxe Pré-Gravação**: Qualquer código Python gerado passa por `ast.parse` antes de tocar o disco.
3. **Execução de Testes Obrigatória**: Ao término de cada ciclo, o runner executa `pytest backend/tests/ -q` e só avança com a suíte verde.
4. **Sem Alucinações de Modelos**: Nenhuma rota ou repositório pode importar classes inexistentes (`# Assuming these models exist`). Todas as dependências devem ser importadas de `app.models`.
