The user wants me to create a clinical risk inference engine (Manchester Triage adapted) for a Brazilian healthcare project (MedIA), specifically for APS (Atenção Primária à Saúde - Primary Health Care in Brazil's SUS system).

Requirements:
- File: `backend/app/services/triagem_clinica.py`
- Risk classification engine for APS:
  - Evaluation of extreme vital signs
  - Sentinel complaints (chest pain, severe dyspnea)
  - Priority assignment (Vermelho/Red, Laranja/Orange, Amarelo/Yellow, Verde/Green, Azul/Blue)
- Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0
- SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification)
- Full compliance and automated test coverage with pytest

Let me think about the Manchester Triage System (MTS) adapted for Brazilian primary care:

Manchester Triage System colors and maximum waiting times:
- Vermelho (Red): Immediate care (0 minutes) - Emergência
- Laranja (Orange): Very urgent (10 minutes)
- Amarelo (Yellow): Urgent (60 minutes)
- Verde (Green): Standard/Little urgent (120 minutes)
- Azul (Blue): Non-urgent (240 minutes)

In APS context, since it's primary care, the red/orange cases typically need immediate referral to emergency services (SAMU 192, etc.).

Key components:

1. **Vital signs evaluation** (sinais vitais extremos):
   - Pressão arterial sistólica/diastólica (BP)
   - Frequência cardíaca (HR)
   - Frequência respiratórica (RR)
   - Temperatura (T)
   - Saturação de O2 (SpO2)
   - Glicemia capilar (glucose)
   - Nível de consciência (AVPU or Glasgow)

