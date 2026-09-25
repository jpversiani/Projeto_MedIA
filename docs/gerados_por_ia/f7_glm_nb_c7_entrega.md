The user is asking me to create a JavaScript file for the MedIA project (a healthcare system following Brazilian SUS/APS standards). The task is:

1. Create `backend/app/static/js/analytics_charts.js` with:
   - Canvas/Chart.js rendering of a heatmap of appointments by shift (turno)
   - Temporal demand charts for doctors working remotely (teletrabalho)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

Since this is a JavaScript file task, but the guidelines mention Python backend standards, I should:
1. Create the main JavaScript file `analytics_charts.js` with Chart.js rendering
2. Possibly provide supporting backend context (Pydantic schemas for the data contract, maybe a pytest test for the JS or the API endpoint that feeds it)

Let me think about what a comprehensive, high-quality response looks like:

**Main deliverable: `backend/app/static/js/analytics_charts.js`**

Features needed:
1. **Heatmap of appointments by shift (turno)**: In Brazilian healthcare, shifts are typically Manhã (morning), Tarde (afternoon), Noite (night) — or more granular. The heatmap could be: days of week (or dates) × shifts, with color intensity = number of appointments. Chart.js doesn't have a native heatmap, but there's `chartjs-chart-matrix` plugin. Alternatively, I can render a custom Canvas heatmap. The task says "Canvas/Chart.js" so I can do both: use Chart.js for temporal charts and a custom Canvas-based heatmap (or use chartjs-chart-matrix if available with fallback).

2. **Temporal demand charts for doctors in teletrabalho (remote work)**: Line/bar charts showing appointment demand over time (e.g., daily/weekly), possibly filtered by modality (presencial vs teleconsulta). Could include CIAP-2 top reasons or CID-10 breakdown.

Design considerations:
- Accessibility (WCAG) — SUS systems need accessibility
- LGPD compliance — no patient-level data in charts, only aggregated/anonymized data
- CNS/CPF should never be displayed in charts
- I18n pt-BR formatting (dates, numbers)
- Theme support (light/dark)
- Responsive canvas with devicePixelRatio handling
- No patient identifiers; aggregate data only

Data contract: I should define the expected JSON payload. Since the guidelines mention Pydantic v2, I can also provide the Pydantic schema that produces this JSON (e.g., `AnalyticsChartsPayload`), and a pytest test. The task says "Execute com precisão conforme as diretrizes" — the guidelines include Python typing, Pydantic, SQLAlchemy, pytest. But the primary task is the JS file. I'll deliver:

1. `backend/app/static/js/analytics_charts.js` — the main file (comprehensive, well-documented)
2. `backend/app/schemas/analytics.py` — Pydantic v2 schema defining the data contract (strict typing)
3. `backend/app/api/routes/analytics.py` — maybe a minimal FastAPI endpoint serving the payload (SQLAlchemy 2.0 style query) — this could be long; maybe keep it focused
4. `backend/tests/test_analytics_charts.py` — pytest tests (for the endpoint/schema; JS testing would need node/jest — I can include a lightweight Node test for the pure functions if the JS is structured to be importable, or use pytest to test the endpoint that feeds the charts)

Given the response length constraints, I should prioritize:
- The JS file (main deliverable) — thorough
- The Pydantic schema (data contract) — important for "tipagem estrita com Pydantic v2"
- A pytest test file — required by guidelines ("cobertura de testes automatizados com pytest")
- Maybe a brief SQLAlchemy 2.0 query example within the route

Let me design the data contract:

