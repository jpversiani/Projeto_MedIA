# 🏥 OpenSUS (Prontuário Eletrônico do Cidadão — PEC)

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

O **OpenSUS** é uma iniciativa aberta que reimagina o **e-SUS APS (PEC — Prontuário Eletrônico do Cidadão)**, desenvolvida para atender com agilidade e simplicidade aos padrões clínicos, estruturais e de interoperabilidade da **Atenção Primária à Saúde (APS)** do **SUS**.

> **Nota:** Este repositório foi construído com auxílio de orquestração multi-agente (HierAgent). Veja [`docs/ESTADO_ATUAL.md`](docs/ESTADO_ATUAL.md) para o estado atual do projeto.

---

## 🚀 Destaques e Funcionalidades

### Identificação do Cidadão no Padrão SUS
- Cadastro individual com **Cartão Nacional de Saúde (CNS — 15 dígitos)** e **CPF**.
- Dados sociodemográficos, condições crônicas autorreferidas (Hipertensão, Diabetes, Tabagismo) e registro de alergias com alertas clínicos visuais.
- Histórico clínico longitudinal unificado por paciente.

### Acolhimento à Demanda Espontânea & Triagem
- Aferição de sinais vitais: PA sistólica/diastólica, FC, FR, Temperatura, Glicemia capilar e Oximetria (SpO₂).
- Antropometria com cálculo automático de **IMC** e percentis OMS infantis.
- **Classificação de Risco**: Vermelho (Emergência), Amarelo (Urgência), Verde (Pouco urgente) e Azul (Não urgente) — Protocolo Manchester.
- Fila de atendimento diária com ordenação por prioridade clínica e tempo de espera.

### Prontuário Clínico Eletrônico (Método SOAP)
- **S (Subjetivo)**: Motivo da consulta, queixa principal e HDA.
- **O (Objetivo)**: Achados do exame físico integrados aos sinais vitais da triagem.
- **A (Avaliação)**: Diagnósticos e condições ativas com autocomplete para **CIAP-2** e **CID-10**.
- **P (Plano)**: Prescrição terapêutica com posologia, exames e plano de cuidados/retorno.

### Interoperabilidade Oficial (LEDI / SISAB)
- Exportação da **Ficha de Atendimento Individual (FAI)** compatível com o **SISAB** (`DadoTransporteThrift` — Ministério da Saúde).

### Telemedicina (WebRTC)
- Salas de teleconsulta com signaling WebRTC, troca de SDP/ICE, controle de mídia local e compartilhamento de tela.
- Consentimento digital com assinatura em canvas (LGPD / Resolução CFM 2.314/2022).
- Gravação e marcação de teleconsultas com player de revisão.

### Interface Web Integrada
- Dashboard, fila de espera, anamnese, sinais vitais, consentimento, copiloto clínico e acessibilidade (WCAG) em **HTML5 + Tailwind CSS + ES Modules**.

---

## 🏛️ Arquitetura do Sistema

```
Projeto_MedIA/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints REST (Cidadãos, Fila, SOAP, Telemedicina, SISAB, Copiloto, Sincronização)
│   │   ├── core/            # Configuração, engine e sessão de banco de dados
│   │   ├── models/          # Modelos relacionais SQLAlchemy 2.0 (tipagem Pydantic v2)
│   │   ├── schemas/         # Contratos de validação Pydantic v2
│   │   ├── seeds/           # Carga inicial: UBS, profissionais, CIAP-2 e CID-10
│   │   ├── services/        # Regras de negócio (validação CNS, TFGe, CID-10, telemedicina, etc.)
│   │   ├── repositories/    # Acesso a dados (SQLAlchemy 2.0, outbox pattern, repositórios)
│   │   ├── static/          # Interface Web (HTML5 + Tailwind + JS ES Modules)
│   │   └── main.py          # Ponto de entrada FastAPI (app = FastAPI(...))
│   ├── tests/               # Suíte de testes automatizados com pytest
│   └── requirements.txt
├── docker-compose.yml       # Orquestração (FastAPI + PostgreSQL 16)
├── Dockerfile               # Build de imagem conteinerizada
├── extrair_odt.py           # Utilitário para extração de especificações .odt
├── start.sh                 # Script para execução local em um clique
└── docs/
    ├── gerados_por_ia/      # Entregas brutas dos agentes (rastro de auditoria)
    └── ESTADO_ATUAL.md      # Estado atual do projeto e métricas de produção
```

---

## ⚡ Como Executar

### Opção 1: Execução Local (SQLite nativo)

1. Instale as dependências:
```bash
cd backend
pip install -r requirements.txt
```

> ⚠️ **Dependência adicional necessária:** O arquivo `requirements.txt` não inclui `pyjwt`. Instale manualmente:
> ```bash
> pip install pyjwt[crypto]
> ```

2. Execute:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Acesse no navegador:
- **Prontuário Eletrônico (Interface)**: [http://localhost:8000](http://localhost:8000)
- **Documentação Interativa (Swagger/OpenAPI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Opção 2: Execução com Docker & PostgreSQL

```bash
docker-compose up --build -d
```

O banco de dados e a API estarão operacionais em `http://localhost:8000`.

---

## 🧪 Testes Automatizados

```bash
source .venv/bin/activate
cd backend
pytest tests/ -v
```

> ⚠️ **Nota sobre testes:** A suíte de testes tem um `conftest.py` que referencia `app.models` e `app.main` como se `backend/` fosse o root do package. Execute a partir de `backend/` com o `.venv` ativado. Verifique `docs/ESTADO_ATUAL.md` para o status atual da suíte.

---

## 🗺️ Roteiro de Evolução (Roadmap)

- [x] **Fase 1**: Núcleo Clínico SOAP, Cadastros SUS, Acolhimento e CIAP-2/CID-10.
- [x] **Fase 1.5**: Serviço de serialização e exportação da Ficha de Atendimento Individual (FAI/LEDI).
- [ ] **Fase 2**: Módulo de Sala de Vacina (PNI — Programa Nacional de Imunizações) com controle de lotes.
- [ ] **Fase 3**: Suporte *Offline-First* com sincronização para Agentes Comunitários de Saúde (ACS).
- [ ] **Fase 4**: Copiloto Clínico com IA local (apoio à codificação CIAP-2/CID-10 e protocolos do Ministério da Saúde).

---

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE).
