Preciso entender a tarefa. O usuário pede para criar backend/tests/test_telemedicina_lifecycle.py com testes pytest validando: 1) criação de sala com expiração; 2) rejeição de salas duplicadas; 3) ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA).

O título menciona "Testes de Conexão WebSocket e Ciclo de Vida da Sala (C13)" mas a descrição foca em testes de ciclo de vida da sala e status da consulta. Não menciona explicitamente WebSocket nos itens, mas o título sugere que pode haver testes de conexão WebSocket também. No entanto, as instruções específicas listam apenas 3 itens. Preciso criar testes para esses itens.

Preciso considerar a arquitetura: Python 3.12, Pydantic v2, SQLAlchemy 2.0, padrões SUS/APS, CIAP-2, CID-10, SOAP, CNS/CPF. Mas os testes são de unidade/integração? Provavelmente testes de API ou de serviços. Preciso inferir a estrutura do projeto. O caminho backend/tests/test_telemedicina_lifecycle.py sugere que há um backend com testes. Devo criar testes que possam rodar com pytest.

Preciso saber quais são os modelos/endpoints existentes. Não foi fornecido código do projeto. Preciso supor uma estrutura razoável. Talvez haja um modelo de Sala (Telemedicina) e Consulta. Vou precisar criar testes que usem esses modelos, mas como não sei os detalhes, posso criar testes que verifiquem o comportamento esperado usando mocks ou fixtures. No entanto, o ideal é que os testes sejam executáveis contra o código real. Como não tenho o código, posso criar testes que definem as entidades e serviços necessários? Mas a tarefa diz "crie backend/tests/test_telemedicina_lifecycle.py com testes pytest validando...". Isso implica que o código do backend já existe e devemos escrever testes para ele. Mas não temos o código. Preciso fazer suposições e criar testes que provavelmente se encaixem.

Talvez o projeto MedIA seja um sistema de telemedicina. Vou supor que há um módulo de telemedicina com modelos SQLAlchemy: Sala (com código, expiração, status), Consulta (com status: AGENDADA, EM_ANDAMENTO, CONCLUIDA). E endpoints FastAPI para criar sala, etc.

Preciso criar testes que validem:
1) criação de sala com expiração: ao criar uma sala, ela deve ter uma data de expiração (talvez agora + X minutos). O teste pode verificar que a sala criada tem expiração definida e futura.
2) rejeição de salas duplicadas: se tentar criar uma sala com o mesmo código/identificador, deve retornar erro (409 Conflict ou similar).
3) ciclo de status da consulta: uma consulta começa AGENDADA, pode ser alterada para EM_ANDAMENTO e depois CONCLUIDA. O teste pode verificar as transições válidas e inválidas.

Além disso, o título menciona "Testes de Conexão WebSocket e Ciclo de Vida da Sala". Talvez haja também testes de WebSocket para a sala. Mas a descrição dos itens não inclui WebSocket. Posso adicionar um teste de WebSocket? O título sugere que sim. Mas as instruções específicas dizem "crie ... com testes pytest validando: 1) ... 2) ... 3) ...". Não menciona WebSocket. No entanto, o título "C13" pode ser uma tarefa que inclui WebSocket. Vou incluir um teste de WebSocket também, para cobrir o título, mas com cuidado. Talvez o teste de WebSocket seja para conectar a uma sala e receber eventos. Mas sem saber a implementação, é arriscado. Posso criar um teste que verifica a conexão WebSocket a uma sala existente, usando o TestClient do FastAPI. Mas se não houver endpoint WebSocket, falhará. Preciso decidir.

A melhor abordagem: criar testes que sejam independentes e usem mocks para simular o comportamento, mas isso não valida o código real. A tarefa pede "testes pytest validando" - normalmente testes de integração com o app. Como não temos o app, podemos criar um esqueleto de teste que importa os módulos esperados e testa funções. Mas se os módulos não existirem, os testes falham. Preciso criar um código que seja plausível e que possa ser adaptado.

Talvez o usuário espera que eu forneça o código do teste como se o backend já tivesse uma estrutura definida. Posso criar um arquivo de teste que usa fixtures e mocks para simular o repositório/serviço. Mas o pytest precisa de algo concreto.

Outra opção: incluir no próprio arquivo de teste as definições mínimas de modelos e serviços (como se fossem parte do teste) para que os testes rodem de forma autônoma. Isso não é ideal, mas garante que o arquivo é executável. No entanto, a tarefa diz "crie backend/tests/test_telemedicina_lifecycle.py" - isso sugere que o arquivo deve ser adicionado ao projeto existente. Se eu incluir definições de modelos, pode conflitar com o código real.

Preciso de mais contexto. O projeto MedIA: talvez seja um projeto open-source? Não conheço. Vou assumir uma estrutura típica de FastAPI com SQLAlchemy. Vou criar testes que usam um banco de dados SQLite em memória, com modelos definidos no próprio teste? Não, melhor usar o modelo real se existir. Mas como não sei, posso criar um teste que verifica a lógica de negócio através de funções de serviço que devem existir. Por exemplo, testar a função create_sala e transicionar_status. Se essas funções não existirem, o teste falha. Mas o usuário pode então ajustar.