```json
{
  "meta": {
    "generated_at": "2025-01-15T10:30:00-03:00",
    "period_start": "2025-01-01",
    "period_end": "2025-01-31",
    "ubs": "UBS Jardim das Flores",
    "ine_code": "1234567",
    "aggregated": true,
    "min_cell_size": 5  // k-anonymity threshold
  },
  "heatmap": {
    "shifts": ["manha", "tarde", "noite", "madrugada"],
    "days": ["2025-01-01", ...],  // or weekdays
    "matrix": [[12, 8, ...], ...],  // shifts × days
    "unit": "agendamentos"
  },
  "teletrabalho": {
    "series": [
      {
        "medico_id": "...",  // pseudonymized
        "medico_rotulo": "Dr. A (CRM ***1234)",
        "modalidade": "teleconsulta",
        "pontos": [{"data": "2025-01-01", "agendamentos": 12, "realizados": 10, "faltas": 2}]
      }
    ],
    "linha_media_movel": 7
  },
  "ciap_top": [{"codigo": "R05", "descricao": "Tosse", "total": 34}],
  "cid10_top": [...]
}
```

Actually, let me keep it focused: heatmap by shift + temporal demand for teletrabalho doctors. CIAP-2/CID-10 could be a bonus (top reasons chart) — the guidelines mention CIAP-2/CID-10 standards, so including a top-motivos chart with CIAP-2 codes would show compliance. But I shouldn't over-engineer. Let me include:

1. Heatmap: agendamentos por turno (rows = turnos: Manhã/Tarde/Noite; columns = dias da semana or dates)
2. Line chart: demanda temporal dos médicos em teletrabalho (agendamentos vs realizados, teleconsulta vs presencial comparison)
3. Optional: bar chart of top CIAP-2 reasons in teleconsultas (shows SUS/APS compliance)

For the heatmap, I'll implement a custom Canvas renderer (no external plugin dependency) with:
- devicePixelRatio scaling
- Color scale (sequential, colorblind-safe — viridis-like or a blue scale)
- Tooltips
- Keyboard accessibility (aria labels, focusable cells via a summary table fallback)
- Fallback: if Chart.js matrix plugin not available, custom canvas

Actually, to keep it robust, I'll write a self-contained heatmap renderer on raw Canvas 2D, and use Chart.js (if loaded) for the line/bar charts, with a graceful fallback to Canvas if Chart.js is missing. That satisfies "Canvas/Chart.js".

Key JS architecture:
- IIFE or ES module? For Django/FastAPI static serving, a plain script with a global namespace `MedIAAnalytics` is safest. I'll use an IIFE with strict mode, exposing `window.MedIAAnalytics = { renderHeatmap, renderDemandChart, renderAll }`.
- Pure functions separated for testability (e.g., `buildColorScale`, `aggregateByWeek`, `formatPtBrDate`, `movingAverage`) — these can be unit-tested with Node if exported. I can add a UMD-ish export: if `typeof module !== 'undefined'` export for Node tests. That enables pytest? No — pytest is Python. For JS testing, I could write tests with Node's built-in `node:test` runner and run via a subprocess in pytest, or just provide a separate JS test file. The guidelines say pytest coverage — I'll write pytest tests for the backend endpoint/schema, and optionally a pytest test that runs Node tests via subprocess (marked skipif node not available). That's a nice touch showing full-stack test coverage.

Let me now write the code.

**File 1: `backend/app/static/js/analytics_charts.js`**

Structure:
```js
/**
 * MedIA — Analytics Charts (C7)
 * Heatmap de agendamentos por turno + demanda temporal (teletrabalho)
 * Conformidade: LGPD (dados agregados, k-anonimato), Acessibilidade WCAG 2.1 AA,
 * SUS/APS (CIAP-2, CID-10), pt-BR.
 */
(function (global) {
  'use strict';

  // ---------- Constantes de domínio (SUS/APS) ----------
  const TURNOS = Object.freeze([
    { id: 'madrugada', rotulo: 'Madrugada (00–06)', faixa: [0, 6) },
    { id: 'manha', rotulo: 'Manhã (07–12)' },
    { id: 'tarde', rotulo: 'Tarde (13–18)' },
    { id: 'noite', rotulo: 'Noite (19–23)' },
  ]);

  const MODALIDADES = Object.freeze({
    PRESENCIAL: 'presencial',
    TELECONSULTA: 'teleconsulta',
  });

  // paleta colorblind-safe
  ...
  
  // ---------- Utilidades puras (testáveis) ----------
  function parseISODate(s) {...}
  function formatPtBrDate(iso) {...}
  function movingAverage(values, window) {...}
  function buildSequentialScale(min, max) {...} // returns fn(v) -> [r,g,b]
  function contrastText(rgb) {...} // luminance for accessible text
  function toISOWeek / weekdayLabel ...
  
  // ---------- Heatmap (Canvas puro) ----------
  function renderHeatmap(canvasId, payload, opts) {...}
  
  // ---------- Demanda temporal (Chart.js com fallback Canvas) ----------
  function renderDemandChart(canvasId, payload, opts) {...}
  
  // ---------- Top motivos CIAP-2 (barra) ----------
  function renderTopCiap(canvasId, payload, opts) {...}
  
  // ---------- Orquestração ----------
  function renderAll(config) {...}
  
  // Export UMD-ish
  const api = { renderAll, renderHeatmap, renderDemandChart, renderTopCiap, utils: {...} };
  global.MedIAAnalytics = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
```

