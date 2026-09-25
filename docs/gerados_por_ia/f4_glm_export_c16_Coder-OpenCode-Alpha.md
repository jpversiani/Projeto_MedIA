The user wants me to create a FAI (Ficha de Atendimento Individual) serializer for the MedIA project, for integration with SISAB (Brazilian Ministry of Health). This is a Brazilian public health system context - e-SUS APS.

Key requirements:
1. File: `backend/app/services/fai_serializer.py`
2. FAI serializer for SISAB integration
3. Validation of CNES, CNS of professional, CBO
4. Conformity with e-SUS APS schema
5. Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
6. SUS/APS standards (CIAP-2, CID-10, SOAP method, identification by CNS/CPF)
7. Full compliance and automated test coverage with pytest

Let me think about what a FAI (Ficha de Atendimento Individual) is in the e-SUS APS context:

The FAI is one of the main records in e-SUS APS (Estratégia e-SUS Atenção Primária à Saúde). It records individual attendances. Key fields include:

**Cabeçalho (Header):**
- Código da Unidade (CNES) - 7 digits
- Data do atendimento
- Número do lote
- Código do profissional (CNS) - 15 digits
- Código CBO do profissional

**Dados do paciente:**
- CNS do cidadão (15 digits) or CPF (11 digits)
- Nome do cidadão
- Data de nascimento
- Sexo (M/F)
- Raça/Cor (1-6: 1=Branca, 2=Preta, 3=Parda, 4=Amarela, 5=Indígena, 6=Sem informação)
- Etnia (if indigenous)
- Nacionalidade
- Município de residência (IBGE code)
- CEP

**Atendimento:**
- Tipo de atendimento (código de atendimento - e.g., 2=Consulta no consultório, 3=Consulta no domicílio, etc.)
- Local de atendimento
- Procedimentos (SIGTAP codes)
- Conduta (1-9: 1=Retorno para acompanhamento, 2=Retorno para resultado de exames, 3=Emissão de receita, 4=Emissão de atestado, 5=Encaminhamento interno, 6=Encaminhamento externo, 7=Evolução registrada, 8=Alta, 9=Óbito)

**Problema/Condição:**
- CIAP-2 codes (3 characters, e.g., A01, K29)
- CID-10 codes (optional)

**SOAP method:**
- S (Subjective)
- O (Objective)
- A (Assessment/Avaliação)
- P (Plan/Plano)

**Medicamentos:**
- Via de administração
- Medicamento (SIGTAP or catalog)
- Dose, frequência

**Exames:**
- SIGTAP codes

The SISAB export format is XML (actually the official format is a compressed file with XML inside, following the ABCS - "Arquivo Base Compartilhado Simplificado"? Actually the e-SUS APS export format is the "Ficha" XML format defined by XSD schemas from the Ministry of Health).

The official e-SUS APS export uses XML files with specific structure. The FAI XML schema (v4/v5) has elements like:

```xml
<fichaAtendimentoIndividual>
  <cabecalho>
    <cnesUnidade>1234567</cnesUnidade>
    <dataAtendimento>2024-01-15</dataAtendimento>
    <numeroLote>1</numeroLote>
    <codigoProfissionalCNS>123456789012345</codigoProfissionalCNS>
    <cboProfissional>225125</cboProfissional>
  </cabecalho>
  <atendimentoIndividual>
    <dadosDoCidadao>
      <cnsCidadao>...</cnsCidadao>
      ...
    </dadosDoCidadao>
    <atendimento>
      <tipoAtendimento>2</tipoAtendimento>
      ...
    </atendimento>
    ...
  </atendimentoIndividual>
</fichaAtendimentoIndividual>
```

Actually, let me recall the real e-SUS APS FAI schema (version 5.0). The structure is roughly:

```xml
<fichaAtendimentoIndividual>
  <cabecalho>
    <cnesUnidade>...</cnesUnidade>
    <dataAtendimento>...</dataAtendimento>
    <numeroLote>...</numeroLote>
    <codigoProfissionalCNS>...</codigoProfissionalCNS>
    <cboProfissional>...</cboProfissional>
  </cabecalho>
  <atendimentoIndividual>
    <dadosDoCidadao>
      <cnsCidadao/>
      <cpfCidadao/>
      <nomeCidadao/>
      <dataNascimento/>
      <sexoCidadao/>
      <racaCorCidadao/>
      <etniaCidadao/>
      <nacionalidadeCidadao/>
      <codigoMunicipioResidencia/>
      <cepCidadao/>
    </dadosDoCidadao>
    <atendimento>
      <tipoAtendimento/>
      <localAtendimento/>
      <procedimentos>
        <procedimento/>
      </procedimentos>
      <conduta/>
    </atendimento>
    <problemas>
      <problema>
        <codigoCIAP2/>
        <codigoCID10/>
      </problema>
    </problemas>
    <medicamentos>
      <medicamento>
        <viaAdministracao/>
        <medicamento/>
        <dose/>
        <unidadeFrequencia/>
        <frequencia/>
        <quantidade/>
        <usoContinuo/>
      </medicamento>
    </medicamentos>
    <exames>
      <exame>
        <codigoExame/>
      </exame>
    </exames>
    <evolucao>
      <registroSOAP>
        <tipoRegistroSOAP/>
        <descricaoRegistro/>
      </registroSOAP>
    </evolucao>
  </atendimentoIndividual>
</fichaAtendimentoIndividual>
```

