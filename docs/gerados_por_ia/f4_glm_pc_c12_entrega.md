The user wants me to create a FAI (Ficha de Atendimento Individual) XML serializer for integration with SISAB (Brazilian Ministry of Health) e-SUS APS system. This is a legitimate healthcare software development task for the Brazilian Unified Health System (SUS).

Let me think about what this involves:

1. **FAI (Ficha de Atendimento Individual)** - This is an official Brazilian Ministry of Health document used in Primary Care (Atenção Primária à Saúde). It's part of the e-SUS APS (Estratégia e-SUS Atenção Primária à Saúde) system.

2. **SISAB** - Sistema de Informação em Saúde para a Atenção Básica - the national information system for primary care.

3. **Thrift** - The e-SUS APS uses Apache Thrift for data transmission to SISAB. The official specification defines Thrift IDL structures for the fichas.

4. Key components of the FAI:
   - **CNS (Cartão Nacional de Saúde)** - National Health Card number - needs validation algorithm
   - **CPF** - Brazilian tax ID - needs validation algorithm
   - **CNES** - Cadastro Nacional de Estabelecimentos de Saúde - 7-digit code
   - **CBO** - Classificação Brasileira de Ocupações - occupation codes
   - **CIAP-2** - International Classification of Primary Care (used in APS instead of CID-10 for reasons of encounter)
   - **CID-10** - International Classification of Diseases
   - **SOAP method** - Subjective, Objective, Assessment, Plan - the clinical note structure
   - **NUVEM/SIGTAP** - procedures taxonomy

Let me recall the FAI structure from the official e-SUS APS documentation (Ficha de Atendimento Individual):

The FAI has:
- **Cabeçalho (Header)**:
  - numCnes (CNES)
  - numLote (batch number)
  - cphCnsOrigin (origin of data)
  - dataAtendimento (attendance date)
  - codigoUnidade (unit code)
  - turno (shift: 1=morning, 2=afternoon, 3=night)

- **Profissional**:
  - cns (CNS of professional)
  - cbo (CBO code)
  - cnpjCpf (optional)

- **Atendimento Individual**:
  - tipoAtendimento (type: 1=consulta agendada, 2=consulta não agendada, 3=consulta de urgência, etc.)
  - numeroProntuario (medical record number)
  - numeroCnsPaciente (patient CNS)
  - localAtendimento (location: UBS, domicílio, etc.)
  - sexo (1=male, 3=female)
  - dataNascimento (birth date)
  - etnia (ethnicity)
  - racaCor (race/color)
  - nacionalidade (nationality)
  - gestante (pregnant)
  - pesoAvaliado (weight)
  - alturaAvaliada (height)
  - procedimentoAvaliado (procedures)
  - situacaoRua (homeless situation)
  - comunidadeTradicional (traditional community)
  - população remanescente de quilombos
  - povo indígena
  - povo cigano
  - povo de terreiro / matriz africana
  - população de rua
  - profissão/ocupação
  - situação de saúde (health conditions - CID-10)
  - motivo do atendimento (CIAP-2)
  - avaliação (SOAP: subjetivo, objetivo, avaliação, plano)
  - conduta (conduct: prescrição, encaminhamento, etc.)

The official Thrift IDL for e-SUS APS (from the "Ficha de Atendimento Individual" specification) looks something like:

```thrift
struct FichaAtendimentoIndividualMaster {
    1: required string numCnes;
    2: required string numLote;
    3: required string cphCnsOrigin;
    4: required list<FichaAtendimentoIndividualChild> atendimentos;
}

struct FichaAtendimentoIndividualChild {
    1: required string uuidFicha;
    2: required i32 turno;
    3: required i32 tipoAtendimento;
    4: required string numeroProntuario;
    5: required string numeroCnsPaciente;
    6: optional string localAtendimento;
    7: required string dataAtendimento;
    8: required i32 sexo;
    9: required string dataNascimento;
    10: optional string nacionalidade;
    11: optional string racaCor;
    12: optional string etnia;
    13: optional bool gestante;
    14: optional bool fumante;
    15: optional bool excessoAlcool;
    16: optional bool usoDrogas;
    17: optional bool obesidade;
    18: optional bool imobilizacao;
    19: optional bool incapacidade;
    20: optional bool situacaoRua;
    21: optional bool comunidadeTradicional;
    22: optional bool povoIndigena;
    23: optional bool povoCigano;
    24: optional bool povoTerreiro;
    25: optional bool quilombola;
    26: optional bool profissaoOcupacao;
    27: optional bool situacaoSaude;
    28: optional bool motivoAtendimento;
    29: optional bool avaliacao;
    30: optional bool conduta;
    31: optional string subjetivo;
    32: optional string objetivo;
    33: optional string avaliacaoTexto;
    34: optional string plano;
    35: optional list<Problema> problemas;
    36: optional list<Procedimento> procedimentos;
    37: optional list<Medicamento> medicamentos;
    38: optional list<Encaminhamento> encaminhamentos;
    39: optional list<Exame> exames;
    40: optional list<AtendimentoIndividualProfissional> profissionais;
}
```

