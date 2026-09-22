Construir um sistema do nível e do porte do e-SUS (um Prontuário Eletrônico do Cidadão - PEC, com módulos para médicos, enfermeiros, dentistas e agentes comunitários) é um dos desafios de engenharia de software mais complexos que existem. Você não está apenas construindo um app; está construindo um ecossistema de saúde crítico.

Para tirar isso do papel, você precisa atuar em quatro frentes simultâneas: Arquitetura de Software, Interoperabilidade (SUS/RNDS), Compliance/Segurança e Regras de Negócio.

Aqui está o guia definitivo de um Arquiteto de Software para construir um "e-SUS Killer" (ou um concorrente/complemento de mercado):


### 1. A Arquitetura: O Desafio do "Offline-First"

O maior diferencial do e-SUS (especialmente o módulo CDS para Agentes Comunitários e áreas rurais) é que ele funciona sem internet e sincroniza depois. Se o seu sistema cair quando o link da UBS (Unidade Básica de Saúde) falhar, os profissionais não vão usar.

- Padrão de Sincronização: Você precisará de uma arquitetura Offline-First.No Cliente (Browser/Tablet): Use bancos locais robustos como WatermelonDB, PouchDB ou SQLite (via WASM).No Servidor: PostgreSQL é o padrão ouro para saúde (relacional, íntegro).A Cola (Sync): Crie um motor de sincronização baseado em CRDTs (Conflict-Free Replicated Data Types) ou Event Sourcing (usando Kafka ou RabbitMQ). Quando o agente volta com internet, o sistema envia os "eventos" (ex: AtendimentoCriado, VacinaAplicada) e o servidor resolve conflitos.
- No Cliente (Browser/Tablet): Use bancos locais robustos como WatermelonDB, PouchDB ou SQLite (via WASM).
- No Servidor: PostgreSQL é o padrão ouro para saúde (relacional, íntegro).
- A Cola (Sync): Crie um motor de sincronização baseado em CRDTs (Conflict-Free Replicated Data Types) ou Event Sourcing (usando Kafka ou RabbitMQ). Quando o agente volta com internet, o sistema envia os "eventos" (ex: AtendimentoCriado, VacinaAplicada) e o servidor resolve conflitos.
- Frontend: React.js ou Vue.js para a web (UBS), e Flutter ou React Native para o app mobile dos Agentes Comunitários de Saúde (ACS).


### 2. O Coração Clínico: Modelagem de Dados e FHIR

Não tente inventar a roda para a estrutura de dados clínicos. O Brasil e o mundo usam o padrão HL7 FHIR.

- Motor FHIR: Implemente um servidor FHIR na sua stack. A referência mundial é o HAPI FHIR (escrito em Java). Ele já vem com validadores de schemas, perfis e APIs prontas.
- Mapeamento Interno: Seu banco de dados interno (PostgreSQL) deve armazenar os dados de forma normalizada, mas a camada de API deve expor e consumir tudo em formato FHIR (JSON).
- Vocabulários Padrão: Seu sistema precisa integrar e validar:CID-10 / CID-11 (Doenças)CIAP-2 (Classificação Internacional de Atenção Primária - obrigatório no SUS)TUSS (Terminologia Unificada em Saúde Suplementar - para procedimentos)RNBMM (Medicamentos) e RBL (Laboratoriais).
- CID-10 / CID-11 (Doenças)
- CIAP-2 (Classificação Internacional de Atenção Primária - obrigatório no SUS)
- TUSS (Terminologia Unificada em Saúde Suplementar - para procedimentos)
- RNBMM (Medicamentos) e RBL (Laboratoriais).


### 3. Os Módulos Essenciais (O que você precisa programar)

Para ser "igual ao e-SUS", seu sistema precisa ter, no mínimo, estes módulos:

- Cadastro Territorial (Ficha A): Mapeamento de microáreas, ruas, famílias e riscos sanitários (dengue, esgoto, etc.).
- Agendamento Inteligente: Regras complexas (ex: "enfermeiro pode agendar 40 pacientes de 15min, médico 20 de 30min", encaixes, bloqueios por agenda de vacinação).
- Atendimento Clínico (SOAP): Evolução em formato Subjetivo, Objetivo, Avaliação e Plano.
- Prescrição e Solicitações: Geração de receitas e pedidos de exame.
- Sala de Vacina: Controle de lote, validade, temperatura da geladeira (cadeia de frio) e esquema vacinal.
- Relatórios e Gerenciamento: Geração de arquivos para o SISAB (para a prefeitura receber o repasse financeiro do Ministério da Saúde).