The SOAP records: tipoRegistroSOAP can be 1=S, 2=O, 3=A, 4=P.

Validation rules:
- CNES: 7 digits
- CNS: 15 digits, valid checksum (mod 11 algorithm with weights 15 to 2)
- CPF: 11 digits, valid checksum
- CBO: 6 digits (e.g., 225125 - Médico de Família e Comunidade)
- CIAP-2: letter + 2 digits (e.g., A01, K29, T90)
- CID-10: letter + 2 digits (+ optional dot and detail)
- SIGTAP: 10 digits (e.g., 0301010017)

CNS validation algorithm:
- The CNS can start with 1, 2, 7, 8, or 9
- For CNS starting with 1 or 2: 15 digits, checksum with weights 15,14,...,2
- For CNS starting with 7, 8, 9: different format (15 digits starting with 7/8/9 + 14 more)

The standard CNS checksum algorithm:
```
soma = 0
for i, digit in enumerate(cns):
    soma += int(digit) * (15 - i)
resto = soma % 11
if resto == 0: valid
else: dv = 11 - resto; if dv > 9: dv = 0... 
```

Actually the standard algorithm for CNS (Cartão Nacional de Saúde):

For CNS starting with 1 or 2 (15 digits):
```
pesos = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
soma = sum(digit * peso)
if soma % 11 == 0: valid
```

For CNS starting with 7, 8, or 9:
```
First 9 digits: 798 000 000 000 000 style
soma = sum of first 9 digits * weights [15..7]
resto = soma % 11
dv = 11 - resto
if dv == 10: dv = 0, and prefix becomes 798/898/998... 
```

Actually the algorithm for 7/8/9:
```
soma = sum(int(cns[i]) * (15 - i) for i in range(9))
resto = soma % 11
dv = 11 - resto
if dv > 9:
    dv = 0
    soma = sum(int(cns[i]) * (15 - i) for i in range(9)) + 2  # add 2 to first digit? 
```

Hmm, let me recall correctly. The CNS validation for cards starting with 7, 8, 9:

```
def valida_cns(cns):
    cns = cns.zfill(15)
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] in '12':
        # checksum over all 15 digits
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    elif cns[0] in '789':
        # first 9 digits determine DV
        soma = sum(int(cns[i]) * (15 - i) for i in range(9))
        resto = soma % 11
        dv = 11 - resto
        if dv > 9:
            soma += 2
            resto = soma % 11
            dv = 11 - resto
        # dv should match digits 10-11
        return str(dv).zfill(2) == cns[9:11]
    return False
```

Wait, the "soma += 2" trick: when dv > 9, you add 2 to the sum (which effectively changes the first digit from 7 to 9, 8 to 10→... hmm). Actually the official algorithm:

```
soma = 0
for i in range(9):
    soma += int(cns[i]) * (15 - i)
resto = soma % 11
dv = 11 - resto
if dv > 9:
    soma += 2
    resto = soma % 11
    dv = 11 - resto
return cns[9:11] == f"{dv:02d}"
```

Yes, that's the standard implementation. The "+2" accounts for the fact that when the DV would be 10 or 11, the first digit is incremented (7→9, 8→... hmm, actually adding 2 to the sum corresponds to incrementing the first digit by 1 since weight of first digit is 15... no wait).

Let me think: if dv > 9, the actual CNS uses a different first digit. The trick: adding 2 to soma. Since first digit weight is 15, adding 2 to soma doesn't directly correspond... Actually the official algorithm from DATASUS:

```
soma = 0;
for (i = 0; i < 9; i++) soma += cns[i] * (15 - i);
resto = soma % 11;
dv = 11 - resto;
if (dv > 9) {
    soma = 0;
    for (i = 0; i < 9; i++) soma += cns[i] * (15 - i);
    soma += 2;
    resto = soma % 11;
    dv = 11 - resto;
}
// dv must equal digits 10-11 of cns
```

Yes, this is the official one. The "+2" is a quirk of the algorithm. OK.

CPF validation: standard mod-11 algorithm.

CNES: 7 digits, no checksum publicly (CNES doesn't have a public checksum algorithm; it's just 7 digits). Some implementations validate just format.

CBO: 6 digits, first digit 0-9... CBO 2002 codes are 6 digits. Common medical ones: 225120 (Médico Clínico), 225125 (Médico de Família e Comunidade), 225100 (Médico), 223505 (Enfermeiro), 223710 (Técnico de Enfermagem), 225250 (Médico Pediatra), 225135 (Médico Ginecologista e Obstetra), 223208 (Agente Comunitário de Saúde? Actually ACS is 515135 - Agente Comunitário de Saúde ou Microarea). Let me be careful: ACS CBO is 515135. Endemic disease agent: 515115.

