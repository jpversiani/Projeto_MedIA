Preciso criar um arquivo de testes chamado backend/tests/test_copiloto_clinico.py conforme solicitado. Devo validar detecção de contraindicações graves na prescrição, bloqueio de medicamento caso alergia declarada, e validar estrutura e completude do rascunho SOAP gerado.

Preciso entender o contexto do projeto: MedIA, backend com Python 3.12, Pydantic v2, SQLAlchemy 2.0. Padrões SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF). Isso sugere que existem modelos de domínio e serviços para prescrição, interações, alergias, SOAP etc. Preciso escrever testes que verifiquem essas funcionalidades. Como não tenho o código real, devo assumir que existem módulos específicos para isso.

Primeiro, decidi criar um arquivo de testes que seja auto-suficiente, talvez mockando as dependências, mas provavelmente devo testar o código existente. Como sou engenheiro de software, devo criar teste que façam sentido para o domínio. Talvez existam classes como Prescricao, Medicamento, Alergia, InteracaoMedicamentosa, Prontuario, SOAP, etc.

Dado que não tenho o código-fonte, vou elaborar um teste que valide funcionalidades esperadas, mas deixarei claro que precisa ser adaptado ao código real. No entanto, como sou um agente que deve fornecer código completo e executável, devo criar um teste que funcione isoladamente, talvez com mocks ou com classes fictícias? A tarefa diz "crie backend/tests/test_copiloto_clinico.py". Provavelmente o projeto já tem uma estrutura com esses serviços. Vou supor que existam funções como:

- detectar_contraindicacoes_graves(prescricao)
- verificar_alergias(paciente, medicamento)
- gerar_soap(consulta)

Mas preciso ter certeza. Talvez seja melhor criar um teste que usa fixtures e mocks, mas que verifique comportamentos definidos. Como não tenho o código, posso criar um teste bem projetado que importa de módulos do projeto, e caso não existam, o teste falharia com erro de importação. Mas a tarefa é para o projeto MedIA, então provavelmente essa é a estrutura esperada. Vou assumir que existem módulos em backend/app ou similar. Preciso examinar a estrutura típica de um projeto FastAPI com SQLAlchemy.

Vou pensar em uma solução: criar um teste que cubra as três solicitações, usando "monkeypatch" para mockar o acesso ao banco de dados ou serviços externos, mas as validações devem ser feitas nas camadas de serviço/regras de negócio.

Melhor abordagem: escrever testes que importam de um módulo de serviços (ex: backend/app/services/seguranca_paciente.py) e testam funções específicas. Mas sem saber a assinatura exata, posso inferir e depois adaptar.

Vou criar um arquivo de teste com funções de teste:

1. test_detectar_contraindicacoes_graves_na_prescricao:
   - Verifica que para uma prescrição que contém dois medicamentos com interação grave (ex: varfarina e aspirina), a função retorna alerta crítico.
   - Verifica que para prescrição sem interações, não retorna alertas.
   - Pode também verificar alertas de dose, mas foco em interações.

2. test_bloqueio_medicamento_por_alergia_declarada:
   - Verifica que se o paciente tem alergia a penicilina, e prescrevem amoxicilina, o sistema bloqueia com erro.
   - Verifica que se não tem alergia, permite prescrição.

3. test_valida_estrutura_e_completude_do_soap:
   - Verifica que o dicionário ou modelo SOAP contém os campos obrigatórios: S (subjetivo), O (objetivo), A (avaliação), P (plano).
   - Verifica que cada seção tem conteúdo mínimo (não vazia) e que as informações-chave estão presentes.
   - Verifica estrutura de dados: ex: modelo Pydantic com campos validados.

Preciso também incluir testes de tipagem e conformidade.

Como não conheço a implementação, vou criar um arquivo de teste que usa mocks e define as funções localmente? Não, o ideal é testar as funções reais. Vou supor que existem funções em um módulo específico: backend/app/services/copiloto_clinico.py ou backend/app/api/v1/routes/copiloto.py.

Vou fazer o seguinte: vou escrever o arquivo de teste com imports de módulos que podem existir, mas se não existirem, forneço classes fake? A instrução é "crie backend/tests/test_copiloto_clinico.py" não me pede para criar outros arquivos. Portanto, devo apenas criar os testes, assumindo que o código dos serviços é importável. Posso incluir comentários sobre adaptação.

Talvez seja mais apropriado criar testes que exercitem a lógica usando objetos de domínio definidos no próprio módulo de teste? Mas isso não testa o código real. Para ser um bom engenheiro, devo seguir a arquitetura existente.

Vou examinar a estrutura típica de um projeto FastAPI com domínio rico. Farei uma suposição razoável:

- Modelos Pydantic em backend/app/schemas (ex: prescricao.py, soap.py)
- Serviços em backend/app/services (ex: copiloto_clinico.py, interacao_medicamentosa.py, alergia.py)
- Repositórios/DB em backend/app/repositories

Criarei o teste com imports:

from app.services.copiloto_clinico import ... 
from app.schemas.prescricao import PrescricaoCreate
etc.

Mas como não tenho certeza, talvez use from backend.app...? O diretório backend/tests/test_copiloto_clinico.py, considerando que a raiz do projeto contém "backend" e dentro há "app" ou apenas "backend"? Normalmente, um projeto FastAPI tem a estrutura: backend/app/main.py, backend/app/models, etc. Se o teste está em backend/tests, então deve importar de app... com o path ajustado. Em testes, geralmente adiciona-se o diretório backend ao PYTHONPATH ou usa-se pytest.ini com pythonpath.

Vou escrever o teste assumindo que os módulos estão em "app." (considerando que o pytest roda a partir de backend). Também posso adicionar um conftest.py que ajusta o sys.path, mas a instrução pede apenas o arquivo de teste. Então vou criar apenas test_copiloto_clinico.py que importa de "app" e se precisar de ajuste, pode ser feito configurando o ambiente.

Outra abordagem: buscar boas práticas e deixar o código adaptável.

Vou escrever o arquivo com os três testes usando pytest, com fixtures para criar dados. Preciso cobrir:

