# 🏛️ MATRIZ DE PERFIS, ESPECIALIDADES E ATRIBUIÇÕES DE MODELOS
## Cluster Multi-Agente HierAgent 2.0 & Ecossistema MedIA

> **Documento Canônico de Referência Técnica**  
> **Versão:** 2.0 (Saúde 4.0 / Multi-Tenancy / Free-Tier Priority)  
> **Finalidade:** Guia estruturado para o Diretor Estrategista e o Scheduler distribuído alocarem tarefas com máxima eficiência computacional, menor latência e custo zero prioritário.

---

## 🎯 1. Princípios Operacionais e Regras de Roteamento

1. **Prioridade de Custo Zero (Free-First):**
   - **Camada 1 (Hardware Local & LAN - R$ 0,00 Absoluto):** Modelos rodando no PC Zorin (GPU RTX 4060 e CPU Ryzen 7) e no Notebook TUF 16 (RTX 5060) devem absorver todo o tráfego sensível, contínuo e volumoso.
   - **Camada 2 (OpenRouter Free Tier `:free`):** Provedores que disponibilizam cotas gratuitas para modelos especializados.
   - **Camada 3 (Cloud PAYG):** Acionada apenas sob demanda extrema ou para prompts de complexidade que exijam o colosso de 550B parâmetros.

2. **Roteamento por Domínio Cognitivo:**
   - **Nunca** delegar tarefas simples de chat a modelos MoE de alto custo ou com reasoning pesado.
   - **Nunca** delegar engenharia de software ou refatoração profunda ao especialista clínico (Ling Santé).
   - **Nunca** delegar geração estrita de JSON ao Laguna S ou Nex-N2.5.
   - **Sempre** utilizar Qwen 2.5 7B na CPU para validação local de sintaxe e schemas com zero impacto na VRAM da GPU.

---

## 📊 2. Matriz Sintética de Roteamento Rápido

| Modelo | Hospedagem / Tier | Perfil Principal | Onde Ganha (Superpoder) | Onde Perde (Evitar) | Responsabilidade no Cluster |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen 2.5 7B** | Local CPU (:11434)<br>`LOCAL R$ 0,00` | Auditor de Código & Schemas | Poder computacional desproporcional; código e matemática de 14B-20B; português nativo | Sem aptidão agêntica complexa; respostas excessivamente concisas | Validação de schemas Pydantic v2, testes rápidos, docstrings e JSON estrito |
| **Qwen 3.6 35B A3B** | Local GPU (:11435)<br>`LOCAL R$ 0,00` | Arquiteto de Backend & Tenancy | Velocidade MoE (ativa ~3B/tok); excelente custo-benefício em roteamento; confidencialidade local | Retenção de fatos isolados de nicho (biologia/leis específicas); VRAM 8GB | Criptografia SHA-256 encadeada, tokens JWT de multi-tenancy, regras de negócio locais |
| **Bonsai 27B** | Notebook TUF LAN (:11434)<br>`LAN R$ 0,00` | Planejador Tree-of-Thought & UI | Busca em árvore (Tree-of-Thought); raciocínio não-linear; baixa alucinação; 35+ t/s | Chat casual truncado; alto tempo deliberando caminhos ocultos em tarefas triviais | Planejamento de refatoração, árvores de dependência, WebRTC e front-end médico |
| **Meta Llama 3.1 8B** | Edge / Chat Local<br>`LOCAL R$ 0,00` | Chatbot & Interação Humana | Leveza de edge; fluidez de conversação; tom amigável e seguro de atendimento | Teto lógico baixo para engenharia pesada; degrada contexto acima de 15k tokens | Atendimento conversacional a pacientes, triagem de queixas e resumos informais |
| **GLM 5.3 Flash** | OpenRouter<br>`FREE TIER / PAYG` | Arquiteto-Chefe & Resolução de Bugs | Raciocínio profundo para repositórios complexos (DeepSWE 63.4); atenção híbrida texto+imagem | Gasta tokens deliberando antes de responder; evitar para tarefas banais | Resolução de bugs difíceis em monorepos, arquitetura de microsserviços e integração |
| **MiMo v2.6 Flash** | OpenRouter<br>`FREE TIER / LOW COST` | Engenheiro CLI & Automação Infra | Multimodal nativo (áudio/vídeo/imagem/texto); custo de saída US$ 0,28/M; CLI (TerminalBench 89.9) | Entra em loop em código quebrado; alucina ferramentas (`browser_use`); chat pouco fluido | Comandos Bash, Docker, deploys, pipelines de infraestrutura e parsing multimodal |
| **DeepSeek v4 Flash** | OpenRouter<br>`FREE TIER / LOW COST` | Autocomplete & Engenheiro QA | Menor latência (TTFT mínimo); menor custo de entrada (US$ 0,038/M); HumanEval 94.5% | Visão de longo horizonte em refatorações massivas de monorepos | Autocomplete de rotas FastAPI, geração em massa de testes unitários Pytest e mocks |
| **Ling 3.0 Flash Santé** | OpenRouter<br>`FREE TIER` | Diretor Clínico & Protocolos SOAP | Especialista biomédico isolado; prontuários, farmacologia, interações e diagnósticos CFM | Programação tradicional de software e lógica de infraestrutura | Validação de consistência clínica, codificação CID-10/CIAP-2, auditoria de receitas |
| **Laguna S 2.1** | OpenRouter / Local<br>`FREE / OPEN-WEIGHT` | Engenheiro de Monorepo & Contexto | Lê bases inteiras de código sem corromper memória; estabilidade máxima; open-weight | Micro-tarefas isoladas fora de contexto; dificuldade nativa de validação JSON pura | Auditoria cross-file em repositórios inteiros, indexação de contexto e detecção de drift |
| **Nex-N2.5-Pro** | OpenRouter<br>`FREE TIER` | Agente Visual & Computer Use | Campeão em Computer Use (OSWorld 56.4); clica, visualiza telas e navega em interfaces e SO | TTFT muito elevado (397B); alta taxa de erro em dados estruturados/JSONs (~26%) | Navegação visual E2E, validação de layouts no navegador e testes de UI de ponta a ponta |
| **NVIDIA Nemotron 3 Ultra** | OpenRouter<br>`FREE TIER / CLOUD` | Estrategista de Hard Prompts & Design | Colosso de 550B para prompts de extrema dificuldade (LMSYS Hard); contexto massivo; pipelines complexas | Overkill para tarefas simples; latência e dependência total de nuvem | Decomposição de metas monumentais, orquestração de segundo nível e Design System 4.0 |

