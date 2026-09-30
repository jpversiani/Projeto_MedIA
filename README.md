# ⚡ MedIA Practice SaaS — Intelligent Clinical Operating System

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Architecture](https://img.shields.io/badge/Architecture-Cloud_SaaS_Multi--Tenant-6366f1.svg)](#)
[![Compliance](https://img.shields.io/badge/CFM-2.314%2F2022-emerald.svg)](#)
[![Security](https://img.shields.io/badge/LGPD-Art._11_SHA--256-blue.svg)](#)
[![Tests](https://img.shields.io/badge/Pytest-445%20Passed%20(100%25)-success.svg)](#)
[![Documentation](https://img.shields.io/badge/Status-Relat%C3%B3rio%20Completo%20de%20Recursos-blue.svg)](docs/STATUS_ATUAL_E_RECURSOS_IMPLEMENTADOS.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

O **MedIA Practice SaaS** é um sistema operacional clínico moderno projetado para consultórios médicos particulares, clínicas de especialidades, clínicos gerais e médicos especialistas (Cardiologia, Psiquiatria, Dermatologia, Endocrinologia, Pediatria, Clínica Médica e Medicina de Família). Combina inteligência clínica assistida por IA, telemedicina WebRTC HD (CFM 2.314/2022), emissão de receituário e atestados médicos em PDF com QR Code público de autenticidade (padrão CFM e ICP-Brasil), faturamento TISS ANS 4.01.00 com exportação de lotes XML, controle fiscal DMED (Receita Federal), Command Bar (`Ctrl+K`), modo escuro/claro nativo e trilha de auditoria criptográfica imutável.

---

## 🌟 Principais Pilares da Plataforma

### 🩺 1. Prontuário Eletrônico & Gestão Clínica Longitudinal
* **Acompanhamento de Pacientes e Linhas de Cuidado**: Gestão contínua de prontuários com estratificação de risco cardiovascular e metabólico (HAS/DM), calculadoras médicas (Framingham, TFGe CKD-EPI) e percentis OMS.
* **Prontuário Orientado por Problemas (SOAP)**: Anamnese detalhada, sinais vitais, hipóteses diagnósticas e planos terapêuticos estruturados.

### 🤖 2. Copiloto Clínico SOAP com IA em Tempo Real
* **Estruturação SOAP Dual-Column**: Anamnese (S), Sinais Vitais com Antropometria (O), Diagnóstico Estruturado (A) e Conduta/Prescrição (P).
* **Busca Inteligente de Terminologias**: Codificação instantânea cruzada entre **CIAP-2**, **CID-10** e **CID-11 (OMS)**.
* **Prevenção de Interações Farmacológicas**: Checagem automática contra alergias registradas e catálogo Rename/Anvisa.

### 🏢 3. Multi-Tenancy & Workspace Switcher (SaaS / Redes)
* **Alternância Contextual de Unidade em 1 Clique**: Suporte a consultórios particulares privados e centros públicos de Saúde da Família (ex.: *Consultório Particular MedIA - Montes Claros* vs. *Centro Integrado de Saúde da Família - Capelinha*).
* **Isolamento Lógico Estrito**: Permissões granulares baseadas em papéis (RBAC/ABAC: Médico, Enfermeiro, ACS, Gestor).

### 🔐 4. Autenticação Moderna & SSO Empresarial
* **Single Sign-On (SSO)**: Integração nativa com **Google Workspace** e **Microsoft Entra ID** (OAuth 2.0 / OpenID Connect).
* **Multi-Factor Authentication (MFA / TOTP)**: Algoritmo RFC 6238 nativo para segurança de acesso clínico.
* **Gov.br Integrável**: Arquitetura pronta para federação de identidade cidadã (Backlog ativo).

### 🛡️ 5. Trilha Criptográfica de Auditoria (LGPD Art. 11 & CFM 2.314/2022)
* **Cadeia de Custódia SHA-256 Chained**: `hash_atual = SHA256(hash_anterior + timestamp + dados)`, assegurando não-repúdio probatório contra adulterações de prontuário.
* **Inspeção em Tempo Real**: Ledger auditável integrado no Cockpit Clínico para conformidade perante peritos e órgãos reguladores.

### 📹 6. Telemedicina WebRTC HD & Prescrição Digital ICP-Brasil
* **Videoconsulta Nativa**: Grade de vídeo médico/paciente com Picture-in-Picture (PIP) e sinalização WebSocket resiliente.
* **Termo de Consentimento com Assinatura Digital**: Registro forense de IP, user-agent e consentimento LGPD antes da chamada.
* **Prescrição Eletrônica**: Hashing de documento para dispensação farmacêutica sem expor dados do prontuário.

### 📊 7. Faturamento TISS ANS 4.01.00 & Motor Fiscal DMED
* Geração automática de lotes XML TISS para consultas e exames SADT com validação pré-envio anti-glosas.
* Emissão de recibos fiscais com rastreabilidade para o leiaute magnético da DMED (Receita Federal).

---

## 🏛️ Arquitetura do Sistema

```
Projeto_MedIA/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints REST (Auth SSO, Fila, SOAP, Cidadãos, Telemedicina, TISS, DMED, Auditoria)
│   │   ├── core/            # Configuração de segurança, JWT, CORS e Engine SQLAlchemy 2.0
│   │   ├── models/          # Modelos relacionais (Usuario, Clinica, Cidadao, Atendimento, TrilhaAuditoria)
│   │   ├── schemas/         # Contratos Pydantic v2 com tipagem estrita
│   │   ├── repositories/    # Camada de persistência e repositórios de dados
│   │   ├── services/        # Lógica clínica, regras CFM/ANS e cálculo de hash SHA-256
│   │   ├── static/          # MedIA Cockpit Clínico & Landing Page (HTML5, Tailwind, JS ES6)
│   │   └── main.py          # Ponto de entrada FastAPI com auto-reload
│   ├── tests/               # 437 testes unitários e de integração (100% green)
│   └── requirements.txt
├── docker-compose.yml       # Stack conteinerizada (FastAPI + PostgreSQL 16)
├── Dockerfile
└── CHANGELOG.md             # Histórico formal de versões SemVer (v0.2.0, v0.3.0, v0.4.0, v0.5.0...)
```

---

## ⚡ Como Executar

### 1. Inicialização Rápida Local

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Iniciar servidor backend com reload automático
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Acesse no navegador:
* **Cockpit Clínico**: [http://localhost:8000/app](http://localhost:8000/app)
* **Landing Page**: [http://localhost:8000/](http://localhost:8000/)
* **Documentação OpenAPI / Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Suíte de Testes Automatizados (445 testes)

```bash
cd backend
pytest tests/ -v
```

---

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE). Desenvolvido para a transformação digital da saúde com padrões abertos, segurança e excelência clínica.