Actually, the exact Thrift IDL from the official e-SUS APS documentation (Ficha de Atendimento Individual - versão 3.1.00 or similar) is:

```thrift
struct FichaAtendimentoIndividualMaster {
  1: required string numCnes;
  2: required string numLote;
  3: required string cphCnsOrigin;
  4: required list<FichaAtendimentoIndividualChild> atendimentos;
}

struct FichaAtendimentoIndividualChild {
  1: required string uuidFicha;
  2: required i32 turno;
  3: required i32 tipoAtendimento;
  4: required string numeroProntuario;
  5: required string numeroCnsPaciente;
  6: optional string localAtendimento;
  7: required string dataAtendimento;
  8: required i32 sexo;
  9: required string dataNascimento;
  10: optional string nacionalidade;
  11: optional string racaCor;
  12: optional string etnia;
  13: optional bool gestante;
  14: optional bool fumante;
  15: optional bool excessoAlcool;
  16: optional bool usoDrogas;
  17: optional bool obesidade;
  18: optional bool imobilizacao;
  19: optional bool incapacidade;
  20: optional bool situacaoRua;
  21: optional bool comunidadeTradicional;
  22: optional bool povoIndigena;
  23: optional bool povoCigano;
  24: optional bool povoTerreiro;
  25: optional bool quilombola;
  26: optional bool profissaoOcupacao;
  27: optional bool situacaoSaude;
  28: optional bool motivoAtendimento;
  29: optional bool avaliacao;
  30: optional bool conduta;
  31: optional string subjetivo;
  32: optional string objetivo;
  33: optional string avaliacaoTexto;
  34: optional string plano;
  35: optional list<Problema> problemas;
  36: optional list<Procedimento> procedimentos;
  37: optional list<Medicamento> medicamentos;
  38: optional list<Encaminhamento> encaminhamentos;
  39: optional list<Exame> exames;
  40: optional list<AtendimentoIndividualProfissional> profissionais;
}
```

Hmm, I don't remember the exact field IDs, but I should create a reasonable, well-documented implementation. Since I can't guarantee exact field numbers from the official spec, I should note that the Thrift field IDs follow the official specification and document them clearly. Actually, let me be careful here — the task says "Exportador Thrift e Serializador XML de FAI (C12)". So the deliverable is:

1. A Thrift exporter (serializing FAI to Thrift binary protocol for SISAB transmission)
2. An XML serializer (the e-SUS APS also has XML export format for the fichas)

The XML format for e-SUS APS export is defined in the "Layout de Exportação" documents. The XML for FAI looks like:

```xml
<atendimentoIndividual>
  <uuidFicha>...</uuidFicha>
  <turno>1</turno>
  <tipoAtendimento>1</tipoAtendimento>
  ...
</atendimentoIndividual>
```

Actually the official XML export format (from the e-SUS APS "Layout de Exportação de Dados" documentation) uses a structure like:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<atendimentoIndividual>
    <uuidFicha>uuid</uuidFicha>
    <turno>1</turno>
    <tipoAtendimento>1</tipoAtendimento>
    <numeroProntuario>123</numeroProntuario>
    <numeroCnsPaciente>...</numeroCnsPaciente>
    <localAtendimento>1</localAtendimento>
    <dataAtendimento>2024-01-15</dataAtendimento>
    <sexo>1</sexo>
    <dataNascimento>1990-05-10</dataNascimento>
    <nacionalidade>76</nacionalidade>
    <racaCor>1</racaCor>
    <etnia>...</etnia>
    <gestante>false</gestante>
    ...
    <profissionais>
        <cns>...</cns>
        <cbo>225120</cbo>
        <cnpjCpf>...</cnpjCpf>
    </profissionais>
    <problemas>
        <problema>
            <codigo>...</codigo>
            <cid10>...</cid10>
        </problema>
    </problemas>
    <procedimentos>
        <procedimento>
            <codigo>...</codigo>
        </procedimento>
    </procedimentos>
    ...
