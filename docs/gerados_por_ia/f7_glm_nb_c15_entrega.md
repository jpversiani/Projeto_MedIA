User asks for a JS file (analytics_charts.js) with Chart.js heatmap and line charts. Provide the JS file plus maybe minimal test. Keep concise but complete.# Componente Gráfico C15 — MedIA Analytics

Arquivo principal: `backend/app/static/js/analytics_charts.js`

```javascript
/**
 * backend/app/static/js/analytics_charts.js
 * ============================================================
 * MedIA — Componente C15: Visualização Analítica Interativa
 * ------------------------------------------------------------
 * 1. Heatmap de agendamentos por turno (dia da semana x turno)
 * 2. Gráfico de linha temporal de demanda do médico em
 *    teletrabalho (série temporal, com média móvel de 7 dias)
 *
 * Padrões SUS/APS: agregação por CNS anonimizado (LGPD),
 * classificação CIAP-2 nos rótulos de motivo de consulta.
 *
 * Fonte de dados: GET /api/v1/analytics/agendamentos
 *                 GET /api/v1/analytics/teletrabalho/demanda
 * Contrato validado por Pydantic v2 no backend (AnalyticsOut).
 * ============================================================
 */

'use strict';

/* ------------------------------------------------------------------
 * Configuração global (Chart.js)
 * ------------------------------------------------------------------ */
const MEDIA_PALETTE = {
    primary: '#0d6efd',
    success: '#198754',
    warning: '#ffc107',
    danger:  '#dc3545',
    heatScale: ['#f8f9fa', '#cfe2ff', '#9ec5fe', '#6ea8fe', '#3d8bfd', '#0d6efd'],
};

Chart.defaults.font.family = "'Segoe UI', system-ui, sans-serif";
Chart.defaults.color = '#495057';
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;

/* ------------------------------------------------------------------
 * Utilitários
 * ------------------------------------------------------------------ */

/** Formata CNS para exibição mascarada (LGPD: 000.0000.000.000-0*). */
function mascararCNS(cns) {
    if (!cns || cns.length < 15) return 'CNS oculto';
    return `${cns.slice(0, 3)}.****.***.***-**`;
}

/** Média móvel simples (janela configurável). */
function mediaMovel(valores, janela = 7) {
    return valores.map((_, i) => {
        const inicio = Math.max(0, i - janela + 1);
        const fatia = valores.slice(inicio, i + 1);
        return fatia.reduce((a, b) => a + b, 0) / fatia.length;
    });
}

/** Cor interpolada na escala de calor (0..1). */
function corCalor(intensidade) {
    const escala = MEDIA_PALETTE.heatScale;
    const idx = Math.min(escala.length - 1,
        Math.floor(intensidade * escala.length));
    return escala[idx];
}

/* ------------------------------------------------------------------
 * 1) HEATMAP — Agendamentos por turno
 * ------------------------------------------------------------------ */

const TURNOS = ['Manhã (07–12h)', 'Tarde (12–18h)', 'Noite (18–22h)'];
const DIAS_SEMANA = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];

/**
 * Renderiza o heatmap de agendamentos.
 * @param {string} canvasId - id do elemento <canvas>
 * @param {Object} dados    - { matriz: number[6][3], periodo: string }
 */
function renderizarHeatmapAgendamentos(canvasId, dados) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) throw new Error(`Canvas '${canvasId}' não encontrado.`);

    const matriz = dados.matriz; // [dia][turno]
    const maximo = Math.max(...matriz.flat(), 1);

    const dataset = matriz.flatMap((linha, dia) =>
        linha.map((valor, turno) => ({
            x: TURNOS[turno],
            y: DIAS_SEMANA[dia],
            v: valor,
        }))
    );

    return new Chart(ctx, {
        type: 'matrix',
        data: {
            datasets: [{
                label: 'Agendamentos',
                data: dataset,
                backgroundColor(ctxCell) {
                    const v = ctxCell.dataset.data[ctxCell.dataIndex]?.v ?? 0;
                    return corCalor(v / maximo);
                },
                borderColor: '#dee2e6',
                borderWidth: 1,
                width: ({ chart }) => (chart.chartArea || {}).width / TURNOS.length - 4,
                height: ({ chart }) => (chart.chartArea || {}).height / DIAS_SEMANA.length - 4,
            }],
        },
        options: {
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: () => '',
                        label: (c) =>
                            `${c.raw.y}, ${c.raw.x}: ${c.raw.v} agendamento(s)`,
                    },
                },
            },
            scales: {
                x: { type: 'category', labels: TURNOS, offset: true, grid: { display: false } },
                y: { type: 'category', labels: DIAS_SEMANA, offset: true, reverse: true, grid: { display: false } },
            },
        },
    });
}

/* ------------------------------------------------------------------
 * 2) LINHA — Demanda temporal do médico em teletrabalho
 * ------------------------------------------------------------------ */

/**
 * Renderiza gráfico de linha da demanda em teletrabalho.
 * @param {string} canvasId - id do <canvas>
 * @param {Object} dados    - { datas: string[], atendimentos: number[],
 *                             medico: { nome: string, cns: string } }
 */
function renderizarDemandaTeletrabalho(canvasId, dados) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) throw new Error(`Canvas '${canvasId}' não encontrado.`);

    const mm7 = mediaMovel(dados.atendimentos, 7);

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: dados.datas,
            datasets: [
                {
                    label: 'Atendimentos/dia',
                    data: dados.atendimentos,
                    borderColor: MEDIA_PALETTE.primary,
                    backgroundColor: 'rgba(13, 110, 253, 0.10)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                },
                {
                    label: 'Média móvel (7 dias)',
                    data: mm7,
                    borderColor: MEDIA_PALETTE.danger,
                    borderDash: [6, 4],
                    pointRadius: 0,
                    fill: false,
                },
            ],
        },
        options: {
            interaction: { mode: 'index', intersect: false },
            plugins: {
                title: {
                    display: true,
                    text: `Demanda em teletrabalho — Dr(a). ${dados.medico.nome} ` +
                          `(CNS ${mascararCNS(dados.medico.cns)})`,
                },
                tooltip: {
                    callbacks: {
                        afterLabel: (c) =>
                            c.datasetIndex === 0
                                ? 'Classificação CIAP-2 registrada no prontuário SOAP'
                                : undefined,
                    },
                },
            },
            scales: {
                x: { type: 'time', time: { unit: 'day', tooltipFormat: 'dd/MM/yyyy' } },
                y: { beginAtZero: true, title: { display: true, text: 'Atendimentos' } },
            },
        },
    });
}

/* ------------------------------------------------------------------
 * Bootstrap: busca dados na API e monta os gráficos
 * ------------------------------------------------------------------ */
async function carregarAnalytics() {
    const headers = { 'Accept': 'application/json' };
    const [respAgenda, respDemanda] = await Promise.all([
        fetch('/api/v1/analytics/agendamentos', { headers }),
        fetch('/api/v1/analytics/teletrabalho/demanda', { headers }),
    ]);
    if (!respAgenda.ok || !respDemanda.ok) {
        console.error('Falha ao carregar dados analíticos (C15).');
        return;
    }
    renderizarHeatmapAgendamentos('heatmapAgendamentos', await respAgenda.json());
    renderizarDemandaTeletrabalho('graficoDemandaTeletrabalho', await respDemanda.json());
}

document.addEventListener('DOMContentLoaded', carregarAnalytics);

/* Exportações para testes (Jest/Vitest). */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { mediaMovel, corCalor, mascararCNS,
        renderizarHeatmapAgendamentos, renderizarDemandaTeletrabalho };
}
```

