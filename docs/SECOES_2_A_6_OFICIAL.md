## 2. O QUE ESSENCIAL E DE ALTO IMPACTO (DETALHAMENTO CLÍNICO)

### 2.1 Tabela de Funcionalidades Essenciais (Fase 1)

| # | Funcionalidade | Especificação Técnica/Regulatória | Impacto na Prática Clínica da APS |
|---|----------------|-----------------------------------|----------------------------------|
| 1 | **Receituário Digital ICP-Brasil** | Conforme Resolução CFM nº 2.314/2022 e Lei nº 14.510/2022; assinatura digital com certificado ICP-Brasil A1 (nuvem) ou A3 (token); QR Code para autenticação pelo paciente no farmacêutico | Elimina receitas manuscritas ilegíveis; reduz prescrições falsificadas; permite rastreabilidade completa da dispensação; agiliza o atendimento na APS |
| 2 | **Atestado Digital** | Mesma infraestrutura de assinatura ICP-Brasil; PDF com carimbo digital e código de verificação; conforme Código Penal art. 299 e padronização CFM | Reduz burocracia na secretaria da unidade; gera relatório automatizado de atestados; facilita o controle de afastamentos e prontidão do plantão |
| 3 | **Pedidos de Exame via SIGTAP** | Integração com Sistema de Gerenciamento da Tabela de Procedimentos, Materiais e Glosas (SIGTAP); CID-10 obrigatório para elegibilidade; geração de guia com carimbo CNES | Padroniza solicitações conforme rede SUS; evita repasse de guias físicas; reduz trocas internas (TISS) e desconsideração de exames por falha de encaminhamento |
| 4 | **Prontuário SOAP com CIAP-2 e CID-10** | Estrutura: Subjetivo / Objetivo / Avaliação / Plano; Classificação Internacional de Atenção Primária (CIAP-2) vinculada a SIA/SUS; CID-10 preenchível com busca hierárquica; retrocompatibilidade com DatSus | Base para indicadores epidemiológicos da APS; alimenta o Sistema de Informação em Saúde sem retrabalho; facilita pesquisa assistencial e gestão de metas por região de saúde |
| 5 | **RENAME e Farmácia Popular com alertas** | Base atualizada do Relação Nacional de Medicamentos Essenciais (RENAME 2023) e do Programa Farmácia Popular; alerta automático de substituição genérica; compatibilidade de dose, via e indicação | Garante prescrição com medicamento disponível na rede SUS; evita desperdício com medicamento não coberto; reduz busca do paciente por alternativas inadequadas |
| 6 | **Alertas de Interações Farmacológicas Graves** | Base de dados validada (Micromedex, Lexicomp ou equivalentes com licença); algoritmo de classificação por severidade (contraindicação, grave, moderada, leve); alertas em tempo real na tela de prescrição | Detecta combinações de risco letal (ex.: inhibidores de CYP3A4 + estatinas); alerta para tríplice whammy (IECA + diurético tiazídico + AINE); reduz eventos adversos evitáveis e interrupção desnecessária de medicação |

---

### 2.2 Telemedicina em Conectividade Crítica (Montes Claros e Jequitinhonha)

- **Degradação dinâmica WebRTC:**
  - **Vídeo HD (720p/1080p)** → Conexão estável, Wi-Fi ou fibra, distância com impacto mínimo no diagnóstico visual (exame de feridas, dermatologia, inspeção de lesões).
  - **Vídeo SD (360p/480p)** → Latência moderada, 3G/4G instável; suficiente para consulta de rotina, triagem e avaliação de expressão facial.
  - **Áudio exclusivo (Opus/Opus 16 kHz)** → Sem banda para vídeo; permite consulta integral com o médico ouvindo paciente e interpretando sinais verbais (tosse, dispneia, dor).
  - **Chat síncrono (WebSocket cifrado)** → Conexão mínima ou intermitente; envio de texto com respostas estruturadas, orientações escritas e troca de imagens comprimidas (ex.: lesão, exame laboratorial).
  - **Transição automática e reversível** sem intervenção manual do usuário — a qualidade degrada e sobe conforme a rede oscila.

- **Arquitetura Offline-First (PWA / Cache local seguro de prontuários agendados):**
  - Progressive Web App instalável em dispositivo sem acesso à Play Store/App Store (crítico para clusters rurais de Jequitinhonha).
  - Cache local cifrado (AES-256) dos dados do prontuário do paciente já agendado para o dia — histórico, alergias, medicações em uso, últimos exames.
  - Funcionalidade total de consulta sem conexão — o profissional preenche o prontuário localmente.
  - Dados sincronizados automaticamente com o servidor assim que a conexão retorna, com resolução automática de conflitos (last-write-wins com verificação de versão).