1. Contraindicações graves: Vou supor que há um serviço que consulta uma base de interações medicamentosas. Talvez o serviço retorne um objeto com alertas. Ex:

from app.services.copiloto_clinico import verificar_contraindicacoes
from app.schemas.prescricao import Prescricao, ItemPrescricao

def test_contraindicacao_grave():
    itens = [
        ItemPrescricao(medicamento_codigo="Varfarina", dose="5mg"),
        ItemPrescricao(medicamento_codigo="Aspirina", dose="100mg"),
    ]
    prescricao = Prescricao(paciente_cns="123", itens=itens)
    alertas = verificar_contraindicacoes(prescricao)
    assert any(alerta.gravidade == "GRAVE" for alerta in alertas)

Mas as assinaturas podem ser diferentes. Vou procurar por nomenclaturas comuns.

Outra possibilidade: existir uma classe "PrescricaoMedicamentosa" com método "validar_seguranca()".

Como sou um agente que deve produzir código, vou criar um arquivo de teste bem elaborado, com comentários indicando pontos de adaptação. Também posso criar um arquivo de teste que usa "mock" de banco de dados, mas não há instruções para criar fixtures de banco.

Vou criar um teste que verifica a lógica de negócio, usando funções que eu vou supor que existam no módulo "app.services.clinico". Vou tentar o seguinte:

- Criar classes de exemplo em um bloco try/except para importar. Se falhar, talvez pular? Não, o teste deve falhar se o código não existir. Mas para fins de completude, vou criar um módulo de teste que funcione mesmo se o código não existir? Improvável.

Vou tomar uma decisão: como a tarefa pede para criar o arquivo de teste, e não implementar a funcionalidade, meu trabalho é somente escrever o arquivo de teste. Se no projeto real não existirem as funções, o teste quebrará, mas isso espera-se para implementação futura. Então posso escrever testes que acessem funções e schemas que devem existir. Devo ter cuidado para que os imports sejam plausíveis.

Vou assumir a seguinte estrutura de módulos:

- backend/app/schemas/prescricao.py: contém
  - class Medicamento(BaseModel): codigo_barras, nome, concentracao, ...
  - class ItemPrescricao(BaseModel): medicamento, dose, via, frequencia, ...
  - class Prescricao(BaseModel): paciente_id/cns, medico_crm, data, itens: List[ItemPrescricao]

- backend/app/services/seguranca_paciente.py: contém
  - def verificar_contraindicacoes_graves(prescricao) -> List[AlertaSeguranca]
  - def verificar_alergias(paciente, medicamento) -> Optional[AlergiaInfo] (ou raise se bloqueada)

- backend/app/schemas/soap.py:
  - class SOAP(BaseModel): subjetivo, objetivo, avaliacao, plano, (talvez com validação)

- backend/app/services/copiloto_clinico.py: contém
  - def gerar_rascunho_soap(consulta) -> SOAP
  - que chama os outros serviços.

Vou importar de app.services.copiloto_clinico import verificar_contraindicacoes, verificar_alergia, gerar_soap. Mas não sei. Vou criar um teste que exercite o fluxo de ponta a ponta: ao prescrever para um paciente com alergia a penicilina, o sistema deve bloquear; e a geração do SOAP deve retornar o rascunho completo.

Para tornar os testes mais concretos, vou usar dados exemplares do SUS: CID-10, CIAP-2, etc.

Também devo garantir que os testes usem tipagem estrita, Pydantic v2, SQLAlchemy 2.0. Não vou usar SQLAlchemy diretamente no teste, a menos que precise de banco. Provavelmente os serviços usam SQLAlchemy para acessar banco. Nos testes, posso usar mocks com pytest-mock ou monkeypatch.

Vou escrever um arquivo de teste que importa os módulos e, caso não existam, dá erro. Mas para minimizar erros de nome, vou usar nomes genéricos e documentar.

Talvez seja melhor criar o teste para uma API (endpoints) em vez de serviços internos. A tarefa diz "Alertas de Interação e Segurança do Paciente". Pode ser um endpoint POST /prescricao que retorna alertas. Mas sem conhecer a API, arrisco.

Outra abordagem: criar testes de unidade para classes de domínio que implementam as regras. Como não tenho o código, vou inventar classes de domínio no próprio arquivo de teste para validar a lógica? Isso não seria um teste do sistema real.

Preciso interpretar a tarefa: "TAREFA: Testes de Validação dos Alertas de Interação e Segurança do Paciente (C30)" - provavelmente é uma tarefa de desenvolvimento onde devo criar os testes para um novo módulo "copiloto_clinico" que será implementado. Então, posso escrever os testes esperados para esse módulo, definindo a interface. Isso é aceitável, pois sou o engenheiro que define o comportamento esperado. Então, posso criar o arquivo de teste com imports de módulos que serão criados (talvez ainda não existam), e descrever os contratos.

Vou fazer isso: escrever testes que importam de "app.services.copiloto_clinico" e "app.schemas.copiloto" etc. Vou documentar no topo do arquivo que esses imports precisam ser implementados conforme especificação.

Mas também posso criar um teste que também valide a estrutura dos dados usando Pydantic, com modelos que eu defino no próprio teste. Por exemplo, defino um modelo Pydantic SOAP em um conftest? Não, melhor não.

Vou pensar: o arquivo de teste é para o projeto MedIA. Talvez o projeto já tenha uma estrutura existente. Vou supor que o módulo principal é "backend/app". Para evitar problema de path, vou escrever o teste usando from app.services.copiloto_clinico import ... e if not import, raise ImportError com mensagem.

Vou elaborar um arquivo de teste completo com:

- Importações necessárias: pytest, typing, pydantic
- Definição de fixtures para paciente, prescricao e medicamentos.

- Teste 1: test_contraindicacao_grave_detectada:

    - Cria uma prescrição contendo varfarina e cetoconazol (interação grave conhecida) - ou usar exemplos reais de interação grave: varfarina + AINEs (aumento risco de sangramento), sinvastatina + claritromicina (rabdomiólise), etc.

    - Chama a função de verificação de contraindicações (suponha verificar_contraindicacoes_na_prescricao) e verifica que há alertas com gravidade >= 2 (ou que é bloqueante).

    - Também verifico que para uma combinação não interagente, não há alertas.

