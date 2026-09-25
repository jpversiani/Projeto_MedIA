The user wants me to create a clinical risk inference engine (Manchester Triage System adapted) for Primary Health Care (APS - Atenção Primária à Saúde) in Brazil, following SUS standards. This is for the MedIA project.

Requirements:
- File: `backend/app/services/triagem_clinica.py`
- Risk classification engine for APS (Primary Care)
- Vital signs extreme evaluation
- Sentinel complaints (chest pain, severe dyspnea)
- Priority assignment: Vermelho (Red), Laranja (Orange), Amarelo (Yellow), Verde (Green), Azul (Blue)
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me design this properly:

1. **Pydantic v2 models** for input/output:
   - `SinaisVitais` (Vital signs): PA sistólica/diastólica, FC, FR, SpO2, temperatura, glicemia capilar, nível de consciência (AVPU/Glasgow)
   - `QueixaPrincipal` with CIAP-2 codes
   - `DadosTriagem` (input for triage)
   - `ResultadoTriagem` (output: priority, score, justificativas, conduta, tempo máximo de espera)

2. **Manchester Adapted logic**:
   - Vermelho (Red): Emergência - immediate care (0 min) - e.g., severe vital sign extremes, unconscious, severe respiratory distress
   - Laranja (Orange): Muito urgente - 10 min
   - Amarelo (Yellow): Urgente - 60 min
   - Verde (Green): Pouco urgente - 120 min
   - Azul (Blue): Não urgente - 240 min (can be redirected)

3. **Vital signs thresholds** (adult, adapted for APS):
   - PA Sistólica: <90 (shock/hypotension) → Red; 90-100 → Orange/Yellow; >180 → Orange (hypertensive crisis); >200 with symptoms → Red
   - PA Diastólica: >110 → Orange; >120 → Red-ish
   - FC: <40 or >130 → Red; <50 or >120 → Orange; >100 → Yellow
   - FR: <10 or >30 → Red; >24 → Orange; >20 → Yellow
   - SpO2: <90% → Red; 90-94% → Orange; 95% → Yellow (with symptoms)
   - Temp: <35 (hypothermia) → Red/Orange; >39.5 → Orange; 38-39.5 → Yellow
   - Glicemia: <50 → Red (hypoglycemia); <70 → Orange; >300 → Orange; >250 → Yellow
   - Consciousness: AVPU - Unresponsive → Red; responds to pain → Red/Orange; responds to voice → Orange; alert → normal

4. **Sentinel complaints** (queixas sentinelas):
   - Dor torácica (chest pain) - CIAP-2: L04, K01, K02, A11 - with red flags → Red/Orange
   - Dispneia grave (severe dyspnea) - CIAP-2: R02 - → Red/Orange
   - Others: cefaleia súbita "pior dor de cabeça" (N01), déficit motor súbito (stroke - N99/K90), convulsão (N88), sangramento digestivo (D13), dor abdominal intensa (D01), reação anafilática (A12/S99), ideação suicida (P19), trauma grave, etc.

