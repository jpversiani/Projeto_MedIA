The user wants me to create a FAI (Ficha de Atendimento Individual) serializer for integration with SISAB (Brazilian Ministry of Health) e-SUS APS system. This is a legitimate healthcare software development task for the Brazilian Unified Health System (SUS).

Let me think about what's needed:

1. **FAI (Ficha de Atendimento Individual)** - This is a real document from e-SUS APS (Estratégia e-SUS Atenção Primária à Saúde). It's used to record individual patient care in Primary Care.

2. **Key requirements:**
   - Thrift exporter and XML serializer
   - CNES validation (Cadastro Nacional de Estabelecimentos de Saúde - 7 digits)
   - CNS validation (Cartão Nacional de Saúde - 15 digits, with check digit validation)
   - CBO validation (Classificação Brasileira de Ocupações - format like "225125")
   - e-SUS APS schema compliance
   - Python 3.12, Pydantic v2, SQLAlchemy 2.0
   - CIAP-2, CID-10, SOAP method
   - pytest tests

Let me recall the actual FAI structure from e-SUS APS:

The FAI (Ficha de Atendimento Individual) has these main sections:
- **Cabeçalho (Header)**: 
  - numLote (lot number)
  - dataAtendimento (care date)
  - cnsProfissional (professional CNS)
  - cbo (occupation code)
  - cnes (establishment code)
  - ine (National Identification of Health Establishment team - optional)
  - dataNascimento (patient birth date)
  - sexo (sex: M/F)
  - nacionalidade (nationality code)
  - localAtendimento (care location: 1=Unidade Básica, 2=Domicílio, 3=Escola, 4=Creche, 5=Comunidade, 6=Outros)
  - cpfCidadao (patient CPF - optional)
  - cnsCidadao (patient CNS)
  - situacaoRua (street situation: 1=Sim, 2=Não)
  - municipioNascimento (IBGE code of birth municipality)
  - paisNascimento (country code)
  - cep (postal code)
  - telefoneCidadao
  - emailCidadao
  - tipoAtendimento (care type: 1=Consulta Agendada, 2=Consulta Demanda Espontânea, 3=Atendimento de Urgência, 4=Consulta no Domicílio)
  - numeroProntuario (medical record number)

- **Atendimento (SOAP)**:
  - sinalizacaoUrgencia (urgency flag)
  - peso (weight)
  - altura (height)
  - cintura (waist)
  - pressaoArterialSistolica
  - pressaoArterialDiastolica
  - glicemiaCapilar (capillary glucose)
  - temperatura (temperature)
  - frequenciaCardiaca
  - frequenciaRespiratoria
  - saturacaoO2
  - hgt (blood glucose)
  - ciap2 (CIAP-2 codes - list, up to 3)
  - cid10 (CID-10 codes - list, up to 3)
  - conduta (conduct codes: 1=Prescrição de Medicamentos, 2=Confecção de Receita, 3=Prescrição de Exames, 4=Solicitação de Exames Complementares, 5=Atestado, 6=Encaminhamento Interno, 7=Encaminhamento Externo, 8=Evolução, 9=Conduta não medicamentosa, 10=Coleta de material, 11=Aplicação de medicamento injetável, 12=Curativo simples, 13=Retirada de pontos, 14=Sutura, 15=Imobilização, 16=Redução de fratura, 17=Fixação de fratura, 18=Desbridamento, 19=Orientação/educação em saúde, 20=Vacinação, 21=Teste rápido, 22=Coleta de material para exame laboratorial, 23=Administração de medicamentos, 24=Outros)
  - observacoes (observations)

Actually, let me be more precise about the e-SUS APS FAI structure. The official structure (from the e-SUS APS documentation, "Ficha de Atendimento Individual"):

