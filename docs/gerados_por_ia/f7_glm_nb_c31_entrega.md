The user is asking me to create a JavaScript file for charts (analytics_charts.js) for a healthcare project called "MedIA". The task is about creating a Line Chart and Interactive Heatmap component (C31) with Canvas/Chart.js rendering for:
1. Heatmap of appointments by shift (turno)
2. Temporal demand charts for doctors working remotely (teletrabalho)

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage.

However, the actual file requested is a JavaScript file: `backend/app/static/js/analytics_charts.js`. This is a frontend component. The Python guidelines seem to be general project guidelines, but the specific task is the JS file. However, since they mention test coverage with pytest, I should probably also consider how this JS would be tested — but pytest tests JS? That's odd. Maybe they want the JS file primarily, and possibly mention how it integrates. Let me think about what's most useful.

The task says: "crie backend/app/static/js/analytics_charts.js com renderização Canvas/Chart.js do mapa de calor de agendamentos por turno e gráficos temporais de demanda do médico em teletrabalho."

So the main deliverable is the JS file. But the guidelines say Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0, SUS/APS standards, and pytest test coverage. This is a bit contradictory — a JS file can't be typed with Pydantic. But I can:

1. Create the JS file with JSDoc typing (strict), Chart.js rendering, heatmap by shift, temporal line charts.
2. Possibly include the Pydantic schemas that define the API contract the JS consumes (to align with the architecture guidelines).
3. Include pytest tests that validate the JS contract (e.g., testing the endpoint that serves the data, or using a JS engine? More realistically, pytest tests for the API endpoints that feed the charts, plus maybe a test that validates the static file exists and contains expected functions).

Given the instruction "Execute com precisão conforme as diretrizes" — I should deliver the JS file as the primary artifact, and to satisfy the architecture guidelines, I can also provide:
- The Pydantic v2 schemas for the analytics data contract (e.g., `HeatmapCell`, `DemandSeriesPoint`, `AnalyticsResponse`).
- The SQLAlchemy 2.0 query (maybe a repository/service function) that produces the data.
- The FastAPI route serving the data.
- pytest tests covering the endpoint and the data contract.

But wait — the task specifically says to create the JS file. The guidelines are "arquitetura" guidelines for the project overall. The best response: focus on the JS file (complete, well-documented, strict JSDoc, Chart.js based, heatmap + line charts, accessibility, LGPD/SUS considerations like no patient-level data — only aggregated data), and then provide the supporting backend contract (Pydantic schemas + endpoint) and pytest tests to ensure full compliance.

Let me design the JS file:

**analytics_charts.js**

Features:
1. **Heatmap de agendamentos por turno**: A heatmap is not native in Chart.js; there's `chartjs-chart-matrix` plugin (matrix chart). I can either use the plugin (if available) or implement a custom Canvas heatmap renderer. To be robust, I could implement a fallback: if `chartjs-chart-matrix` is available, use it; otherwise render a custom canvas heatmap. Actually, to keep it dependency-light and precise, I could implement the heatmap with pure Canvas 2D API (custom renderer) — full control, no plugin dependency. But the task says "Canvas/Chart.js" — meaning either. I'll do: heatmap via custom Canvas renderer (or matrix plugin if present), line charts via Chart.js.

Actually, let me think about what's cleanest: Use Chart.js for line charts (temporal demand), and for the heatmap use `chartjs-chart-matrix` if registered, else a self-contained Canvas fallback. That's a lot of code but demonstrates precision. Alternatively, implement the heatmap entirely with a custom canvas renderer — deterministic, testable, no plugin. I'll implement a custom Canvas heatmap class with:
- Axes: days of week (or dates) on Y, shifts (manhã/tarde/noite — turns) on X, or vice versa. "Agendamentos por turno" — shifts: MANHA, TARDE, NOITE, maybe MADRUGADA. Rows = turnos, columns = dias (e.g., last N days or days of week).
- Color scale (e.g., sequential blues/greens), tooltips on hover, keyboard accessibility (aria), click to drill down maybe.
- Legend (colorbar).
- HiDPI support (devicePixelRatio).
- Redraw on resize (ResizeObserver).