5. **CIAP-2 codes** relevant:
   - A11: Dor torácica
   - K01: Pressão arterial alta
   - K02: Pressão arterial baixa
   - K29: Doença isquêmica cardíaca / angina
   - K74: IAM agudo
   - K75: IAM agudo (actually K75 is "Infarto agudo do miocárdio")
   - R02: Sintomas/sinais respiratórios (dispneia)
   - R05: Tosse
   - R72: IAM? No... R72 doesn't exist. Let me recall CIAP-2:
     - R01: Dispneia
     - R02: Sintomas/sinais respiratórios
     - R03: Sibilos
     - R04: Outros sintomas respiratórios
     - R05: Tosse
     - R06: Sangramento respiratório
     - R07: Espirros/nasal
     - R21: Asma
     - R22: DPOC
     - R74: Infecção respiratória aguda
     - R75: Bronquite/bronquiolite
     - R77: Pneumonia
     - R83: Infarto do miocárdio agudo? No, that's K75.
     - R96: Insuficiência respiratória aguda
     - N01: Cefaleia
     - N03: Dor facial
     - N17: Enxaqueca
     - N88: Convulsão
     - N99: Doença neurológica outra
     - K90: AVC/AVD (Acidente vascular cerebral)
     - D01: Dor abdominal
     - D13: Pirose? Actually D13 is "Sangramento gastrointestinal"? Let me recall: D13 = "Sangramento gastrointestinal"? Hmm. CIAP-2 digestive: D01 dor abdominal, D02 náusea, D03 vômito, D04 pirose, D05 flatulência, D06 constipação, D07 diarreia, D08 constipação/diarreia, D09 dispepsia, D10 vômito com sangue (hematemese), D11 sangue nas fezes (melena/reto), D12 diarreia aguda, D13 constipação crônica... Actually:
       - D10: Vômito com sangue
       - D11: Sangue nas fezes
       - D12: Diarreia aguda
       - D13: Constipação
       - D14: Sangramento gastrointestinal? 
     Hmm, I should be careful. Common CIAP-2 codes:
     - A01: dor generalizada
     - A02: calafrios
     - A03: febre
     - A04: fraqueza/fadiga
     - A11: dor torácica
     - A12: sintomas/sinais cardiovasculares outros
     - A13: pulso irregular
     - A29: sintomas/sinais gerais
     - A71: febre? No, A78 is "Febre"? Actually A78 = "Febre" doesn't exist... A03 = "Calafrios", A04 = "Fraqueza", A05 = "Sudorese", A06 = "Astenia"... Let me just use well-known ones:
     - A03: Calafrios
     - A04: Fraqueza/exaustão
     - A11: Dor torácica
     - A12: Outros sintomas cardiovasculares
     - A13: Pulso irregular
     - A29: Sintomas/sinais gerais NE
     - A78: Febre? Hmm, in CIAP-2, "Febre" is A78? Actually I recall A78 = "Febre" is not standard; fever is "A03 Calafrios" and "A78 Febre" — I believe A78 is indeed "Febre" in CIAP-2. Let me think... CIAP-2 Chapter A (General and unspecified): A01 Dor generalizada/outra, A02 Calafrios, A03 Febre, A04 Fraqueza/fadiga, A05 Sudorese, A06 Astenia... Hmm, actually:
       - A01: Dor generalizada/outra
       - A02: Calafrios
       - A03: Febre
       - A04: Fraqueza/fadiga
       - A05: Sudorese
       - A06: Astenia? 
     I'm not 100% sure. Common references: A03 = "Febre" — yes, I'm fairly confident A03 is Febre in CIAP-2. And A04 = "Fraqueza/fadiga". A11 = "Dor torácica". A12 = "Sintomas/sinais cardiovasculares outros". A13 = "Pulso irregular". A29 = "Sintomas/sinais gerais outros". A71 = "Febre"? No.
     
     Actually in CIAP-2: A78 = "Febre" doesn't exist; A78 = "Febre" is wrong. Let me recall the actual list:
     - A01 Dor generalizada/outra
     - A02 Calafrios
     - A03 Febre
     - A04 Fraqueza/fadiga
     - A05 Sudorese
     - A06 Astenia
     - A07 Tontura
     - A08 Perda de peso
     - A09 Anomalia de sangue
     - A10 Sangramento
     - A11 Dor torácica
     - A12 Sintomas/sinais cardiovasculares outros
     - A13 Pulso irregular
     - A14 Sopro cardíaco
     - A15 Dor em membros
     - A16 Edema periférico
     - A17 Hipotensão
     - A18 Hipertensão
     - A19 Choque
     - A20 Abscesso
     - A21 Abscesso em membros
     - A22 Abscesso cutâneo
     - A23 Abscesso glândula apócrina
     - A24 Abscesso glândula mamária
     - A25 Abscesso glândula sudorípara
     - A26 Abscesso subcutâneo
     - A27 Abscesso tendão
     - A28 Abscesso tecido mole
     - A29 Sintomas/sinais gerais outros
     - A71 Febre? No...
     
     Hmm, I recall "A78 Febre" — actually I think A78 is "Febre" in CIAP-2! Let me verify: CIAP-2 codes ending in 7x are "injuries" (lesões), 8x are "diagnoses"... Actually the structure: x1-x29 = symptoms/complaints, x30-x69 = process codes, x70-x79 = injuries/lesions, x80-x99 = diagnoses. So A78 would be a lesion/injury code. "Febre" as a symptom would be A03. Hmm, but I've seen "A78 Febre" somewhere... Actually no — I recall in CIAP-2, A78 = "Febre" is indeed listed in some Brazilian adaptations. Hmm. Let me check my memory of CIAP-2 chapter A:
     
     A01 Dor generalizada/outra
     A02 Calafrios
     A03 Febre
     A04 Fraqueza/fadiga
     A05 Sudorese
     A06 Astenia
     A07 Tontura
     A08 Perda de peso
     A09 Anomalia de sangue
     A10 Sangramento
     A11 Dor torácica
     A12 Sintomas/sinais cardiovasculares outros
     A13 Pulso irregular
     A14 Sopro cardíaco
     A15 Dor em membros
     A16 Edema periférico
     A17 Hipotensão
     A18 Hipertensão
     A19 Choque
     A20 Abscesso
     A21 Abscesso em membros
     A22 Abscesso cutâneo
     A23 Abscesso glândula apócrina
     A24 Abscesso glândula mamária
     A25 Abscesso glândula sudorípara
     A26 Abscesso subcutâneo
     A27 Abscesso tendão
     A28 Abscesso tecido mole
     A29 Sintomas/sinais gerais outros
     A30 Alteração da composição do sangue
     A31 Anormalidade do sangue
     A32 Anemia NE
     A33 Policitemia
     A34 Anormalidade da coagulação
     A35 Alteração da função imunológica
     A36 Alteração da temperatura corporal
     A37 Alteração da temperatura NE
     A38 Hipotermia
     A39 Hipertermia
     A40 Alteração do pulso
     A41 Pulso fraco
     A42 Pulso ausente
     A43 Alteração da pressão arterial
     A44 Hipertensão NE
     A45 Hipotensão NE
     A46 Choque NE
     A47 Alteração de outros parâmetros
     A48 Alteração de outros parâmetros NE
     A49 Alteração da função imunológica NE
     A50 Febre NE? 
     
     Hmm, this is getting too deep. I'll use the well-established ones: A03 (Febre), A11 (Dor torácica), A12, A13, A17 (Hipotensão), A18 (Hipertensão), A19 (Choque), A29. These are standard.
     
     K chapter (Cardiovascular):
     - K01 Pressão arterial alta
     - K02 Pressão arterial baixa
     - K03 Pulso irregular
     - K04 Sopro cardíaco
     - K05 Dor cardíaca
     - K06 Outros sintomas cardiovasculares
     - K07 Edema periférico
     - K08 Sopro cardíaco NE
     - K29 Doença isquêmica cardíaca
     - K74 Angina pectoris
     - K75 Infarto agudo do miocárdio
     - K76 Insuficiência cardíaca? Actually K77 = "Insuficiência cardíaca". K76 = "Insuficiência cardíaca"? Hmm: K76 = "Insuficiência cardíaca", K77 = "Insuficiência cardíaca"? I recall K77 = "Insuficiência cardíaca". K76 = "Insuficiência cardíaca NE"? Let me just use K75 (IAM), K74 (Angina), K90 (AVC), K89 (AVC NE), K78 (Arritmia), K71 (Hipertensão sem complicação? Actually K86/K87 = hipertensão). K86 = "Hipertensão não complicada", K87 = "Hipertensão com envolvimento de órgão-alvo". K90 = "Acidente vascular cerebral", K89 = "Acidente vascular cerebral NE", K91 = "Doença vascular cerebral crônica". K78 = "Arritmia cardíaca". K72 = "Fibrilação e tremulação atrial"? Hmm.
     
     R chapter (Respiratory):
     - R01 Dispneia
     - R02 Sintomas/sinais respiratórios outros
     - R03 Sibilos
     - R04 Outros sintomas respiratórios
     - R05 Tosse
     - R06 Sangramento respiratório
     - R07 Espirros/nasal
     - R21 Asma
     - R22 DPOC
     - R74 Infecção respiratória aguda
     - R75 Bronquite/bronquiolite
     - R77 Pneumonia
     - R83 Infarto do miocárdio? No. R83 = "Pneumonia"? Hmm, R77 = "Pneumonia". R83 = "Infecção respiratória"? I'll use R01, R02, R03, R05, R21, R22, R74, R75, R77, R96 (Insuficiência respiratória aguda).
     
     N chapter (Neurological):
     - N01 Cefaleia
     - N03 Dor facial
     - N05 Tontura
     - N07 Convulsão? Actually N07 = "Convulsões". Hmm: N07 = "Convulsões"? I recall N88 = "Convulsão/convulsões". Let me think: N01 Cefaleia, N02 Tontura? ... N07 = "Convulsões"? In CIAP-2: N01 Cefaleia, N02 Tontura? Hmm. Standard: N01 = Cefaleia, N03 = Dor facial, N05 = Tontura, N07 = Convulsões? Actually I'm fairly sure N88 = "Convulsão" and N07 = "Convulsões" — one of them. In CIAP-2, N07 = "Convulsões" (symptom) and N88 = "Convulsão/epilepsia"? Hmm, N88 = "Epilepsia"? Let me recall: N88 = "Convulsão/epilepsia"? In CIAP-2, N88 = "Epilepsia". N07 = "Convulsões". Hmm, actually I've seen "N88 Convulsões" in Brazilian CIAP-2 lists. And N89 = "Epilepsia". Let me go with N07 = "Convulsões" (symptom) — I'm fairly confident. And N88 = "Epilepsia". Hmm, but many Brazilian sources list "N88 Convulsões". Ugh.
     
     To be safe, I'll include a small CIAP-2 dictionary with codes I'm confident about and note they're used for classification. The key ones for the engine:
     - A11 Dor torácica
     - K29 Doença isquêmica cardíaca / K74 Angina / K75 IAM
     - R01 Dispneia
     - R02 Sintomas respiratórios
     - R03 Sibilos
     - R21 Asma
     - R22 DPOC
     - R77 Pneumonia
     - R96 Insuficiência respiratória aguda
     - N01 Cefaleia
     - N07 Convulsões (I'll use this)
     - N99 Doença neurológica NE
     - K90 AVC
     - D01 Dor abdominal
     - D10 Vômito com sangue
     - D11 Sangue nas fezes
     - D93 Sí