---

## 🔍 3. Fichas Técnicas e Diretrizes de Engenharia por Modelo

---

### 1. NVIDIA Nemotron 3 Ultra (550B)
- **Perfil:** Estrategista Master de "Hard Prompts" & Arquiteto de Design System
- **Onde Ganha:**
  - Orquestração e "Hard Prompts": É um colosso arquitetural focado em raciocínio de múltiplas etapas e coordenação de outros agentes. Brilha no topo do ranking para prompts de alta complexidade (*LMSYS Hard*).
  - Capacidade de Contexto: Manipula gigantescas quantidades de dados e documentos densos sem esquecer as instruções iniciais, suportando nativamente pipelines robustas e autônomas.
- **Onde Perde:**
  - Overkill para Tarefas Simples: Por ter 550 bilhões de parâmetros, sua inferência é naturalmente mais pesada e com maior latência (TTFT elevado). Usá-lo para traduzir um texto ou gerar um script curto é como usar um guindaste para levantar um copo.
  - Dependência de Nuvem: Praticamente impossível de ser rodado localmente por usuários comuns, exigindo dependência total de endpoints de API.
- **Atribuições no Cluster:**
  - Decomposição inicial de épicos complexos.
  - Resolução de conflitos de design de alto nível.
  - Arquitetura de design systems de missão crítica para saúde.
- **Diretriz de Prompting:** Fornecer metas de alto nível com restrições explícitas; não micromanagear detalhes de baixo nível.

---

### 2. Qwen 2.5 7B
- **Perfil:** Auditor Local de Código, Schemas Pydantic v2 & Sintaxe Python
- **Hospedagem:** PC Zorin (Local CPU - Ryzen 7 5700G, 16 Threads, 0 VRAM)
- **Custo:** R$ 0,00
- **Onde Ganha:**
  - Poder Computacional Desproporcional: O modelo da Alibaba entrega resultados de matemática e código que rivalizam com modelos do dobro do seu tamanho (14B-20B).
  - Multilinguismo Robusto: É excepcionalmente bom em português brasileiro, processando nuances culturais, legislativas e gramaticais com superioridade.
- **Onde Perde:**
  - Falta de Habilidade Agêntica: Não foi feito para orquestrar uso complexo de ferramentas (*tool-use*) encadeadas ou agir de forma totalmente autônoma em um terminal.
  - Respostas Concisas Demais: Tende a ser tão direto que às vezes falha em explicar didaticamente o raciocínio por trás da solução, a menos que seja forçado via prompt.