- Teste 2: test_bloqueio_por_alergia:

    - Cria paciente com alergia a penicilina (reação anafilática).

    - Cria prescrição com amoxicilina (derivado de penicilina).

    - Ao chamar a função que valida a prescrição (ex: validar_prescricao_segura), deve lançar exceção ou retornar erro de bloqueio.

    - Verifica que com um medicamento seguro (não alérgico) não bloqueia.

- Teste 3: test_soap_estrutura_completa:

    - Cria uma consulta com dados do paciente e sintomas, exame físico, hipótese (CID-10 A09 - diarreia), e prescrição/vacina.

    - Chama gerar_rascunho_soap(consulta) e verifica que o objeto retornado tem todos os quatro componentes SOAP com conteúdo não vazio.

    - Verifica que os campos respeitam os códigos ICD/CIAP quando aplicável.

    - Verifica que é um modelo Pydantic com validação.

Para isso, preciso escolher nomes de funções. Vou definir no arquivo de teste constantes de import com try/except para permitir falha clara.

Também posso usar monkeypatch para simular banco de dados, mas não é necessário se as funções de serviço são puras (não acessam banco) - mas como é SQLAlchemy, provavelmente acessam. Posso então usar um mock do repositório.

Vou criar um teste que executa as regras de negócio puras, assumindo que a interação medicamentosa e a alergia são baseadas em dados de referência (que podem ser em memória). Assim, os serviços podem consultar uma base de dados via SQLAlchemy; nos testes, devemos fornecer dados de referência via fixtures de banco (usando SQLAlchemy em modo SQLite ou mock).

Como o projeto usa SQLAlchemy 2.0, posso criar uma fixture que configura uma sessão de banco em memória e popula com dados de alergias e interações. Mas isso exigiria conhecer os modelos. Vou evitar isso e usar mocks para as consultas de dados.

Melhor: escrever os testes de forma que as funções de serviço recebam dados de referência de uma forma injetável, e eu forneça dicts localmente. Vou assumir que o serviço tem uma interface como:

def verificar_contraindicacoes(prescricao, base_interacoes=None):
    if base_interacoes is None:
        # consulta banco
    ...

Aí eu passo uma base fictícia.

Outra: usar monkeypatch para substituir a função de consulta à base de interações por uma que retorna dados pré-definidos.

Vou escrever um teste que monkeypatch uma função de repositório, por exemplo, "app.repositories.interacoes.buscar_interacoes_por_medicamento" para retornar uma lista com interação grave. Mas isso é acoplado à implementação.

Como não tenho a implementação, vou criar testes de caixa preta que chamam as funções públicas do módulo "copiloto_clinico" e verificam resultados. Vou escolher nomes de funções genéricos e documentar no docstring que a implementação deve atender.

Vou criar o arquivo com o seguinte conteúdo:

```python
"""
Testes para o Copiloto Clínico - Alertas de Interação e Segurança do Paciente.

Valida:
1. Detecção de contraindicações graves na prescrição.
2. Bloqueio de medicamento quando paciente tem alergia declarada.
3. Estrutura e completude do rascunho SOAP gerado.
"""
```

Então importo:

```python
import pytest
from pydantic import ValidationError
from typing import List, Dict, Any, Optional

# Importações do domínio (assumindo que existem; ajustar conforme implementação)
try:
    from app.schemas.prescricao import Prescricao, ItemPrescricao, Medicamento
    from app.schemas.paciente import Paciente
    from app.schemas.soap import SOAP, Consulta
    from app.services.copiloto_clinico import (
        verificar_contraindicacoes_graves,
        verificar_alergias_e_bloquear,
        gerar_soap,
        PrescricaoInvalidaError,
    )
except ImportError as e:
    raise ImportError(
        "Módulos do Copiloto Clínico não encontrados. Verifique a implementação."
    ) from e
```

Mas isso pode gerar erro de importação no pytest. Vou manter assim, pois o teste exige esses módulos.

Depois, escrevo data classes/fixtures:

```python
@pytest.fixture
def paciente_sem_alergia():
    return Paciente(
        cns="123456789012345",
        cpf="11122233344",
        nome="Fulano de Tal",
        alergias=[],
        ...
    )

@pytest.fixture
def paciente_com_alergia_penicilina():
    return Paciente(
        cns="123456789012345",
        cpf="11122233344",
        nome="Beltrano",
        alergias=[Alergia(substancia="penicilina", reacao="anafilaxia", gravidade="GRAVE")],
    )
```

Mas precisamos de schemas Alergia. Vou definir classes locais? Não, dentro do teste, usar dicts? O ideal é usar os modelos Pydantic, mas como não sei, posso usar dicts para os testes. Mas a função de bloqueio provavelmente recebe um paciente Pydantic com campo alergias.

Se eu usar dicts, o teste pode ser menos útil.

Uma abordagem: definir os modelos mínimos dentro do arquivo de teste (ex: classes Pydantic para teste), e o serviço os utiliza? Isso não seria integrado.

Outra: usar "Session" com SQLAlchemy? Não.

Vou tentar um caminho intermediário: assumir que os modelos existem e usar a tipagem, mas para os testes, crio instâncias com argumentos que julgo necessários. Se a definição não bater, o teste falhará com erro claro.

Vou fazer uma busca mental: em um projeto FastAPI, os schemas Pydantic geralmente correspondem aos modelos ORM, com campos como cns, cpf, nome, alergias (lista de strings ou de modelos).

Vou definir nos testes:

```python
class Paciente(BaseModel):
    cns: str
    cpf: str
    nome: str
    alergias: List[str] = []

class ItemPrescricao(BaseModel):
    medicamento: str
    dose: str
    via: str = "oral"
    frequencia: str = "1x/dia"

class Prescricao(BaseModel):
    paciente_cns: str
    itens: List[ItemPrescricao] = []

class SOAP(BaseModel):
    subjetivo: str
    objetivo: str
    avaliacao: str
    plano: str
```

Isso são meus próprios modelos. Mas o teste então não valida o código real. Não é bom.