### 4. Segurança, Assinatura Digital e LGPD

Dados de saúde são dados sensíveis sob a LGPD. A multa por um vazamento pode falir a empresa.

- Assinatura Digital (ICP-Brasil): Toda prescrição e atestado precisa ser assinado digitalmente. Integre provedores de assinatura (como Certisign, Soluti, ou a própria API do ITI - Instituto Nacional de Tecnologia da Informação) usando OAuth2 + ICP-Brasil.
- Trilha de Auditoria Imutável: Cada clique, visualização, alteração ou exclusão deve ser logada com: Quem, Quando, O quê, IP e Assinatura Digital do log. Use tabelas "append-only" no banco de dados.
- Controle de Acesso (RBAC): Médico não vê o que o recepcionista vê. Enfermeiro tem permissões diferentes do dentista.
- Criptografia: Dados em repouso (AES-256) e em trânsito (TLS 1.3).


### 5. Interoperabilidade: Conectando ao Governo (RNDS e BPS)

Se você quer que seu sistema seja adotado por prefeituras, ele precisa "conversar" com o SUS.

- Cadastre-se no BPS (Barramento de Prestadores de Saúde): Sua empresa (CNPJ) precisa se credenciar no Ministério da Saúde para obter as credenciais de acesso.
- Envio para o Conecte SUS: Toda vez que um médico der um diagnóstico, prescrever um remédio ou aplicar uma vacina no seu sistema, você deve enviar um Bundle FHIR para a API da RNDS. Assim, o paciente verá o atendimento no app "Conecte SUS" do governo.
- Exportação para o SISAB: Seu sistema deve gerar os XMLs diários/mensais com as produções (BPA, Atendimento Individual) para que a prefeitura possa validar as metas e receber verbas.


### 6. Compliance e Certificação (A Barreira de Entrada)

Você não pode simplesmente vender um software de saúde. Para que as prefeituras ou clínicas comprem seu sistema e ele seja válido legalmente:

- Certificação SBIS: Seu sistema precisa ser certificado pela Sociedade Brasileira de Informática em Saúde (SBIS). Eles testam se o seu PEP atende aos requisitos mínimos de segurança, usabilidade e funcionalidade clínica.
- Termo de Uso do BPS: Você deve assinar termos de responsabilidade com o DATASUS para usar as APIs públicas.


### 🚀 Plano de Ação: Como começar amanhã?

Não tente construir o e-SUS inteiro de uma vez. Siga esta estratégia de MVP (Produto Viável Mínimo):

Fase 1: O Núcleo (Meses 1-3)

- Configure o HAPI FHIR (Java) como seu motor de dados clínicos.
- Crie o módulo de Cadastro de Pacientes e Agendamento básico.
- Implemente a autenticação com Login.gov.br (Gov.br) para facilitar o acesso dos profissionais.

Fase 2: O Atendimento (Meses 4-6)

- Construa a tela de Atendimento Clínico (Evolução, CID-10, CIAP-2).
- Implemente a Assinatura Digital (ICP-Brasil) nas prescrições.
- Crie a trilha de auditoria imutável.

Fase 3: A Integração (Meses 7-9)

- Consiga o acesso ao ambiente de Homologação da RNDS/BPS.
- Faça seu sistema enviar um "Atendimento" e uma "Vacina" para o Conecte SUS via FHIR.
- Gere os arquivos XML para o SISAB.

Fase 4: O Diferencial (Meses 10+)

- Implemente o Offline-First para os Agentes Comunitários.
- Adicione IA para sugestão de CIDs baseada no texto livre do médico.
- Crie dashboards gerenciais para os Secretários de Saúde (Baseado em FHIR Analytics).


### 💡 Dica de Ouro do Mercado

O e-SUS AB (o sistema gratuito do governo) é bom, mas é pesado, tem uma UX (experiência do usuário) datada e sofre com lentidão. A grande oportunidade de mercado não é fazer um sistema "igual", mas sim fazer um sistema que faça TUDO o que o e-SUS faz, mas que seja 10x mais rápido, com uma interface moderna (estilo iClinic/Doctoralia) e que funcione perfeitamente offline. Se você resolver a dor da UX e da sincronização offline, as prefeituras e clínicas populares migrarão para o seu sistema.