- **Atribuições no Cluster:**
  - Auditoria estrita de schemas Pydantic v2.
  - Validação sintática AST e geração de docstrings.
  - Conversão e saneamento de estruturas JSON/SQLAlchemy.
- **Diretriz de Prompting:** Solicitar sempre saídas diretas em código ou JSON puro sem rodeios; exigir explicações apenas quando necessário.

---

### 3. Qwen 3.6 35B A3B
- **Perfil:** Engenheiro Local de Backend, Criptografia & Tenancy
- **Hospedagem:** PC Zorin (Local GPU - RTX 4060 8GB VRAM + llama.cpp)
- **Custo:** R$ 0,00
- **Onde Ganha:**
  - Velocidade de Arquitetura MoE: Sendo um modelo *Mixture of Experts* (35B no total, ativando ~3B por token), entrega a inteligência de um modelo de peso médio com a velocidade de um modelo microscópico.
  - Custo-Benefício de Roteamento: Excelente para pipelines corporativos que precisam de milhares de decisões lógicas por minuto sem estourar orçamento.
- **Onde Perde:**
  - Retenção de Fatos Específicos: Como ativa poucos parâmetros por vez (3B), sua capacidade de memorizar fatos isolados de nicho (biologia rara, história, leis pontuais) é inferior a modelos densos de 30B+.
- **Atribuições no Cluster:**
  - Cálculo de hash SHA-256 encadeado da Trilha de Auditoria LGPD.
  - Verificação e assinatura de tokens JWT de multi-tenancy.
  - Lógica central de transações de prontuário eletrônico.
- **Diretriz de Prompting:** Especificar sempre o formato exato da entrada e saída de dados; excelente para tarefas lógicas algorítmicas.

---

### 4. Bonsai 27B
- **Perfil:** Planejador Tree-of-Thought, WebRTC & Front-End Clínico Distribuído
- **Hospedagem:** Notebook TUF 16 (Remoto LAN - i7 14650HX, RTX 5060 8GB VRAM, Ollama)
- **Custo:** R$ 0,00
- **Onde Ganha:**
  - Busca em Árvore (Tree-of-Thought): Foco em raciocínio não-linear. Fenomenal para planejamento estruturado, quebra-cabeças lógicos, refatoração de árvores de dependência em código.
  - Redução de Alucinação: Gera caminhos de raciocínio ocultos antes de responder, sendo extremamente seguro e preciso em afirmações finais.
- **Onde Perde:**
  - Desempenho em Chat Casual: A arquitetura baseada em etapas torna a resposta truncada e mais lenta. Não é fluido para redação literária ou interações humanas rápidas.
  - Consumo de Tokens de Pensamento: Tarefas simples são penalizadas pelo tempo gasto mapeando alternativas antes do primeiro token visível.
- **Atribuições no Cluster:**
  - Refatoração de componentes de interface HTML5/Tailwind/JavaScript.
  - Sinalização de salas WebRTC e vídeo PIP para telemedicina.
  - Mapeamento de grafos de dependência entre módulos clínicos.
- **Diretriz de Prompting:** Apresentar o problema estruturalmente e solicitar a árvore de decisão ou a arquitetura de blocos.

---

### 5. Meta Llama 3.1 8B
- **Perfil:** Especialista em Diálogo, Triagem Inicial & Comunicação com o Paciente
- **Hospedagem:** Edge Computing / Nós Leves / Celular / Laptop
- **Custo:** R$ 0,00
- **Onde Ganha:**
  - Leveza e Deploy Local: Rei do edge computing. Roda em hardware modesto com facilidade.
  - Fluidez Conversacional: Excelente tom humano, acolhimento clínico, estruturação de textos e moderação segura.
- **Onde Perde:**
  - Teto Lógico Baixo: Falha em problemas matemáticos avançados ou dedução em várias etapas.
  - Degradação de Contexto: Perde detalhes e alucina quando o prompt ultrapassa 15k-20k tokens.
- **Atribuições no Cluster:**
  - Acolhimento e chat com pacientes na recepção virtual.
  - Redação de mensagens preventivas de saúde via WhatsApp/Push.
  - Resumo de prontuário em linguagem acessível ao cidadão.
- **Diretriz de Prompting:** Manter prompts com menos de 10k tokens e instruções claras de tom de voz.

---

### 6. MiMo v2.6 Flash (Xiaomi)
- **Perfil:** Engenheiro de CLI, Automação de Infraestrutura & Multimodalidade
- **Hospedagem:** OpenRouter (`xiaomi/mimo-v2.6-flash:free`)
- **Onde Ganha:**
  - Multimodalidade Integrada: O único na categoria de baixo custo a processar texto, imagem, vídeo e áudio nativamente na mesma janela.
  - Custo de Saída: US$ 0,28 por milhão de tokens gerados, ideal para grandes documentações.
  - Automação de CLI: Pontuação 89.9 no *Terminal Bench* para comandos Bash, Docker e infraestrutura.