- **Fila assíncrona de prescições e atestados com sincronização automática e assinatura em lote:**
  - Prescrições e atestados gerados offline ficam em fila local com hash SHA-256 e timestamp.
  - Quando a conexão retorna, a fila drena automaticamente e o médico recebe **tela única de revisão em lote** — visualiza todos os documentos gerados offline, confirma assinatura com um clique (ou certificado ICP-Brasil via token).
  - Nenhum documento é transmitido sem revisão explícita do médico.
  - Falha de sincronização gera alerta persistente no painel do médico até resolução.

---

### 2.3 Conformidade Legal e Segurança

- **Resolução CFM nº 2.314/2022 e Lei nº 14.510/2022:**
  - A Lei nº 14.510/2022 **revogou** a Lei nº 14.063/2020 (que autorizava assinatura digital por ICP-Brasil como regra geral para saúde) e **instituiu** a exigência de **assinatura eletrônica qualificada com certificado ICP-Brasil** para todo ato médico e odontológico — prescrição, atestado, encaminhamento, laudo e teleconsulta.
  - O Ling Santé deve permitir **exclusivamente** assinatura qualificada (A1/A3), **não** aceitando assinatura com certificado simples (A2) nem assinatura por senha de plataforma.

- **Certificado ICP-Brasil (A1 em nuvem segura ou A3 token físico):**
  - **A1 em nuvem segura:** gerenciado por autoridade certificadora licenciada (ex.: Certisign, ICp-Brasil AC), armazenado em HSM (Hardware Security Module), válido por 12 meses. Indicado para o médico que assina em múltiplos dispositivos.
  - **A3 token físico:** certificado em smartcard ou token USB, protegido por PIN, válido por 12 meses. Indicado para o médico que prefere controle físico do certificado.
  - O sistema deve exibir o **carimbo do tempo** (RFC 3161) e o **QR Code de verificação** em todo documento gerado, permitindo validação pública por terceiros.

- **LGPD para dados sensíveis em saúde e guarda de prontuário por 20 anos:**
  - Dados de saúde são **dados sensíveis** (art. 5º, II, LGPD): exigem base legal específica (consentimento ou tutela da saúde), criptografia em repouso e em trânsito, controle de acesso granular por perfil (médico, enfermeiro, secretário, administração).
  - **Base legal recomendada:** Art. 11, II, alínea "f" (tutela da saúde em procedimento realizado por profissionais de saúde) — dispensa consentimento explícito para tratamento normal, mas **exige consentimento** para compartilhamento com terceiros não vinculados.
  - **Guarda de prontuário por 20 anos** (art. 11, §4º, Lei nº 8.080/1990, interpretado à luz da Lei nº 13.787/2018): o sistema deve garantir armazenamento com retenção mínima de 20 anos contados da última anotação, com backup redundante e testes de restauração periódicos.
  - **Registro de operações de tratamento** (art. 37, LGPD): log completo de quem acessou, o quê, quando e por quê — auditável por qualquer momento.
  - **Notificação de incidente à ANPD** em prazo máximo de 2 dias úteis (art. 48, LGPD), com comunicação ao titular se houver risco relevante.

---

## 3. O PAPEL DA INTELIGÊNCIA ARTIFICIAL: VALOR REAL VS. RISCO CLÍNICO

### 3.1 Onde a IA é Indispensável (Alto Retorno e Segurança)

- **Ambient Clinical Scribe (escuta silenciosa e transcrição SOAP estruturada em tempo real):**
  - O médico conversa com o paciente — o sistema ouve, transcreve e **estrutura automaticamente** as informações no modelo SOAP (Subjetivo, Objetivo, Avaliação, Plano).
  - Reduz o tempo de digitação do prontuário em **60 a 80%**, liberando o médico para olhar para o paciente, não para a tela.
  - A transcrição é tratada como **rascunho assistivo** — o médico revisa, edita e aprova antes de salvar. Nunca é salvo sem confirmação humana.
  - Valor clínico direto: mais tempo de escuta ativa = mais pacientes atendidos por turno = menos esgotamento do profissional.

- **Checagem ativa de interações medicamentosas graves e alergias cruzadas:**
  - **Tríplice Whammy (tríplice de risco):** IECA + diurético tiazídico + AINE → risco de insuficiência renal aguda e hipercalemia. Alerta automático no momento da prescrição.
  - **Clarithromicina + Sinvastatina:** inibidor potente de CYP3A4 → aumento de até **10 vezes** na concentração plasmática de sinvastatina → miólise grave e rabdomiólise. Alerta de severidade crítica.
  - **IECA + Espironolactona:** hipercalemia combinada que pode ser fatal em paciente com TFG reduzida. Alerta com sugestão de monitoramento de potássio.
  - O alerta **exige resposta explícita** do médico (justificar, substituir ou ignorar com justificativa registrada) — nunca pode ser silenciosamente dispensado.

