# PROJETO MEDIA — DIRETRIZES ESTRATÉGICAS DE ARQUITETURA CLÍNICA
## Sistema Clínico Especializado: Prática Particular, Convênios e Telemedicina de Alta Performance
**Elaborado por:** Ling 3.0 Flash Santé & Arquitetura de Sistemas de Saúde  
**Destinatário:** Médico Responsável / Diretor Técnico  
**Cenário de Operação:** Consultório Home Office / Telemedicina Particular e Saúde da Família  
**Versão:** 2.0 (Revisado com Diretrizes do Médico)

---

## 1. VISÃO GERAL DO CASO DE USO E MODELO DE ATENDIMENTO

O **PROJETO MEDIA** é projetado para um médico atuando em **Home Office** em atendimentos **Particulares e de Convênios de Saúde**, adotando uma abordagem clínica e humanizada de **Saúde da Família e Comunidade**:

1. **Atendimento Particular & Convênios:** Suporte a emissão de guias TISS (Consulta e SP/SADT), recibos com informações fiscais para dedução (DMED / IRPF), e controle financeiro de particulares e operadoras de saúde.
2. **Abordagem de Saúde da Família (APS):** Longitudinalidade, visão integral do paciente, prontuário SOAP orientado por problemas, histórico familiar e acompanhamento de condições crônicas.
3. **Sem Burocracia SUS:** Sem obrigatoriedade de transmissão ou remessa de lotes ao SISAB/e-SUS APS do Ministério da Saúde. O sistema foca na agilidade do atendimento privado.
4. **Infraestrutura com Internet e Alta Resiliência:** Opera preferencialmente conectado para teleconsultas em tempo real, mas com arquitetura blindada contra quedas temporárias de rede (não perde digitação, rascunha prescrições e sincroniza de forma transparente).
5. **Diagnóstico Assistido por IA (Sistema Especialista Integrado):** O sistema traz suporte ativo ao diagnóstico clínico com sugestão de hipóteses, diagnósticos diferenciais, protocolos clínicos e cálculo de risco, em uma interface direta e desobstruída.
6. **Hardware Limpo:** Sem periféricos IoT complexos (estetoscópios ou otoscópios digitais estão 100% descartados).

---

## 2. O QUE SÃO "TELAS LABIRINTO" E SUA RELAÇÃO COM SISTEMAS ESPECIALISTAS DE DIAGNÓSTICO

### O Problema Histórico das "Telas Labirinto"
Nos anos 1990 e 2000, os primeiros **Sistemas Especialistas de Diagnóstico** em saúde tentavam guiar o médico por meio de árvores de decisão rígidas. O resultado prático foi o surgimento dos chamados "prontuários labirinto":
- **Árvores de perguntas sucessivas:** Para cada resposta (ex: "tem tosse?"), o sistema abria uma nova sub-aba ou modal (ex: "tosse com secreção?"), gerando dezenas de cliques obrigatórios.
- **Formulários encadeados e engessados:** O médico passava a consulta inteira olhando para o monitor, procurando onde clicar para avançar o fluxo, em vez de olhar e conversar com o paciente.
- **Fragmentação da tela:** Prontuários com 15 a 40 abas separadas (aba de sintomas, aba de antecedentes, aba de hipóteses, aba de prescrição, aba de atestados).

### Como o MedIA Resolve Isso com IA Moderna
No **MedIA**, o diagnóstico assistido por IA e sistema especialista não exige navegação labiríntica. Ele opera com o conceito de **Painel Clínico Unificado (Cockpit)**:
1. **Escuta Ativa ou Digitação Livre (SOAP):** O médico registra a anamnese em campo aberto ou deixa o *Ambient Scribe* capturar a conversa da teleconsulta.
2. **Motor Especialista em Background:** A IA analisa as queixas, sinais e histórico, cruzando com bases clínicas validadas.
3. **Card Lateral de Diagnóstico Assistido:** Em uma barra lateral limpa (sem modais nem bloqueios), a IA apresenta:
   - *Hipóteses Diagnósticas mais prováveis* (com código CID-10 e CIAP-2 correspondentes).
   - *Diagnósticos Diferenciais a não esquecer* ("Red Flags").
   - *Exames complementares recomendados* para esclarecimento.
   - *Escores automáticos calculados* (Framingham, CKD-EPI, Naegele, FINDRISC).