- **Onde Perde:**
  - Loops de Pensamento: Em ambientes de código quebrados, tende a travar relendo arquivos e gastando tokens.
  - Alucinação de Ferramentas: Tende a invocar ferramentas inexistentes (`browser_use`) fora de seu framework nativo.
  - Fluidez Textual: Escrita em chat cotidiana truncada.
- **Atribuições no Cluster:**
  - Scripts de deploy, contêineres Docker e rotinas de backup.
  - Processamento de anexos multimodais (áudios de teleconsulta, exames em imagem).
  - Automação de pipelines de CI/CD.
- **Diretriz de Prompting:** Passar comandos Bash explícitos; proibir chamadas de ferramentas externas fora das fornecidas.

---

### 7. DeepSeek v4 Flash 0731
- **Perfil:** Autocomplete Ultra-Rápido, Geração de Mocks & Suites Pytest
- **Hospedagem:** OpenRouter (`deepseek/deepseek-v4-flash-0731` / `deepseek-chat:free`)
- **Onde Ganha:**
  - Velocidade Bruta: Menor latência e resposta mais rápida do cluster.
  - Custo de Entrada: US$ 0,038 por milhão de tokens (extremamente econômico para prompts volumosos).
  - Autocomplete de Código: Respostas diretas e limpas (94.5% no *HumanEval* com Thinking Max).
- **Onde Perde:**
  - Foco Estrito: Menos eficiente na compreensão de arquiteturas complexas ou refatorações massivas de longo horizonte.
- **Atribuições no Cluster:**
  - Geração concorrente de testes automatizados unitários com pytest.
  - Autocomplete em tempo real de endpoints FastAPI.
  - Mocks e geradores de dados de teste sintéticos (pacientes, guias TISS).
- **Diretriz de Prompting:** Solicitar diretamente a implementação da função com seus testes associados.

---

### 8. GLM 5.3 Flash (Z.ai)
- **Perfil:** Arquiteto-Chefe de Software, Análise de Repositórios & Resolução de Bugs
- **Hospedagem:** OpenRouter (`z-ai/glm-5.3-flash:free`)
- **Onde Ganha:**
  - Lógica e Resolução de Bugs: O mais inteligente para entender repositórios complexos e corrigir bugs de arquitetura (63.4 no *DeepSWE*).
  - Equilíbrio Analítico: Atenção híbrida para navegar entre lógica densa e suporte a diagramas/imagens.
- **Onde Perde:**
  - Consumo de Tokens: Gasta tempo e tokens deliberando antes de entregar respostas para tarefas simples.
- **Atribuições no Cluster:**
  - Depuração e correção de quebras em testes de integração.
  - Resolução de dependências circulares e acoplamentos indevidos.
  - Revisão arquitetural de rotas FastAPI e SQLAlchemy 2.0.
- **Diretriz de Prompting:** Fornecer o stack trace completo do erro e o trecho dos arquivos envolvidos.

---

### 9. Laguna S 2.1 (Poolside)
- **Perfil:** Engenheiro de Contexto de Repositório & Estabilidade em Monorepos
- **Hospedagem:** OpenRouter (`poolside/laguna-s-2.1:free`) / Execução Local Open-Weight
- **Onde Ganha:**
  - Estabilidade em Repositórios: Lê bases de código inteiras sem corromper a memória de contexto.
  - Privacidade e Acesso: Modelo *open-weight*, permitindo download e execução local via vLLM.
- **Onde Perde:**
  - Micro-tarefas Isoladas: Abaixo dos concorrentes em scripts soltos fora do contexto do projeto.
  - Validação JSON: Dificuldade nativa em forçar saída estrita em JSON puro.
- **Atribuições no Cluster:**
  - Leitura global do repositório para garantia de aderência a padrões arquiteturais.
  - Detecção de código duplicado ou órfão entre frontend e backend.
  - Refatorações que dependem do entendimento de múltiplos pacotes.
- **Diretriz de Prompting:** Fornecer o mapa da árvore de arquivos e perguntar sobre consistência global.

---

### 10. Nex-N2.5-Pro (Nex-AGI)
- **Perfil:** Especialista em Computer Use & Validação Visual de UI/SO
- **Hospedagem:** OpenRouter (`nex-agi/nex-n2.5-pro:free`)
- **Onde Ganha:**
  - Uso Visual de Computador: Campeão absoluto (56.4 no *OSWorld*). Clica em botões, inspeciona telas e navega em interfaces e SO autonomamente.
