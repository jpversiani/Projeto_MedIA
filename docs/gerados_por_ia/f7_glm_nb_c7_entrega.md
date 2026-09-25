 # Componente Gráfico C7 — `analytics_charts.js`

Criação do arquivo de produção em `backend/app/static/js/analytics_charts.js`, conforme as diretrizes do Projeto MedIA (atendimento particular/convênios, TISS ANS 4.01 / DMED; sem integrações SUS/SISAB ou IoT).

```javascript
/**
 * MedIA — Componente Gráfico C7 (analytics_charts.js)
 * ---------------------------------------------------------------------------
 * Renderização Canvas/Chart.js para o módulo de Analytics do médico em
 * teletrabalho:
 *
 *   1. Heatmap de agendamentos por turno (manhã / tarde / noite) x dia da
 *      semana — desenhado em Canvas 2D puro (sem dependência de plugin
 *      externo de matriz), com tooltip interativo e legenda de intensidade.
 *   2. Gráfico temporal de demanda (Chart.js line) — volume de consultas
 *      presenciais vs. teleconsulta ao longo do tempo, com suporte a
 *      filtros por convênio/particular (contexto TISS ANS 4.01 / DMED).
 *
 * Escopo: Atenção Primária / Saúde da Família, atendimento particular e
 * convênios. NÃO há integração com SUS/SISAB nem com periféricos IoT.
 *
 * Contrato de dados esperado (servido pelo backend FastAPI/Pydantic v2):
 *   GET /api/v1/analytics/agendamentos-heatmap  -> HeatmapResponse
 *   GET /api/v1/analytics/demanda-teletrabalho  -> DemandaResponse
 *
 * Requer: Chart.js >= 4.x carregado globalmente (window.Chart).
 * ---------------------------------------------------------------------------
 */
'use strict';

/* ========================================================================== *
 * Constantes e configuração
 * ========================================================================== */

/** @type {Readonly<Record<string, string>>} Paleta do heatmap (baixo -> alto). */
const HEATMAP_PALETTE = Object.freeze({
  vazio: '#eef2f7',
  baixo: '#cfe3f5',
  medio: '#7fb2e5',
  alto: '#3d7fc1',
  maximo: '#1a4e8a',
});

/** @type {ReadonlyArray<string>} Dias da semana (índice 0 = segunda). */
const DIAS_SEMANA = Object.freeze([
  'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo',
]);

/** @type {ReadonlyArray<string>} Turnos clínicos da agenda. */
const TURNOS = Object.freeze(['Manhã', 'Tarde', 'Noite']);

/** @type {Readonly<Record<string, string>>} Cores das séries de demanda. */
const CORES_DEMANDA = Object.freeze({
  teleconsulta: '#1a4e8a',
  presencial: '#e08a3c',
});

/** @type {number} Duração do fade-in das células do heatmap (ms). */
const HEATMAP_ANIMACAO_MS = 350;

/* ========================================================================== *
 * Utilitários
 * ========================================================================== */

/**
 * Interpola linearmente entre duas cores hex.
 * @param {string} corA Cor inicial (#rrggbb).
 * @param {string} corB Cor final (#rrggbb).
 * @param {number} t Fator de interpolação em [0, 1].
 * @returns {string} Cor interpolada em rgb().
 */
function interpolarCor(corA, corB, t) {
  const hexParaRgb = (hex) => {
    const v = parseInt(hex.slice(1), 16);
    return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
  };
  const [r1, g1, b1] = hexParaRgb(corA);
  const [r2, g2, b2] = hexParaRgb(corB);
  const mix = (a, b) => Math.round(a + (b - a) * t);
  return `rgb(${mix(r1, r2)}, ${mix(g1, g2)}, ${mix(b1, b2)})`;
}

/**
 * Mapeia um valor para a paleta discreta do heatmap.
 * @param {number} valor Valor normalizado em [0, 1].
 * @returns {string} Cor CSS.
 */
function corParaIntensidade(valor) {
  if (valor <= 0) return HEATMAP_PALETTE.vazio;
  if (valor < 0.25) return interpolarCor(HEATMAP_PALETTE.vazio, HEATMAP_PALETTE.baixo, valor / 0.25);
  if (valor < 0.50) return interpolarCor(HEATMAP_PALETTE.baixo, HEATMAP_PALETTE.medio, (valor - 0.25) / 0.25);
  if (valor < 0.75) return interpolarCor(HEATMAP_PALETTE.medio, HEATMAP_PALETTE.alto, (valor - 0.50) / 0.25);
  return interpolarCor(HEATMAP_PALETTE.alto, HEATMAP_PALETTE.maximo, (valor - 0.75) / 0.25);
}

/**
 * Destrói com segurança uma instância Chart.js pré-existente no canvas.
 * @param {HTMLCanvasElement} canvas Elemento alvo.
 * @returns {void}
 */
function destruirChartExistente(canvas) {
  const existente = Chart.getChart(canvas);
  if (existente) existente.destroy();
}

/**
 * Realiza fetch com tratamento de erro tipado para os endpoints de analytics.
 * @param {string} url Endpoint da API.
 * @returns {Promise<unknown>} JSON desserializado.
 * @throws {Error} Quando a resposta HTTP não é 2xx.
 */
async function buscarJson(url) {
  const resposta = await fetch(url, {
    headers: { Accept: 'application/json' },
    credentials: 'same-origin',
  });
  if (!resposta.ok) {
    throw new Error(`Falha ao carregar analytics (${resposta.status}): ${url}`);
  }
  return resposta.json();
}

/* ========================================================================== *
 * 1) Heatmap — Agendamentos por turno x dia da semana (Canvas 2D puro)
 * ========================================================================== */

/**
 * @typedef {Object} HeatmapCell
 * @property {number} dia Índice do dia (0=Segunda .. 6=Domingo).
 * @property {number} turno Índice do turno (0=Manhã, 1=Tarde, 2=Noite).
 * @property {number} total Agendamentos no período.
 */

/**
 * @typedef {Object} HeatmapPayload
 * @property {ReadonlyArray<HeatmapCell>} celulas Células preenchidas.
 * @property {string} [periodo] Rótulo do período analisado (ex.: "Últimos 90 dias").
 */

/**
 * Renderiza o heatmap de agendamentos por turno em Canvas 2D.
 * Inclui tooltip interativo, animação de fade-in e legenda de intensidade.
 *
 * @param {string} canvasId ID do elemento <canvas>.
 * @param {HeatmapPayload} payload Dados vindos da API.
 * @returns {void}
 */
function renderHeatmapAgendamentos(canvasId, payload) {
  const canvas = document.getElementById(canvasId);
  if (!(canvas instanceof HTMLCanvasElement)) {
    console.warn(`[MedIA][heatmap] Canvas "${canvasId}" não encontrado.`);
    return;
  }

  const celulas = payload?.celulas ?? [];
  const maximo = Math.max(1, ...celulas.map((c) => c.total));
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const larguraCss = canvas.clientWidth || 640;
  const alturaCss = canvas.clientHeight || 320;

  canvas.width = larguraCss * dpr;
  canvas.height = alturaCss * dpr;
  ctx.scale(dpr, dpr);

  const margem = { topo: 28, direita: 16, baixo: 40, esquerda: 72 };
  const areaW = larguraCss - margem.esquerda - margem.direita;
  const areaH = alturaCss - margem.topo - margem.baixo;
  const celW = areaW / DIAS_SEMANA.length;
  const celH = areaH / TURNOS.length;
  const gap = 3;

  ctx.clearRect(0, 0, larguraCss, alturaCss);

  // Rótulos dos dias (colunas) e turnos (linhas).
  ctx.font = '12px system-ui, sans-serif';
  ctx.fillStyle = '#4a5568';
  ctx.textAlign = 'center';
  DIAS_SEMANA.forEach((dia, i) => {
    ctx.fillText(dia, margem.esquerda + celW * (i + 0.5), margem.topo - 8);
  });
  ctx.textAlign = 'right';
  TURNOS.forEach((turno, i) => {
    ctx.fillText(turno, margem.esquerda - 10, margem.topo + celH * (i + 0.5) + 4);
  });

  // Células com fade-in progressivo.
  const inicio = performance.now();
  const mapa = new Map(celulas.map((c) => [`${c.dia}:${c.turno}`, c.total]));

  const desenhar = (agora) => {
    const progresso = Math.min(1, (agora - inicio) / HEATMAP_ANIMACAO_MS);
    ctx.clearRect(0, 0, larguraCss, alturaCss);

    DIAS_SEMANA.forEach((_, dia) => {
      TURNOS.forEach((_, turno) => {
        const total = mapa.get(`${dia}:${turno}`) ?? 0;
        const x = margem.esquerda + dia * celW + gap / 2;
        const y = margem.topo + turno * celH + gap / 2;
        ctx.fillStyle = corParaIntensidade((total / maximo) * progresso);
        ctx.beginPath();
        ctx.roundRect(x, y, celW - gap, celH - gap, 4);
        ctx.fill();
        if (total > 0) {
          ctx.fillStyle = total / maximo > 0.55 ? '#ffffff' : '#1a202c';
          ctx.font = '11px system-ui, sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(String(total), x + (celW - gap) / 2, y + (celH - gap) / 2 + 4);
        }
      });
    });

    // Rótulos redesenhados sobre as células.
    ctx.font = '12px system-ui, sans-serif';
    ctx.fillStyle = '#4a5568';
    ctx.textAlign = 'center';
    DIAS_SEMANA.forEach((dia, i) => {
      ctx.fillText(dia, margem.esquerda + celW * (i + 0.5), margem.topo - 8);
    });
    ctx.textAlign = 'right';
    TURNOS.forEach((turno, i) => {
      ctx.fillText(turno, margem.esquerda - 10, margem.topo + celH * (i + 0.5) + 4);
    });

    if (progresso < 1) requestAnimationFrame(desenhar);
  };
  requestAnimationFrame(desenhar);

  // Tooltip interativo.
  canvas.onmousemove = (evento) => {
    const rect = canvas.getBoundingClientRect();
    const dia = Math.floor((evento.clientX - rect.left - margem.esquerda) / celW);
    const turno = Math.floor((evento.clientY - rect.top - margem.topo) / celH);
    const valido = dia >= 0 && dia < DIAS_SEMANA.length && turno >= 0 && turno < TURNOS.length;
    canvas.title = valido
      ? `${DIAS_SEMANA[dia]} — ${TURNOS[turno]}: ${mapa.get(`${dia}:${turno}`) ?? 0} agendamento(s)` +
        (payload.periodo ? ` (${payload.periodo})` : '')
      : '';
  };
  canvas.onmouseleave = () => { canvas.title = ''; };
}

/* ========================================================================== *
 * 2) Demanda temporal — Presencial vs. Teleconsulta (Chart.js line)
 * ========================================================================== */

/**
 * @typedef {Object} DemandaPonto
 * @property {string} data Data ISO (YYYY-MM-DD).
 * @property {number} presencial Consultas presenciais no dia.
 * @property {number} teleconsulta Teleconsultas realizadas no dia.
 */

/**
 * @typedef {Object} DemandaPayload
 * @property {ReadonlyArray<DemandaPonto>} serie Série temporal diária.
 * @property {string} [convenio] Filtro aplicado (ex.: código TISS da operadora,
 *                                ou "particular" para atendimento direto).
 */

/**
 * Renderiza o gráfico temporal de demanda do médico em teletrabalho,
 * comparando teleconsulta (remota) e consulta presencial.
 *
 * @param {string} canvasId ID do elemento <canvas>.
 * @param {DemandaPayload} payload Dados vindos da API.
 * @returns {Chart|undefined} Instância Chart.js criada.
 */
function renderDemandaTeletrabalho(canvasId, payload) {
  const canvas = document.getElementById(canvasId);
  if (!(canvas instanceof HTMLCanvasElement)) {
    console.warn(`[MedIA][demanda] Canvas "${canvasId}" não encontrado.`);
    return undefined;
  }
  if (typeof Chart === 'undefined') {
    console.error('[MedIA][demanda] Chart.js não carregado.');
    return undefined;
  }
  destruirChartExistente(canvas);

  const serie = [...(payload?.serie ?? [])].sort(
    (a, b) => new Date(a.data).getTime() - new Date(b.data).getTime(),
  );
  const rotulos = serie.map((p) =>
    new Date(`${p.data}T12:00:00`).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }),
  );

  const opacidade = (hex, alpha) => `${hex}${Math.round(alpha * 255).toString(16).padStart(2, '0')}`;

  return new Chart(canvas, {
    type: 'line',
    data: {
      labels: rotulos,
      datasets: [
        {
          label: 'Teleconsulta',
          data: serie.map((p) => p.teleconsulta),
          borderColor: CORES_DEMANDA.teleconsulta,
          backgroundColor: opacidade(CORES_DEMANDA.teleconsulta, 0.12),
          fill: true,
          tension: 0.3,
          pointRadius: 2,
          pointHoverRadius: 5,
        },
        {
          label: 'Presencial',
          data: serie.map((p) => p.presencial),
          borderColor: CORES_DEMANDA.presencial,
          backgroundColor: opacidade(CORES_DEMANDA.presencial, 0.12),
          fill: true,
          tension: 0.3,
          pointRadius: 2,
          pointHoverRadius: 5,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top', labels: { usePointStyle: true, boxWidth: 8 } },
        tooltip: {
          callbacks: {
            afterBody: (itens) => {
              const idx = itens[0]?.dataIndex ?? 0;
              const ponto = serie[idx];
              const total = ponto ? ponto.presencial + ponto.teleconsulta : 0;
              const pctRemoto = total > 0 ? ((ponto.teleconsulta / total) * 100).toFixed(1) : '0.0';
              return `Índice de teletrabalho: ${pctRemoto}%`;
            },
          },
        },
        title: {
          display: Boolean(payload?.convenio),
          text: payload?.convenio
            ? `Demanda — ${payload.convenio} (particular/convênio · TISS ANS 4.01)`
            : '',
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { maxRotation: 45, autoSkip: true } },
        y: {
          beginAtZero: true,
          grid: { color: '#e2e8f0' },
          title: { display: true, text: 'Consultas' },
          ticks: { precision: 0 },
        },
      },
    },
  });
}

/* ========================================================================== *
 * 3) Orquestração — carregamento e inicialização
 * ========================================================================== */

/**
 *