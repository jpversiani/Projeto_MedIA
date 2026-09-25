O usuário quer que eu crie um arquivo de testes backend/tests/test_mensageria_preventiva.py para o Projeto MedIA. O foco é testar regras de busca ativa e prevenção de spam clínico. Especificamente: 1) valida filtro de pacientes com consultas de hipertensão vencidas; 2) assegura que lembretes respeitam janela de tolerância de horário; 3) valida idempotência no disparo de notificações.

Preciso entender o contexto do projeto. É um sistema de saúde (APS - Atenção Primária à Saúde), com padrões SUS, CIAP-2, CID-10, SOAP, CNS/CPF. O código deve ser Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0. Vou precisar criar um arquivo de teste que seja executável com pytest.

Como não tenho acesso ao código existente, preciso inferir uma estrutura razoável para o sistema. Vou criar um teste unitário que valide as regras de negócio mencionadas. Para isso, posso criar funções/módulos fictícios que representam a lógica de filtro de pacientes, janela de tolerância e idempotência. O teste deve cobrir esses cenários.

Preciso que o teste seja autocontido, mas seguindo as diretrizes de arquitetura. Talvez o melhor seja criar também alguns módulos auxiliares? O usuário pede apenas o arquivo de teste, mas os testes precisam de implementações para testar. Posso assumir que existem módulos no projeto como backend/app/services/mensageria.py etc. Mas como não sei, posso criar o teste de forma que importe módulos existentes e, se não existirem, o pytest falhará. Melhor abordagem: criar o teste completo com fixtures e testes que referenciam funções do projeto. Para garantir que o arquivo seja executável, posso incluir a definição dessas funções dentro do próprio arquivo de teste? Isso não é ideal, mas o usuário pede "crie backend/tests/test_mensageria_preventiva.py" e "execute com precisão conforme as diretrizes". O teste deve testar regras, mas sem o código real, não há como testar. Então provavelmente o objetivo é que eu forneça o arquivo de teste que será usado em um repositório existente, e as funções importadas são esperadas. Vou assumir uma estrutura plausível:

- backend/app/models/patient.py com model Patient (CNS, CPF, etc)
- backend/app/models/consulta.py com Consulta (data, tipo, etc)
- backend/app/services/busca_ativa.py que contém filtro_pacientes_hipertensao_vencida()
- backend/app/services/lembrete.py com funções de agendamento de lembretes e janela de tolerância.
- backend/app/services/notificacao.py com função disparar_notificacao() e verificação de idempotência.

Como não sei os nomes exatos, posso criar o teste com imports que provavelmente existem, e esperar que o usuário ajuste. Mas a instrução é "Forneça o código completo e executável" – se eu importar módulos inexistentes, não será executável. Então talvez eu deva criar o teste de forma que defina a lógica minimalista para os testes, mas usando Pydantic e SQLAlchemy? O usuário não pediu para criar o código de produção, apenas os testes. Contudo, para que os testes rodem, precisamos do código de produção. A tarefa é "crie backend/tests/test_mensageria_preventiva.py". Em um projeto real, esse arquivo fará parte da suíte de testes. O usuário provavelmente espera que eu escreva os testes com base em uma API conhecida (do próprio projeto) que ele tem. Como não tenho essa informação, uma solução é criar o arquivo de teste com definições locais de funções auxiliares que simulam as regras, e testá-las. Isso garante execução e demonstra as regras. Mas isso não testa o código real. No entanto, é a única forma de fornecer algo executável agora.

Vou seguir uma abordagem pragmática: criar o arquivo de teste com uma pequena implementação (dentro do próprio teste ou em um módulo importável separado) que contenha as regras de negócio, e então testá-las. Para não violar a arquitetura, posso estruturar o código em classes/objetos com Pydantic e SQLAlchemy? Em testes unitários, geralmente usamos fakes. Vou criar funções puras que recebem modelos Pydantic e retornam resultados. Para fins de teste, posso definir modelos Pydantic locais (ex: `Paciente`, `Consulta`, `Notificacao`) que representam as entidades, e services como funções. O teste estará completo e executável, mas não dependerá do código real. No entanto, o nome do arquivo `test_mensageria_preventiva.py` sugere que é para testar um módulo de mensageria. Posso incluir no docstring que as funções testadas devem corresponder às do módulo real.

Vou implementar:

1. `filtrar_pacientes_hipertensao_vencida`:
   - Recebe lista de pacientes com consultas.
   - Hipertensão: CID-10 I10-I15 ou CIAP-2 K86? CIAP-2 para hipertensão é K86. Vou usar CID-10 e CIAP-2.
   - Consulta vencida: data da consulta < hoje, e não há consulta futura agendada? A busca ativa quer pacientes que não retornaram para acompanhamento. Então um paciente é elegível se tiver diagnóstico de hipertensão registrado (em algum campo) e a última consulta de acompanhamento está vencida além de um limite (ex: atraso > 30 dias). Mas a regra exata não foi especificada. Vou criar um cenário simples: pacientes com consulta de hipertensão cuja data é anterior à data atual e não existe consulta futura agendada. Ou então pacientes com "consulta vencida" significa que a consulta agendada passou e não foi realizada? Vou definir: uma consulta é vencida se `data_consulta < hoje` e `status != 'realizada'`? Preciso escolher algo.
   
   A busca ativa geralmente identifica pacientes que precisam de acompanhamento, baseado no último atendimento. Para hipertensão, o Ministério da Saúde recomenda consulta a cada 6 meses. Então poderia ser: pacientes com diagnóstico de hipertensão cuja última consulta de hipertensão ocorreu há mais de 6 meses. Mas a palavra "vencidas" pode se referir a "consultas vencidas" no sentido de expiradas (agendadas e não realizadas). Vou usar interpretação: pacientes com consultas de hipertensão cuja data da próxima consulta (ou última) está vencida. Para simplificar, vou modelar `Consulta` com `data_programada` e `status`; consultas vencidas são aquelas com `data_programada < data_atual` e `status == 'agendada'` (não realizada). O filtro deve retornar pacientes com pelo menos uma consulta de hipertensão vencida.

2. Janela de tolerância de horário:
   - Lembretes devem ser enviados respeitando uma janela de tolerância. Por exemplo, não enviar lembretes fora do horário comercial (8h-18h) ou respeitar um intervalo mínimo entre lembretes.
   - Vou implementar uma função `pode_enviar_lembrete(horario_atual, horario_agendamento, janela_tolerancia)` que verifica se o horário atual está dentro de uma janela em torno do horário de agendamento. Ex: lembrete de consulta às 10h pode ser enviado entre 9h30 e 9h45 (janela de 15-30 min antes). Ou "janela de tolerância de horário" pode significar que, ao disparar lembretes em lote, devemos respeitar uma janela de horário permitida (ex: não enviar antes das 8h ou depois das 20h). Vou escolher uma interpretação: a função `respeita_janela_tolerancia(data_agendada, hora_inicio_janela, hora_fim_janela)` verifica se a data/hora em que o lembrete será enviado está dentro de um intervalo permitido (ex: das 8h às 18h, ou dentro de X horas antes da consulta). Como o teste pede "lembretes respeitam janela de tolerância de horário", posso testar que um lembrete agendado para ser enviado às 7h (fora da janela) é adiado/rejeitado, e um às 9h é aceito.

   Vou definir `proximo_envio_lembrete(horario_atual, horario_consulta, inicio_janela, fim_janela)` que retorna o horário de envio ou None se não for permitido. Mas simplifico: função `esta_dentro_janela(horario_envio, inicio_janela, fim_janela)` que verifica se `inicio_janela <= horario_envio <= fim_janela`. Assim, os testes podem validar casos limite.

3. Idempotência no disparo de notificações:
   - Garantir que a mesma notificação não seja enviada mais de uma vez. Vou implementar um registro de notificações (em memória) e uma função `disparar_notificacao(notificacao, armazenamento)` que retorna False se já foi disparada, e True se foi disparada agora. A idempotência pode ser baseada em uma chave única (ex: ID da consulta + tipo de lembrete + destinatário). Vou testar que chamadas repetidas não enviam duplicatas.

Como o arquivo de teste deve ser completo, vou incluir essas funções auxiliares dentro do próprio arquivo de teste (ou em um conftest?). O ideal é separar, mas para um único arquivo, posso colocar tudo junto. Vou criar a estrutura:

- Modelos Pydantic: `Consulta` com campos `id`, `paciente_cns`, `codigo_ciap`, `codigo_cid`, `data_programada`, `status`.
- Modelo `Paciente` com `cns`, `cpf`, `nome`, `nascimento`, `telefone`, `diagnosticos` (lista de strings).
- Serviço `filtrar_pacientes_hipertensao_vencida(pacientes, consultas, hoje)` que recebe listas e retorna lista de pacientes.
- Serviço `respeita_janela_tolerancia(horario_envio, inicio_janela, fim_janela)`.
- Serviço `disparar_notificacao(notificacao, cache)`.

O teste deve usar pytest e tipagem. Vou escrever com Pydantic v2 (modeos via `BaseModel`). Para SQLAlchemy 2.0, não é necessário no teste unitário, pois não vamos interagir com banco. Mas as diretrizes mencionam SQLAlchemy 2.0 – posso usar `Mapped` se quiser, mas não necessário. Vou focar no código Python.

Além disso, usar `datetime` e `time`.

Vou criar o arquivo com:

```python
# backend/tests/test_mensageria_preventiva.py
"""
Testes para as regras de busca ativa e prevenção de spam clínico (C16).

Valida:
- Filtro de pacientes com consultas de hipertensão vencidas.
- Respeito à janela de tolerância para envio de lembretes.
- Idempotência no disparo de notificações.
...
"""
```