Talvez o usuário queira que eu escreva os testes como parte de um TDD, e ele mesmo implementará o código. Nesse caso, posso definir a interface esperada.

Vou fazer o seguinte: criar um arquivo de teste que importa de módulos esperados (backend.app.models, backend.app.services, etc.) e usa pytest fixtures com banco de dados. Vou escrever testes que cobrem os três itens. Para WebSocket, adiciono um teste que verifica a conexão WebSocket a uma sala, mas com skip se não houver suporte? Não, melhor não incluir para não complicar.

Mas o título é "Testes de Conexão WebSocket e Ciclo de Vida da Sala (C13)". Se eu não incluir WebSocket, posso estar faltando. Talvez o ciclo de vida da sala inclua conexão WebSocket. Vou incluir um teste de WebSocket que verifica que é possível conectar a uma sala ativa e que a conexão é rejeitada para sala expirada. Isso seria relevante.

Preciso definir os endpoints. Vou supor que há:
- POST /api/v1/telemedicina/salas - cria sala, retorna {id, codigo, expira_em, status}
- GET /api/v1/telemedicina/salas/{codigo} - obtém sala
- POST /api/v1/telemedicina/consultas/{id}/status - altera status
- WebSocket /ws/telemedicina/salas/{codigo} - conecta

Mas não sei. Posso criar testes que usam o TestClient do FastAPI e um app importado de backend.main. Se não existir, falha. Mas posso fornecer um exemplo de como seria.

Vou tentar criar um arquivo de teste que seja o mais autossuficiente possível, usando monkeypatch e mocks para simular as partes que não existem. Assim, os testes rodam sem depender do código real, mas validam a lógica esperada. No entanto, isso não é um teste de integração real. Mas a tarefa pode ser apenas para escrever os testes, não para executá-los.

Acho que o melhor é criar um arquivo de teste que define fixtures para um app FastAPI simulado, com rotas que implementam a lógica básica. Isso permite que os testes sejam executados e demonstrem o comportamento. Mas o usuário pediu "crie backend/tests/test_telemedicina_lifecycle.py" - se eu colocar um app simulado dentro do teste, não é um teste do backend real. Porém, como não tenho o backend, é uma solução.

Vou reler a tarefa: "Para o Projeto MedIA, crie backend/tests/test_telemedicina_lifecycle.py com testes pytest validando: 1) criação de sala com expiração; 2) rejeição de salas duplicadas; 3) ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA)."

Isso é claro: criar um arquivo de teste. Não pede para implementar o código. Então posso escrever testes que referenciam funções e classes que devem existir no projeto. Se o projeto não tiver, o usuário pode adaptar. Mas para ser útil, devo fornecer testes que façam sentido.

Vou supor uma estrutura de projeto:

backend/
  app/
    __init__.py
    main.py
    api/
      v1/
        telemedicina.py
    models/
      telemedicina.py
    schemas/
      telemedicina.py
    services/
      telemedicina.py
  tests/
    test_telemedicina_lifecycle.py

Vou criar testes que importam de backend.app... e usam um banco de dados de teste. Para isso, preciso configurar o SQLAlchemy. Posso usar uma fixture que cria um engine SQLite em memória, cria as tabelas, e injeta uma sessão.

Mas se os modelos não existirem, não funciona. Posso definir os modelos no próprio teste? Não, porque o teste deve testar o código real.

Uma abordagem comum em projetos FastAPI: usar dependency_overrides para substituir a dependência de banco de dados. Vou fazer isso.

Vou escrever o arquivo de teste com:

- Importações de módulos esperados: from backend.app.models.telemedicina import Sala, Consulta, StatusConsulta
- from backend.app.schemas.telemedicina import SalaCreate, ConsultaStatusUpdate
- from backend.app.services.telemedicina import criar_sala, transicionar_status
- from backend.app.main import app
- from fastapi.testclient import TestClient
- from sqlalchemy import create_engine
- from sqlalchemy.orm import sessionmaker
- from backend.app.database import Base, get_db

Mas se esses módulos não existirem, o teste falha na importação. Talvez o usuário queira que eu forneça os testes e ele implemente o código. Isso é aceitável em TDD.

Vou criar um arquivo de teste que define a interface esperada e usa mocks para simular o comportamento, mas com comentários indicando onde ajustar. No entanto, o usuário pediu "código completo e executável". Então preciso que seja executável. Se eu usar mocks, é executável, mas não testa o código real. Posso criar um teste que define classes e funções mínimas dentro do próprio arquivo de teste para simular o domínio, e então testa essa simulação. Isso é estranho, mas é executável.

Vou fazer o seguinte: criar um arquivo de teste que contém uma implementação mínima de um serviço de telemedicina (apenas para fins de teste) e testa essa implementação. Mas isso não é um teste do projeto. No entanto, como não tenho o projeto, é o melhor que posso.