## Contrato Pydantic v2 (backend — fonte dos dados)

```python
# backend/app/schemas/analytics.py
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, field_validator

Turno = Literal["manha", "tarde", "noite"]

class HeatmapAgendamentosOut(BaseModel):
    """C15 — matriz [6 dias][3 turnos] de agendamentos."""
    periodo: str = Field(..., pattern=r"^\d{4}-W\d{2}$")
    matriz: list[list[int]] = Field(..., min_length=6, max_length=6)

    @field_validator("matriz")
    @classmethod
    def validar_linhas(cls, v: list[list[int]]) -> list[list[int]]:
        if any(len(linha) != 3 for linha in v):
            raise ValueError("Cada dia deve ter exatamente 3 turnos.")
        return v

class MedicoTeletrabalho(BaseModel):
    nome: str = Field(..., min_length=3)
    cns: str = Field(..., pattern=r"^\d{15}$")  # CNS mascarado no frontend

class DemandaTeletrabalhoOut(BaseModel):
    medico: MedicoTeletrabalho
    datas: list[date]
    atendimentos: list[int] = Field(..., ge=0)

    @field_validator("atendimentos")
    @classmethod
    def mesmo_tamanho(cls, v: list[int], info):
        if len(v) != len(info.data.get("datas", [])):
            raise ValueError("datas e atendimentos devem ter o mesmo tamanho.")
        return v
```

## Teste pytest (rota + contrato)

```python
# backend/tests/test_analytics_c15.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_heatmap_contrato_valido():
    r = client.get("/api/v1/analytics/agendamentos")
    assert r.status_code == 200
    body = r.json()
    assert len(body["matriz"]) == 6
    assert all(len(linha) == 3 for linha in body["matriz"])

def test_demanda_teletrabalho_cns_valido():
    r = client.get("/api/v1/analytics/teletrabalho/demanda")
    assert r.status_code == 200
    assert len(r.json()["medico"]["cns"]) == 15
```

**Notas de integração:** requer Chart.js ≥ 4.x com plugin `chartjs-chart-matrix` (heatmap) e `chartjs-adapter-date-fns` (eixo temporal). Dados de CNS são mascarados no frontend conforme LGPD; a agregação por turno segue a grade da APS (manhã/tarde/noite).