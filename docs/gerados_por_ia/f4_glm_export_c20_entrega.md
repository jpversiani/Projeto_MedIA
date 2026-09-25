The user wants me to create a FAI (Ficha de Atendimento Individual) serializer for the MedIA project, for integration with SISAB (Brazilian Ministry of Health). This is a real Brazilian health system requirement - e-SUS APS uses Thrift for data export.

Key requirements:
1. File: `backend/app/services/fai_serializer.py`
2. FAI serializer for SISAB integration
3. Validation of CNES, CNS of professional, CBO
4. Conformity with e-SUS APS schema
5. Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
6. SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
7. Full conformity and automated test coverage with pytest

The e-SUS APS system actually uses Apache Thrift for data serialization/export. The FAI (Ficha de Atendimento Individual) is one of the main records. The Thrift IDL defines structures like:
- `FichaDeAtendimentoIndividualMasterThrift`
- `FichaAtendimentoIndividualThrift`
- Various enums like `SexoThrift`, `TipoAtendimentoThrift`, `LocalDeAtendimentoThrift`, `ObitoThrift`, `FichaOrigemThrift`, `TipoAtendimentoEspecialidadeThrift` (actually `TipoDeAtendimentoEspecialidadeThrift`), `TipoFichaThrift`, etc.

Since we can't include the actual Thrift generated code (it's proprietary/generated from the official IDL), I should create a serializer that:
1. Validates the FAI data according to e-SUS APS rules
2. Serializes to Thrift binary format (or a structure compatible with it)
3. Also provides XML serialization (the task title mentions "Exportador Thrift e Serializador XML de FAI")

The task title says "Exportador Thrift e Serializador XML de FAI (C20)" - so both Thrift export and XML serialization.

Let me design this properly:

**Domain knowledge about FAI (e-SUS APS):**

The Ficha de Atendimento Individual (FAI) contains:
- `uuidFicha` (UUID)
- `uuidTurno` (UUID)
- `cnes` (7 digits)
- `cnsProfissional` (15 digits, starts with 1 or 7)
- `cbo` (6 digits, e.g., 225120 - médico clínico)
- `dataAtendimento` (epoch)
- `codigoUnidadeOrigem` (cnes)
- `ine` (equipe, 10 digits)
- `turno` (enum: PRIMEIRO_TURNO=1, SEGUNDO_TURNO=2, TERCEIRO_TURNO=3, NOITE=4)
- `tipoAtendimento` (enum: CONSULTA_NO_CONSULTORIO=1, etc.)
- `localAtendimento` (enum: UNIDADE_DE_SAUDE=1, DOMICILIO=2, etc.)
- `procedAvaliado` (CID-10 or CIAP-2 code)
- `tipoProcedAvaliado` (enum: CID10=1, CIAP2=2)
- `procedSolicitados` (list of CIDs/CIAPs)
- `procedConfere` (bool)
- `exameFisico` (SOAP - S)
- `problemaRelatado` (SOAP - A)
- `analise` (SOAP - A)
- `conduta` (SOAP - P)
- `medicamentos` (list)
- `alergias` (list)
- `cuidadosContinuos` (list)
- `vacinas` (list)
- `ciap2` (main problem)
- `outrosSinaisESintomas` (list)
- `desfecho` (enum: ALTA=1, ENCAMINHAMENTO=2, EVASAO=3, OBITO=4)
- `numeroDomicilio`, `bairro`, `cep`, etc. for home visits
- `paciente` (dados do cidadão: cns, nome, sexo, dataNascimento, etc.)

CNS validation rules:
- 15 digits
- Starts with 1, 7, 8, or 9 (provisional starts with 9? Actually: definitive starts with 1 or 7; provisional with 8 or 9... let me recall)
- Actually: CNS definitive cards start with 1 or 7 (8 or 9 are temporary/provisional)
- Check digit algorithm (modulo 11):
  - Sum: for each digit i (0-indexed), multiply by (15 - i), sum all
  - The sum must be divisible by 11
  
The CNS validation algorithm:
```
soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
return soma % 11 == 0
```

CNES validation: 7 digits. There's a check digit algorithm for CNES:
- CNES has 7 digits where the last is a check digit
- Algorithm: multiply digits by weights 1,2,1,2,1,2 (for first 6 digits), sum digits of products, check digit = (10 - (sum % 10)) % 10... Let me recall the actual algorithm:

CNES check digit (módulo 11 with weights 15,14,13,12,11,10,1? No...). The official algorithm:
```
pesos = [1, 2, 1, 2, 1, 2]  # for first 6 digits
soma = 0
for i, peso in enumerate(pesos):
    produto = int(cnes[i]) * peso
    if produto >= 10:
        soma += produto - 9  # sum digits: e.g. 12 -> 1+2=3
    else:
        soma += produto
dv = (10 - (soma % 10)) % 10
```
Hmm, actually the CNES validation uses "módulo 11" with weights... Let me think. The official CNES validation algorithm (from DATASUS):

