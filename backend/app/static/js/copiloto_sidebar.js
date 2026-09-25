class AlertaRisco(BaseModel):
    id: str
    tipo: Literal["ALERGIA", "RISCO", "INTERACAO_MEDICAMENTOSA", "DADOS_VITAIS_CRITICOS", "OUTRO"]
    severidade: Literal["CRITICO", "ALTO", "MODERADO"]
    descricao: str
    fonte: str | None
    cid10: str | None
    ciap2: str | None
    criado_em: datetime

class SugestaoSOAP(BaseModel):
    subjetivo: str
    objetivo: str
    avaliacao: str  # with CID-10 / CIAP-2 hypotheses
    plano: str
    cid10_sugeridos: list[str]
    ciap2_sugeridos: list[str]
    confianca: float  # 0..1
    modelo: str
    gerado_em: datetime
    requer_revisao_medica: Literal[True] = True

class ExameComplementar(BaseModel):
    id, nome, codigo (SUS SIGTAP?), justificativa, prioridade: Literal["ROTINA","URGENTE","URGENCIA"], ciap2?

class DosagemSUS(BaseModel):
    id, medicamento, apresentacao, posologia, via, referencia (e.g., "FTN/RENIFER 2024"), alerta_alergia_relacionada?

class CopilotoSnapshot(BaseModel):
    atendimento_id: UUID
    paciente: PacienteResumo (nome, cns, idade, sexo)
    alertas: list[AlertaRisco]
    sugestao_soap: SugestaoSOAP | None
    exames: list[ExameComplementar]
    dosagens: list[DosagemSUS]
    atualizado_em: datetime

/**
 * ============================================================================
 * MedIA — Copiloto Clínico (Painel Lateral) — Tela de Teleatendimento Médico
 * Card C30 — Home Office / Teleatendimento (APS / SUS)
 * ============================================================================
 * ...
 */

(function (global) {
  'use strict';

  // ---------- Constantes / Strings ----------
  const STRINGS = {...};
  const SEVERIDADE = { CRITICO: {...}, ALTO: {...}, MODERADO: {...} };
  const WS_MSG_TYPES = {...}; // must match backend enums

  // ---------- Utilidades ----------
  function el(tag, attrs, children) {...} // safe DOM builder using textContent
  function formatarCNS(cns) {...}
  function validarCNS(cns) {...} // dígitos verificadores (SUS) — nice touch
  function formatarDataISO(iso) {...} // pt-BR
  function debounce / etc.

  // ---------- Estado ----------
  class CopilotoStore { ... } // holds snapshot, emits change events

  // ---------- Widget ----------
  class CopilotoSidebar {
    constructor(root, opcoes) {...}
    init() {...}
    // render sections
    _renderCabecalho(), _renderAlertas(), _renderSOAP(), _renderExames(), _renderDosagens(), _renderRodape()
    // realtime
    _conectarWebSocket(), _agendarReconnect(), _iniciarPolling()
    // actions
    _aplicarSugestaoSOAP(), _incluirExameNoPlano(exame), _registrarAuditoria(acao, detalhe)
    // soap form integration
    _preencherFormularioSOAP(sugestao)
    destroy()
  }

  // auto-init from DOM
  function autoInit() {...}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', autoInit); else autoInit();

  global.MedIACopilotoSidebar = { init: ..., CopilotoSidebar };
})(window);

soma = Σ (digito[i] * peso[i]) where pesos = 15,14,...,1?

pesos = [15,14,13,12,11,10,9,8,7,6,5,4,3,2]
soma = n[0]*15 + n[1]*14 + ... + n[13]*2
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0
if dv != n[14]: invalid

function validaCNS(cns) {
  cns = cns.replace(/\D/g, '');
  if (cns.length !== 15) return false;
  if (!/[1-9]/.test(cns[0])) return false;
  if ('789'.includes(cns[0])) {
    // CNS provisório: soma = Σ digito * peso (pesos 15..2 for first 14? no...)
  }
}

soma = 0
for i in 0..14: soma += Number(cns[i]) * (15 - i)
resto = soma % 11
dv = 11 - resto
if dv == 11: dv = 0  // actually if resto == 0 then dv = 11 - 0 = 11 → becomes 0?

rotina = "1" (1/2) or "2" (7/8/9)
For 1/2:
  soma = n1*15 + n2*14 + ... + n14*2
  resto = soma % 11
  dv = 11 - resto
  if dv == 11: dv = 0
  if dv == 10: invalid
  compare with n15
For 7/8/9:
  soma = n1*15 + ... + n15*1  (all 15 digits with weights 15..1)
  if soma % 11 == 0: valid

@keyframes copiloto-piscar-critico {
  0%, 100% { background-color: #d32f2f; }
  50% { background-color: #ffcdd2; } /* or opacity */
}
@media (prefers-reduced-motion: reduce) {
  .copiloto-alerta--critico { animation: none !important; ... }
}

const SOAP_SELECTORS = {
  S: ['#soap-subjetivo', '[name="soap_subjetivo"]', '#id_soap_subjetivo', 'textarea[name="subjetivo"]'],
  O: [...], A: [...], P: [...]
};