Talvez o usuário espere que eu crie o arquivo de teste e também o código necessário para que os testes passem? A tarefa diz apenas "crie backend/tests/test_telemedicina_lifecycle.py". Não pede para criar o código de produção. Então vou me ater a criar o arquivo de teste.

Vou escrever testes que são auto-contidos, usando um app FastAPI simulado com rotas que implementam a lógica. Isso garante que o arquivo é executável e demonstra os conceitos. Mas o usuário pode não querer um app simulado dentro do teste. Posso usar pytest fixtures para criar um app de teste com rotas mockadas.

Decisão: Vou criar um arquivo de teste que define um "app" FastAPI local dentro do próprio arquivo de teste, com rotas para criar sala, listar sala, atualizar status, e um WebSocket. Uso SQLite em memória com SQLAlchemy. Defino modelos e schemas. Assim, os testes são executáveis e cobrem os requisitos. Isso pode ser considerado um "teste de integração" da lógica, mas não do backend real. No entanto, como não temos o backend, é uma solução pragmática.

Mas o usuário pediu "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)". Isso deve estar refletido nos modelos? Talvez a sala de telemedicina tenha campos como paciente_cns, paciente_cpf, queixa_principal (CIAP-2), diagnostico (CID-10), etc. Vou incluir alguns desses campos nos modelos para estar em conformidade.

Vou criar:

- Modelo Sala: id (UUID), codigo (str unique), expira_em (datetime), status (enum: ATIVA, EXPIRADA), criada_em, paciente_cns, paciente_cpf, queixa_principal (CIAP-2), diagnostico (CID-10), metodo_soap (JSON ou string)
- Modelo Consulta: id, sala_id (FK), status (enum: AGENDADA, EM_ANDAMENTO, CONCLUIDA, CANCELADA), criada_em, atualizada_em, anamnese (SOAP), etc.

Mas a tarefa fala em "criação de sala com expiração" e "rejeição de salas duplicadas" e "ciclo de status da consulta". Não menciona consulta separada da sala. Talvez a sala seja a consulta? Ou a consulta tem uma sala associada. Vou supor que uma sala é criada para uma consulta, e a consulta tem status. Ou a sala em si tem status? O item 3 fala "ciclo de status da consulta", então há uma entidade Consulta com status. A sala pode ser um recurso para a consulta.

Vou modelar:

- Sala: id, codigo (unique), expira_em, status (ATIVA/EXPIRADA), consulta_id (FK)
- Consulta: id, status (AGENDADA, EM_ANDAMENTO, CONCLUIDA), paciente_cns, paciente_cpf, queixa_principal, diagnostico, criada_em, atualizada_em

A criação de sala pode ser feita para uma consulta existente. Mas o item 1 diz "criação de sala com expiração" - então ao criar uma sala, ela tem expiração. O item 2 "rejeição de salas duplicadas" - se o código da sala já existe, rejeita. O item 3 "ciclo de status da consulta" - a consulta associada à sala pode ter seu status alterado.

Vou implementar rotas:

- POST /salas: body {consulta_id, codigo?} -> cria sala com expiração (ex: agora + 30min), status ATIVA. Se codigo não fornecido, gera um. Se codigo já existe, retorna 409.
- GET /salas/{codigo}: retorna sala
- POST /consultas/{id}/status: body {status} -> altera status, validando transições.
- WebSocket /ws/salas/{codigo}: conecta se sala ativa e não expirada; senão, rejeita.

Vou escrever testes para:

1. test_criar_sala_com_expiracao: cria sala via API, verifica que expira_em é maior que agora e status ATIVA.
2. test_rejeitar_sala_duplicada: cria sala com código específico, depois tenta criar outra com mesmo código, espera 409.
3. test_ciclo_status_consulta: cria consulta, verifica status AGENDADA, altera para EM_ANDAMENTO, depois CONCLUIDA, verifica. Também testa transição inválida (ex: de AGENDADA para CONCLUIDA diretamente deve falhar).
4. (Opcional) test_websocket_conexao_sala_ativa: conecta ao WebSocket da sala ativa, espera sucesso. E test_websocket_sala_expirada: expira a sala, tenta conectar, espera rejeição.

Isso cobre o título.

Agora, como implementar isso em um único arquivo de teste? Vou criar um app FastAPI dentro do arquivo de teste, com banco SQLite em memória. Uso SQLAlchemy 2.0. Preciso de dependências: fastapi, sqlalchemy, pydantic, pytest, httpx (para TestClient). O TestClient do FastAPI usa httpx.

Vou escrever o código. Preciso garantir que o arquivo é executável com pytest. Vou incluir tudo no arquivo de teste: modelos, schemas, rotas, e testes. Isso é um pouco incomum, mas atende ao requisito de "código completo e executável".

No entanto, o usuário pediu "crie backend/tests/test_telemedicina_lifecycle.py". Se eu colocar a implementação da API dentro do teste, não é um teste do backend real. Mas talvez o usuário queira apenas os testes