</atendimentoIndividual>
```

Since I can't reproduce the exact official spec from memory with 100% fidelity, I'll build a well-structured, production-quality implementation that:
1. Implements the known structure faithfully (based on the public e-SUS APS specifications)
2. Documents clearly where field IDs come from
3. Includes robust validation (CNS, CPF, CNES, CBO, CIAP-2, CID-10)
4. Uses Pydantic v2 for strict typing
5. Includes SQLAlchemy 2.0 models for persistence
6. Includes comprehensive pytest tests

Let me now design the module:

**File: backend/app/services/fai_serializer.py**

Components:
1. **Validators**:
   - `validate_cns` - CNS validation algorithm (Mod 11 based)
   - `validate_cpf` - CPF validation algorithm
   - `validate_cnes` - CNES validation (7 digits)
   - `validate_cbo` - CBO-2002 format (6 digits, e.g., 225120 for médico clínico)
   - `validate_ciap2` - CIAP-2 code format (letter + 2 digits)
   - `validate_cid10` - CID-10 format (letter + 2-4 chars)

2. **Pydantic models** (strict typing):
   - `ProfissionalFAI`
   - `ProblemaFAI` (CID-10)
   - `ProcedimentoFAI` (SIGTAP)
   - `MedicamentoFAI`
   - `EncaminhamentoFAI`
   - `ExameFAI`
   - `AtendimentoIndividualFAI` (the child record)
   - `FichaAtendimentoIndividualMaster` (the batch)
   - Enums for turno, tipoAtendimento, sexo, racaCor, localAtendimento, nacionalidade, etc.

3. **Serializers**:
   - `FAIXMLSerializer` - produces the official XML export format
   - `FAIThriftExporter` - produces Thrift binary using the official IDL structure

4. **SQLAlchemy 2.0 model** for persistence of FAI records (maybe in a separate models file, but the task says create the service file — I can include the SQLAlchemy model in the service or reference it. The task says "crie backend/app/services/fai_serializer.py" — one file. But it also says SQLAlchemy 2.0. I could include a SQLAlchemy model in the same file or show integration. Let me include a minimal SQLAlchemy 2.0 model in the file for persistence of serialized batches, or better, accept SQLAlchemy models as input. Hmm.

Actually, re-reading: "Código em Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0." — so the code should use both Pydantic v2 and SQLAlchemy 2.0. I'll include:
- Pydantic models for validation/serialization
- A SQLAlchemy 2.0 model (DeclarativeBase, Mapped, mapped_column) for the FAI record persistence
- A function to build Pydantic FAI from SQLAlchemy ORM objects (from_orm pattern)

And tests: "Manter conformidade total e cobertura de testes automatizados com pytest." — I should provide a test file `backend/tests/services/test_fai_serializer.py` with comprehensive coverage.

Let me now write the actual validation algorithms:

**CNS validation (Cartão Nacional de Saúde)**:
The CNS can be 15 digits starting with 1, 2, 7, 8, or 9. The validation algorithm:
- For CNS starting with 1, 2 (definitive cards): 15 digits, validated with Mod 11 with weights 15, 14, 13, ..., 2.
- For CNS starting with 7, 8, 9 (provisional): also validated with a different algorithm.

The standard algorithm (from DATASUS):

```
def validate_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] not in '12789':
        return False
    # First 12 digits + check digits
    soma = 0
    peso = 15
    for i in range(12):
        soma += int(cns[i]) * peso
        peso -= 1
    resto = soma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    if dv == 10:
        # special case: add 100 to first 12 digits... 
        # Actually: dv = 11 - (soma % 11); if dv == 10, then soma += 2 and recompute
        soma = soma + 2
        resto = soma % 11
        dv = 11 - resto
        if dv == 11:
            dv = 0
    # The result dv is the first check digit; the last two digits are dv and 0? 
```

Let me recall the exact algorithm. The official CNS validation (from DATASUS):

```
function validaCNS(vCNS) {
    var soma = 0;
    var resto = 0;
    var dv = 0;
    var pis = new String;
    var resultado = new String;
    pis = vCNS.toString();
    if ((pis.trim().length != 15) || (pis == "000000000000000")) {
        return false;
    }
    // gera o primeiro dígito verificador
    soma = (parseInt(pis.substring(0, 1), 10) * 15) +
           (parseInt(pis.substring(1, 2), 10) * 14) +
           (parseInt(pis.substring(2, 3), 10) * 13) +
           (parseInt(pis.substring(3, 4), 10) * 12) +
           (parseInt(pis.substring(4, 5), 10) * 11) +
           (parseInt(pis.substring(5, 6), 10) * 10) +
           (parseInt(pis.substring(6, 7), 10) * 9) +
           (parseInt(pis.substring(7, 8), 10) * 8) +
           (parseInt(pis.substring(8, 9), 10) * 7) +
           (parseInt(pis.substring(9, 10), 10) * 6) +
           (parseInt(pis.substring(10, 11), 10) * 5) +
           (parseInt(pis.substring(11, 12), 10) * 4);
    resto = soma % 11;
    dv = 11 - resto;
    if (dv == 11) dv = 0;
    if (dv == 10) {
        soma = 2 + (parseInt(pis.substring(0, 1), 10) * 15) + ... (same but +2)
        resto = soma % 11;
        dv = 11 - resto;
        resultado = pis + "001" + dv.toString();
    } else {
        resultado = pis + "000" + dv.toString();
    }
    if (vCNS != resultado) {
        return false;
    }
    return true;
}
```

Wait, this is the algorithm for generating a CNS from 11 digits (PIS-like). For validating a full 15-digit CNS, the algorithm is:

For CNS starting with 1 or 2 (15 digits): 
- Take first 12 digits, compute check digits as above, and the full number must match `pis + "000" + dv` or `pis + "001" + dv`.

Hmm, actually the full validation for 15-digit CNS:

```
def valida_cns(cns: str) -> bool:
    cns = ''.join(filter