Construir um sistema com funcionalidade equivalente ao e-SUS APS é uma tarefa complexa que envolve múltiplas dimensões: especificação de dados, integração com infraestrutura governamental, conformidade regulatória e capacidade de operação em saúde pública. Com base na documentação técnica oficial disponível, este é um roteiro estruturado para desenvolvedores que desejam seguir esse caminho.


### 🏗️ Compreenda a Arquitetura Conceitual do Sistema

Antes de escrever qualquer linha de código, é essencial entender o modelo de dados e o fluxo de informações que o e-SUS APS exige. A estratégia define dois sistemas centrais: o Prontuário Eletrônico do Cidadão (PEC), para informatização das unidades de saúde, e o Coleta de Dados Simplificada (CDS), como sistema de contingência . Um sistema equivalente precisa espelhar essa lógica de registro individualizado (por CPF ou CNS), integração via RNDS e gestão do cuidado.


### 📚 Domine as Especificações Técnicas da LEDI APS

A documentação mais crítica para quem vai construir um sistema é o Layout e-SUS APS de Dados e Interface (LEDI APS) . Esse é o contrato de dados que define todos os campos, tipos, regras de validação e formatos de envio. Você precisará implementar:

- Estrutura de Fichas: Cadastro Individual, Atendimento Individual, Visita Domiciliar, Atividade Coletiva, entre outras .
- Formatos de Serialização: O LEDI APS pode ser implementado usando XML ou Apache Thrift, de forma independente de linguagem de programação . Escolha o formato e crie a camada de serialização/desserialização.
- Regras de Validação: Horários em epoch time, validação de CNS, limites de tamanho de campos, obrigatoriedade condicional . Essas regras precisam ser codificadas no seu sistema para garantir que os dados sejam aceitos.


### 🔌 Implemente a API de Transmissão LEDI

Para um sistema que precisa se comunicar com instalações do PEC, você deve implementar o cliente da API de Transmissão. A documentação do Ministério da Saúde descreve os dois endpoints essenciais :

- POST /api/recebimento/login: Autenticação com usuário/senha gerados pelo administrador da instalação. Retorna um cookie JSESSIONID que deve ser enviado nas requisições seguintes .
- POST /api/v1/recebimento/ficha: Envio da ficha serializada em binário. O nome do arquivo deve seguir o padrão {uuid da ficha}.esus .

Sua aplicação precisará gerenciar o fluxo de autenticação, serializar a ficha no formato LEDI e tratar os erros retornados pela API (armazenando-os para correção posterior) .


### 🔗 Desenvolva Integrações para Sistemas Externos (Embedded)

Se o seu sistema também precisar ser embutido dentro do PEC como um módulo complementar, você precisará implementar o suporte a Sistemas Externos . Isso envolve:

- Iframes com Parâmetros Dinâmicos: O PEC passa parâmetros como documento-profissional, documento-cidadao, cnes e pec_timestamp na URL .
- Validação de Assinatura HMAC-SHA256: O sistema externo deve validar que a requisição realmente partiu do PEC. A chave secreta é obtida junto ao administrador da instalação. A assinatura é calculada sobre a URL até o parâmetro timestamp (inclusive) . Implemente a verificação de assinatura e a janela de validade do timestamp (ex.: 30 minutos).


### 🗄️ Projete o Armazenamento e o Data Warehouse

Para a geração de relatórios e análise de dados, o e-SUS APS utiliza uma arquitetura de Data Warehouse (DW) com tabelas Fato e Dimensão . O seu sistema precisará de uma estrutura similar para armazenar os dados de forma que permita:

- Extração via SQL: A documentação do DW PEC orienta como consultar tabelas como tb_fat_cad_individual para obter dados de cadastro .
- ETL dos Dados LEDI: O fluxo é: dados chegam via LEDI, são extraídos, transformados e carregados nas tabelas do DW .


### 🧪 Considere Projetos de Referência e Código Aberto

Você não precisa começar do zero absoluto. Existem iniciativas de código aberto que podem servir como base ou referência:

- OpenPEC: Um projeto de software livre que visa implementar uma arquitetura de referência para o PEC, com base nas documentações oficiais. O código está disponível no GitHub .
- Painel e-SUS APS: Desenvolvido pela Fiocruz, é um software livre que se integra ao banco de dados do PEC ou Centralizador. A documentação técnica do código-fonte está disponível .
- Repositórios no GitHub: Existem projetos como o filipedochalopes/e-SUS-PEC que automatizam a instalação do PEC em Docker, úteis para entender o ambiente de execução .


### ⚠️ Requisitos Críticos e Conformidade

Um sistema "igual" ao e-SUS APS precisa atender a exigências que vão além do código:

- Interoperabilidade com a RNDS: O sistema deve ser capaz de enviar dados em saúde para a Rede Nacional de Dados em Saúde usando modelos padronizados .
- Envio para o Siaps/SISAB: Os dados de produção precisam ser transmitidos ao sistema nacional para fins de monitoramento, financiamento e adesão a programas .
- Segurança e LGPD: Informações de saúde são dados sensíveis. O sistema deve garantir criptografia de campos (como nome, email, CNS), controle de acesso e conformidade com a LGPD .


### 💡 Recomendação de Abordagem

O caminho mais viável para um desenvolvedor é começar pela camada de integração:

- Estude a fundo o LEDI APS e implemente a serialização/desserialização nos formatos XML e Thrift.
- Implemente um cliente da API de Transmissão para enviar fichas a uma instalação PEC de teste.
- Crie o modelo de dados do seu sistema espelhando as tabelas Fato e Dimensão do DW PEC.
- Desenvolva a lógica de validação de campos conforme especificado no LEDI.

Construir um PEC completo é um projeto de grande porte, mas focar na interoperabilidade com o ecossistema e-SUS existente é um ponto de partida realista e alinhado às necessidades dos municípios que buscam soluções complementares ou alternativas.

Sim. Se o seu objetivo é criar um sistema semelhante ao e-SUS APS, mas pensado desde o início para ser desenvolvido, mantido e integrado por uma equipe de software, eu não começaria apenas pelo manual de uso. O caminho é montar uma especificação técnica própria, usando o e-SUS como referência funcional e os padrões oficiais do SUS como referência de interoperabilidade.

O Ministério da Saúde mantém atualmente a documentação oficial do e-SUS APS, inclusive com material atualizado em setembro de 2026.


### 1. Onde está a documentação que interessa ao desenvolvedor?

A documentação oficial está espalhada em várias partes:

- Manual oficial do e-SUS APS — documentação geral, atualmente atualizada para as versões recentes.
- Manual do Prontuário Eletrônico e-SUS APS — funcionalidades do PEC.
- Apoio à implantação — arquitetura de instalação, SO, banco, servidores etc.
- Sistemas externos e integração — particularmente importante para entender integração entre sistemas.
- Normativas e portarias — requisitos normativos e integrações com outros sistemas do SUS.

O ponto interessante é que a própria documentação técnica mostra que o e-SUS APS não é simplesmente uma aplicação web: ele contempla instalação local, banco PostgreSQL/Oracle, comunicação com sistemas externos, transmissão de dados e diferentes cenários de infraestrutura.


# 2. Mas você quer fazer "um e-SUS". Como eu faria?

Eu dividiria o projeto em 6 camadas:

┌───────────────────────────┐

│ Aplicação Web │

│ PEC / Profissionais │

└─────────────┬─────────────┘

│

┌─────────────▼─────────────┐

│ API / Backend │

│ REST + autenticação │

│ regras de negócio │

└─────────────┬─────────────┘

│

┌───────────────────┼───────────────────┐

│ │ │

┌──────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐

│ PostgreSQL │ │ Redis/Queue │ │ Object │

│ transacional│ │ eventos │ │ Storage │

└─────────────┘ └─────────────┘ └────────────┘

│

┌─────────────▼─────────────┐

│ Integrações │

│ RNDS / SISAB / CADSUS │

│ outros sistemas │

└───────────────────────────┘

E separaria três coisas que no e-SUS podem aparecer muito misturadas para quem está olhando apenas o manual:


### A. Sistema operacional

O que o profissional usa:

- cadastro do cidadão;
- agenda;
- atendimento;
- consulta;
- procedimentos;
- vacinação;
- acompanhamento;
- prescrição;
- histórico;
- relatórios;
- gestão da unidade.