- **Automação de escores clínicos da APS:**
  - **MEWS (Modified Early Warning Score):** cálculo automático de frequência cardíaca, pressão arterial, frequência respiratória, temperatura e nível de consciência — identifica deterioração precoce e gera alerta de escalonamento.
  - **Naegele / Data Provável do Parto:** calculada a partir da última menstruação ou data da ultrassonografia — com ajuste automático e alerta se os dois métodos divergem em >7 dias.
  - **CKD-EPI 2021:** calcula TFG estimada a partir de creatinina e cistatina C — classifica automaticamente estadiamento da DRC (G1-G5) e notifica se há progressão.
  - **FINDRISC:** escore de risco para diabetes tipo 2 em 10 anos — aplicado automaticamente a pacientes com glicemia de jejum entre 100-125 mg/dL ou com sobrepeso e idade >45.
  - **Framingham:** escore de risco cardiovascular de 10 anos — automatizado com dados já presentes no prontuário (pressão arterial, colesterol, tabagismo, idade, diabetes).
  - Todos os escores são calculados automaticamente quando os dados necessários estão preenchidos, com **menção explícita da fórmula e da referência bibliográfica** exibida ao médico.

- **Rastreio de sinais de alerta e busca ativa de faltosos:**
  - Algoritmo varre a agenda e o prontuário para identificar pacientes com **faltas consecutivas** a consultas crônicas (hipertensão, diabetes, pré-natal, tuberculose).
  - Detecta **sinais de alerta** cruzados: pressão arterial não controlada em 3 consultas seguidas, hemoglobina em queda progressiva, criança sem acompanhamento de crescimento.
  - Gera **lista priorizada de busca ativa** para o agente comunitário de saúde (ACS), com motivo clínico e última visita registrada.
  - Acompanhamento de gravidez de alto risco com alerta se o pré-natal tardio (iniciado após 20 semanas) — gera encaminhamento obrigatório.

---

### 3.2 Onde a IA NÃO Deve Ser Usada (Linhas Vermelhas)

- **Diagnóstico autônomo sem validação do médico soberano:**
  - A IA **não pode** emitir diagnóstico, CID-10 ou CIAP-2 autonomamente.
  - A IA **pode** sugerir diagnósticos diferenciais como auxílio cognitivo, sempre com a frase visível: *"Sugestão assistida por IA — Confirmação médica obrigatória."*
  - O médico é **soberano** no diagnóstico. A IA não substitui o raciocínio clínico, o exame físico nem a anamnese.
  - Qualquer classificação automática de gravidade ou de urgência deve ser **revisada e validada** antes de ser registrada no prontuário.

- **Geração descontrolada de receitas (risco de alucinação posológica):**
  - A IA **não pode** gerar prescrições sem revisão humana.
  - Risco concreto de **alucinação posológica:** modelo de linguagem pode "inventar" dose, via ou frequência plausível tecnicamente mas clinicamente errada (ex.: digoxina em dose 10x superior; metformina por via intravenosa).
  - Prescrições assistidas por IA devem ser sempre **rascunho que passa por revisão integral do médico** — dose, via, frequência, duração, período de tratamento, alertas de interação e contraindicação.
  - **Proibido:** auto-prescrição por IA baseada apenas em diagnóstico (ex.: "paciente com HAS → prescrever losartana 50mg") sem contexto clínico individual.

- **Chatbots de triagem frios e burocráticos para pacientes vulneráveis do SUS:**
  - Muitos pacientes da APS são idosos, com baixa escolaridade, sem familiaridade com tecnologia ou com condições neuropsiquiátricas (ex.: idosos com demência, pacientes com transtorno bipolar em crise).
  - Chatbot de triagem automatizada **sem opção humana imediata** é percebido como abandono — o paciente desiste, não retorna e agravam-se os indicadores.
  - A IA **pode** ser usada como **pré-triagem guiada** (ex.: paciente responde 3-4 perguntas, o sistema sugere a especialidade), **sempre** com botão visível de falar com humano em um clique.
  - **Proibido:** triagem por IA para crianças, idosos com ≥70 anos, pacientes em vigilância de suicídio, pacientes com transtornos cognitivos ou alteração de consciência — esses casos vão **direto** para atendimento humano.

---

## 4. O QUE NÃO É IMPORTANTE / DEVE SER DESCARTADO (DESPERDÍCIO DE ESFORÇO)

- **Módulos hospitalares (escalas de plantonistas, controle de leitos, TISS de planos de saúde):**
  - O Ling Santé é uma ferramenta de **Atenção Primária à Saúde (APS)**. Não é um sistema hospitalar.
  - **Escala de plantonistas** é responsabilidade da gestão hospitalar (RNDS,