2. **Gráfico temporal de demanda do médico em teletrabalho**: Line chart with Chart.js: series like "agendamentos", "faltas" (no-shows), "teleconsultas realizadas" over time (daily/weekly). Maybe two datasets: presencial vs teleconsulta, or demand vs capacity. Include:
- SUS/APS context: teleconsulta is part of Telessaúde (Programa Telessaúde Brasil). Data aggregated, no patient identifiers (LGPD).
- Tooltips formatted with pt-BR.
- Trend line maybe.

3. **Data contract**: The JS expects JSON from an endpoint like `/api/v1/analytics/teletrabalho/{medico_id}?periodo=...`. Contract mirrors Pydantic schemas:

```json
{
  "medico": {"id": ..., "nome": ..., "cns": null, "cpf_masked": "***.***.***-**"},
  "periodo": {"inicio": "2025-01-01", "fim": "2025-01-31"},
  "heatmap": {
    "colunas": ["2025-01-01", ...],  // datas
    "turnos": ["MANHA", "TARDE", "NOITE"],
    "celulas": [{"data": "...", "turno": "MANHA", "total": 12, "teleconsultas": 5, "faltas": 1}, ...]
  },
  "series_temporais": {
    "granularidade": "DIA",
    "pontos": [{"data": "2025-01-01", "agendamentos": 10, "teleconsultas": 6, "presenciais": 4, "faltas": 2, "taxa_ocupacao": 0.8}]
  },
  "kpis": {...}
}
```

4. **Strict typing in JS**: Use JSDoc with `@typedef`, and maybe `"use strict"`. Could also add `// @ts-check` for type checking. That aligns with "tipagem estrita" adapted to JS.

5. **Accessibility & i18n**: pt-BR labels, ARIA roles, `role="img"` with `aria-label`, keyboard navigation on heatmap cells (tabindex, arrow keys), tooltips.

6. **LGPD/SUS compliance**: Only aggregated, anonymized data; no CNS/CPF rendered in charts; mask identifiers. Add comment noting data minimization (art. 6º LGPD, Lei 13.709/2018) and that charts use aggregate counts (dados anonimizados/estatísticos, art. 12 LGPD — dados anonimizados não são dados pessoais). CNS/CPF never sent to frontend in analytics.

Now the backend support (to comply with guidelines):

**Pydantic v2 schemas** (`backend/app/schemas/analytics.py`):

```python
from __future__ import annotations
from datetime import date
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, field_validator

class Turno(StrEnum):
    MANHA = "MANHA"
    TARDE = "TARDE"
    NOITE = "NOITE"

class Granularidade(StrEnum):
    DIA = "DIA"
    SEMANA = "SEMANA"
    MES = "MES"

class CelulaHeatmap(BaseModel):
    model_config = ConfigDict(frozen=True)
    data: date
    turno: Turno
    total: int = Field(ge=0)
    teleconsultas: int = Field(ge=0)
    faltas: int = Field(ge=0)

    @field_validator("teleconsultas", "faltas")
    @classmethod
    def _validar_limites(cls, v, info): ...  # ensure <= total
```

Hmm, cross-field validation: use `model_validator(mode="after")`.

```python
class PontoSerieTemporal(BaseModel):
    data: date
    agendamentos: int = Field(ge=0)
    teleconsultas: int = Field(ge=0)
    presenciais: int = Field(ge=0)
    faltas: int = Field(ge=0)
    taxa_ocupacao: float = Field(ge=0.0, le=1.0)

class HeatmapAnalytics(BaseModel):
    colunas: list[date]
    turnos: list[Turno]
    celulas: list[CelulaHeatmap]

class SerieTemporalAnalytics(BaseModel):
    granularidade: Granularidade
    pontos: list[PontoSerieTemporal]

class MedicoAnalytics(BaseModel):
    id: int
    nome: str  # nome social/civil
    # CNS/CPF NUNCA expostos em analytics (minimização LGPD)
    uf: str | None = None
    unidade_saude: str | None = None

class RespostaAnalyticsTeletrabalho(BaseModel):
    medico: MedicoAnalytics
    periodo: PeriodoAnalytics
    heatmap: HeatmapAnalytics
    series_temporais: SerieTemporalAnalytics
    gerado_em: datetime
```