### B. Modelo de dados

Aqui está uma das partes mais importantes.

Você precisa definir entidades como:

Pessoa

├── Identificação

├── CPF

├── CNS

├── endereço

└── contatos

Paciente

└── Pessoa

Profissional

├── Pessoa

├── CNS

├── CBO

└── equipe

Unidade

├── CNES

├── endereço

└── equipes

Atendimento

├── paciente

├── profissional

├── unidade

├── data/hora

├── motivo

├── avaliação

├── conduta

└── procedimentos

E depois:

Paciente

│

├── Atendimentos

├── Problemas/Condições

├── Medicamentos

├── Alergias

├── Exames

├── Vacinas

├── Encaminhamentos

└── Documentos


### C. Interoperabilidade

Essa parte é fundamental se você pretende fazer algo realmente equivalente ao ecossistema do SUS.

Não faça:

Seu sistema → banco próprio → acabou

Faça:

┌─────────────┐

│ Seu sistema│

└──────┬──────┘

│

API / Eventos

│

┌─────────────┼──────────────┐

▼ ▼ ▼

RNDS SISAB Outros


# 3. A documentação que você realmente precisa produzir

Se eu fosse montar esse projeto com você, criaria um repositório assim:

meu-esus/

│

├── docs/

│ │

│ ├── 01-visao-geral/

│ │ ├── objetivo.md

│ │ ├── escopo.md

│ │ └── arquitetura.md

│ │

│ ├── 02-requisitos/

│ │ ├── funcionais.md

│ │ ├── nao-funcionais.md

│ │ └── regras-negocio.md

│ │

│ ├── 03-dominio/

│ │ ├── pacientes.md

│ │ ├── profissionais.md

│ │ ├── unidades.md

│ │ ├── atendimentos.md

│ │ └── medicamentos.md

│ │

│ ├── 04-modelo-dados/

│ │ ├── modelo-conceitual.md

│ │ ├── modelo-logico.md

│ │ └── dicionario-dados.md

│ │

│ ├── 05-api/

│ │ ├── openapi.yaml

│ │ ├── autenticacao.md

│ │ └── endpoints.md

│ │

│ ├── 06-integracoes/

│ │ ├── rnds.md

│ │ ├── sisab.md

│ │ └── sistemas-externos.md

│ │

│ ├── 07-seguranca/

│ │ ├── autenticacao.md

│ │ ├── autorizacao.md

│ │ ├── auditoria.md

│ │ └── lgpd.md

│ │

│ └── 08-infraestrutura/

│ ├── desenvolvimento.md

│ ├── homologacao.md

│ └── producao.md

│

├── backend/

├── frontend/

├── database/

├── integration/

├── infrastructure/

├── tests/

└── README.md

Isso transforma a ideia de "quero fazer um sistema igual ao e-SUS" em um projeto de engenharia de software executável.


# 4. E tem uma coisa ainda mais importante

Eu não tentaria copiar o e-SUS internamente.

Usaria o e-SUS como referência funcional e de interoperabilidade, mas construiria uma arquitetura moderna.

Por exemplo:


### Backend

Eu consideraria:

Java/Spring Boot

ou

Python/FastAPI


### Banco

PostgreSQL


### Frontend

React + TypeScript


### API

REST

OpenAPI/Swagger

OAuth2/OIDC

JWT


### Infra

Docker

Kubernetes (se realmente necessário)

PostgreSQL

Redis

RabbitMQ/Kafka

Object Storage

E, inicialmente, eu não usaria microserviços.

Começaria com:

FRONTEND

│

▼

┌─────────────┐

│ API Backend │

│ modular │

└──────┬──────┘

│

┌──────▼──────┐

│ PostgreSQL │

└─────────────┘

Um monólito modular provavelmente seria muito mais simples para começar.

Depois:

API

│

┌────────┼────────┐

▼ ▼ ▼

Paciente Atendimento Agenda

│ │ │

└────────┼────────┘

▼

PostgreSQL

E só separar serviços quando existir uma razão técnica.


# 5. Para um sistema de saúde, o banco é particularmente importante

Eu começaria pelo modelo de domínio, antes de programar telas.

Por exemplo:

PESSOA

│

┌─────────────┼─────────────┐

│ │ │

PACIENTE PROFISSIONAL RESPONSÁVEL