Vou verificar se há alguma chance de que o projeto já tenha esses módulos. Não tenho acesso. O melhor que posso fazer é escrever um teste que importa de app e, se não existir, indicar o erro. Assim o usuário saberá o que precisa implementar.

Decisão final: criar o arquivo de teste com imports de "app" e funções de serviços. O código será robusto, com docstrings explicando o comportamento esperado. Se houver discrepância nos nomes, será fácil ajustar.

Vou escrever:

```python
# backend/tests/test_copiloto_clinico.py

"""Testes de validação para o Copiloto Clínico do MedIA.

Cobertura:
- C30.1: Detecção de contraindicações graves na prescrição.
- C30.2: Bloqueio de medicamento quando o paciente possui alergia declarada.
- C30.3: Estrutura e completude do rascunho SOAP gerado.

Para executar: pytest backend/tests/test_copiloto_clinico.py -v
"""
```

Importações:

```python
import pytest
from pydantic import BaseModel, ValidationError
```

Mas para usar BaseModel, eu preciso definir modelos? Se os modelos vêm de app, não preciso defini-los, apenas importar. Vou importar com try/except.

Exemplo:

```python
try:
    from app.schemas.prescricao import Prescricao, ItemPrescricao
    from app.schemas.paciente import Paciente
    from app.schemas.soap import SoapRascunho
    from app.services.copiloto_clinico import (
        detectar_contraindicacoes_graves,
        verificar_bloqueio_alergia,
        gerar_rascunho_soap,
        ErroPrescricao,
    )
except ImportError as e:
    raise ImportError(
        "Dependências do Copiloto Clínico não encontradas. "
        "Certifique-se de que os módulos de domínio e serviços estão implementados: "
        f"Erro original: {e}"
    )
```

Aí as fixtures:

```python
@pytest.fixture
def paciente_com_alergia_a_penicilina():
    return Paciente(
        cns="898001722300001",
        cpf="12345678901",
        nome="Maria da Silva",
        alergias=["Penicilina", "Amoxicilina"],
        data_nascimento="1990-01-01"
    )
```

Mas se o schema Paciente não tiver o campo alergias, falha. Para mitigar, posso construir o objeto usando model_validate e passar dict; se o modelo mudar, o pytest mostrará o erro.

Os dados de exemplo:

- Contraindicação: Varfarina + Cetoconazol (aumenta risco de sangramento) - é uma interação grave. Ou Varfarina + Ácido acetilsalicílico (AAS) - também grave.

- Alergia: penicilina + amoxicilina (derivado) - deve bloquear.

- SOAP: gerar a partir de atendimento com sintomas, exame, CID-10/CIAP.

Teste 1:

```python
def test_detectar_contraindicacao_grave_na_prescricao():
    """Verifica que prescrição contendo interação grave é detectada."""
    prescricao = Prescricao(
        paciente_cns="898001722300001",
        itens=[
            ItemPrescricao(medicamento="Varfarina", dose="5mg", frequencia="1x/dia"),
            ItemPrescricao(medicamento="Cetoconazol", dose="200mg", frequencia="1x/dia"),
        ]
    )
    alertas = detectar_contraindicacoes_graves(prescricao)
    assert len(alertas) > 0, "Deveria haver alerta de interação grave"
    assert any(alerta.gravidade == "GRAVE" for alerta in alertas)
```

Preciso garantir que o retorno é uma lista de objetos com atributo gravidade. Caso contrário, posso ajustar.

Teste 2:

```python
def test_bloqueia_medicamento_para_alergia_declarada():
    """Verifica que medicamento alergênico é bloqueado."""
    prescricao = Prescricao(
        paciente_cns="898001722300001",
        itens=[ItemPrescricao(medicamento="Amoxicilina", dose="500mg", ...)]
    )
    with pytest.raises(ErroPrescricao):
        verificar_bloqueio_alergia(prescricao, paciente_com_alergia_a_penicilina)
```

Mas talvez a função retorne um alerta bloqueante em vez de lançar exceção. Vamos fazer duas asserções? Posso escrever um teste que verifica que a função retorna um alerta de bloqueio.

Melhor: dizer que a função "verificar_bloqueio_alergia" retorna uma lista de alertas, e um com "bloqueante: True". Mas para simplicidade, vou usar uma exceção customizada.

Se não houver, adaptar.

Vou criar duas funções: `verificar_contraindicacoes_graves(prescricao) -> List[AlertaSeguranca]` e `validar_prescricao(prescricao, paciente) -> List[AlertaSeguranca]` que lança erro se bloqueante. Mas isso é minha invenção.

Para ficar mais robusto, vou usar pytest.raises apenas se a função levantar exceção. Vou escrever com `pytest.raises(ErroPrescricao)` e se a função não levantar, falha.

Teste 3:

```python
def test_soap_rascunho_estrutura_completa():
    """Valida que o rascunho SOAP possui os quatro componentes não vazios."""
    consulta = Consulta(
        paciente_cns="898001722300001",
        queixa_principal="Dor de garganta há 3 dias",
        historia_doenca_atual="Paciente refere odinofagia, febre baixa, sem tosse",
        exame_fisico="Orofaringe hiperemiada, amígdalas aumentadas, sem exsudato",
        hipoteses_diagnosticas=["J03.0"],
        prescricao=Prescricao(...),  # etc
    )
    rascunho = gerar_rascunho_soap(consulta)
    assert hasattr(rascunho, "s") ...
```

Mas não vou definir o modelo Consulta. Vou usar um objeto com atributos fornecidos via kwargs.

Melhor: simplesmente chamar `gerar_rascunho_soap(paciente_id, dados_consulta)`.

Deixe-me criar uma interface mais simplificada para os testes, baseada em "service". Posso ter `gerar_soap(cns_paciente, dados_clinicos)` que retorna um dicionário/objeto com chaves "S", "O", "A", "P".

Vou escrever testes que verifiquem que o retorno é um dict com essas chaves e valores não vazios.

Exemplo:

```python
def test_gerar_rascunho_soap():
    dados_clinicos = {
        "queixa_principal": "Dor abdominal",
        "historia": "Dor em cólica há 2 dias",
        "exame_fisico": "abdome doloroso difuso",
        "hipotese_diagnostica": "CID10 R10.4",
        "plano": "Hidratação, antiespasmódico, retorno em 48h",
    }
    soap = gerar_rascunho_soap(paciente_cns="123", dados_clinicos=dados_clinicos)
    assert "S" in soap and "O" in soap and "A" in soap and "P" in soap
    for section in ["S", "O", "A", "P"]:
        assert soap[section].strip(), f"Seção {section} vazia"
```

Mas se retornar um modelo Pydantic, posso usar .model_dump().

Vou usar .model_dump() ou atributos.

Ok, vou combinar.

Além disso, a tarefa menciona "completude" - posso verificar que os campos de dados de entrada foram corretamente refletidos.

Agora, vou escrever o arquivo final com comentários explicando que a intenção é testar o módulo "copiloto clinico", e que os imports foram realizados conforme esperado.

Para simplificar, vou definir os modelos de exemplo no próprio arquivo de teste se não existirem, mas isso iria conflitar com os imports. Na verdade, posso fazer o try/except e se os módulos não existirem, definir classes locais com a mesma interface? Isso faria o teste passar mesmo sem implementação, o que não é desejado. Então não vou fazer isso. Vou manter o try/except com ImportError para direcionar o desenvolvedor.

Vou também adicionar um `pytestmark` para testes de unidade.

Outra ideia: usar `pytest.importorskip` para pular se não existir, mas a tarefa é para validar, então deve rodar.

Vou fazer o seguinte: criar uma seção de "mocks" para testes que não dependem de banco de dados, usando `monkeypatch` para simular repositórios. Isso pode ser útil. Por exemplo, a função `detectar_contraindicacoes` pode depender de um repositório que consulta uma tabela de interações. Nos testes, posso monkeypatch essa consulta para retornar um resultado específico.

Mas como não sei o nome do repositório, evito.

Vou escrever um teste de alto nível que chama um serviço `validar_prescricao` que recebe prescricao e paciente e retorna lista de alertas. Nele, eu forneço dados simples que a implementação deve interpretar.

Para as alergias: suponha que a função `validar_prescricao` consulta as alergias do paciente (que podem ser strings). Então se o nome do medicamento contém "amox" e paciente tem alergia "penicilina" e "amoxicilina", deve retornar alerta de bloqueio.

Isso é mais teste funcional.

Vou redigir o arquivo agora.

Preciso incluir exemplos de dados com padrões SUS: CNS, CPF, CID-10, CIAP-2. Vou usar códigos de exemplo.

- CNS: 898 0017 2230 0001 (mas é 15 dígitos). Vou usar "898001722300001" (15 dígitos).
- CID-10: J03.0 (amigdalite aguda), A09 (diarreia).
- CIAP-2: R72 (amigdalite), D70 (infecção intestinal).

Vou usar esses.

Agora, o código do arquivo de teste:

```python
# backend/tests/test_copiloto_clinico.py
"""
Testes do Copiloto Clínico - Segurança na Prescrição e SOAP.
...
"""

import pytest
from typing import List, Optional, Dict, Any

# Importações dos módulos do domínio - ajustar conforme implementação real
try:
    from app.schemas.prescricao import Prescricao, ItemPrescricao, Medicamento
    from app.schemas.paciente import Paciente
    from app.schemas.prontuario import SoapRascunho
    from app.services.copiloto_clinico import (
        verificar_interacoes,
        verificar_alergias,
        gerar_soap,
        SegurancaPacienteException,
    )
except ImportError as e:
    raise ImportError(
        "Não foi possível importar os componentes do Copiloto Clínico. "
        "Verifique a estrutura de pastas e implementação dos módulos. "
        f"Detalhes: {e}"
    )
```

Mas os nomes podem variar. Posso escolher nomes mais simples:

- `detectar_contraindicacoes(prescricao)`
- `validar_alergias(paciente, prescricao)`
- `gerar_rascunho_soap(dados_consulta)`

Vou usar esses.

Agora, testes:

```python
class TestDetectarContraindicacoesGraves:
    def test_prescricao_sem_interacao_grave_nao_gera_alerta(self):
        prescricao = Prescricao(
            paciente_cns="898001722300001",
            itens=[
                ItemPrescricao(medicamento="Dipirona", dose="500mg"),
                ItemPrescricao(medicamento="Paracetamol", dose="750mg"),
            ]
        )
        alertas = detectar_contraindicacoes(prescricao)
        assert not any(a.gravidade == "GRAVE" for a in alertas)

    def test_prescricao_com_interacao_grave_gera_alerta(self):
        prescricao = Prescricao(
            paciente_cns="898001722300001",
            itens=[
                ItemPrescricao(medicamento="Varfarina", dose="5mg"),
                ItemPrescricao(medicamento="Cetoconazol", dose="200mg"),
            ]
        )
        alertas = detectar_contraindicacoes(prescricao)
        assert any(a.gravidade == "GRAVE" for a in alertas)
        # opcional: verifica se contém descrição da interação
```

Para testar alergias:

```python
class TestAlergiaPaciente:
    @pytest.fixture
    def paciente_alergico(self):
        return Paciente(
            cns="898001722300001",
            cpf="12345678901",
            nome="Fulano",
            alergias=["Penicilina", "Amoxicilina"]
        )

    def test_bloqueio_medicamento_alergico(self, paciente_alergico):
        prescricao = Prescricao(
            paciente_cns=paciente_alergico.cns,
            itens=[ItemPrescricao(medicamento="Amoxicilina", dose="500mg")]
        )
        with pytest.raises(SegurancaPacienteException):
            validar_alergias(paciente_alergico, prescricao)

    def test_permitir_medicamento_sem_alergia(self, paciente_alergico):
        prescricao = Prescricao(
            paciente_cns=paciente_alergico.cns,
            itens=[ItemPrescricao(medicamento="Dipirona", dose="500mg")]
        )
        # não deve levantar exceção
        validar_alergias(paciente_alergico, prescricao)
```

SOAP:

```python
class TestGeracaoSoap:
    def test_estrutura_completa(self):
        consulta = {
            "paciente_cns": "898001722300001",
            "queixa_principal": "Dor de garganta há 3 dias",
            "historia_doenca": "Dor ao deglutir, febre baixa, sem tosse",
            "exame_fisico": "Orofaringe hiperemiada, amígdalas aumentadas sem exsudato",
            "hipotese_diagnostica": "J03.0",  # CID-10 Amigdalite aguda
            "conduta": "Sintomáticos, repouso, retorno em 48h se febre",
        }
        soap = gerar_rascunho_soap(consulta)
        # se for BaseModel, usar .model_dump(); se for dict, direto
        if hasattr(soap, "model_dump"):
            soap_dict = soap.model_dump()
        else:
            soap_dict = soap
        for section in ("S", "O", "A", "P"):
            assert section in soap_dict, f"Seção {section} ausente"
            assert soap_dict[section].strip(), f"Seção {section} vazia"
        # verificar que a hipótese diagnóstica aparece na avaliação e o plano na conduta
        assert "J03.0" in soap_dict["A"]
```

Mas pode ser que o SOAP seja uma classe com atributos subjetivo, objetivo, avaliacao, plano. Prefiro usar nomes completos.

Vou usar:

```python
for campo in ["subjetivo", "objetivo", "avaliacao", "plano"]:
    assert getattr(soap, campo).strip(), f"Campo {campo} vazio"
```

Isso é melhor.

Vou juntar tudo.

Também preciso garantir que as funções `detectar_contraindicacoes`, `validar_alergias`, `gerar_rascunho_soap` existam. Talvez elas estejam em `app.services.copiloto_clinico`.

Se alguma não existir, o teste falha com ImportError, o que é bom.

Vou adicionar um teste também para verificar que os modelos usados estão tipados (Pydantic v2). Por exemplo, `Prescricao` é BaseModel, e se eu criar com dados inválidos, levanta ValidationError.

```python
def test_modelos_usam_pydantic_v2():
    assert hasattr(Prescricao, "model_validate")
```

Não necessário.

Agora, vou escrever o código final. Vou fornecer o arquivo completo.

Talvez eu deva tornar as funções mais flexíveis: em vez de lançar exceção, retornar alertas de bloqueio. Mas escolhi a exceção. Para robustez, posso usar `with pytest.raises(SegurancaPacienteException)` e se a função não levantar, falha. Tudo bem.

Além disso, posso testar que o alerta de interação grave tem dados como medicamentos envolvidos, descrição, etc.

Vou incluir.

Agora, o arquivo:

```python
# backend/tests/test_copiloto_clinico.py
```

Coloco importações e testes.

Preciso lembrar que o teste deve ser executável. Se o projeto estiver configurado com `backend` como raiz, e `tests` dentro de `backend`, então `app` está em `backend/app`. O pytest precisa rodar a partir de `backend` para importar `app`. Isso pode ser configurado com `pytest.ini` ou `pyproject.toml`. Como não vou criar esses, apenas o teste, mas é esperado.

Posso adicionar um comentário no topo sobre configuração do PYTHONPATH.

Vou elaborar o conteúdo final do arquivo.

Preciso incluir `from __future__ import annotations` para tipagem.

Também vou usar dataclasses? Não.

Vou criar o código com testes organizados.

Aqui vai:

```python
# backend/tests/test_copiloto_clinico.py
"""Testes do módulo Copiloto Clínico para segurança do paciente.

Cobre:
- C30.1: Contraindicações graves em prescrições.
- C30.2: Bloqueio de medicamentos para pacientes com alergias declaradas.
- C30.3: Estrutura e completude do rascunho SOAP.

Execute com:
    cd backend
    pytest tests/test_copiloto_clinico.py -v
"""

from __future__ import annotations

import pytest

from typing import List, Dict, Any

# Importações do domínio MedIA.
# Se o módulo ainda não existir, o teste falhará com mensagem orientativa.
try:
    from app.schemas.prescricao import Prescricao, ItemPrescricao, Medicamento
    from app.schemas.paciente import Paciente, Alergia
    from app.schemas.prontuario import SoapRascunho
    from app.services.copiloto_clinico import (
        detectar_contraindicacoes_graves,
        validar_prescricao_contra_alergias,
        gerar_rascunho_soap,
    )
except ImportError as e:
    raise ImportError(
        "Não foi possível importar os componentes do Copiloto Clínico. "
        "Verifique se os módulos foram implementados em backend/app. "
        f"Erro: {e}"
    )
```

Vou ajustar os nomes das funções para serem mais consistentes: `detectar_contraindicacoes_graves`, `validar_prescricao_contra_alergias`, `gerar_rascunho_soap`. Talvez `validar_prescricao_contra_alergias` retorne uma lista de alertas, não exceção. Para simplificar, vou assumir que ela lança uma exceção `AlergiaBloqueanteError` que pode ser importada.

Mas não defini essa exceção. Vou usar `ValueError` ou criar uma exceção local? Melhor importar `SegurancaPacienteError`.

Ok, vou importar `SegurancaPacienteError` no try.

```python
    from app.services.copiloto_clinico import (
        detectar_contraindicacoes_graves,
        validar_prescricao_contra_alergias,
        gerar_rascunho_soap,
        SegurancaPacienteError,
    )
```

Aí nos testes, uso `pytest.raises(SegurancaPacienteError)`.

Vou ajustar.

Agora, os fixtures.

```python
@pytest.fixture
def paciente_sem_alergia():
    return Paciente(
        cns="898001722300001",
        cpf="12345678901",
        nome="Paciente Teste",
        data_nascimento="1990-01-01",
        alergias=[],
    )

@pytest.fixture
def paciente_com_alergia_penicilina():
    return Paciente(
        cns="898001722300001",
        cpf="12345678901",
        nome="Paciente Alergico",
        data_nascimento="1990-01-01",
        alergias=["Penicilina", "Amoxicilina"],
    )
```

Preciso saber o schema de Alergia - pode ser uma lista de strings. Vou usar strings.

Teste 1:

```python
class TestContraindicacoesGraves:
    def test_prescricao_com_interacao_grave(self):
        prescricao = Prescricao(
            paciente_cns="898001722300001",
            itens=[
                ItemPrescricao(medicamento="Varfarina", dose="5mg"),
                ItemPrescricao(medicamento="Cetoconazol", dose="200mg"),
            ]
        )
        alertas = detectar_contraindicacoes_graves(prescricao)
        assert len(alertas) > 0
        assert any(alerta.gravidade == "GRAVE" for alerta in alertas)

    def test_prescricao_sem_interacao_grave(self):
        prescricao = Prescricao(
            paciente_cns="898001722300001",
            itens=[
                ItemPrescricao(medicamento="Dipirona", dose="500mg"),
                ItemPrescricao(medicamento="Paracetamol", dose="750mg"),
            ]
        )
        alertas = detectar_contraindicacoes_graves(prescricao)
        assert not any(alerta.gravidade == "GRAVE" for alerta in alertas)
```

Note que "paracetamol e dipirona" não tem interação grave.

Teste 2:

```python
class TestAlergiasPaciente:
    def test_bloqueia_medicamento_alergico(self, paciente_com_alergia_penicilina):
        prescricao = Prescricao(
            paciente_cns=paciente_com_alergia_penicilina.cns,
            itens=[ItemPrescricao(medicamento="Amoxicilina", dose="500mg")]
        )
        with pytest.raises(SegurancaPacienteError):
            validar_prescricao_contra_alergias(paciente_com_alergia_penicilina, prescricao)

    def test_permite_medicamento_seguro(self, paciente_com_alergia_penicilina):
        prescricao = Prescricao(
            paciente_cns=paciente_com_alergia_penicilina.cns,
            itens=[ItemPrescricao(medicamento="Dipirona", dose="500mg")]
        )
        # não deve lançar erro
        validar_prescricao_contra_alergias(paciente_com_alergia_penicilina, prescricao)
```

Se a função não lançar erro, o teste passa.

Teste 3:

```python
class TestGeracaoSoap:
    def test_soap_completo(self):
        dados_clinicos = {
            "queixa_principal": "Dor de garganta há 3 dias",
            "historia_doenca": "Odynofagia, febre baixa, sem tosse.",
            "exame_fisico": "Orofaringe hiperemiada, amígdalas aumentadas, sem exsudato.",
            "hipotese_diagnostica": "J03.0",  # CID-10 Amigdalite aguda
            "conduta": "Sintomáticos, repouso, retorno em 48h se febre.",
        }
        soap = gerar_rascunho_soap(
            paciente_cns="898001722300001",
            dados_clinicos=dados_clinicos,
        )
        assert soap.subjetivo.strip() != ""
        assert soap.objetivo.strip() != ""
        assert soap.avaliacao.strip() != ""
        assert soap.plano.strip() != ""
        # Verifica se o diagnóstico foi incorporado à avaliação
        assert "J03.0" in soap.avaliacao
        # Verifica se a conduta foi incorporada ao plano
        assert "Sintomático" in soap.plano
```

Mas a assinatura da função `gerar_rascunho_soap` pode variar. Posso usar `soap = gerar_rascunho_soap(dados_clinicos)`. Vou deixar assim: `gerar_rascunho_soap(paciente_cns, dados_clinicos)`.

Se `SoapRascunho` tiver campos com nomes diferentes (ex: `subjetivo`, `objetivo`, `avaliacao`, `plano`), ok. Se for `S`, `O`, etc, preciso ajustar. Vou usar nomes completos.

Mas no padrão SOAP, geralmente os campos são `subjetivo`, `objetivo`, `avaliacao`, `plano` em português. Vou manter.

Se a classe tiver campos obrigatórios, o teste verificará.

Para validar que é um Pydantic v2, posso adicionar no teste:

```python
assert "model_config" in dir(soap)
```

Não é necessário.

Vou finalizar o arquivo com esses conteúdos.

Talvez haja necessidade de importar `SegurancaPacienteError`. Se não existir, o try/except vai capturar ImportError e re-lançar, então o teste nem roda. Isso é aceitável.

Para melhorar a legibilidade, vou adicionar docstrings nos testes.