```
def valida_cnes(cnes):
    cnes = str(cnes).zfill(7)
    pesos = [15, 14, 13, 12, 11, 10]
    soma = 0
    for i in range(6):
        soma += int(cnes[i]) * pesos[i]
    resto = soma % 11
    dv = 11 - resto
    if dv == 11: dv = 0  # hmm
    ...
```

Actually, the known CNES algorithm is:
- Weights: 1, 2, 1, 2, 1, 2 applied to first 6 digits
- If product > 9, sum the digits (or subtract 9)
- Sum all
- DV = (10 - (soma % 10)) % 10

Let me verify with a known CNES: e.g., 2023109? I don't have a verified example memorized. The commonly cited algorithm in Python communities:

```python
def valida_cnes(cnes: str) -> bool:
    if len(cnes) != 7:
        return False
    pesos = [1, 2, 1, 2, 1, 2]
    soma = 0
    for i in range(6):
        valor = int(cnes[i]) * pesos[i]
        soma += valor if valor < 10 else valor - 9
    digito = 10 - (soma % 10)
    if digito == 10:
        digito = 0
    return digito == int(cnes[6])
```

Hmm, there are variations. Another version uses modulo 11:

Actually the official one from DATASUS documentation (CNES check digit):
```
pesos = [15, 14, 13, 12, 11, 10]  # no...
```

Let me think about what's commonly used. From the "cnes" validation in various projects (e.g., pyCNES):

```python
def validate_cnes(cnes):
    cnes = [int(x) for x in str(cnes)]
    if len(cnes) != 7:
        return False
    pesos = [1, 2, 1, 2, 1, 2]
    soma = 0
    for i in range(6):
        prod = cnes[i] * pesos[i]
        if prod >= 10:
            prod = sum(int(d) for d in str(prod))
        soma += prod
    dv = 10 - (soma % 10)
    if dv == 10:
        dv = 0
    return dv == cnes[6]
```

Hmm wait, actually I recall the CNES algorithm being "módulo 11" with weights 15,14,13,12,11,10:

From the official CNES documentation (Manual de validação):
- Multiply digits 1-6 by weights 15, 14, 13, 12, 11, 10 respectively
- Sum results
- Divide by 11, take remainder
- DV = 11 - remainder; if DV = 11 or DV = 10, DV = 0? 

Hmm, I'm not 100% sure. Let me check with a real CNES. A commonly known test CNES: 2023109? Or the example from documentation...

Actually, I found in my memory: the CNES validation algorithm widely used (e.g., in the `validar-docbr` packages):

```python
def valida_cnes(cnes):
    cnes = re.sub('[^0-9]', '', str(cnes))
    if len(cnes) != 7 or cnes == '0000000':
        return False
    pesos = [15, 14, 13, 12, 11, 10]
    soma = 0
    for i in range(6):
        soma += int(cnes[i]) * pesos[i]
    resto = soma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0  # hmm, or 10->0?
    return dv == int(cnes[6])
```

Hmm, there's ambiguity. Let me test with a real CNES I might know: "2791710"? I don't have reliable memory of specific CNES check digits.

Let me think about the docbr library (Python). In `docbr` there's no CNES I think. In `brutils` there might be. 

Actually, I recall the official algorithm from the CNES manual (Banco de Dados Nacional - manual de referência):

"O dígito verificador do CNES é calculado pelo módulo 11, com pesos 15, 14, 13, 12, 11, 10 para os seis primeiros dígitos..."

Hmm wait, that doesn't sound right either. Let me think about the "módulo 11-10-9-8..." pattern.

Actually I do remember now: The CNES check digit uses weights [1, 2, 1, 2, 1, 2] with the "sum of digits if >= 10" rule, then DV = (10 - soma % 10) % 10. This is the "módulo 10" style. Let me verify with a known CNES: 

Known example: CNES 2023109? Let's compute: digits 2,0,2,3,1,0 with weights 1,2,1,2,1,2:
- 2*1=2
- 0*2=0
- 2*1=2
- 3*2=6
- 1*1=1
- 0*2=0
- soma = 11
- dv = 10 - (11 % 10) = 10 - 1 = 9
- So CNES would be 2023109-9 → 20231099? That's 8 digits, wrong.

Hmm, that doesn't work. Let me try the módulo 11 with weights 15,14,13,12,11,10 on some CNES. Take CNES "2337791" (I don't know if real). 

I can't verify without a real example. Let me search memory for "validação CNES dígito verificador": 

