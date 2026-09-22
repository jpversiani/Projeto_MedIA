# 🏥 e-SUS APS Open Source (Prontuário Eletrônico do Cidadão - PEC)

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org)
[![Tests](https://img.shields.io/badge/Pytest-10%20passed-success.svg)](https://docs.pytest.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Réplica de arquitetura aberta, moderna e de alta performance do **e-SUS APS (PEC - Prontuário Eletrônico do Cidadão)**, desenvolvida para atender os padrões clínicos, estruturais e de dados da Atenção Primária à Saúde do Sistema Único de Saúde (SUS).

---

## 🚀 Destaques e Funcionalidades

- **Identificação do Cidadão no Padrão SUS**:
  - Cadastro individual com **Cartão Nacional de Saúde (CNS - 15 dígitos)** e **CPF**.
  - Dados sociodemográficos, condições crônicas autorreferidas (Hipertensão, Diabetes, Tabagismo) e registro de alergias com alertas clínicos visuais.
  - Histórico clínico longitudinal unificado por paciente.

- **Acolhimento à Demanda Espontânea & Triagem**:
  - Aferição de sinais vitais: Pressão Arterial (Sistólica/Diastólica), Frequência Cardíaca, Frequência Respiratória, Temperatura, Glicemia Capilar e Oximetria ($SpO_2$).
  - Antropometria com cálculo automático de **Índice de Massa Corporal (IMC)**.
  - **Classificação de Risco**: Vermelho (Emergência), Amarelo (Urgência), Verde (Pouco urgente) e Azul (Não urgente).
  - Fila de atendimento diária com ordenação por prioridade clínica e tempo de espera.

- **Prontuário Clínico Eletrônico (Método SOAP)**:
  - **S (Subjetivo)**: Motivo da consulta, queixa principal e Histórico da Moléstia Atual (HDA).
  - **O (Objetivo)**: Achados do exame físico com integração imediata aos dados vitais da triagem.
  - **A (Avaliação)**: Diagnósticos e condições ativas codificadas com autocomplete em tempo real para:
    - **CIAP-2** (Classificação Internacional de Atenção Primária).
    - **CID-10** (Classificação Internacional de Doenças).
  - **P (Plano)**: Prescrição terapêutica com posologia, solicitação de exames laboratoriais/imagem e plano de cuidados/retorno.

- **Interoperabilidade Oficial (LEDI / SISAB)**:
  - Exportação de **Ficha de Atendimento Individual (FAI)** compatível com as regras de transporte do **SISAB** (`DadoTransporteThrift` / LEDI APS do Ministério da Saúde).

- **Interface Web Integrada**:
  - Dashboard completo em HTML5 + Tailwind CSS simulando a experiência do PEC oficial.

---

## 🏛️ Arquitetura do Sistema

```
Projeto_dados_tabnet_Sus/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints REST (Cidadãos, Fila, SOAP, Terminologias, UBS)
│   │   ├── core/            # Configurações de ambiente, engine e sessão de banco
│   │   ├── models/          # Modelos relacionais SQLAlchemy
│   │   ├── schemas/         # Validação de dados e contratos com Pydantic v2
│   │   ├── seeds/           # Carga inicial com UBS, profissionais, CIAP-2 e CID-10
│   │   ├── services/        # Módulo de exportação FAI no formato oficial do SISAB
│   │   ├── static/          # Interface Web do Prontuário Eletrônico
│   │   └── main.py          # Ponto de entrada FastAPI
│   ├── tests/               # Suíte de testes automatizados com pytest
│   └── requirements.txt
├── docker-compose.yml       # Orquestração de containers (FastAPI + PostgreSQL 16)
├── Dockerfile               # Build de imagem conteinerizada
├── extrair_odt.py           # Utilitário para extração de especificações em .odt
├── start.sh                 # Script para execução local em um clique
└── README.md
```

---

## ⚡ Como Executar

### Opção 1: Execução Local Rápida (com SQLite nativo)

1. Ative o ambiente virtual e execute o script de inicialização:
```bash
./start.sh
```

2. Acesse no navegador:
- **Prontuário Eletrônico (Interface)**: [http://localhost:8000](http://localhost:8000)
- **Documentação Interativa (Swagger/OpenAPI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Opção 2: Execução com Docker & PostgreSQL

Para rodar o ambiente completo com banco de dados PostgreSQL:

```bash
docker-compose up --build -d
```

O banco de dados e a API estarão operacionais em `http://localhost:8000`.

---

## 🧪 Testes Automatizados

O repositório inclui bateria de testes cobrindo todo o ciclo do paciente (cadastro, cálculo de IMC, acolhimento, validação de unicidade de CPF/CNS, atendimento SOAP e exportação FAI):

```bash
source .venv/bin/activate
pytest backend/tests -v
```

---

## 🗺️ Roteiro de Evolução (Roadmap)

Conforme documentado nas diretrizes técnicas de arquitetura do sistema:
- [x] **Fase 1**: Núcleo Clínico SOAP, Cadastros SUS, Acolhimento e CIAP-2/CID-10.
- [x] **Fase 1.5**: Serviço de serialização e exportação da Ficha de Atendimento Individual (FAI/LEDI).
- [ ] **Fase 2**: Módulo de Sala de Vacina (PNI - Programa Nacional de Imunizações) com controle de lotes.
- [ ] **Fase 3**: Suporte a *Offline-First* com sincronização para Agentes Comunitários de Saúde (ACS).
- [ ] **Fase 4**: Copilot Clínico com IA local (apoio à codificação CIAP-2/CID-10 e protocolos do Ministério da Saúde).

---

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE).