CIAP-2: 3 characters: first is letter (A-Z excluding some?), then 2 digits. CIAP-2 chapters: A (General), B (Blood), D (Digestive), F (Eye), H (Ear), K (Cardiovascular), L (Musculoskeletal), N (Neurological), P (Psychological), R (Respiratory), S (Skin), T (Endocrine/Metabolic), U (Urological), W (Pregnancy), X (Female genital), Y (Male genital), Z (Social). Note: no E, G, I, J, M, O, Q, V chapters in CIAP-2. So valid first letters: A, B, D, F, H, K, L, N, P, R, S, T, U, W, X, Y, Z.

CID-10: letter + 2 digits, optionally .X or more characters. Format: [A-Z]\d{2}(\.\d{1,2})? or with X wildcard.

SIGTAP: 10 digits.

Now, the task says "Exportador Thrift e Serializador XML de FAI (C16)". Interesting - "Exportador Thrift" - Thrift is the serialization framework from Apache. Hmm, the e-SUS APS actually uses Apache Thrift internally for its database storage! Yes, the e-SUS APS (PEC) stores fichas using Thrift serialization in its internal database. The export to SISAB is XML (compressed in ZIP with .xml files following XSD).

So the task title mentions both Thrift exporter and XML serializer. The INSTRUCTIONS section says: "crie backend/app/services/fai_serializer.py com serializador oficial da Ficha de Atendimento Individual (FAI) para integração com o SISAB (Ministério da Saúde): validação de CNES, CNS do profissional, CBO e conformidade com esquema e-SUS APS."

So the main deliverable is `backend/app/services/fai_serializer.py`. The title mentions Thrift exporter too, but the instruction focuses on the XML serializer. I could include a Thrift-compatible export (maybe a simple Thrift IDL-based binary serialization or a note). Given "Forneça o código completo e executável", I should provide:

1. `backend/app/services/fai_serializer.py` - main serializer (Pydantic models + XML generation + validations)
2. Tests: `backend/tests/services/test_fai_serializer.py` - pytest coverage
3. Maybe supporting files: `backend/app/core/exceptions.py` or similar if needed. But I should keep it self-contained where possible, though the project presumably has existing structure. Since I don't know the existing project structure, I'll make the serializer module self-contained (define exceptions inside or import from a core module with fallback?). Better to be self-contained to guarantee executability, but the architecture guidelines mention SQLAlchemy 2.0 - maybe the serializer should accept SQLAlchemy models? Hmm.

The guidelines say "tipagem estrita com Pydantic v2 e SQLAlchemy 2.0". So maybe I should include a SQLAlchemy model for FAI persistence and the serializer converts from ORM to Pydantic to XML. But the instruction says create `backend/app/services/fai_serializer.py`. To be safe and complete, I can:

- Create `backend/app/services/fai_serializer.py` with:
  - Pydantic v2 models for FAI (header, citizen data, attendance, problems, medications, exams, SOAP evolution)
  - Validators: CNES, CNS, CPF, CBO, CIAP-2, CID-10, SIGTAP, dates, enum domains (raca/cor, conduta, tipo atendimento, local atendimento, via administração, unidade frequência, tipo registro SOAP)
  - XML generation conforming to e-SUS APS schema (FAI v5)
  - Thrift exporter: a compact binary serialization using Thrift-style protocol (or provide a `.thrift` IDL and a TCompactProtocol-based writer using `thrift` package). Hmm, adding dependency on `thrift` package... The instruction says "Exportador Thrift e Serializador XML de FAI (C16)". I think I should implement both: a Thrift exporter (using Apache Thrift compact protocol, writing binary) and the XML serializer. To keep it executable without heavy deps, I could implement a minimal Thrift Compact Protocol writer in pure Python (TCompactProtocol is well-specified). That's doable: varint zigzag encoding, field headers, etc. That would be impressive and executable without the thrift library. Alternatively use `thrift` package if installed. A pure-Python minimal TCompactProtocol writer is ~100 lines and well-defined. Let me do that — it makes the code fully executable with only pydantic + stdlib.

Actually, let me reconsider: maybe simpler to implement the Thrift export using the `thrift` library's TCompactProtocol with generated classes... but we don't have generated classes. Writing raw compact protocol bytes by hand is feasible: struct fields with field id + type delta encoding, etc. I can implement a small helper class `ThriftCompactWriter` that supports i32/i64/string/bool/list/struct. That's a nice "Exportador Thrift".

Also "C16" - probably a task code. Not important.

Let me design the module:

```
backend/app/services/fai_serializer.py
```

Contents:
- Module docstring explaining purpose, SISAB, e-SUS APS schema version.
- Imports: datetime, decimal, enum, re, typing, xml.etree.ElementTree or manual string building? For XSD conformity, better to build XML with ElementTree and control namespace. The official e-SUS XML files don't use namespaces typically; they're plain XML with specific element order. I'll use `xml.etree.ElementTree` with ordered children (Python 3.8+ preserves insertion order).
- Constants: schema version "5.1" or "5.0"? The