│ │

│ ├── CBO

│ └── CNS

│

├── ATENDIMENTO

│ │

│ ├── SOAP

│ ├── diagnóstico

│ ├── procedimento

│ └── prescrição

│

├── MEDICAMENTO

│

├── CONDIÇÃO

│

├── ALERGIA

│

├── EXAME

│

└── VACINAÇÃO

Isso permite posteriormente construir:

┌───────────────┐

│ Prontuário │

└───────┬───────┘

│

┌────────────┼─────────────┐

▼ ▼ ▼

Médico Enfermeiro ACS

│ │ │

└────────────┼─────────────┘

▼

Paciente


# 6. E eu faria uma engenharia reversa documental do e-SUS

Esse é provavelmente o caminho que mais combina com o que você está querendo fazer.

Em vez de simplesmente perguntar:

"Como programo um e-SUS?"

faria:


### Fase 1 — Engenharia de requisitos

Extrair da documentação oficial:

FUNCIONALIDADE

↓

ATO/PROCESSO DE SAÚDE

↓

DADOS NECESSÁRIOS

↓

REGRA DE NEGÓCIO

↓

RESULTADO

↓

INTEGRAÇÃO

Por exemplo:

Consulta médica

↓

Identificação do paciente

↓

Profissional

↓

Unidade

↓

Queixa

↓

Histórico

↓

Exame

↓

Avaliação

↓

Conduta

↓

Prescrição

↓

Registro

↓

Transmissão


### Fase 2 — Modelo de dados

Transformar isso em:

ERD

↓

tabelas

↓

PK/FK

↓

constraints

↓

índices

↓

auditoria


### Fase 3 — API

Transformar em:

POST /patients

GET /patients/{id}

POST /appointments

GET /appointments/{id}

POST /encounters

GET /encounters/{id}

POST /prescriptions

GET /patients/{id}/prescriptions


### Fase 4 — Interface

Somente então:

Login

↓

Unidade

↓

Agenda

↓

Paciente

↓

Atendimento

↓

Prontuário


## 7. Um detalhe muito interessante do e-SUS

A documentação oficial possui inclusive uma seção específica sobre sistemas externos, onde o administrador pode cadastrar um sistema para integração e é gerada uma chave de assinatura para as requisições.

Isso é exatamente o tipo de coisa que você deveria reproduzir conceitualmente no seu projeto:

┌──────────────────────┐

│ Sistema externo │

└──────────┬───────────┘

│

API Key /

OAuth2

│

▼

┌──────────────────────┐

│ API de integração │

├──────────────────────┤

│ autenticação │

│ autorização │

│ rate limit │

│ auditoria │

│ validação │

└──────────┬───────────┘

│

▼

Backend


# 8. Se o seu objetivo é realmente desenvolver isso, eu faria diferente do que você está imaginando

Em vez de começar pelo código, podemos montar um "e-SUS para desenvolvedores".

Eu posso pegar a documentação oficial atual e transformar em uma especificação técnica estruturada:

e-SUS APS

│

├── 1. Arquitetura

├── 2. Módulos

├── 3. Funcionalidades

├── 4. Atores

├── 5. Processos

├── 6. Entidades

├── 7. Modelo de dados

├── 8. Regras de negócio

├── 9. APIs

├── 10. Integrações

├── 11. Segurança

├── 12. Auditoria

├── 13. LGPD

├── 14. Infraestrutura

└── 15. Testes

E o resultado poderia virar um documento ESUS_ANALISE_TECNICA.md, suficientemente detalhado para você entregar a uma LLM e dizer:

"Implemente este sistema seguindo esta especificação."

Isso é muito mais útil para desenvolvimento do que simplesmente baixar o manual do e-SUS.

Se você quiser fazer isso, eu sugiro que o próximo passo seja justamente eu levantar a documentação oficial atual do e-SUS APS e construir a primeira versão desse ESUS_ANALISE_TECNICA.md, separando o que é funcionalidade, modelo de dados, API, integração e infraestrutura.

A documentação oficial do e-SUS APS (especialmente o Prontuário Eletrônico – PEC) voltada para desenvolvedores e programadores está disponível publicamente. O foco principal é a integração de sistemas próprios/terceiros com o e-SUS APS, e não o código-fonte completo do sistema (que não é aberto de forma plena).


### Principais fontes de documentação técnica