Agora, detalhar cada parte.

### 1. Filtro de pacientes com consultas de hipertensão vencidas

Definição:

```python
def filtrar_pacientes_hipertensao_vencida(pacientes: list[Paciente], consultas: list[Consulta], hoje: date) -> list[Paciente]:
    """
    Retorna pacientes que possuem ao menos uma consulta de hipertensão
    agendada cuja data já passou (status 'agendada' ou 'pendente') e não há
    consulta futura de hipertensão para o mesmo paciente.
    """
    consultas_hipertensao = [
        c for c in consultas
        if c.codigo_cid and c.codigo_cid.startswith("I10") or c.codigo_ciap == "K86"
    ]
    # Correção: precisa agrupar por paciente.
```

Cuidado com a precedência: `c.codigo_cid and c.codigo_cid.startswith("I10") or c.codigo_ciap == "K86"` é aceitável, mas melhor usar parênteses.

Hipertensão: CID-10 I10-I15. Vou verificar se o código CID começa com "I10", "I11", "I12", "I13", "I14", "I15" ou se CIAP-2 é "K86". Para simplificar: `c.codigo_cid and c.codigo_cid.startswith("I1")`? I1 pode incluir outras doenças. Melhor definir conjunto de códigos: `{"I10","I11","I12","I13","I14","I15"}`. Em CIAP-2, K86 é hipertensão não complicada, K87 hipertensão complicada? Segundo CIAP-2, K86 = Hipertensão não complicada, K87 = Hipertensão com complicação. Vou incluir ambos: {"K86", "K87"}.

Então:

```python
CODIGOS_HIPERTENSAO_CID = {"I10", "I11", "I12", "I13", "I14", "I15"}
CODIGOS_HIPERTENSAO_CIAP = {"K86", "K87"}

def _is_hipertensao(consulta):
    return consulta.codigo_cid in CODIGOS_HIPERTENSAO_CID or consulta.codigo_ciap in CODIGOS_HIPERTENSAO_CIAP
```

Consulta vencida: `consulta.data_programada < hoje` e `consulta.status not in {"realizada", "cancelada"}` (i.e., agendada, pendente, etc.). Além disso, para evitar spam, se já existe uma consulta futura para o mesmo paciente e hipertensão, não incluir. Vou implementar isso.

Função:

```python
def filtrar_pacientes_hipertensao_vencida(pacientes, consultas, hoje):
    pacientes_retorno = []
    for paciente in pacientes:
        consultas_paciente_hiper = [c for c in consultas if c.paciente_cns == paciente.cns and _is_hipertensao(c)]
        # Se não houver nenhuma consulta de hipertensão, não incluir.
        if not consultas_paciente_hiper:
            continue
        vencidas = [c for c in consultas_paciente_hiper if c.data_programada < hoje and c.status not in {"realizada", "cancelada"}]
        futuras = [c for c in consultas_paciente_hiper if c.data_programada >= hoje]
        if vencidas and not futuras:
            pacientes_retorno.append(paciente)
    return pacientes_retorno
```

Testes: criar pacientes e consultas, verificar retorno.

### 2. Janela de tolerância de horário

Definir função que valida se um horário de envio está dentro da janela permitida. Por exemplo, lembretes de consultas só podem ser enviados entre 8h e 18h. Ou, mais especificamente, "janela de tolerância de horário" pode ser um intervalo de tempo antes da consulta (ex: até 60 minutos antes, e não antes de 30 minutos). Mas a descrição é vaga. Vou implementar uma função genérica:

```python
def respeita_janela_tolerancia(horario: datetime, inicio_janela: time, fim_janela: time) -> bool:
    """Verifica se o horário está dentro da janela diária permitida."""
    if inicio_janela <= fim_janela:
        return inicio_janela <= horario.time() <= fim_janela
    else:  # janela que atravessa a meia-noite (ex: 22:00 às 06:00)
        return horario.time() >= inicio_janela or horario.time() <= fim_janela
```

Mas essa função não considera a data, apenas horário. Talvez a "janela de tolerância" se refira a tolerância entre o horário agendado e o envio: não enviar com muita antecedência. Vou criar uma função que verifica se o envio está dentro de um intervalo antes da consulta:

```python
def respeita_janela_tolerancia(horario_envio: datetime, horario_consulta: datetime, antecedencia_maxima: timedelta, antecedencia_minima: timedelta) -> bool:
    """Retorna True se horario_envio está entre antecedencia_minima e antecedencia_maxima antes da consulta."""
    delta = horario_consulta - horario_envio
    return antecedencia_minima <= delta <= antecedencia_maxima
```

Isso testa se o lembrete está sendo enviado na janela correta (ex: entre 24h e 1h antes da consulta). Mas também precisamos verificar se não é envi