**Cabeçalho:**
- numLote: string (max 10)
- dataAtendimento: date
- cnsProfissional: CNS (15 digits, valid check digit)
- cbo: CBO (6 digits)
- cnes: CNES (7 digits)
- ine: INE (13 digits, optional)
- dataNascimento: date
- sexo: 1=Feminino, 2=Masculino (actually in e-SUS it's M/F or 1/2... let me think. In the XML schema it's typically "M" or "F"... Actually in e-SUS APS the sexo field uses values like "M" and "F" in some versions, or 1/2. Let me use the standard: in the FichaB individual, sexo is "M" or "F". Hmm, actually in the e-SUS APS schema, sexo is defined as: 1 - Feminino, 2 - Masculino. Wait no.

Let me recall: In the e-SUS APS XML schema (XSD), the field sexo has enumeration: "M" (Masculino) and "F" (Feminino)? Or numeric?

Looking at the actual e-SUS APS schema documentation (Ficha de Atendimento Individual - FAI):
- sexo: Sexo do cidadão. Valores: 1 - Feminino, 2 - Masculino. Hmm, actually I believe in the individual care sheets it's "M"/"F"... 

Actually, from the e-SUS APS documentation for FichaB (Ficha de Atendimento Individual), the field is:
- sexo: Sexo do cidadão. Domínio: 1 - Feminino; 2 - Masculino. 

Hmm, I recall in the older e-SUS Território it was M/F. In the newer e-SUS APS (FichaB), the sexo field in the XML is "M" or "F". Let me think again...

From the official e-SUS APS documentation (Manual de Orientações para envio de dados - Ficha de Atendimento Individual):
- sexo: Sexo do cidadão. Valores possíveis: M - Masculino; F - Feminino.

Actually I've seen both. In the XSD for FichaAtendimentoIndividual, I believe it's:
```xml
<xs:element name="sexo">
  <xs:simpleType>
    <xs:restriction base="xs:string">
      <xs:enumeration value="M"/>
      <xs:enumeration value="F"/>
    </xs:restriction>
  </xs:simpleType>
</xs:element>
```

Hmm, but I also recall numeric values 1/2 in some versions. To be safe, I'll implement with "M"/"F" and note it, or make it flexible. Actually, for the FAI in e-SUS APS, I'm fairly confident the sexo field uses "M" and "F" in the XML. Let me go with that but document it clearly.

Wait — actually, I remember now. In the e-SUS APS schema (FichaB), the header fields include:
- sexo: "M" or "F"

And in Ficha Cadastro Individual, sexo is also M/F. OK, going with M/F.

- nacionalidade: country code (IBGE), default 10 (Brasil)
- localAtendimento: 1 - Unidade Básica de Saúde; 2 - Domicílio; 3 - Escola; 4 - Creche; 5 - Comunidade; 6 - Outros
- cpfCidadao: 11 digits with check digit validation (optional)
- cnsCidadao: 15 digits with check digit
- situacaoRua: 1 - Sim; 2 - Não
- municipioNascimento: IBGE code (7 digits)
- paisNascimento: country code
- cep: 8 digits
- telefoneCidadao: 10-11 digits
- emailCidadao: email
- tipoAtendimento: 1 - Consulta Agendada; 2 - Consulta Demanda Espontânea; 3 - Atendimento de Urgência; 4 - Consulta no Domicílio
- numeroProntuario: medical record number

**Atendimento (SOAP):**
- sinalizacaoUrgencia: 1 - Sim; 2 - Não
- peso: weight in kg (0.1-500)
- altura: height in cm (0.1-250)
- cintura: waist circumference
- pressaoArterialSistolica: systolic BP (0-300)
- pressaoArterialDiastolica: diastolic BP (0-200)
- glicemiaCapilar: capillary glucose (0-6000 mg/dL)
- temperatura: temperature (30-45 °C)
- frequenciaCardiaca: heart rate (0-300 bpm)
- frequenciaRespiratoria: respiratory rate (0-100)
- saturacaoO2: O2 saturation (0-100%)
- hgt: HGT (0-6000)
- ciap2: list of CIAP-2 codes (up to 3), each 3 chars (letter + 2 digits)
- cid10: list of CID-10 codes (up to 3)
- conduta: list of conduct codes (up to 4? or more)
- observacoes: free text (max 4000 chars)

**Problema/Condição avaliada** — actually in newer versions there's a section for "problemas" with CIAP-2/CID-10.

Let me structure the FAI per the official e-SUS APS "Ficha de Atendimento Individual" (FichaB):

The XML structure is roughly:
```xml
<FichaAtendimentoIndividual>
  <numLote>...</numLote>
  <dataAtendimento>2024-01-15</dataAtendimento>
  <cnsProfissional>...</cnsProfissional>
  <cbo>225125</cbo>
  <cnes>1234567</cnes>
  <ine>...</ine>
  <dataNascimento>1980-05-10</dataNascimento>
  <sexo>M</sexo>
  <nacionalidade>10</nacionalidade>
  <localAtendimento>1</localAtendimento>
  <cpfCidadao>...</cpfCidadao>
  <cnsCidadao>...</cnsCidadao>
  <situacaoRua>2</situacaoRua>
  <municipioNascimento>...</municipioNascimento>
  <paisNascimento>10</paisNascimento>
  <cep>...</cep>
  <telefoneCidadao>...</telefoneCidadao>
  <emailCidadao>...</emailCidadao>
  <tipoAtendimento>2</tipoAtendimento>
  <numeroProntuario>...</numeroProntuario>
  <atendimento>
    <sinalizacaoUrgencia>2</sinalizacaoUrgencia>
    <peso>70.5</peso>
    <altura>175</altura>
    <cintura>85</cintura>
    <pressaoArterialSistolica>120</pressaoArterialSistolica>
    <pressaoArterialDiastolica>80</pressaoArterialDiastolica>
    <glicemiaCapilar>95</glicemiaCapilar>
    <temperatura>36.5</temperatura>
    <frequenciaCardiaca>72</frequenciaCardiaca>
    <frequenciaRespiratoria>16</frequenciaRespiratoria>
    <saturacaoO2>98</saturacaoO2>
    <hgt>95</hgt>
    <ciap2>R74</ciap2>
    <ciap2>A96</ciap2>
    <cid10>J069</cid10>
    <conduta>8</conduta>
    <observacoes>...</observacoes>
  </atendimento>
</FichaAtendimentoIndividual>
```

Hmm, actually the real e-SUS APS export format uses Thrift binary protocol (the "FichaB" thrift definition) — the e-SUS APS system exports .fai files which are Thrift-serialized. The XML is used in some integrations. The task says "Exportador Thrift e Serializador XML de FAI" — so both Thrift and XML serialization.

For Thrift, the actual e-SUS APS uses Apache Thrift with a specific IDL. Implementing the full official Thrift IDL would be very long. I can implement a Thrift-compatible serializer using the Thrift compact/binary protocol with field IDs matching a reasonable IDL definition, or use the `thrift` package if available. Since we can't guarantee the thrift package, I could implement a minimal Thrift Compact Protocol writer in pure Python — that's actually feasible and interesting. But it adds complexity.

Alternative: implement the Thrift serializer with the `thrift` library (TCompactProtocol) and define the FAI structures as Thrift-generated-style classes (with thrift_spec). That's the standard approach: define classes with `thrift_spec` attributes and use `thrift.Thrift.TApplicationException`... Actually the standard way is to use generated code from the IDL. I can hand-write "generated-style" classes that mimic what Thrift's compiler generates, including `thrift_spec` and `read`/`write` methods. That's a lot of boilerplate but doable.

Alternatively, implement a small pure-Python Thrift Compact Protocol encoder that takes a dict/structure definition. This is cleaner and testable without external deps.

Given the constraints (pytest coverage, no guarantee of thrift package), I'll implement:

1. **Domain models (Pydantic v2)**: FAI header, atendimento, ficha completa — with strict validation:
   - CNES: 7 digits
   - CNS: 15 digits, check digit algorithm (the official CNS validation algorithm)
   - CPF: 11 digits, check digit algorithm
   - CBO: 6 digits, format validation (and optionally a registry of common CBOs for health professionals)
   - CIAP-2: 3-char codes (letter A-Z + 2 digits), with validation against known chapters
   - CID-10: letter + 2 digits + optional dot + 1-2 chars
   - IBGE municipality codes: 7 digits
   - Enumerations for sexo, localAtendimento, tipoAtendimento, conduta, situacaoRua, sinalizacaoUrgencia

2. **XML serializer**: generates e-SUS APS-compliant XML (FichaAtendimentoIndividual), with proper element ordering, date formats (YYYY-MM-DD), decimal formatting.

3. **Thrift exporter**: pure-Python Thrift Compact Protocol encoder producing binary bytes compatible with Thrift, with field IDs matching a documented IDL. Include a decoder for round-trip testing.

4. **SQLAlchemy 2.0 model**: FAI record persistence (ficha table) with status tracking (pending/exported), so the service can pull records and serialize them.

5. **Service layer**: FAISerializerService that loads FAI from DB (SQLAlchemy 2.0 style), validates, serializes to XML and Thrift, builds lot (lote) with header (numLote, dataExportacao, responsável, etc.).

6. **pytest tests**: comprehensive coverage — validators (CNS valid/invalid, CPF, CNES, CBO, CIAP-2, CID-10), XML structure, Thrift round-trip, service integration with in-memory SQLite.

Let me now write the CNS validation algorithm (official):

CNS validation:
- CNS must have 15 digits.
- Valid starting digits: 1, 2, 7, 8, 9 (1/2 are definitive cards, 7/8/9 are temporary/provisional).
- Algorithm (for CNS starting with 1, 2, or 7/8/9 — the standard algorithm):
  ```
  soma = sum over i of digit[i] * (15 - i)
  resto = soma % 11
  if resto == 0: valid
  else:
    soma = sum over i of digit[i] * (15 - i) + extra... 
  ```
  The official algorithm:
  ```
  def valida_cns(cns):
      cns = cns.strip().replace('.', '').replace(' ', '').replace('-', '')
      if len(cns) != 15: return False
      if any(not c.isdigit() for c in cns): return False
      if cns[0] not in '12789': return False
      # first check
      soma = sum(int(cns[i]) * (15 - i) for i in range(15))
      if soma % 11 == 0:
          return True
      # second check (for CNS starting with 7, 8, 9)
      # The algorithm: 
      resto = soma % 11
      dv = 11 - resto
      # ... 
  ```
  
  The official algorithm (from DATASUS):
  ```
  function validaCNS(vCNS) {
      // Formato: 15 dígitos, primeiro caractere em [1,2,7,8,9]
      soma = 0;
      for (i = 0; i < 15; i++) {
          soma += parseInt(vCNS[i]) * (15 - i);
      }
      resto = soma % 11;
      if (resto != 0) {
          // Recalcula para CNS provisório (7,8,9)
          soma = 0;
          for (i = 0; i < 15; i++) {
              // pega os 12 primeiros dígitos, multiplica por (15-i), 
              // e o dígito verificador...
          }
      }
  }
  ```
  
  Let me recall the exact algorithm. The well-known JS implementation:
  
  ```javascript
  function validaCNS(vCNS) {
    vCNS = vCNS.replace(/\D/g, '');
    if (vCNS.length !== 15) return false;
    if ('1234567890'.indexOf(vCNS[0]) === -1) return false; // must be digit
    // Actually: primeiro dígito deve ser 1, 2,