From the DATASUS CNES database documentation (Manual do CNES, Anexo - Dígito Verificador):

The CNES DV calculation:
```
1 2 1 2 1 2  (pesos)
x x x x x x  (6 primeiros dígitos)
```
If the product is >= 10, subtract 9 (equivalent to digit sum for two-digit products). Sum everything. The DV is the value that completes the total sum to the next multiple of 10: DV = (10 - (soma % 10)) % 10.

Test with real CNES: 7654321? Not real. 

Hmm, let me try a CNES I might actually know: "2077223"? No.

OK here's another approach: I recall a GitHub gist for CNES validation:

```python
def validate_cnes(cnes):
    """Validate CNES number."""
    cnes = str(cnes).zfill(7)
    if len(cnes) != 7:
        return False
    weights = [1, 2, 1, 2, 1, 2]
    total = 0
    for i in range(6):
        product = int(cnes[i]) * weights[i]
        total += product if product < 10 else product - 9
    check = (10 - (total % 10)) % 10
    return check == int(cnes[6])
```

Hmm, but I also recall the módulo 11 version with weights 15..10. Let me think about which is official.

From the official CNES documentation "CNES – Cadastro Nacional de Estabelecimentos de Saúde – Manual de utilização" ... I believe the DV algorithm is:

"Para o cálculo do dígito verificador do CNES, utiliza-se o módulo 11 com os pesos 2, 1, 2, 1, 2, 1..." 

I genuinely am not certain. Given the ambiguity, the safest approach for the code is to implement the widely-used algorithm and document it. Many Brazilian health IT projects use this one (from the "cnes" package on PyPI or similar):

Actually! I remember now. There's a well-known implementation in the "esus" / "pyesn" projects and in the JS library "cnes-validator". The algorithm from DATASUS:

```
pesos = [15, 14, 13, 12, 11, 10]
soma = Σ digito[i] * peso[i]
resto = soma % 11
dv = 11 - resto
se dv >= 10 → dv = 0? or dv = dv - 10?
```

Hmm. Let me try to verify with a real CNES. Real CNES examples: 
- Hospital das Clínicas da FMUSP: CNES 2023109? Hmm.
- UBS examples in test data: "2023109" appears in some e-SUS test data? 

Actually, in e-SUS APS test data, common CNES values like "0000000" are used. 

Let me try to recall a definitely-real CNES: The CNES of "Hospital de Clínicas de Porto Alegre" is 2234567? No idea.

OK, different approach: I'll implement the algorithm that's most commonly cited and note it. Actually, I found it — I'm fairly confident about this one from the official DATASUS documentation (it appears in the "Manual de Digito Verificador do CNES"):

The CNES DV uses **módulo 11** with weights **15, 14, 13, 12, 11, 10** (from left to right, first digit × 15, second × 14, ..., sixth × 10). Sum, then DV = 11 - (soma mod 11). If DV = 11 → DV = 0? If DV = 10 → DV = 0? 

Let me test with a CNES I can verify... I really need a real one. Let me think: "2791710" is the CNES of some unit? I can't verify.

Alternative: I recall the Python package `validate-docbr` doesn't have CNES, but `python-brasil` docs... 

There's a known JS implementation (from the "CNES validation" in some projects):

```javascript
function validarCNES(cnes) {
  const pesos = [1, 2, 1, 2, 1, 2];
  let soma = 0;
  for (let i = 0; i < 6; i++) {
    let prod = parseInt(cnes[i]) * pesos[i];
    if (prod >= 10) prod -= 9;
    soma += prod;
  }
  const dv = (10 - (soma % 10)) % 10;
  return dv === parseInt(cnes[6]);
}
```

Hmm, I've seen this "1,2,1,2,1,2" version multiple times. But I've also seen the 15..10 version. 

Let me try to settle it with an actual known CNES. A very famous one: **CNES 2023109** — hmm. Let me think of UBS test data in e-SUS: In e-SUS APS demos, CNES "0000000" is used for testing.

What about the CNES of Hospital Albert Einstein? Not memorized.

OK here's a real one I might remember from DATASUS documentation examples: The manual example computes DV for CNES "1234567"? 

Honestly, given uncertainty, I'll implement the módulo 11 with weights 15,14,13,12,11,10 version BUT... hmm, wait. Let me think harder. 

I recall a Stack Overflow answer "Validação de CNES" with this code:

```python
def valida_cnes(cnes):
    padrao = [1, 2, 1, 2, 1, 2]
    soma = 0
    cnes = str(cnes)
    for i in range(6):
        valor = int(cnes[i]) * padrao[i]
        if valor > 9:
            soma += valor - 9
        else:
            soma += valor
    dv = 10 - (soma % 10)
    if dv == 10:
        dv = 0
    return dv == int(c