- LEDI APS (Layout de Estrutura de Dados e Intercâmbio) – documentação essencial para desenvolvedoresSite oficial: https://integracao.esusab.ufsc.br (ou variantes como integracao.esusaps.bridge.ufsc.tech)Contém o dicionário de dados completo, estrutura dos arquivos, regras de preenchimento, modelos de informação (fichas de cadastro individual, atendimento individual, odontologia, visita domiciliar, vacinação, etc.), camada de transporte, cabeçalhos e compatibilidade de versões entre LEDI e PEC.Link direto para estrutura dos arquivos: https://integracao.esusab.ufsc.br/ledi/documentacao/estrutura_arquivos/index.html (ou versão atualizada equivalente).O LEDI pode ser implementado em Apache Thrift ou XML.
- Site oficial: https://integracao.esusab.ufsc.br (ou variantes como integracao.esusaps.bridge.ufsc.tech)
- Contém o dicionário de dados completo, estrutura dos arquivos, regras de preenchimento, modelos de informação (fichas de cadastro individual, atendimento individual, odontologia, visita domiciliar, vacinação, etc.), camada de transporte, cabeçalhos e compatibilidade de versões entre LEDI e PEC.
- Link direto para estrutura dos arquivos: https://integracao.esusab.ufsc.br/ledi/documentacao/estrutura_arquivos/index.html (ou versão atualizada equivalente).
- O LEDI pode ser implementado em Apache Thrift ou XML.
- Repositório oficial de integração (GitHub)https://github.com/laboratoriobridge/esusab-integracao (ou esusaps-integracao)Contém:Arquivos Thrift para várias linguagens (Java, Python, C#, PHP, Node.js, Go, Delphi, Ruby etc.)Exemplos de código (thrift-exemplo)Schemas XSD para XMLExemplos de arquivos XML válidosEsse é o material mais prático para programadores.
- https://github.com/laboratoriobridge/esusab-integracao (ou esusaps-integracao)
- Contém:Arquivos Thrift para várias linguagens (Java, Python, C#, PHP, Node.js, Go, Delphi, Ruby etc.)Exemplos de código (thrift-exemplo)Schemas XSD para XMLExemplos de arquivos XML válidos
- Arquivos Thrift para várias linguagens (Java, Python, C#, PHP, Node.js, Go, Delphi, Ruby etc.)
- Exemplos de código (thrift-exemplo)
- Schemas XSD para XML
- Exemplos de arquivos XML válidos
- Esse é o material mais prático para programadores.
- Manual oficial e-SUS APS (Ministério da Saúde / SAPS)https://sisaps.saude.gov.br/sistemas/esusaps/docs/manual/Inclui seções de Apoio à Implantação, Transmissão de Dados e API de Transmissão de Registro no Formato LEDI:https://sisaps.saude.gov.br/sistemas/esusaps/docs/manual/APOIO/API_transmissaoA partir da versão 5.3.19 do PEC é possível enviar fichas LEDI via API REST (com autenticação por credenciais geradas no próprio PEC + HTTPS obrigatório).
- https://sisaps.saude.gov.br/sistemas/esusaps/docs/manual/
- Inclui seções de Apoio à Implantação, Transmissão de Dados e API de Transmissão de Registro no Formato LEDI:https://sisaps.saude.gov.br/sistemas/esusaps/docs/manual/APOIO/API_transmissao
- A partir da versão 5.3.19 do PEC é possível enviar fichas LEDI via API REST (com autenticação por credenciais geradas no próprio PEC + HTTPS obrigatório).
- Portal de Serviços do DATASUShttps://servicos-datasus.saude.gov.br/APIs oficiais de integração com outros sistemas do SUS (CADSUS, CNES, RNDS, e-SUS Notifica, e-SUS Regulação, SIGTAP, etc.). Útil se quiser interoperar com a Rede Nacional de Dados em Saúde (RNDS).
- https://servicos-datasus.saude.gov.br/
- APIs oficiais de integração com outros sistemas do SUS (CADSUS, CNES, RNDS, e-SUS Notifica, e-SUS Regulação, SIGTAP, etc.). Útil se quiser interoperar com a Rede Nacional de Dados em Saúde (RNDS).
- Site principal do e-SUS APShttps://sisaps.saude.gov.br/esus/Downloads do sistema, manuais de uso, materiais de apoio e FAQ de integração.
- https://sisaps.saude.gov.br/esus/
- Downloads do sistema, manuais de uso, materiais de apoio e FAQ de integração.
- Suporte oficial para integraçãoPortal de suporte: http://esusaps.bridge.ufsc.br (cadastre-se e abra tickets).
- Portal de suporte: http://esusaps.bridge.ufsc.br (cadastre-se e abra tickets).


### Como fazer um sistema “igual” (ou compatível)

Não existe código-fonte completo aberto do PEC e-SUS APS para copiar literalmente. O caminho correto e oficial é desenvolver um sistema próprio que se integre ao e-SUS APS (enviando dados para o PEC/Centralizador municipal e, indiretamente, para o SISAB/RNDS).

Passos recomendados:

- Estude o LEDI APSBaixe a documentação mais recente e os arquivos Thrift/XSD do GitHub. Entenda cada modelo de informação (fichas) e as regras de validação.
- Escolha a tecnologia de integraçãoThrift (recomendado para performance e tipagem forte) – use as libs oficiais.XML (mais simples de validar com XSD).API REST (a partir da v5.3.19): autentique com usuário/senha gerados no PEC e envie arquivos .esus serializados.
- Thrift (recomendado para performance e tipagem forte) – use as libs oficiais.
- XML (mais simples de validar com XSD).
- API REST (a partir da v5.3.19): autentique com usuário/senha gerados no PEC e envie arquivos .esus serializados.
- Implemente a serialização das fichasUse os exemplos do repositório GitHub. Cada ficha precisa de UUID válido, cabeçalho correto e dados conforme o dicionário LEDI da versão compatível com o PEC instalado no município.
- Teste em ambiente de treinamentoO e-SUS APS oferece instalação de treinamento (dados não vão para o Ministério da Saúde). Baixe no site oficial e configure HTTPS + credenciais de API.
- Integre com outros sistemas do SUSCadastro de cidadãos → API CADSUSEstabelecimentos → CNESProcedimentos → SIGTAPDados clínicos/vacinação → RNDS
- Cadastro de cidadãos → API CADSUS
- Estabelecimentos → CNES
- Procedimentos → SIGTAP
- Dados clínicos/vacinação → RNDS
- Aspectos legais e de conformidadeSiga as portarias do Ministério da Saúde sobre interoperabilidade e padrões (ex.: Portaria GM/MS 2.073/2011 e atualizações).Respeite a LGPD (dados sensíveis de saúde).Para uso em produção em municípios, o sistema precisa ser homologado/aceito pela gestão local e alimentar corretamente o SISAB.
- Siga as portarias do Ministério da Saúde sobre interoperabilidade e padrões (ex.: Portaria GM/MS 2.073/2011 e atualizações).
- Respeite a LGPD (dados sensíveis de saúde).
- Para uso em produção em municípios, o sistema precisa ser homologado/aceito pela gestão local e alimentar corretamente o SISAB.
- Recursos adicionais úteisPainel e-SUS APS (Fiocruz + SAPS) tem código aberto em parte: https://github.com/CampusVirtualFiocruz/painel-esusComunidades e repositórios de terceiros no GitHub (busque “e-SUS” ou “esus-aps”) – use com cautela e valide contra a documentação oficial.
- Painel e-SUS APS (Fiocruz + SAPS) tem código aberto em parte: https://github.com/CampusVirtualFiocruz/painel-esus
- Comunidades e repositórios de terceiros no GitHub (busque “e-SUS” ou “esus-aps”) – use com cautela e valide contra a documentação oficial.


### Resumo prático para começar agora

| Recurso | Link principal | Uso |
| LEDI + dicionário | integracao.esusab.ufsc.br | Regras de dados e estrutura |
| Código + exemplos | github.com/laboratoriobridge/esusab-integracao | Thrift/XML pronto |
| Manual + API | sisaps.saude.gov.br/sistemas/esusaps/docs/manual | Uso e transmissão via API |
| Downloads e FAQ | sisaps.saude.gov.br/esus | Sistema e materiais |

Se precisar de ajuda com alguma parte específica (ex.: como serializar uma ficha de atendimento individual em Python/Java, endpoints da API, ou integração com RNDS), detalhe a linguagem e o módulo que você quer implementar que eu oriento com mais precisão.