**SQLAlchemy 2.0 query** (`backend/app/repositories/analytics_repository.py` or service): aggregate query using `func.count`, `func.date(Agendamento.data_hora_inicio)`, grouped by date and turno. Use `select(...).where(...).group_by(...)` with 2.0 style. Models: `Agendamento` with fields: `id`, `medico_id`, `inicio` (DateTime), `turno` (maybe derived), `modalidade` (TELECONSULTA/PRESENCIAL), `status` (REALIZADO, FALTA, CANCELADO...). Derive turno from hour: MANHA 7-12, TARDE 12-18, NOITE 18-24 (or use stored enum). Use `case()` from SQLAlchemy.

**FastAPI endpoint** (`backend/app/api/v1/analytics.py`): GET `/analytics/teletrabalho/{medico_id}` with query params `data_inicio`, `data_fim`, `granularidade`. Auth via OAuth2 (medico or gestor). Returns `RespostaAnalyticsTeletrabalho`.

**pytest tests** (`backend/tests/...`): 
- Test schemas validation (Pydantic): invalid cells (teleconsultas > total), taxa_ocupacao bounds.
- Test endpoint with httpx AsyncClient/TestClient + SQLite: seed data, assert JSON contract matches what JS expects (keys, enums uppercase, dates ISO 8601).
- Test that no CNS/CPF appears in response payload (LGPD test) — nice touch: `assert "cns" not in payload`, `assert "cpf" not in payload`.
- Maybe a test that the static JS file exists and exposes the global init function (simple file-content smoke test) — a bit hacky but ensures the asset is wired. Could do: read file, assert `window.MedIAAnalytics` defined. That's a reasonable "contract" smoke test in pytest without a JS runtime. Or optionally use node if available — skip; keep pytest-only with a static contract test.

Given the response length constraints, I need to be judicious. The primary deliverable is the JS file — it should be complete and high quality. The backend contract + tests should be included but more concise. Let me aim for:

1. `analytics_charts.js` — full implementation (~350-450 lines with JSDoc).
2. `schemas/analytics.py` — Pydantic v2 contract (~80 lines).
3. Maybe a brief repository snippet (SQLAlchemy 2.0) — ~50 lines.
4. Endpoint snippet — ~40 lines.
5. pytest tests — ~120 lines.

That's a lot. The user asked specifically for the JS file; the guidelines are context. I think the ideal answer: deliver the JS file fully, plus the Pydantic contract (since "tipagem estrita com Pydantic v2" is a directive and the JS must match it), plus pytest tests (directive: "cobertura de testes automatizados com pytest"). The SQLAlchemy part can be summarized briefly or included compactly. Let me include a compact repository function to show the aggregation, since it defines turno derivation.

Let me now write the JS carefully.

**JS design:**

```js
/**
 * backend/app/static/js/analytics_charts.js
 * C31 — Componente Gráfico de Linha e Heatmap Interativo
 * ...
 */
"use strict"; // hmm, modules are strict by default; if loaded as classic script, "use strict" helps.

// @ts-check
```

Structure:

- Constants: `TURNOS = ["MANHA","TARDE","NOITE"]`, labels pt-BR, color palettes.
- `formatarDataISO(iso)` → `dd/mm/aaaa` (pt-BR).
- `escalaCores` — interpolate between colors for heatmap intensity (e.g., from light to dark teal). Implement lerp in RGB.
- `class HeatmapTurnos`:
  - constructor(canvas, options)
  - `render(dados)` where dados = {colunas: [...], turnos: [...], celulas: [...]}
  - builds matrix map keyed by `${data}|${turno}`
  - computes max value for scale
  - draws grid, labels, cells with rounded rects, values in cells if large enough
  - handles mousemove → tooltip (HTML div positioned), mouseleave hides
  - keyboard: make canvas focusable, arrow keys move selection, Enter triggers callback `onSelecionar`
  - HiDPI: canvas.width = cssWidth * dpr; ctx.scale(dpr, dpr)
  - ResizeObserver to re-render
  - destroy()