Heatmap details:
- Data: `payload.heatmap = { turnos: [{id, rotulo}], dias: ['2025-01-06', ...], matriz: number[][] }` where matriz[turnoIdx][diaIdx]
- Render: margins, axis labels (weekdays pt-BR), cells with rounded rects, color scale, value text if cell large enough and contrast ok, weekend shading, tooltip on hover (custom div), highlight max cell
- Accessibility: canvas gets `role="img"` and `aria-label` summary; also generate an offscreen `<table>` for screen readers (or a visually-hidden table). I'll generate a sr-only table.
- k-anonymity: values below `meta.min_celula` (e.g., <5) shown as aggregated/suppressed? Actually k-anonymity is about not publishing cells with small counts that could identify patients. I'll render cells with value < min as "n/a" hatched or just show the value but the backend should already suppress. I'll respect a `suprimido` flag: if backend sends `null` for suppressed cells, render hatched "s". Good LGPD touch.

Demand chart details:
- Chart.js line chart: x = dates, datasets: teleconsulta (agendados), teleconsulta (realizados), presencial (for comparison), moving average line
- If Chart.js undefined → fallback: simple canvas line renderer (I'll implement a minimal one to guarantee "Canvas" rendering works standalone)
- Options: pt-BR locale for tooltips/axes, responsive, maintainAspectRatio false, accessible fallback table

CIAP-2 bar chart: horizontal bars of top N reasons with code + description.

Also handle `prefers-reduced-motion` (disable animations).

Theme: read CSS custom properties for colors with fallbacks.

**File 2: `backend/app/schemas/analytics.py`** (Pydantic v2, strict typing)

```python
from __future__ import annotations
from datetime import date, datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import numpy as np?  # no, keep stdlib

class Turno(StrEnum):
    MADRUGADA = "madrugada"
    MANHA = "manha"
    TARDE = "tarde"
    NOITE = "noite"

class Modalidade(StrEnum):
    PRESENCIAL = "presencial"
    TELECONSULTA = "teleconsulta"

class HeatmapMeta(BaseModel): ...
class CelulaHeatmap(BaseModel):
    total: int | None  # None => suprimido (k-anonimato)
class HeatmapPayload(BaseModel):
    turnos: list[Turno]
    dias: list[date]
    matriz: list[list[int | None]]
    # validators: dims consistentes
class PontoSerie(BaseModel):
    data: date
    agendados: int
    realizados: int
    faltas: int = 0  # or computed
class SerieMedico(BaseModel):
    medico_pseudonimo: str  # LGPD: sem CPF/CNS
    modalidade: Modalidade
    pontos: list[PontoSerie]
class MotivoCiap(BaseModel):
    codigo_ciap2: str = Field(pattern=r"^[A-Z]\d{2}$")  # CIAP-2: letra + 2 dígitos
    descricao: str
    total: int = Field(ge=1)
class AnalyticsChartsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", ...)
    meta: MetaPayload
    heatmap: HeatmapPayload
    teletrabalho: list[SerieMedico]
    ciap2_top: list[MotivoCiap] = []
    @model_validator: matriz dims == len(turnos) x len(dias)
```

CIAP-2 codes: format is letter + 2 digits (e.g., R05, A01... actually CIAP-2 codes like "A01", "R05", "K29", "L03"). Pattern `^[A-Z]\d{2}$` works.

**File 3: `backend/app/api/routes/analytics.py`** — FastAPI router with SQLAlchemy 2.0 style query (select + func.count, group by). Keep it reasonably compact. Include LGPD note: aggregation with k-anonymity (HAVING count >= k). Use `func.count().label(...)`, `having()`. Pseudonymize doctor via hash of CRM (e.g., sha256 truncated) — or store pseudonym. I'll show hashing with hmac + salt from settings.

Actually, to control response length, maybe I merge the route into a compact version. The task's core is the JS file; the Python parts demonstrate compliance with the architecture guidelines. I'll include:

- schemas/analytics.py (full)
- api/routes/analytics.py (compact but complete: endpoint `/api/analytics/charts` with SQLAlchemy 2.0 query, k-anonymity, pseudonymization)
- tests/test_analytics_charts.py (pytest: schema validation tests + endpoint test with httpx/TestClient + in-memory SQLite; plus optional Node subprocess test for JS pure functions)

Hmm, that's a lot. Let me budget: JS file ~350-450 lines, schema ~120 lines, route ~120 lines, tests ~150 lines. That's a big response but the task explicitly demands full-stack compliance. I'll aim for completeness but keep each part tight. Maybe I can trim the route to essentials and make tests focused.

Actually, let me reconsider: the primary deliverable is the JS file. The guidelines are "arquitetura" directives. A good response: deliver the JS file fully, plus the Pydantic contract (essential so the JS knows the payload shape), plus pytest tests. The SQLAlchemy route can be included briefly since "SQLAlchemy 2.0" is mentioned. I'll include a compact route.

Let me write the JS carefully.

```js
/* eslint-env browser */
/**
 * ============================================================================
 *  MedIA · C7 — Componentes Gráficos Analíticos
 *  backend/app/static/js/analytics_charts.js
 * ============================================================================
 *  Renderização (Canvas 2D / Chart.js v4) de:
 *    1. Mapa de calor — agendamentos por turno (Madrugada/Manhã/Tarde/Noite);
 *    2. Série temporal — demanda de médicos em teletrabalho (teleconsulta);
 *    3. Barras — motivos de atendimento mais frequentes (CIAP-2 / CID-10).
 *
 *  Conformidade:
 *    · LGPD/Lei 14.129 — somente dados AGREGADOS; células com n < k
 *      (k-anonimato, default 5) chegam suprimidas (null) e são sinalizadas;
 *    · Nenhum dado identificador (CNS/CPF/CRM completo) é renderizado;
 *    · WCAG 2.1 AA — tabela oculta equivalente, contraste ≥ 4.5:1,
 *      suporte a prefers-reduced-motion e navegação por teclado;
 *    · SUS/APS — rótulos pt-BR, códigos CIAP-2 e CID-10 preservados.
 *
 *  Contrato de dados: backend/app/schemas/analytics.py (Pydantic v2).
 *  Dependência opcional: Chart.js v4 (fallback 100% Canvas se ausente).
 * ============================================================================
 */
```

Then the IIFE. Let me write the pure utils:

```js
const K_ANONIMATO_DEFAULT = 5;

const TURNOS_ORDEM = Object.freeze(['madrugada', 'manha', 'tarde', 'noite']);

const ROTULOS_TURNO = Object.freeze({
  madrugada: 'Madrugada (00h–06h)',
  manha: 'Manhã (07h–12h)',
  tarde: 'Tarde (13h–18h)',
  noite: 'Noite (19h–23h)',
});

const DIAS_SEMANA_PTBR = Object.freeze(['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb']);
```

Utils:
- `parseISO(iso)` → Date (UTC-safe: new Date(iso + 'T00:00:00Z')? For date-only strings, parse manually to avoid TZ issues: split('-')).
- `formatarDataPtBR(iso)` → '06/01'
- `rotuloDiaSemana(iso)` → 'seg 06/01'
- `mediaMovel(valores, janela)` → array with