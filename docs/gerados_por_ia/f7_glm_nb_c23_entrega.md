The user is asking me to create a JavaScript file for the MedIA project (a healthcare system following Brazilian SUS/APS standards). The task is to create `backend/app/static/js/analytics_charts.js` with:

1. Canvas/Chart.js rendering of a heatmap of appointments by shift (turno)
2. Temporal demand charts for doctors working remotely (teletrabalho)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage. However, the actual file requested is a JavaScript file. The Python guidelines are architectural context — the JS file should consume API endpoints that presumably follow those patterns.

Let me think about what this file should contain:

1. **Heatmap of appointments by shift (turno)**: In Brazilian primary care (APS), shifts are typically manhã (morning), tarde (afternoon), noite (evening). Could also be by day of week × shift. A heatmap with days of week on one axis and shifts on another, showing appointment counts.

2. **Temporal demand charts for telework doctors**: Line charts showing demand over time (e.g., appointments per day/week) for doctors in teletrabalho (remote work), possibly comparing telehealth vs in-person.

Since Chart.js doesn't have a native heatmap, I'll need to implement one using a matrix approach — either with a custom Chart.js plugin/regression, or render on raw Canvas. A common approach is to use Chart.js with a custom plugin that draws colored rectangles, or use the `chartjs-chart-matrix` plugin. To avoid external dependencies beyond Chart.js, I could implement a custom heatmap renderer on Canvas directly, or write a Chart.js plugin inline.

Best approach: Write a self-contained module that:
- Uses Chart.js (loaded via CDN or bundled) for line/bar charts
- Implements a custom heatmap via Canvas 2D API (or a Chart.js plugin using a matrix controller)

I should make it robust:
- Fetch data from API endpoints (e.g., `/api/v1/analytics/agendamentos-turno`, `/api/v1/analytics/demanda-teletrabalho`)
- Handle LGPD considerations (aggregate data only, no patient identifiers — important for SUS compliance)
- Handle CNS/CPF masking if any identifiers appear (though analytics should be aggregated)
- Accessibility (ARIA, colorblind-friendly palettes)
- Responsive design with devicePixelRatio handling
- Error handling, loading states
- i18n in pt-BR (dates, month names)
- Export functionality maybe (PNG download)

Also, since the guidelines mention pytest coverage, I should probably also provide a minimal test file? The task says "Manter conformidade total e cobertura de testes automatizados com pytest." The main deliverable is the JS file. But to honor the guidelines, I could include a pytest test that verifies the static file is served and contains expected functions, and maybe a fixture endpoint. Let me include:

1. `backend/app/static/js/analytics_charts.js` — the main deliverable
2. A brief pytest test file `backend/tests/test_analytics_charts_static.py` that validates the static asset exists, is served, and has key functions (smoke test via regex/JS parsing is hacky but common for static assets). Also maybe test the API contract the JS expects (schema validation with Pydantic).

Actually, the instruction says "Execute com precisão conforme as diretrizes" — the guidelines are architecture directives for the project. The primary deliverable is the JS file. I'll focus on that, and add a compact pytest to satisfy the testing guideline, plus maybe a small Pydantic schema snippet showing the API contract the JS consumes. But I shouldn't over-scope. Let me deliver:

1. The main JS file (comprehensive, well-commented in Portuguese since it's a Brazilian SUS project)
2. A pytest test file for the static asset + API contract
3. Brief notes on integration

Let me design the JS module:

```javascript
/**
 * analytics_charts.js — MedIA | Componentes gráficos (C23)
 * ...
 */
```

Structure:
- IIFE or ES module? Use an ES module pattern but also attach to window for compatibility. Actually, since it's served as static JS, an IIFE with a global namespace `MedIACharts` is safest, or a proper ES module. I'll use an IIFE exposing `window.MedIACharts` with `init`, `renderHeatmapTurnos`, `renderDemandaTeletrabalho`, etc.

Key features:

**Heatmap (Mapa de calor de agendamentos por turno):**
- Grid: linhas = dias da semana (seg–dom) or períodos; colunas = turnos (Manhã 07–12, Tarde 12–18, Noite 18–22) — maybe also by hour? Let's do dias da semana × turnos, with cell values = número de agendamentos. Optionally sub-breakdown by modalidade (presencial vs teleconsulta).
- Custom Canvas rendering with:
  - Color scale (sequential, colorblind-safe — e.g., viridis-like or a blue scale)
  - Tooltips on hover
  - Axis labels
  - Legend (gradient bar)
  - devicePixelRatio scaling
  - Keyboard accessibility (cells focusable? At least an accessible table alternative — generate a hidden `<table>` or aria-label summary)
- Data contract from API:
```json
{
  "periodo": {"inicio": "2025-01-01", "fim": "2025-01-31"},
  "celulas": [
    {"dia_semana": 1, "turno": "MANHA", "total": 42, "teleconsulta": 12, "presencial": 30}
  ]
}
```

**Temporal demand chart (Demanda do médico em teletrabalho):**
- Line chart with Chart.js: eixo X = datas (dias ou semanas), séries = agendamentos teleconsulta, presencial (para comparar), taxa de absenteísmo maybe, or "fila de espera". Also maybe a second axis for occupancy rate (%).
- Data contract:
```json
{
  "medico": {"cns": "***.***.***.**-**" masked? No — analytics aggregated; maybe medico_id and nome},
  "granularidade": "DIA" | "SEMANA" | "MES",
  "serie": [
    {"data": "2025-01-01", "teleconsulta": 8, "presencial": 20, "absenteismo_pct": 12.5}
  ]
}
```

- Include CIAP-2/CID-10 top motives? Could add a horizontal bar chart of top CIAP-2 chapters for teleconsultas — that ties into SUS standards. Maybe as an optional third chart. The task says "gráficos temporais de demanda do médico em teletrabalho" — plural "gráficos", so a main line chart + maybe a stacked area or bar. I'll include:
  - Line chart: volume de atendimentos (teleconsulta vs presencial) ao longo do tempo, com média móvel de 7 dias.
  - Optional bar overlay: absenteísmo %.
  - Maybe a small multiple for CIAP-2 top reasons over time? Keep it focused: main line chart + heatmap + optional CIAP-2 bar.

Let me keep scope tight but complete: 
1. `renderHeatmapTurnos(canvas, dados)` — custom Canvas heatmap
2. `renderDemandaTeletrabalho(canvas, dados)` — Chart.js line/stacked
3. `renderTopMotivosCIAP(canvas, dados)` — Chart.js horizontal bar (bonus, ties CIAP-2)
4. `initAnalyticsDashboard(config)` — orchestrator: fetches from endpoints, renders, handles refresh, exports PNG, prints.

Also utilities:
- `formatarDataBR`, `formatarNumero` (Intl pt-BR)
- Color scales with colorblind-safe palettes
- Debounce for resize
- LGPD: ensure no patient-level data; add a note; mask CNS if ever present (function `mascararCNS`).

Chart.js loading: assume global `Chart` available (loaded via CDN/base template). Guard if not loaded — fallback message. For heatmap, pure Canvas so no dependency.

Accessibility: 
- `role="img"` + `aria-label` summarizing data
- Provide data table alternative (visually hidden) for heatmap
- Focusable cells with keyboard navigation? That's a lot; I'll implement hover tooltip + aria-label summary + hidden table. Maybe keyboard: arrow keys move a "focused cell" highlight. I can implement basic keyboard nav — it adds value and shows care. Let me implement a simple version: canvas tabindex=0, arrow keys move selection, Enter/tooltip shows value, Escape clears. Good.

Tooltips: custom div tooltip positioned near cursor.

Color scale: implement a small interpolation between color stops (e.g., viridis approximation or a blue→teal scale). I'll implement viridis-ish stops for colorblind safety.

Export: `exportarPNG(canvas, nomeArquivo)`.

Resize: ResizeObserver on container, re-render with debounce.

API endpoints (following a plausible MedIA API v1):
- `GET /api/v1/analytics/agendamentos-por-turno?ues_id=&inicio=&fim=` (UES = Unidade de Saúde — APS terminology: UBS/ESF)
- `GET /api/v1/analytics/demanda-teletrabalho?medico_id=&inicio=&fim=&granularidade=`
- `GET /api/v1/analytics/top-motivos-ciap2?...`

Include `credentials: 'same-origin'`, handle 401/403 (redirect to login?), 422, 5xx with friendly messages in pt-BR.

Also CSRF? Typically cookie-based session; include `X-Requested-With` maybe. Keep simple.

Now the pytest file: test that:
- Static file exists and is served at `/static/js/analytics_charts.js` (using httpx/TestClient with the app; but to keep it decoupled, test file presence + content markers, and optionally TestClient if app importable). I'll write tests that:
  1. File exists and contains required functions (regex).
  2. If app is importable, TestClient GET returns 200 with correct content-type.
  3. Pydantic schemas for the analytics contracts validate sample payloads (define schemas in the test or reference `app.schemas.analytics`). Better: define the contract schemas in test to validate sample JSON — but ideally they exist in the app. I'll write the test to import `app.schemas.analytics` schemas if available, else skip. Hmm, to be safe and self-contained, I'll define minimal Pydantic models in the test file mirroring the contract and validate the sample fixtures embedded in the JS docstring? That's odd. 

Better approach: provide the pytest file that tests the static asset serving + a contract test using Pydantic models defined in `backend/app/schemas/analytics.py`... but I'm not asked to create that file. Creating it might be over-scope but it makes the deliverable coherent: the JS consumes an API; providing the Pydantic schema ensures "tipagem estrita com Pydantic v2". The guidelines explicitly mention Pydantic v2 and pytest. I think a compact `schemas/analytics.py` addition + tests would fully satisfy "conformidade com as diretrizes". But the task says "crie backend/app/static/js/analytics_charts.js" — one file. The guidelines are context. I'll deliver the JS as the core, plus a pytest test file (since cobertura de testes is explicitly required) that validates the static asset and the data contract with Pydantic v2 models defined inline in the test (self-contained, no need to modify app code). That keeps scope reasonable while honoring guidelines.

Actually, let me reconsider: including a small Pydantic schema in the test file that mirrors the API contract is a legit "contract test" pattern. I'll do that.

Let me now write the JS carefully.

```javascript
/* =============================================================================
 * MedIA — analytics_charts.js (C23)
 * -----------------------------------------------------------------------------
 * Componentes gráficos do painel de analítica da APS (SUS):
 *   1) Mapa de calor de agendamentos por turno (Canvas 2D puro, sem plugins);
 *   2) Séries temporais de demanda do médico em teletrabalho (Chart.js);
 *   3) Top motivos de consulta (CIAP-2) em teleconsulta (Chart.js, opcional).
 *
 * Conformidade:
 *   - Dados estritamente AGREGADOS (LGPD art. 12, V — dados anonimizados);
 *     nenhuma função deste módulo renderiza CNS/CPF ou identificadores diretos.
 *   - Terminologia APS: UBS/ESF, turnos (Manhã/Tarde/Noite), CIAP-2.
 * ...
 */
```

Design decisions:

- Namespace: `window.MedIACharts` via IIFE, `'use strict'`.
- Config defaults with endpoints.
- `Chart` may be loaded globally; if missing, line charts show fallback message; heatmap still works (pure canvas).

Heatmap implementation details:

Data in: `celulas: [{dia_semana: 0..6 (0=domingo? or 1=segunda?)}, ...]`. I'll define ISO-like: 1=segunda ... 7=domingo (ISO-8601, common in health analytics). Turnos: `MANHA`, `TARDE`, `NOITE` (+ optional `MADRUGADA`? APS usually manhã/tarde/noite for UBS; some 24h UPE... keep three + allow extra). I'll map labels: MANHA→'Manhã (07–12h)', TARDE→'Tarde (12–18h)', NOITE→'Noite (18–22h)'. Make labels configurable.

Rendering:
- Compute margins for axes; draw title? Title handled by HTML heading; canvas draws axes + cells + values (optional show values when cell large enough).
- Color scale: normalize value 0..max; if max==0, all zero-color. Use viridis-like stops. Zero cells: very light gray to distinguish "sem dado" vs zero? Use distinct hatch for "sem registro" (null) vs 0. I'll support `null` = sem dado (hatched), 0 = zero (lightest color).
- Legend: gradient bar with min/max labels drawn on canvas right side or separate small canvas. I'll draw legend inside canvas right margin.
- Tooltip: absolutely positioned div; on mousemove compute cell from coords; show "Segunda-feira • Manhã (07–12h): 42 agendamentos (12 teleconsulta, 30 presencial)".
- Keyboard: tabindex=0, arrows move cell selection, draw focus outline, aria-live region updates with cell description.
- Hidden data table for screen readers: build `<table class="visually-hidden">` next to canvas.
- devicePixelRatio scaling: canvas.width = cssW * dpr; ctx.setTransform(dpr,0,0,dpr,0,0).
- Resize: ResizeObserver → re-render.

Line chart (Chart.js):
- Type 'line', datasets: Teleconsulta (fill area), Presencial (line), plus dashed "média móvel 7 dias" for total? Keep: teleconsulta, presencial, and optional absenteísmo on y1 axis (percent, dashed).
- Options: pt-BR date adapter — Chart.js time scale needs an adapter (chartjs-adapter-date-fns or luxon). To avoid extra deps, I'll use category axis with pre-formatted labels (dd/mm) — safer for zero-dependency. Yes: use `labels` as formatted strings from ISO dates. Good — avoids adapter dependency.
- Tooltips: custom callbacks pt-BR.
- Stacked? No — two lines + bar? I'll do: line teleconsulta (filled), line presencial, and optional bar for absenteísmo on second axis via mixed chart. Mixed chart type: `type:'bar'` base with line datasets — Chart.js supports `type: 'bar'` with datasets having `type:'line'`. I'll implement: base bar (absenteísmo, y1) + two lines (y). Configurable.
- Also "capacidade" reference line? Could add `anotacoes` but plugin dependency — skip; instead allow optional `limite` drawn via a simple plugin inline (small custom plugin to draw horizontal threshold). I can write a tiny inline plugin `limiteReferencia` — nice touch, no dependency.

CIAP-2 chart: horizontal bar of top N capítulos CIAP-2 (e.g., 'K — Circulatório', 'R — Respiratório'...). Provide a map of CIAP-2 chapter codes to pt-BR names (the 17 chapters: A General, B Blood, C Digestive, D Eye, E Ear, F Cardiovascular, G Musculoskeletal? wait — actual CIAP-2 chapters: A General/unclassified, B Blood/blood forming, C Digestive, D Eye, E Ear, F Cardiovascular, G Musculoskeletal, H Neurological, K Respiratory? Let me recall correctly: CIAP-2 chapters:
- A — General, unspecified
- B — Blood, blood-forming organs, lymphatics
- C — Digestive
- D — Eye
- E — Ear
- F — Cardiovascular
- G — Musculoskeletal
- H — Neurological
- K — Respiratory
- L — Skin
- N — Urological
- P — Psychological
- R — Pregnancy, childbearing, family planning
- S — Social
- T — Endocrine, metabolic, nutritional
- U — Urological? no wait.

Correct CIAP-2 chapters (WONCA):
A General, unspecified
B Blood, blood-forming organs and immune mechanism
C Digestive
D Eye
E Ear
F Cardiovascular
G Musculoskeletal
H Neurological
K Respiratory
L Skin
N Urological
P Psychological
R Pregnancy, childbearing, family planning
S Social problems
T Endocrine, metabolic and nutritional
U Urological? No — U is Urinary? Let me be careful: N is Female genital? Hmm.

Actual CIAP-2:
- A: General, unspecified
- B: Blood, blood-forming organs, lymphatic system and immune mechanism
- C: Digestive
- D: Eye and adnexa
- E: Ear and mastoid process
- F: Cardiovascular
- G: Musculoskeletal (excluding spine?) — actually "Musculoskeletal"
- H: Neurological
- K: Respiratory
- L: Skin and subcutaneous tissue
- N: Female genital system and breast? Hmm no.

Let me recall the standard list (17 chapters, letters A–U excluding some):
A, B, C, D, E, F, G, H, K, L