- **Onde Perde:**
  - Latência (TTFT): Tempo até o primeiro token elevado (arquitetura massiva de 397B).
  - Estruturação de Dados: Taxa de erro de ~26% ao tentar gerar dados formatados/JSONs.
- **Atribuições no Cluster:**
  - Testes visuais de ponta a ponta na Landing Page e no Cockpit Clínico.
  - Validação de quebra de layout, alinhamento de componentes e responsividade.
  - Simulação de navegação do médico pelo fluxo de acolhimento e SOAP.
- **Diretriz de Prompting:** Fornecer screenshots ou layouts e solicitar verificação de usabilidade e ação visual.

---

### 11. Ling 3.0 Flash Santé (InclusionAI)
- **Perfil:** Diretor Clínico, Terminologias Médicas, SOAP & Farmacologia
- **Hospedagem:** OpenRouter (`inclusionai/ling-3.0-flash-sante:free`)
- **Onde Ganha:**
  - Domínio Clínico e Biomédico: Especialista isolado para leitura de prontuários, farmacologia, interações medicamentosas e diagnósticos baseados em evidências.
- **Onde Perde:**
  - TI e Desenvolvimento: Arquitetura desperdiçada para programação tradicional de software; perde para todos os outros em engenharia pura.
- **Atribuições no Cluster:**
  - Validação de regras clínicas de acolhimento (Manchester adaptado).
  - Codificação semântica automática para CIAP-2 e CID-10.
  - Alerta de interações medicamentosas e contraindicações em prescrições digitais.
  - Conformidade com as diretrizes do CFM (Resolução 2.314/2022).
- **Diretriz de Prompting:** Prompts focados em casos clínicos, sintomas, posologia e hipóteses diagnósticas.

---

## 🌳 4. Fluxograma de Decisão do Scheduler (Decision Tree)

```text
                                [NOVA TAREFA RECEBIDA]
                                          │
              ┌───────────────────────────┴───────────────────────────┐
     [Tarefa Clínica / Médica]                               [Tarefa de Software / Infra]
              │                                                       │
    Ling 3.0 Flash Santé                           ┌──────────────────┴──────────────────┐
    (CID-10, CIAP-2, SOAP)                  [Infra / CLI / Deploy]              [Código / Backend / Testes]
                                                   │                                     │
                                            MiMo v2.6 Flash               ┌──────────────┴──────────────┐
                                            (Bash, Docker, CI/CD)  [Bugs Difíceis / Repos]   [Schemas / Validações]
                                                                          │                             │
                                                                   GLM 5.3 Flash                 Qwen 2.5 7B
                                                                   (DeepSWE 63.4)             (CPU Local R$ 0,00)
                                                                                                        │
                                                                                          ┌─────────────┴─────────────┐
                                                                                 [Testes / Mocks Rápidos]   [Cripto / Tenancy]
                                                                                          │                         │
                                                                                   DeepSeek v4 Flash          Qwen 3.6 35B
                                                                                   (HumanEval 94.5%)        (GPU Local R$ 0,00)
```

---

## 🛡️ 5. Políticas de Fallback e Resiliência

1. **Se o Nó Local GPU (Qwen 3.6 35B) estiver ocupado:**
   - Fallback de inferência imediato para o **Qwen 2.5 7B** (CPU) para manter custo zero (R$ 0,00).
2. **Se o Nó LAN Notebook (Bonsai 27B) estiver desconectado:**
   - Fallback para o **DeepSeek v4 Flash** ou **GLM 5.3 Flash** na nuvem Free Tier.
3. **Se o OpenRouter atingir Cota Momentânea ou Rate-Limit na versão `:free` (HTTP 429/402):**
   - O orquestrador aciona imediatamente o fallback para a **API Key com os créditos disponíveis** na conta OpenRouter (~$3.05 de saldo verificado), migrando dinamicamente do sufixo `:free` para o endpoint padrão do modelo (ex: `z-ai/glm-5.3-flash`, `xiaomi/mimo-v2.6-flash`, etc.).
   - Se o modelo específico não estiver disponível ou persistir o limite, realiza fallback para os modelos mais velozes e econômicos (`deepseek/deepseek-v4-flash-0731`) ou para os nós locais da rede (PC Zorin GPU/CPU e Notebook TUF 16), garantindo **zero interrupção** do fluxo de desenvolvimento.

---
*Este documento deve ser consultado a cada nova atribuição de tarefas pelo orquestrador e guardado como referência permanente.*
