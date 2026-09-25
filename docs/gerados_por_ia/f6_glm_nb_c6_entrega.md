The user wants me to create a JavaScript file: `backend/app/static/js/copiloto_sidebar.js` — a widget for the doctor's telemedicine screen (home office) that displays in real-time:
- Blinking risk/allergy alerts
- Button "Preencher SOAP com Sugestão da IA" (Fill SOAP with AI Suggestion)
- Suggestions of complementary exams and usual SUS dosages

The task mentions architecture guidelines about Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest coverage. However, the actual deliverable is a JavaScript file (frontend widget). The guidelines seem to be general project guidelines — but since the deliverable is JS, I should focus on the JS file, and possibly mention how it integrates with the backend (which would be Python). The instruction says "Execute com precisão conforme as diretrizes" — execute precisely according to the guidelines.

Given the deliverable is explicitly `backend/app/static/js/copiloto_sidebar.js`, I should write a high-quality vanilla JS widget (no framework dependency, since it's served as static JS). I should:

1. Create the widget with:
   - Real-time display (WebSocket or polling via SSE/fetch) of patient data
   - Blinking alerts for risks/allergies (CSS animations)
   - Button "Preencher SOAP com Sugestão da IA" that fills the SOAP note fields (S, P, A, O) with AI suggestions
   - Suggestions of complementary exams (with CIAP-2/CID-10 codes) and usual SUS dosages

2. Since the guidelines mention Python/Pydantic/SQLAlchemy/pytest, I could also provide:
   - The backend endpoint contract (Pydantic schemas) that the JS consumes — maybe briefly
   - Tests for the JS? pytest can't test JS directly, but I could mention pytest-playwright or provide a Python test that validates the endpoint. The task says "Manter conformidade total e cobertura de testes automatizados com pytest" — I could include a pytest test file for the backend endpoint that feeds the widget, plus maybe a JS test harness. But the primary deliverable is the JS file.

Let me think about what's most useful: The user asked specifically for the JS file. I'll deliver:

1. `backend/app/static/js/copiloto_sidebar.js` — the main widget (well-structured, documented, accessible, LGPD-conscious).
2. A companion CSS? The task only asks for the JS. I can inject styles via JS (a `<style>` injected by the widget) to keep it self-contained — that's a common pattern for widgets. That way blinking animations etc. are included.
3. Optionally, the backend contract: Pydantic v2 schemas for the payload the widget consumes (so the JS matches the backend), and a pytest test for the endpoint. Given the guidelines emphasize Python typing and pytest, including a minimal backend contract + test would show "conformidade total". But I must be careful not to bloat. The instruction says "Execute com precisão conforme as diretrizes" — the guidelines are for the project; the task is the JS widget. I think providing:
   - The JS widget (main deliverable)
   - A short section documenting the expected API contract (Pydantic schema snippet) so the frontend matches backend
   - A pytest test file for the endpoint (e.g., `tests/test_copiloto_api.py`) verifying the contract the widget depends on

That would satisfy "cobertura de testes automatizados com pytest" reasonably.

Let me design the widget carefully.

## Widget design

**Name**: Copiloto IA — Painel Lateral (C6)

**Context**: Doctor's telemedicine screen (home office). The widget is a sidebar panel that:
- Connects to a realtime channel (WebSocket preferred, with SSE fallback and polling fallback) to receive "copiloto updates" as the consultation proceeds (e.g., transcript analysis, anamnesis data).
- Displays patient safety header: allergies (blink red), risk conditions (blink amber/red) — e.g., "ALERGIA: Penicilina", "Risco: Doença renal crônica (CID-10 N18.3)".
- Displays AI suggestions: SOAP draft (S, O, A, P sections), with CIAP-2 code and CID-10 suggestion.
- Displays suggested complementary exams (SUS protocol-based, e.g., from PCDT/Protocolos da Atenção Básica) with CIAP-2 codes.
- Displays usual SUS dosages for suggested medications (from Rename/Componentes da Assistência Farmacêutica), with dose, via, frequency, duration — and warnings for allergies/renal impairment.
- Button "Preencher SOAP com Sugestão da IA" — fills the SOAP textareas in the main telemedicine form (by ID or via custom event), with confirmation modal (doctor must review — AI is decision support, final decision is the doctor's; LGPD/CFM resolution on telemedicine — Resolução CFM 2.314/2022).
- Audit: log when doctor accepts AI suggestion (consentimento/registro em prontuário).

**Technical approach**:
- Vanilla JS, IIFE or ES module? Since it's served as static file, I'll write it as an ES module? Many Flask apps just include `<script src=...>` without `type="module"`. To be safe, write it as an IIFE that attaches to `window.CopilotoSidebar` and auto-initializes if a mount point exists. Provide `data-*` configuration on the mount element.
- No external dependencies.
- Accessible: ARIA roles, `aria-live="assertive"` for alerts, focus management, keyboard.
- Security: escape HTML (patient data), no innerHTML with untrusted data — use textContent / create elements. Use a small `esc()` helper if needed.
- Realtime: WebSocket with auto-reconnect + exponential backoff; fallback to polling `GET /api/v1/consultas/{id}/copiloto` every N seconds. Also handle `document.visibilityState`.
- State machine: disconnected / connecting / connected / error.
- Blinking: CSS class `.copiloto-alerta--piscante` with `@keyframes` blink; respect `prefers-reduced-motion` (accessibility) — then use static highlight instead of blink.
- SOAP fill: dispatch custom event `copiloto:preencher-soap` and also directly fill fields if present (`#soap-subjetivo`, `#soap-objetivo`, `#soap-avaliacao`, `#soap-plano`). Confirmation dialog before overwriting non-empty fields.
- Dosage suggestions: table with medicamento (DCB), apresentação, posologia (dose, via, intervalo, duração), restrições (ex.: "evitar em IRC"), fonte (Rename 2022 / PCDT). Include CIAP-2 for the reason for encounter.
- Exams: table with exame, código SISMAMA/SISLAB? Better: exame + justificativa clínica + CID-10 relacionado + CIAP-2. SUS exams use SIGTAP codes (e.g., "40302011 - Hemograma complete"? Actually SIGTAP: hemograma completo is 40302011? Let me recall: SIGTAP code for "HEMOGRAMA COMPLETE" is 40302011? I believe hemograma is 40302011 (LAB). Actually, common knowledge: 40302011 - HEMOGRAMA. Hmm, I'm not 100% sure. To avoid inventing wrong codes, I can include SIGTAP codes that are widely known: 
  - Hemograma completo: 40302011 (I think this is right — "HEMOGRAMA" 40302011? There's also 40302019? Let me think. SIGTAP: 40302011 HEMOGRAMA. I've seen 40302011 for hemograma in many BPA files. Yes, 40302011 is "HEMOGRAMA".)
  - Glicose: 40302063? Hmm. "GLICOSE" is 40302063? I recall 40302063 - GLICOSE? Not sure. Common: 40302063 (glicose). Actually I recall "40302063 - GLICOSE" appears in SISLAB lists. I'm fairly confident 40302063 is glicose... but not certain.
  - Creatinina: 40302012? "CREATININA" 40302012? I recall 40302012 - CREATININA. Hmm.
  - Lipidograma: 40302013? "COLESTEROL TOTAL" 40302013? Not sure.

Given uncertainty, better approach: the widget should render codes provided by the backend; in the demo/sample data I can include codes but mark them as examples. To be safe and accurate, I'll include a few well-known ones and note that codes come from the backend (SIGTAP). Actually, the safest: the widget displays whatever the backend sends (including `codigo_sigtap`, `codigo_ciap2`, `codigo_cid10`). The sample/seed data in the JS (for offline demo) can include a few codes with a comment that they're examples. I'll include commonly cited ones: Hemograma 40302011, Glicose jejum 40302063? Hmm... Let me just be careful: I'll include SIGTAP codes for a handful and add a comment "códigos SIGTAP de exemplo — validar contra a tabela vigente". That's honest.

CIAP-2 codes (well-known, I'm confident):
- A97? No. Common CIAP-2 codes:
  - R05? CIAP-2: "R05" = Tosse? Actually CIAP-2: R05 is "Tosse"? Let me recall CIAP-2 chapters: A (general), B (blood), C (cardiovascular), D (digestive), E (eye), F (ear), H (ENT), K (circulation), L (musculoskeletal), N (neurological), P (psychological), R (respiratory), S (skin), T (endocrine/metabolic), U (urinary), W (pregnancy), X (female genital), Y (male genital), Z (social).
  - R05 = Tosse (yes, R05 cough in CIAP-2).
  - R74 = Faringite aguda? R72 = "dor de garganta"? CIAP-2: R72 is "Dor de garganta"? Hmm: R71? Common: R74 "Infecção aguda das vias aéreas superiores"? Actually CIAP-2: R74 = "Infeção aguda das vias respiratórias superiores"? I recall R74 = "Upper respiratory infection". Yes, R74 is URI/IVAS. R05 = cough. R72 = "throat symptom"? Hmm, R72 = "Dor de garganta" I believe.
  - K74? K74 = "Angina pectoris"? CIAP-2: K74 = angina pectoris (yes). K75 = "Infarto agudo do miocárdio"? K75 = AMI? Actually K75 = "Infarto agudo do miocárdio" yes. K76 = "Outras doenças isquêmicas do coração"? K76 angina? Hmm: K74 = angina pectoris, K75 = acute myocardial infarction, K76 = other ischemic heart disease? I think K76 = "Other/ischemic heart disease"? Not fully sure. K77? K77 = "Insuficiência cardíaca"? Hmm, K77 = "Heart failure"? I believe K77 = insuficiência cardíaca congestiva. Yes, K77 = heart failure.
  - T90 = "Diabetes não-insulino-dependente"? CIAP-2: T90 = "Diabetes mellitus tipo 2"? Actually CIAP-2 T90 = "Diabetes não insulino-dependente" (DM2). T91 = "Diabetes insulino-dependente"? Hmm, T91 = DM1? I recall T91 = "Diabetes insulino-dependente". Yes.
  - U71 = "Cistite/Uso... "? U71 = "Cistite e outras infecções urinárias"? CIAP-2 U71 = "Cistite e outras infecções do trato urinário"? I think U71 = cystitis/UTI. Yes.
  - L03 = "Dor lombar"? CIAP-2 L03 = "Dor nas costas (lombalgia)"? L03 = "Back symptom/dor lombar". Yes.
  - P76 = "Depressão"? CIAP-2 P76 = "Depressão, transtorno depressivo". Yes.
  - A04? A04 = "Fraqueza geral/debilitação"? A04 = "General weakness". Yes.
  - R96 = "Dispneia"? CIAP-2 R96 = "Dispneia". Yes.
  - F93? F93 = "conjuntivite". Yes.
  - D93? D93 = "Dor abdominal"? D93 = "Abdominal pain". Yes.
  - N01? N01 = "Cefaleia"? N01 = "Headache". Yes.
  - S74? Hmm skip.

CID-10 codes (confident): J06.9 (IVAS), J03.9 (amigdalite aguda), E11 (DM2), I10 (hipertensão), N39.0 (ITU), M54.5 (lombalgia), J45 (asma), E66 (obesidade), I20 (angina), K29 (gastrite), R51? (cefaleia R51 — actually R51 cefaleia in CID-10), F32 (depressão), N30 (cistite), J20 (bronquite aguda), A09 (gastroenterite).

Dosages (SUS Rename usual): 
- Amoxicilina 500 mg VO 8/8h por 7 dias (faringite/otite) — but note penicillin allergy alert interplay! Good demo: if patient allergic to penicillin, the widget should flag incompatibility when suggesting amoxicilina. That's a nice safety feature: cross-check allergy vs medication class.
- Azitromicina 500 mg VO 1x/dia por 3 dias (alternative for penicillin allergy? For respiratory infections).
- Metformina 500 mg VO 12/12h (DM2) — contraindicated in severe renal impairment (eGFR <30) — nice interplay with risk "DRC".
- Losartana 50 mg VO 1x/dia (HAS).
- Hidroclorotiazida 25 mg VO 1x/dia.
- Enalapril 10 mg VO 12/12h.
- Paracetamol 500–750 mg VO 6/6h se dor/febre.
- Ibuprofeno — caution in DRC (NSAID nephrotoxicity) — good alert interplay.
- Nitrofurantoína 100 mg VO 8/8h por 5 dias (cistite) — avoid if eGFR <30? Actually nitrofurantoin avoided in CrCl <30 (some say <60 historically; current guidance <30). 
- Fosfomicina 3g VO dose única.
- AAS 100 mg? For secondary prevention.

I'll implement a small built-in knowledge base (KB) in the JS for offline/demo mode, but emphasize that production data comes from the backend API (which would be backed by SQLAlchemy models + Pydantic schemas). The KB entries include fields: `ciap2`, `cid10`, `exames` (with sigtap), `medicamentos` (with posologia, restrições, classe de risco), `soap` template.

**Allergy cross-check**: maintain list of patient allergies (from payload). Each medication has `classes_risco` (e.g., ["penicilinas", "AINS", "sulfas"]). If intersection with patient allergies → render alert and mark medication as contraindicated (do not include in SOAP fill, or include with warning). Also risk conditions: DRC → avoid AINS, metformina dose adjust; gestação → avoid certain drugs. Keep it simple: `contraindicacoes` list of condition tags.

**Blinking alerts**: `.copiloto-alerta` with severity levels: `critico` (red blink), `atencao` (amber blink), `info` (blue static). Respect `prefers-reduced-motion`.

**SOAP fill**: The main form fields IDs configurable via data attributes: `data-soap-subjetivo="#soap-subjetivo"` etc. Default IDs: `soap-subjetivo`, `soap-objetivo`, `soap-avaliacao`, `soap-plano`. On click: modal confirm listing what will be filled; if fields non-empty, warn about overwrite; then fill via `value` (for textarea/input) and dispatch `input`/`change` events so any framework listeners update. Also dispatch `window` CustomEvent `copiloto:soap-preenchido` with detail for audit hook (the app can POST to audit endpoint).

**Audit**: `POST /api/v1/consultas/{consulta_id}/copiloto/auditoria` with `{acao: "aceite_sugestao_soap", ...}` — fire-and-forget with `navigator.sendBeacon` fallback? Use fetch keepalive. Include timestamp, medico CNS? The backend knows the medic from session; frontend sends acao + hash of suggestion version. Keep simple.

**LGPD**: The widget handles sensitive health data. Notes: don't log PHI to console; avoid persisting in localStorage; clear on unload. I'll include a comment and behavior: no localStorage of PHI; `beforeunload` clears DOM.

**Connection**: 
- Config via `data-ws-url`, `data-api-base`, `data-consulta-id`, `data-csrf` (for POSTs), `data-poll-interval`.
- WebSocket message protocol: JSON `{tipo: "snapshot"|"alerta"|"sugestao"|"exames"|"medicamentos"|"status", dados: {...}}`. On connect, request snapshot. Heartbeat ping/pong every 25s. Reconnect with backoff (1s → 30s max, jitter).
- Fallback polling: GET `${apiBase}/consultas/${consultaId}/copiloto/snapshot`.

**Pydantic contract**: I'll document the schema