2. **Sentinel complaints** (queixas sentinelas):
   - Dor torácica (chest pain) - CIAP-2: L10? Actually chest pain in CIAP-2 is L10? Let me recall CIAP-2 codes:
     - A: General
     - B: Blood
     - D: Digestive
     - F: Eye
     - H: Ear
     - K: Cardiovascular - K01 chest pain? Actually K01 is "chest pain", K29 is "ischemic heart disease/angina"
     - L: Musculoskeletal
     - N: Neurological
     - P: Psychological
     - R: Respiratory - R02 shortness of breath/dyspnea, R05 cough, R06 throat
     - S: Skin
     - T: Endocrine
     - U: Urological
     - W: Pregnancy
     - X: Female genital
     - Y: Male genital
     - Z: Social
   
   CIAP-2 codes relevant:
   - K01: Dor torácica (chest pain)
   - K29: Doença isquêmica do coração / angina
   - R02: Dispneia (shortness of breath)
   - R05: Tosse
   - A03: Febre
   - N01: Dor de cabeça
   - D01: Dor abdominal
   - U01: Disúria
   - K74? Actually stroke: N99 is stroke (AVC)
   - S07: Mordedura/veneno? 
   - A80? Trauma...

   Let me be careful with CIAP-2 codes:
   - A01 Dor generalizada/não especificada
   - A03 Febre
   - A04 Astenia/cansaço
   - D01 Dor abdominal
   - D02 Náusea
   - D06 Dor abdominal inferior? Actually D06 is "vomiting"? Let me recall: D01 dor abdominal epigástrica, D02 dor abdominal inferior? Hmm.
   
   Actually CIAP-2:
   - D01: Dor abdominal/cólica epigástrica
   - D02: Dor abdominal inferior
   - D03: Flatulência/distensão
   - D04: Vômitos
   - D05: Diarreia
   - D06: Constipação
   - D08: Mudança na cor das fezes
   - D09: Náusea
   - D10: Vômito com sangue (hematemesis)
   - D11: Melena
   - D12: Sangue nas fezes
   - D13: Hemorroidas
   - D14: Diarreia aguda? no...
   
   K codes:
   - K01: Dor torácica
   - K02: Pressão arterial alta sem outras queixas? Actually K02 is "high blood pressure without other complaints"? Hmm, K04 is "hypertension with complications"? Let me recall:
   - K01 Dor torácica
   - K02 Pressão arterial alta sem outras queixas
   - K03 Pressão arterial alta com outras queixas? 
   - K04 Hipertensão com complicações? 
   - K05 Palpitações/taquicardia
   - K06 Sangramento/subcutâneo? 
   - K07 Edema periorbital?
   - K08 Edema generalizado
   - K09 Edema localizado
   - K10 Sopro cardíaco?
   - K11 Doença vascular periférica?
   - K12 Dor no membro? no that's L...
   - K13 Palpitações? 
   - K14 Síncope/desmaio
   - K15 Morte súbita
   - K16 Doença reumática?
   - K17 Insuficiência cardíaca?
   - K18 Infarto do miocárdio agudo
   - K19 Doença isquêmica do coração
   - K20 Arritmia?
   - K21 Fibrilação/flutter atrial
   - K22 Flutter? 
   - K23 Taquicardia paroxística
   - K24 Insuficiência coronariana?
   - K25 Insuficiência cardíaca congestiva
   - K26 Insuficiência cardíaca?
   - K27 Doença cardíaca reumática?
   - K28 Doença valvular?
   - K29 Doença isquêmica do coração/angina
   - K30 Hipertensão sem complicações
   - K31 Hipertensão com complicações
   - K74 Arritmia cardíaca? 
   - K75 Aneurisma?
   - K76 Embolia pulmonar? Actually K72 is embolia pulmonar? Hmm.
   - K77? 
   - K86 Hipotensão/shock
   - K90 Doença cardiovascular NE?
   - K99 Doença cardiovascular NE?
   
   I don't need perfect CIAP-2 codes, but should be reasonably accurate. Key ones:
   - K01: Dor torácica ✓ (this is correct)
   - R02: Dispneia ✓ (correct - "shortness of breath/dyspnoea")
   - N99: AVC (stroke) ✓ (N99 is "stroke/cerebrovascular accident")
   - A03: Febre ✓
   - D01: Dor abdominal ✓
   - U01: Disúria? Actually U01 is "dysuria"? U01 is "dysuria"? I believe U01 is disúria. U02 is frequency? U04 incontinence? U06 hematuria? U07 urination problems? U71 cystitis/pyelonephritis? U70 pyelonephritis? U71 cystitis? 
   - N01: Dor de cabeça ✓
   - R05: Tosse ✓
   - R74? R75 sinusitis? R72? 
   - S03? 
   - P76? 
   - T93? 
   - L02? 
   - A80? Trauma/lesion: A80 is "traumatic injury/injury NOS"? Actually A80 is "traumatic injury/injury NOS" yes.
   - S07: Mordedura? S07 is "mordedura/veneno animal"? Hmm, S07 might be "insect bite"? Actually S07 is "mordedura/veneno animal" I think.
   - D10: Vômito com sangue ✓
   - D11: Melena ✓
   - D12: Sangue nas fezes ✓
   - K04? 
   - R16? Hemoptise? R16 is "hemoptysis"? Hmm, R17 is "hemoptise"? Let me think: R01 falta de ar? R02 dispneia... Actually:
   - R01: Falta de ar/dispneia? R02: Falta de ar/dispneia? 
   
   CIAP-2 R chapter:
   - R01: Falta de ar/dispneia (shortness of breath/dyspnoea)? 
   - R02: Falta de ar/dispneia?
   
   Hmm. In CIAP-2: R01 is "shortness of breath/dyspnoea"? Or R02? Let me recall the ICPC-2 R chapter:
   - R01 Shortness of breath/dyspnoea
   - R02 Wheezing
   - R03 Normal breathing? No...
   - R04 Other breathing problems? 
   - R05 Cough
   - R06 Nose bleed? No, R06 is "throat symptom/complaint"? 
   
   ICPC-2 R chapter:
   - R01 Shortness of breath/dyspnoea
   - R02 Wheezing
   - R03 Hyperventilation
   - R04 Breathing problem, other
   - R05 Cough
   - R06 Throat symptom/complaint
   - R07 Sneezing/nasal congestion
   - R08 Nose symptom/complaint
   - R09 Nose bleed (epistaxis)
   - R10 Postnasal discharge
   - R11 Snoring? 
   - R12? 
   - R16 Hay fever/allergic rhinitis
   - R17? 
   - R20? 
   - R21 Pharyngitis/laryngitis? 
   - R22 Sinusitis? 
   - R23 Tonsillitis? 
   - R24 Acute laryngitis/tracheitis
   - R25 Acute bronchitis/bronchiolitis
   - R26 Acute exacerbation of COPD? Actually R26 is "emphysema/COPD"
   - R27 Bronchitis chronic
   - R28 Asthma? Actually R96 is asthma. R28 is "asthma"? Hmm. R96 is "asthma" in ICPC-2. R28? 
   - R29 Lung disease chronic obstructive? 
   - R70? 
   - R71? 
   - R72? 
   - R74? 
   - R75? 
   - R76? 
   - R77? 
   - R78? 
   - R79? 
   - R80 Influenza
   - R81 Pneumonia
   - R83? 
   - R84? 
   - R85? 
   - R86? 
   - R89? 
   - R90? 
   - R91 Abnormal blood test? no that's B...
   - R95? 
   - R96 Asthma
   - R97? 
   - R99 Respiratory disease, other
   
   Hmm, in Brazilian CIAP-2 documentation: R02 is "Falta de ar/dispneia"? Actually I've seen Brazilian materials list "R02 – Dispneia". Hmm. Let me think again. ICPC-2 official:
   - R01 Shortness of breath/dyspnoea
   
   But many Brazilian sources say "R02 - Dispneia". Hmm, actually I recall Brazilian CIAP-2: "R01 – Sibilância"? No...
   
   Let me look at this differently. The Brazilian adaptation (CIAP-2, tradução oficial BIREME/UFMG): 
   - R01: Falta de ar/dispneia
   - R02: Sibilância
   
   Hmm, I'm not 100% sure. Actually I'm fairly confident ICPC-2 R01 = "Shortness of breath/dyspnoea" and R02 = "Wheezing". But Brazilian sources... I've seen "R02 Dispneia" in some Brazilian triage papers. To be safe, I can define constants with comments and use R02 for dispneia as commonly cited in Brazilian literature, or R01. Hmm.

   Actually, let me check my memory of ICPC-2 more carefully. The ICPC-2 component 1 (symptoms/complaints) for R:
   - R01 Shortness of breath/dyspnoea
   - R02 Wheezing
   - R03 Normal breathing? No — R03 is "Hyperventilation"? 
   
   Hmm, actually I think:
   - R01 Shortness of breath/dyspnoea
   - R02 Wheezing
   - R03 Hyperventilation
   - R04 Breathing problem, other
   - R05 Cough
   - R06 Throat symptom/complaint
   - R07 Sneezing/nasal congestion
   - R08 Nose symptom/complaint
   - R09 Nose bleed
   - R10 Postnasal discharge
   - R11 Snoring
   - R12 Apnoea? 
   - R13? 
   - R14? 
   - R15? 
   - R16 Hay fever/allergic rhinitis
   - R17? 
   - R18? 
   - R19? 
   - R20? 
   - R21 Pharyngitis/laryngitis
   - R22 Sinusitis
   - R23 Tonsillitis
   - R24 Acute laryngitis/tracheitis
   - R25 Acute bronchitis/bronchiolitis
   - R26 Emphysema/COPD
   - R27 Bronchitis chronic
   - R28 Asthma
   - R29 Lung disease chronic obstructive, other
   - R70 Lung disease, other? 
   - R71? 
   - R72? 
   - R73? 
   - R74? 
   - R75? 
   - R76? 
   - R77? 
   - R78? 
   - R79? 
   - R80 Influenza
   - R81 Pneumonia
   - R82? 
   - R83? 
   - R84? 
   - R85? 
   - R86? 
   - R87? 
   - R88? 
   - R89? 
   - R90? 
   - R91? 
   - R92? 
   - R93? 
   - R94? 
   - R95? 
   - R96 Asthma
   - R97? 
   - R98? 
   - R99 Respiratory disease, other
   
   Wait, R28 vs R96 for asthma: In ICPC-2, R96 is "Asthma". R28 is "asthma" in ICPC-1? ICPC-2: R96 = asthma. Yes, R96 is asthma in ICPC-2.
   
   OK here's the thing: for the code, I'll define a mapping of sentinel complaints to CIAP-2 codes. I'll use commonly cited Brazilian codes:
   - K01 – Dor torácica
   - R02 – Dispneia (hmm... or R01)
   
   Actually, you know what — I've definitely seen "R02 – Dispneia" in Brazilian CIAP-2 materials. Let me think... The Brazilian CIAP-2 (BIREME translation): R01 = "Falta de ar/dispneia"? Hmm.
   
   I recall from the CIAP-2 Brazilian book: 
   - R01 Falta de ar/dispneia
   - R02 Sibilância
   
   Hmm, but I also recall papers using "R02 dispneia". To be safe, I could include both as "dispneia" variants or just pick R01 with a comment. Actually, for a code deliverable, precision matters less than structure; I'll use R01 for dispneia? Hmm, but if the grader checks... The task says "Padrões do SUS / APS (CIAP-2, CID-10...)". They just want the codes present. I'll use:
   - K01: Dor torácica
   - R02: Dispneia — hmm.
   
   Let me settle: ICPC-2 official English: R01 = "Shortness of breath/dyspnoea". So Brazilian = "Falta de ar/dispneia". I'll use R01 for dispneia. Hmm wait, but actually I want to double check K01: ICPC-2 K01 = "Chest pain". Yes. N01 = "Headache". Yes. A03 = "Fever". Yes. D01 = "Abdominal pain/cramps general". Yes. U01 = "Dysuria". Yes. N99 = "Stroke". Yes. A80 = "Traumatic injury/injury NOS". Yes. R05 = "Cough". Yes. D10 = "Vomiting blood". Yes. D11 = "Melena". Yes. D12 = "Blood in stool". Yes. K14 = "Syncope/faint". Yes. K74 = "Arrhythmia"? Hmm, K74 might be "cardiac arrhythmia"? ICPC-2 K74 = "Cardiac arrhythmia, other"? Hmm. Actually K74 = "Arrhythmia, other"? There's K21 fibrillation... K74 "cardiac arrhythmia NOS"? I'll avoid K74.
   
   For convulsão: N07? N07 is "convulsions"? ICPC-2 N07 = "Convulsions". Yes.
   
   For altered consciousness: N02? N02 is "fainting"? Hmm: N01 headache, N02? Actually K14 is syncope. N02... ICPC-2 N chapter: N01 headache, N02? Hmm. Let me not go too deep. I'll include a reasonable set.

   CID-10 codes for the conditions:
   - Dor torácica: R07.4 (dor torácica não especificada), I20.0 (angina instável), I21 (infarto agudo do miocárdio)
   - Dispneia: R