4. **Aplicação com 1 Clique:** O médico simplesmente clica na hipótese sugerida para incorporá-la à sua avaliação no prontuário. Zero formulários encadeados.

---

## 3. O PAPEL DA INTELIGÊNCIA ARTIFICIAL: DIAGNÓSTICO E PRESCRIÇÃO

### 3.1 Recursos de Diagnóstico por IA (Bem-vindos e Ativos)
- **Motor de Diagnóstico Diferencial:** Análise sintomatológica cruzada que sugere causas prováveis e doenças raras ou graves a descartar.
- **Escores de Risco em Tempo Real:** Cálculo instantâneo de risco cardiovascular, metabólico, renal e obstétrico.
- **Protocolos Clínicos Integrados:** Guias terapêuticos rápidos no ponto de cuidado (ex: conduta em asma descompensada, metas de PA conforme perfil do paciente).
- **Farmacovigilância Ativa:** Bloqueio e alerta imediato de interações fatais (ex: Tríplice Whammy, Claritromicina + Sinvastatina) e alergias medicamentosas registradas.

### 3.2 Diretrizes de Uso Seguro
- As sugestões diagnósticas da IA servem como suporte e auxílio cognitivo rápido durante a consulta.
- A prescrição final e a validação do plano terapêutico são sempre confirmadas pelo profissional antes da assinatura digital ICP-Brasil.
- Evitam-se alucinações de dosagem por meio de dicionários farmacológicos com travas de segurança posológica.

---

## 4. CONECTIVIDADE E RESILIÊNCIA: TELEMEDICINA ESTÁVEL COM PROTEÇÃO CONTRA QUEDAS

Como o consultório opera online com telemedicina:
- **Fluxo Normal (Online):** Chamada de vídeo WebRTC fluida, busca rápida em nuvem, integração bancária/convênios e envio instantâneo de receitas por WhatsApp e e-mail.
- **Proteção Contra Quedas (Resiliência Local):**
  - **Auto-save local contínuo:** A cada caractere digitado no prontuário, os dados são salvos no cache seguro do navegador/aplicação. Se a luz oscilar ou a internet piscar, nada é perdido.
  - **Fallback de Vídeo:** Se a banda estreitar momentaneamente, a chamada reduz resolução ou mantém áudio contínuo sem derrubar a sala.
  - **Fila de Saída (Outbox):** Se a conexão cair na hora de emitir a receita, o documento fica armazenado e aguardando confirmação de envio assim que a conexão restabelecer.

---

## 5. MATRIZ DE DECISÃO ESTRATÉGICA ATUALIZADA (22 ITENS)