Agora, vou escrever o código final.```python
# backend/tests/test_copiloto_clinico.py
"""
Testes do módulo Copiloto Clínico para segurança do paciente.

Cobertura:
- C30.1: Detecção de contraindicações graves na prescrição.
- C30.2: Bloqueio de medicamento quando o paciente possui alergia declarada.
- C30.3: Estrutura e completude do rascunho SOAP gerado.

Execute com:
    cd backend
    pytest tests/test_copiloto_clinico.py -v
"""

from __future__ import annotations

import pytest

# Importações do domínio MedIA.
# Se o módulo ainda não existir, o teste falhará com mensagem orientativa.
try:
    from app.schemas.prescricao import Prescricao, ItemPrescricao, Medicamento
    from app.schemas.paciente import Paciente, Alergia
    from app.schemas.prontuario import SoapRascunho
    from app.services.copiloto_clinico import (
        detectar_contraindicacoes_graves,
        validar_prescricao_contra_alergias,
        gerar_rascunho_soap,
        SegurancaPacienteError,
    )
except ImportError as e:
    raise ImportError(
        "Não foi possível importar os componentes do Copiloto Clínico. "
        "Certifique-se de que os módulos foram implementados em backend/app "
        "conforme a arquitetura do MedIA. "
        f"Erro original: {e}"
    ) from e


# Fixtures de pacientes
@pytest.fixture
def paciente_sem_alergia():
    """Paciente sem alergias declaradas."""
    return Paciente(
        cns="898001722300001",
        cpf="12345678901",
        nome="Paciente Teste",
        data_nascimento="1990-01-01",
        alergias=[],
    )


@pytest.fixture
def paciente_com_alergia_penicilina():
    """Paciente com alergia a penicilina e derivados."""
    return Paciente(
        cns="898001722300001",
        cpf="12345678901",
        nome="Paciente Alergico",
        data_nascimento="1990-01-01",
        alergias=["Penicilina", "Amoxicilina"],
    )


# ---------------------------------------------------------------------------
# C30.1 - Contraindicações graves na prescrição
# ---------------------------------------------------------------------------
class TestContraindicacoesGraves:
    """Testes para detecção de interações medicamentosas graves."""

    def test_prescricao_com_interacao_grave_gera_alerta(self):
        """
        Prescrição com varfarina + cetoconazol deve disparar alerta de alto risco.
        """
        prescricao = Prescricao(
            paciente_cns="898001722300001",
            itens=[
                ItemPrescricao(medicamento="Varfarina", dose="5mg", frequencia="1x/dia"),
                ItemPrescricao(medicamento="Cetoconazol", dose="200mg", frequencia="1x/dia"),
            ],
        )

        alertas = detectar_contraindicacoes_graves(prescricao)

        assert len(alertas) > 0, "Deveria existir ao menos um alerta de interação"
        assert any(
            alerta.gravidade == "GRAVE" for alerta in alertas
        ), "A interação Varfarina-Cetoconazol deve ser classificada como GRAVE"

    def test_prescricao_sem_interacao_grave_nao_gera_alerta(self):
        """
        Uma combinação segura não deve produzir alertas graves.
        """
        prescricao = Prescricao(
            paciente_cns="898001722300001",
            itens=[
                ItemPrescricao(medicamento="Dipirona", dose="500mg", frequencia="6/6h"),
                ItemPrescricao(medicamento="Paracetamol", dose="750mg", frequencia="6/6h"),
            ],
        )

        alertas = detectar_contraindicacoes_graves(prescricao)

        assert not any(alerta.gravidade == "GRAVE" for alerta in alertas), (
            "Combinação sem interação grave não deve gerar alerta GRAVE"
        )


# ---------------------------------------------------------------------------
# C30.2 - Bloqueio de medicamento por alergia declarada
# ---------------------------------------------------------------------------
class TestAlergiasPaciente:
    """Testes de segurança para medicamentos alergênicos."""

    def test_bloqueia_medicamento_alergico(self, paciente_com_alergia_penicilina):
        """
        Administrar amoxicilina em paciente com alergia a penicilina deve bloquear.
        """
        prescricao = Prescricao(
            paciente_cns=paciente_com_alergia_penicilina.cns,
            itens=[
                ItemPrescricao(medicamento="Amoxicilina", dose="500mg", frequencia="8/8h"),
            ],
        )

        with pytest.raises(SegurancaPacienteError):
            validar_prescricao_contra_alergias(paciente_com_alergia_penicilina, prescricao)

    def test_permite_medicamento_nao_alergico(self, paciente_com_alergia_penicilina):
        """
        Administrar um medicamento seguro ao mesmo paciente não deve bloquear.
        """
        prescricao = Prescricao(
            paciente_cns=paciente_com_alergia_penicilina.cns,
            itens=[
                ItemPrescricao(medicamento="Dipirona", dose="500mg", frequencia="6/6h"),
            ],
        )

        # Deve executar sem levantar exceção
        validar_prescricao_contra_alergias(paciente_com_alergia_penicilina, prescricao)

    def test_paciente_sem_alergia_pode_usar_amoxicilina(self, paciente_sem_alergia):
        """
        Paciente sem alergia declarada pode receber amoxicilina normalmente.
        """
        prescricao = Prescricao(
            paciente_cns=paciente_sem_alergia.cns,
            itens=[
                ItemPrescricao(medicamento="Amoxicilina", dose="500mg", frequencia="8/8h"),
            ],
        )

        validar_prescricao_contra_alergias(paciente_sem_alergia, prescricao)


# ---------------------------------------------------------------------------
# C30.3 - Estrutura e completude do rascunho SOAP
# ---------------------------------------------------------------------------
class TestGeracaoSoap:
    """Testes de geração do rascunho SOAP."""

    @pytest.fixture
    def dados_consulta_amigdalite(self) -> dict:
        """Dados clínicos típicos de uma consulta de amigdalite aguda."""
        return {
            "queixa_principal": "Dor de garganta há 3 dias",
            "historia_doenca": "Odynofagia, febre baixa, sem tosse.",
            "exame_fisico": "Orofaringe hiperemiada, amígdalas aumentadas, sem exsudato.",
            "hipotese_diagnostica": "J03.0",  # CID-10 Amigdalite aguda
            "conduta": "Sintomáticos, repouso, retorno em 48h se febre.",
        }

    def test_soap_possui_quatro_componentes_preenchidos(self, dados_consulta_amigdalite):
        """O rascunho SOAP deve conter S, O, A e P com conteúdo não vazio."""
        soap = gerar_rascunho_soap(
            paciente_cns="898001722300001",
            dados_clinicos=dados_consulta_amigdalite,
        )

        # Caso o retorno seja um modelo Pydantic v2
        assert soap.subjetivo.strip(), "Seção Subjetivo (S) não pode ser vazia"
        assert soap.objetivo.strip(), "Seção Objetivo (O) não pode ser vazia"
        assert soap.avaliacao.strip(), "Seção Avaliação (A) não pode ser vazia"
        assert soap.plano.strip(), "Seção Plano (P) não pode ser vazia"

    def test_soap_reflete_diagnostico_na_avaliacao(self, dados_consulta_amigdalite):
        """O CID-10 informado deve aparecer na seção Avaliação."""
        soap = gerar_rascunho_soap(
            paciente_cns="898001722300001",
            dados_clinicos=dados_consulta_amigdalite,
        )

        assert "J03.0" in soap.avaliacao, (
            "O diagnóstico CID-10 J03.0 deve ser citado na avaliação (A) do SOAP"
        )

    def test_soap_reflete_conduta_no_plano(self, dados_consulta_amigdalite):
        """A conduta prescrita deve ser refletida na seção Plano."""
        soap = gerar_rascunho_soap(
            paciente_cns="898001722300001",
            dados_clinicos=dados_consulta_amigdalite,
        )

        assert "Sintomático" in soap.plano, (
            "A conduta 'Sintomáticos' deve aparecer no plano (P) do SOAP"
        )

    def test_soap_valida_campos_obrigatorios(self):
        """Se a entrada não contiver campos essenciais, deve falhar na validação."""
        with pytest.raises(Exception):
            gerar_rascunho_soap(
                paciente_cns="898001722300001",
                dados_clinicos={"queixa_principal": "Dor de cabeça"},
            )
```