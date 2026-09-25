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

/**
 * backend/app/static/js/analytics_charts.js
 * C31 — Componente Gráfico de Linha e Heatmap Interativo
 * ...
 */
"use strict"; // hmm, modules are strict by default; if loaded as classic script, "use strict" helps.

// @ts-check

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