| # | Categoria | Funcionalidade / Item | Veredito | Status no MedIA | Racional Clínico & Operacional |
|:---:|:---|:---|:---:|:---:|:---|
| **1** | **Prontuário** | SOAP estruturado com CIAP-2 e CID-10 | **Manter** | `[X] APROVADO` | Estrutura ágil, clara e compatível com saúde da família. |
| **2** | **Prontuário** | Proteção anti-perda (Auto-save local contínuo) | **Manter** | `[X] APROVADO` | Se houver queda de luz ou oscilação de sinal, nenhuma anotação se perde. |
| **3** | **Prontuário** | Resumo em 1 clique: Histórico, Problemas e Remédios | **Manter** | `[X] APROVADO` | Visão panorâmica imediata do paciente e da família. |
| **4** | **Prontuário** | Telas labirinto (árvores rígidas com dezenas de cliques) | **Descartar** | `[X] DESCARTADO` | Substituído por campo aberto com IA contextual em barra lateral. |
| **5** | **Telemedicina** | WebRTC fluida com adaptação dinâmica de banda | **Manter** | `[X] APROVADO` | Garante teleconsulta de alta qualidade com contingência automática de áudio. |
| **6** | **Telemedicina** | Consentimento informado digital do paciente | **Manter** | `[X] APROVADO` | Conformidade legal mandatória da Resolução CFM nº 2.314/2022. |
| **7** | **Telemedicina** | Sala de espera virtual e link direto de acesso | **Manter** | `[X] APROVADO` | Paciente acessa pelo navegador do celular ou PC sem instalar nada. |
| **8** | **Telemedicina** | Conexão com estetoscópios / otoscópios IoT | **Descartar** | `[X] DESCARTADO` | Desnecessário para a proposta de telemedicina do MedIA. |
| **9** | **IA Clínica** | Sistema Especialista & Diagnóstico Assistido | **Manter** | `[X] APROVADO` | Sugestão rápida de hipóteses, diagnósticos diferenciais e condutas. |
| **10** | **IA Clínica** | Ambient Scribe (transcrição de fala para nota SOAP) | **Manter** | `[X] APROVADO` | Gera a minuta da consulta automaticamente enquanto o médico conversa. |
| **11** | **IA Clínica** | Checagem de interações fatais (Tríplice Whammy, etc.) | **Manter** | `[X] APROVADO` | Segurança máxima na farmacoterapia e blindagem profissional. |
| **12** | **IA Clínica** | Cálculo de Escores: Naegele, CKD-EPI, Framingham | **Manter** | `[X] APROVADO` | Automatiza escores clínicos complexos em tempo real. |
| **13** | **IA Clínica** | Diagnóstico autônomo sem supervisão do médico | **Descartar** | `[X] DESCARTADO` | A IA atua como apoio cognitivo; a decisão clínica é do médico. |
| **14** | **Prescrição** | Receituário com assinatura digital ICP-Brasil | **Manter** | `[X] APROVADO` | Validade jurídica em todas as farmácias do Brasil (CFM 2.314). |
| **15** | **Prescrição** | Envio direto da receita por WhatsApp e E-mail | **Manter** | `[X] APROVADO` | Paciente recebe link seguro e QR Code no ato da consulta. |
| **16** | **Prescrição** | Base farmacológica completa com posologias usuais | **Manter** | `[X] APROVADO` | Facilita prescrição de medicamentos de referência, genéricos e similares. |
| **17** | **Convênios** | Geração e Emissão de Guias TISS (Consulta e SP/SADT) | **Manter** | `[X] APROVADO` | Permite faturamento e atendimento a operadoras e planos de saúde. |
| **18** | **Convênios** | Recibos para Reembolso e Relatório Fiscal DMED | **Manter** | `[X] APROVADO` | Fundamental para pacientes particulares solicitarem reembolso no plano. |
| **19** | **Integrações** | Exportação e envio de lotes SISAB / e-SUS APS | **Descartar** | `[X] DESCARTADO` | Desnecessário para atendimento em consultório particular. |
| **20** | **Integrações** | Pedidos de Exames com justificativa clínica | **Manter** | `[X] APROVADO` | Solicitações com indicação que atendem às exigências dos convênios. |
| **21** | **Gestão** | Acompanhamento Longitudinal de Famílias e Crônicos | **Manter** | `[X] APROVADO` | Gestão de hipertensos, diabéticos, gestantes e saúde preventiva. |
| **22** | **Gestão** | Módulos hospitalares (escala de leitos e plantões) | **Descartar** | `[X] DESCARTADO` | Fora do escopo do consultório de Home Office. |

---

## 6. DIRETRIZ ARQUITETURAL CONCLUSIVA

> *"O Projeto MedIA consolida o melhor dos dois mundos: a profundidade humana e longitudinal da **Medicina de Família**, unida à eficiência e agilidade da **Prática Particular e de Convênios**.*  
> *A Inteligência Artificial atua como um sistema especialista de diagnóstico e copiloto clínico em uma interface limpa, sem árvores burocráticas e sem dependência de hardware externo."*