- `class GraficoDemandaTeletrabalho`:
  - wraps Chart.js line chart
  - datasets: Agendamentos (total), Teleconsultas, Presenciais, Faltas (dashed), maybe Taxa de ocupação on second axis (0-100%)
  - options: pt-BR locale tooltips, `interaction: {mode: 'index', intersect: false}`, responsive, maintainAspectRatio false, scales with `ticks.callback` formatting
  - `render(serie)` maps pontos → labels (formatted dates) and datasets
  - destroy()
- `inicializarAnalyticsTeletrabalho(config)`:
  - config: { urlApi, canvasHeatmapId, canvasLinhaId, containerTooltipId?, filtros?, onSelecionarCelula? }
  - fetch with `credentials: 'same-origin'`, headers Accept json; handle 401/403/404; parse JSON; validate minimal shape (defensive `validarPayload`); render both charts; return controller with `atualizar(filtros)` and `destruir()`.
- Export: `window.MedIAAnalytics = { HeatmapTurnos, GraficoDemandaTeletrabalho, inicializarAnalyticsTeletrabalho }` (UMD-ish guard for module systems).

Defensive validation function `validarPayload(payload)` throwing `ErroPayloadInvalido`.

Colors: SUS-ish palette — SUS uses blue (#0071BC-ish / #1351B4 gov.br blue). Use gov.br palette: blue #1351B4, and sequential scale for heatmap from #E8EEF7 to #1351B4. Faltas in red #D92B2F? gov.br red is #D5245E? Actually gov.br: red #E5223A / critical #D92B2F. Fine.

Accessibility: `aria-label` on canvases summarizing data; tooltip div with `role="status"` `aria-live="polite"`.

Let me write the heatmap renderer in detail:

```js
class HeatmapTurnos {
  #canvas; #ctx; #dados; #tooltip; #onSelecionar; #indiceAtivo = null; #observer;
  constructor(canvas, { tooltipEl = null, onSelecionar = null, paleta = PALETA_HEATMAP } = {}) {...}
  render(dados) {
    this.#dados = this.#normalizar(dados);
    this.#desenhar();
    this.#observarRedimensionamento();
  }
  #normalizar(dados) {
    // build Map chave "data|turno" -> celula; compute maximo
  }
  #desenhar() {
    const dpr = window.devicePixelRatio || 1;
    const { width, height } = canvas.getBoundingClientRect();
    canvas.width = Math.round(width*dpr); canvas.height = Math.round(height*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    // layout: margens, área do gráfico, células
    // eixos: colunas = datas (top or bottom), linhas = turnos (left)
    // desenhar células com cor = interpolar(paleta, valor/max)
    // texto do valor se célula >= 28px
    // destaque célula ativa (borda)
  }
  #corPara(valor, max) { lerp entre cores }
  #manipularMovimentoMouse(evt) { calcular célula sob cursor; tooltip }
  #manipularTeclado(evt) { setas movem #indiceAtivo; Enter/Space → onSelecionar(celula) }
  destruir() { observer.disconnect(); listeners off; }
}
```

Cell hit-testing: compute from mouse offset relative to canvas rect minus margins, divide by cell size.

Tooltip content: `12/01/2025 · Tarde — 14 agendamentos (9 teleconsultas, 2 faltas)`.

Line chart datasets:

```js
const ROTULOS_SERIES = {
  agendamentos: { rotulo: "Agendamentos", cor: "#1351B4" },
  teleconsultas: { rotulo: "Teleconsultas (teletrabalho)", cor: "#20877B" }, // teal
  presenciais: { rotulo: "Consultas presenciais", cor: "#C2872B"? } // amber
  faltas: { rotulo: "Faltas (no-show)", cor: "#D92B2F", dash: [6,4] },
  taxa_ocupacao: {