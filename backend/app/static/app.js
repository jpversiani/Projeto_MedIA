let pacienteAtivo = null;
let filaAtivaId = null;
let problemasSelecionados = [];
let cidadaosCache = [];

let usuarioAtual = null;

document.addEventListener("DOMContentLoaded", () => {
  inicializarSessaoUsuario();
  carregarFila();
  carregarCidadaos();
});

function trocarAba(aba) {
  document.getElementById("aba-fila").classList.add("hidden");
  document.getElementById("aba-cidadaos").classList.add("hidden");
  document.getElementById("aba-soap").classList.add("hidden");

  const baseClass = "w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-all";
  const activeClass = "w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/20 transition-all";

  document.getElementById("btn-menu-fila").className = baseClass;
  document.getElementById("btn-menu-cidadaos").className = baseClass;
  document.getElementById("btn-menu-soap").className = baseClass;

  if (aba === 'fila') {
    document.getElementById("aba-fila").classList.remove("hidden");
    document.getElementById("btn-menu-fila").className = activeClass;
    carregarFila();
  } else if (aba === 'cidadaos') {
    document.getElementById("aba-cidadaos").classList.remove("hidden");
    document.getElementById("btn-menu-cidadaos").className = activeClass;
  } else if (aba === 'soap') {
    document.getElementById("aba-soap").classList.remove("hidden");
    document.getElementById("btn-menu-soap").className = activeClass;
  }
}

async function carregarFila() {
  try {
    const res = await fetch("/api/v1/fila/?status=AGUARDANDO_ATENDIMENTO");
    const itens = await res.json();
    const tabela = document.getElementById("tabela-fila-corpo");
    document.getElementById("badge-contador-fila").textContent = itens.length;
    tabela.innerHTML = "";

    if (itens.length === 0) {
      tabela.innerHTML = `<tr><td colspan="7" class="px-5 py-8 text-center text-slate-400">Nenhum cidadão aguardando na fila no momento.</td></tr>`;
      return;
    }

    itens.forEach(item => {
      const cid = item.cidadao;
      const riscoCores = {
        'VERMELHO': 'bg-rose-500/15 text-rose-600 border border-rose-500/30',
        'AMARELO': 'bg-amber-500/15 text-amber-600 border border-amber-500/30',
        'VERDE': 'bg-emerald-500/15 text-emerald-600 border border-emerald-500/30',
        'AZUL': 'bg-blue-500/15 text-blue-600 border border-blue-500/30'
      };
      const badgeCls = riscoCores[item.classificacao_risco] || 'bg-emerald-500/15 text-emerald-600 border border-emerald-500/30';
      const vitais = `PA: ${item.pressao_sistolica || '--'}/${item.pressao_diastolica || '--'} | FC: ${item.frequencia_cardiaca || '--'} | Temp: ${item.temperatura ? item.temperatura + '°C' : '--'}`;
      const hora = new Date(item.data_hora_entrada).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50/80 transition-colors group";
      tr.innerHTML = `
        <td class="px-5 py-4">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold tracking-wide uppercase ${badgeCls}">
            <span class="w-1.5 h-1.5 rounded-full ${item.classificacao_risco === 'VERMELHO' ? 'bg-rose-500 animate-pulse' : 'bg-current'}"></span>
            ${item.classificacao_risco}
          </span>
        </td>
        <td class="px-5 py-4">
          <div class="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors text-sm">${cid ? cid.nome_completo : 'Paciente sem cadastro'}</div>
          <div class="text-xs text-slate-500 truncate max-w-xs mt-0.5">${item.motivo_acolhimento || 'Triagem inicial de demanda'}</div>
        </td>
        <td class="px-5 py-4 text-xs font-mono text-slate-600">
          <div class="flex items-center gap-1 text-slate-800 font-medium"><span>CPF:</span> ${cid && cid.cpf ? cid.cpf : '--'}</div>
          <div class="text-slate-400 text-[11px]">ID Família: ${cid && cid.cns ? cid.cns.slice(-6) : '--'}</div>
        </td>
        <td class="px-5 py-4 text-xs">
          <span class="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-medium border border-slate-200/60">${item.tipo_demanda}</span>
        </td>
        <td class="px-5 py-4 text-xs font-mono text-slate-600">
          <span class="px-2 py-1 bg-slate-100 rounded border border-slate-200/80">${vitais}</span>
        </td>
        <td class="px-5 py-4 text-xs text-slate-400 font-mono">${hora}</td>
        <td class="px-5 py-4 text-right">
          <button onclick="iniciarAtendimento(${item.id})" class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm shadow-blue-500/20 transition-all hover:scale-[1.02] ml-auto">
            <i class="fa-solid fa-wand-magic-sparkles text-[10px]"></i>
            <span>Copiloto SOAP</span>
          </button>
        </td>
      `;
      tabela.appendChild(tr);
    });
  } catch (err) {
    console.error("Erro ao carregar fila:", err);
  }
}

async function carregarCidadaos() {
  const filtro = document.getElementById("filtro-cidadao")?.value || "";
  try {
    const res = await fetch(`/api/v1/cidadaos/?busca=${encodeURIComponent(filtro)}`);
    cidadaosCache = await res.json();
    
    // Atualizar dropdown do modal de acolhimento
    const select = document.getElementById("modal-select-cidadao");
    if (select) {
      select.innerHTML = cidadaosCache.map(c => `<option value="${c.id}">${c.nome_completo} (CPF: ${c.cpf || 'Sem CPF'} | ID Família: ${c.cns || '--'})</option>`).join("");
    }

    // Atualizar cards
    const container = document.getElementById("cards-cidadaos");
    if (!container) return;
    container.innerHTML = "";

    cidadaosCache.forEach(c => {
      const card = document.createElement("div");
      card.className = "bg-white p-5 rounded-2xl border border-slate-200/80 hover:border-blue-400/60 shadow-sm hover:shadow-md transition-all space-y-3 group";
      card.innerHTML = `
        <div class="flex items-start justify-between">
          <div>
            <h4 class="font-bold text-slate-900 group-hover:text-blue-600 transition-colors text-sm">${c.nome_completo}</h4>
            <div class="text-[11px] text-slate-400 font-mono mt-0.5">Nasc: ${c.data_nascimento} • ${c.sexo === 'M' ? 'Masc' : 'Fem'}</div>
          </div>
          <span class="text-[10px] bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded-full font-mono font-semibold">#${c.id}</span>
        </div>
        <div class="text-xs text-slate-600 space-y-1 pt-1 border-t border-slate-100">
          <div class="font-mono text-[11px] text-slate-700"><span class="text-slate-400 font-sans">CPF:</span> ${c.cpf || '--'}</div>
          <div class="text-[11px] text-slate-500 truncate"><span class="text-slate-400">Território:</span> ${c.bairro || 'Montes Claros/MG'}</div>
          <div class="text-[11px] text-slate-400 truncate">${c.logradouro || ''}, ${c.numero || ''}</div>
        </div>
        <div class="flex flex-wrap gap-1.5 pt-1">
          ${c.hipertenso ? '<span class="text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-md">HAS Risco</span>' : ''}
          ${c.diabetico ? '<span class="text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-md">DM Controlada</span>' : ''}
          ${c.alergias ? `<span class="text-[10px] font-semibold bg-purple-50 text-purple-700 border border-purple-200 px-2 py-0.5 rounded-md">Alergia: ${c.alergias}</span>` : ''}
          <span class="text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200/50 px-2 py-0.5 rounded-md">Saúde da Família</span>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Erro ao carregar cidadãos:", err);
  }
}

async function iniciarAtendimento(filaId) {
  try {
    const res = await fetch(`/api/v1/fila/${filaId}`);
    const item = await res.json();
    filaAtivaId = item.id;
    pacienteAtivo = item.cidadao;

    // Atualizar cabeçalho do SOAP
    document.getElementById("soap-paciente-nome").textContent = pacienteAtivo.nome_completo;
    document.getElementById("soap-paciente-iniciais").textContent = pacienteAtivo.nome_completo.split(" ").map(n => n[0]).slice(0, 2).join("");
    document.getElementById("soap-paciente-sub").textContent = `CNS: ${pacienteAtivo.cns || '--'} | CPF: ${pacienteAtivo.cpf || '--'} | Nasc: ${pacienteAtivo.data_nascimento} | Alergias: ${pacienteAtivo.alergias || 'Nenhuma informada'}`;
    
    const tagEl = document.getElementById("soap-paciente-tags");
    if (pacienteAtivo.hipertenso) {
      tagEl.textContent = "Hipertenso";
      tagEl.classList.remove("hidden");
    } else {
      tagEl.classList.add("hidden");
    }

    // Puxar dados vitais do acolhimento
    document.getElementById("soap-pa").textContent = `${item.pressao_sistolica || '--'}/${item.pressao_diastolica || '--'}`;
    document.getElementById("soap-fc").textContent = `${item.frequencia_cardiaca || '--'} bpm`;
    document.getElementById("soap-temp").textContent = `${item.temperatura ? item.temperatura + ' °C' : '--'}`;
    document.getElementById("soap-spo2").textContent = `${item.saturacao_o2 ? item.saturacao_o2 + ' %' : '--'}`;
    document.getElementById("soap-glicemia").textContent = `${item.glicemia_capilar ? item.glicemia_capilar + ' mg/dL' : '--'}`;
    document.getElementById("soap-imc").textContent = `${item.imc || '--'}`;

    // Preencher queixa inicial no Subjetivo
    document.getElementById("soap-motivo").value = item.motivo_acolhimento || "";

    // Trocar para a tela de SOAP
    trocarAba('soap');
  } catch (err) {
    console.error("Erro ao iniciar atendimento:", err);
  }
}

async function buscarTerminologias() {
  const busca = document.getElementById("input-busca-terminologia").value.trim();
  if (!busca) return;

  const resContainer = document.getElementById("resultados-busca-terminologias");
  resContainer.innerHTML = "<div class='text-xs text-slate-400'>Buscando...</div>";
  resContainer.classList.remove("hidden");

  try {
    const [resCiap, resCid] = await Promise.all([
      fetch(`/api/v1/terminologias/ciap2?busca=${encodeURIComponent(busca)}`),
      fetch(`/api/v1/terminologias/cid10?busca=${encodeURIComponent(busca)}`)
    ]);
    const ciap2 = await resCiap.json();
    const cid10 = await resCid.json();

    resContainer.innerHTML = "";
    if (ciap2.length === 0 && cid10.length === 0) {
      resContainer.innerHTML = "<div class='text-xs text-slate-400'>Nenhum termo encontrado.</div>";
      return;
    }

    ciap2.forEach(c => {
      const btn = document.createElement("div");
      btn.className = "flex items-center justify-between p-1.5 hover:bg-blue-100 rounded cursor-pointer text-xs";
      btn.innerHTML = `<span><b class="text-blue-700 font-mono">[CIAP-2 ${c.codigo}]</b> ${c.descricao}</span><i class="fa-solid fa-plus text-blue-600"></i>`;
      btn.onclick = () => adicionarProblema('CIAP2', c.codigo, c.descricao);
      resContainer.appendChild(btn);
    });

    cid10.forEach(c => {
      const btn = document.createElement("div");
      btn.className = "flex items-center justify-between p-1.5 hover:bg-emerald-100 rounded cursor-pointer text-xs";
      btn.innerHTML = `<span><b class="text-emerald-700 font-mono">[CID-10 ${c.codigo}]</b> ${c.descricao}</span><i class="fa-solid fa-plus text-emerald-600"></i>`;
      btn.onclick = () => adicionarProblema('CID10', c.codigo, c.descricao);
      resContainer.appendChild(btn);
    });
  } catch (err) {
    console.error("Erro na busca de termos:", err);
  }
}

function adicionarProblema(tipo, codigo, descricao) {
  if (problemasSelecionados.some(p => p.tipo_codigo === tipo && p.codigo === codigo)) {
    return;
  }
  problemasSelecionados.push({ tipo_codigo: tipo, codigo, descricao, situacao: "ATIVO" });
  renderizarProblemasSelecionados();
  document.getElementById("resultados-busca-terminologias").classList.add("hidden");
  document.getElementById("input-busca-terminologia").value = "";
}

function removerProblema(idx) {
  problemasSelecionados.splice(idx, 1);
  renderizarProblemasSelecionados();
}

function renderizarProblemasSelecionados() {
  const container = document.getElementById("lista-problemas-selecionados");
  container.innerHTML = "";
  if (problemasSelecionados.length === 0) {
    container.innerHTML = `<div class="text-xs text-slate-400 italic">Nenhum diagnóstico anexado ainda.</div>`;
    return;
  }

  problemasSelecionados.forEach((p, idx) => {
    const badgeColor = p.tipo_codigo === 'CIAP2' ? 'bg-blue-50 border-blue-200 text-blue-800' : 'bg-emerald-50 border-emerald-200 text-emerald-800';
    const tag = document.createElement("div");
    tag.className = `flex items-center justify-between p-2 rounded-lg border text-xs ${badgeColor}`;
    tag.innerHTML = `
      <div>
        <span class="font-bold font-mono">[${p.tipo_codigo} ${p.codigo}]</span> ${p.descricao}
      </div>
      <button onclick="removerProblema(${idx})" class="text-slate-400 hover:text-red-600 ml-2"><i class="fa-solid fa-trash-can"></i></button>
    `;
    container.appendChild(tag);
  });
}

async function finalizarAtendimentoSOAP() {
  if (!pacienteAtivo) {
    alert("Selecione um paciente antes de finalizar o atendimento.");
    return;
  }

  const payload = {
    cidadao_id: pacienteAtivo.id,
    profissional_id: 1, // Dra. Ana Paula
    estabelecimento_id: 1, // ESF Santos Reis
    fila_id: filaAtivaId,
    subjetivo_motivo: document.getElementById("soap-motivo").value,
    subjetivo_notas: document.getElementById("soap-subjetivo-notas").value,
    objetivo_exame_fisico: document.getElementById("soap-exame-fisico").value,
    objetivo_antropometria_sinais: `PA: ${document.getElementById("soap-pa").textContent}, FC: ${document.getElementById("soap-fc").textContent}`,
    avaliacao_notas: document.getElementById("soap-avaliacao-notas").value,
    plano_conduta: document.getElementById("soap-conduta").value,
    plano_prescricoes: document.getElementById("soap-prescricao").value,
    plano_exames: document.getElementById("soap-exames").value,
    problemas: problemasSelecionados
  };

  try {
    const res = await fetch("/api/v1/atendimentos/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const atendSalvo = await res.json();
      const exportUrl = `/api/v1/atendimentos/${atendSalvo.id}/exportar-fai`;
      alert(`Atendimento SOAP registrado e finalizado com sucesso!\n\nVocê pode exportar a Ficha FAI (Padrão SISAB/LEDI) em:\n${window.location.origin}${exportUrl}`);
      limparFormularioSOAP();
      trocarAba('fila');
    } else {
      const err = await res.json();
      alert(`Erro ao registrar atendimento: ${JSON.stringify(err)}`);
    }
  } catch (err) {
    console.error("Erro ao salvar SOAP:", err);
    alert("Erro de comunicação ao salvar atendimento.");
  }
}

function limparFormularioSOAP() {
  pacienteAtivo = null;
  filaAtivaId = null;
  problemasSelecionados = [];
  document.getElementById("soap-paciente-nome").textContent = "Selecione um paciente na fila";
  document.getElementById("soap-paciente-iniciais").textContent = "--";
  document.getElementById("soap-paciente-sub").textContent = "CNS: -- | Nasc: -- | Alergias: --";
  document.getElementById("soap-motivo").value = "";
  document.getElementById("soap-subjetivo-notas").value = "";
  document.getElementById("soap-exame-fisico").value = "";
  document.getElementById("soap-avaliacao-notas").value = "";
  document.getElementById("soap-conduta").value = "";
  document.getElementById("soap-prescricao").value = "";
  document.getElementById("soap-exames").value = "";
  renderizarProblemasSelecionados();
}

function abrirModalAcolhimento() {
  document.getElementById("modal-acolhimento").classList.remove("hidden");
}

function fecharModalAcolhimento() {
  document.getElementById("modal-acolhimento").classList.add("hidden");
}

async function salvarAcolhimento() {
  const cidadaoId = document.getElementById("modal-select-cidadao").value;
  if (!cidadaoId) {
    alert("Selecione um cidadão.");
    return;
  }

  const payload = {
    cidadao_id: parseInt(cidadaoId),
    estabelecimento_id: 1,
    profissional_triagem_id: 2, // Enf. Marcos Vinícius
    classificacao_risco: document.getElementById("modal-risco").value,
    tipo_demanda: document.getElementById("modal-demanda").value,
    motivo_acolhimento: document.getElementById("modal-motivo").value,
    pressao_sistolica: parseInt(document.getElementById("modal-pa-sis").value) || null,
    pressao_diastolica: parseInt(document.getElementById("modal-pa-dia").value) || null,
    frequencia_cardiaca: parseInt(document.getElementById("modal-fc").value) || null,
    temperatura: parseFloat(document.getElementById("modal-temp").value) || null,
    saturacao_o2: parseInt(document.getElementById("modal-spo2").value) || null,
    glicemia_capilar: parseInt(document.getElementById("modal-glicemia").value) || null,
    peso_kg: parseFloat(document.getElementById("modal-peso").value) || null,
    altura_cm: parseFloat(document.getElementById("modal-altura").value) || null
  };

  try {
    const res = await fetch("/api/v1/fila/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      fecharModalAcolhimento();
      carregarFila();
    } else {
      const err = await res.json();
      alert(`Erro ao registrar acolhimento: ${JSON.stringify(err)}`);
    }
  } catch (err) {
    console.error("Erro ao salvar acolhimento:", err);
  }
}

/* ==============================================================================
 * Multi-Tenancy & Autenticação Avançada (SSO / Health 4.0 / LGPD)
 * ============================================================================== */

async function inicializarSessaoUsuario() {
  let token = localStorage.getItem("media_token");
  let userStr = localStorage.getItem("media_user");

  if (!token || !userStr) {
    // Modo de demonstração automática (Médico Titular: Dr. João Paulo Versiani)
    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: "medico_titular@media-saude.com.br", demo_role: "medico_titular" })
      });
      if (res.ok) {
        const data = await res.json();
        token = data.access_token;
        usuarioAtual = data.usuario;
        localStorage.setItem("media_token", token);
        localStorage.setItem("media_user", JSON.stringify(usuarioAtual));
      }
    } catch (e) {
      console.warn("Não foi possível autenticar o usuário padrão:", e);
    }
  } else {
    try {
      usuarioAtual = JSON.parse(userStr);
      // Validar / sincronizar com /api/v1/auth/me
      const meRes = await fetch("/api/v1/auth/me", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (meRes.ok) {
        usuarioAtual = await meRes.json();
        localStorage.setItem("media_user", JSON.stringify(usuarioAtual));
      }
    } catch (e) {
      console.warn("Erro ao ler sessão local:", e);
    }
  }

  atualizarInterfaceUsuario();
}

function atualizarInterfaceUsuario() {
  if (!usuarioAtual) return;

  // Nome e CRM
  const elNome = document.getElementById("top-profissional");
  if (elNome) elNome.textContent = usuarioAtual.nome_completo || "Dr. João Paulo Versiani";

  const elCrm = document.getElementById("top-crm-badge");
  if (elCrm) {
    elCrm.textContent = usuarioAtual.crm ? `CRM-MG ${usuarioAtual.crm}` : (usuarioAtual.papel_ativo || "MÉDICO");
  }

  // Provedor SSO
  const elSso = document.getElementById("top-sso-badge");
  if (elSso) {
    const prov = usuarioAtual.sso_provider || "local";
    if (prov === "google") {
      elSso.innerHTML = `<i class="fa-brands fa-google mr-1 text-[9px]"></i> Google Workspace`;
      elSso.className = "bg-blue-800 text-[10px] px-1.5 rounded text-blue-100 flex items-center";
    } else if (prov === "microsoft") {
      elSso.innerHTML = `<i class="fa-brands fa-microsoft mr-1 text-[9px]"></i> Entra ID (OIDC)`;
      elSso.className = "bg-sky-800 text-[10px] px-1.5 rounded text-sky-100 flex items-center";
    } else {
      elSso.innerHTML = `<i class="fa-solid fa-lock mr-1 text-[9px]"></i> Autenticado MedIA`;
      elSso.className = "bg-emerald-800 text-[10px] px-1.5 rounded text-emerald-100 flex items-center";
    }
  }

  // Preencher clínicas no seletor
  const selectClinica = document.getElementById("select-clinica-ativa");
  if (selectClinica && usuarioAtual.clinicas && usuarioAtual.clinicas.length > 0) {
    selectClinica.innerHTML = usuarioAtual.clinicas.map(c => {
      const selected = c.estabelecimento_id === usuarioAtual.clinica_ativa_id ? "selected" : "";
      return `<option value="${c.estabelecimento_id}" ${selected} class="text-slate-800">${c.estabelecimento_nome} (CNES ${c.cnes || 'N/A'})</option>`;
    }).join("");
  }

  // Atualizar subtítulo da unidade
  const elUnidade = document.getElementById("top-unidade");
  if (elUnidade && usuarioAtual.clinica_ativa_nome) {
    elUnidade.textContent = `• ${usuarioAtual.clinica_ativa_nome}`;
  }
}

async function alternarClinica(estabelecimentoId) {
  const token = localStorage.getItem("media_token");
  if (!token) {
    alert("Sessão expirada. Faça login novamente.");
    window.location.href = "/";
    return;
  }

  try {
    const res = await fetch("/api/v1/auth/switch-clinic", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ estabelecimento_id: parseInt(estabelecimentoId) })
    });

    if (res.ok) {
      const data = await res.json();
      localStorage.setItem("media_token", data.access_token);
      localStorage.setItem("media_user", JSON.stringify(data.usuario));
      usuarioAtual = data.usuario;
      atualizarInterfaceUsuario();
      carregarFila();
      carregarCidadaos();
    } else {
      const err = await res.json();
      alert(`Não foi possível alternar de clínica: ${err.detail || 'Permissão negada'}`);
    }
  } catch (e) {
    console.error("Erro ao alternar clínica:", e);
    alert("Erro na conexão com o servidor ao alternar unidade.");
  }
}

function fazerLogout() {
  localStorage.removeItem("media_token");
  localStorage.removeItem("media_user");
  window.location.href = "/";
}

/* ==============================================================================
 * Modal Trilha de Auditoria Criptográfica LGPD (SHA-256 Chained)
 * ============================================================================== */

function abrirModalAuditoria() {
  document.getElementById("modal-auditoria").classList.remove("hidden");
  carregarTrilhaAuditoria();
}

function fecharModalAuditoria() {
  document.getElementById("modal-auditoria").classList.add("hidden");
}

async function carregarTrilhaAuditoria() {
  const token = localStorage.getItem("media_token");
  const tabela = document.getElementById("tabela-auditoria-corpo");
  tabela.innerHTML = `<tr><td colspan="4" class="px-4 py-8 text-center text-slate-400 font-sans">Carregando registros imutáveis...</td></tr>`;

  try {
    const res = await fetch("/api/v1/auth/audit-trail?limit=30", {
      headers: { "Authorization": `Bearer ${token || ''}` }
    });

    if (!res.ok) {
      tabela.innerHTML = `<tr><td colspan="4" class="px-4 py-8 text-center text-rose-500 font-sans">Erro ao carregar auditoria: Acesso restrito a usuários autenticados.</td></tr>`;
      return;
    }

    const registros = await res.json();
    if (registros.length === 0) {
      tabela.innerHTML = `<tr><td colspan="4" class="px-4 py-8 text-center text-slate-400 font-sans">Nenhum evento registrado ainda.</td></tr>`;
      return;
    }

    tabela.innerHTML = registros.map(r => {
      const dataStr = new Date(r.timestamp).toLocaleString("pt-BR");
      const hashCurto = r.hash_atual ? `${r.hash_atual.substring(0, 16)}...` : "--";
      const hashTooltip = r.hash_atual || "";
      const hashPrevCurto = r.hash_anterior ? `${r.hash_anterior.substring(0, 12)}...` : "GENESIS";
      
      let badgeCor = "bg-blue-100 text-blue-800";
      if (r.acao.includes("LOGIN")) badgeCor = "bg-emerald-100 text-emerald-800";
      if (r.acao.includes("CLINICA")) badgeCor = "bg-purple-100 text-purple-800";
      if (r.acao.includes("DELETE") || r.acao.includes("REMOVER")) badgeCor = "bg-rose-100 text-rose-800";

      return `
        <tr class="hover:bg-slate-50 transition border-b border-slate-100">
          <td class="px-4 py-3">
            <span class="px-2 py-0.5 rounded text-[11px] font-bold ${badgeCor}">${r.acao}</span>
            <div class="text-[10px] text-slate-400 mt-1 font-sans">${dataStr}</div>
          </td>
          <td class="px-4 py-3 font-sans text-xs">
            <div class="font-semibold text-slate-800">Usuário #${r.usuario_id || 'Sistema'}</div>
            <div class="text-[11px] text-slate-500">Unidade ID: ${r.estabelecimento_id || 'Global'}</div>
          </td>
          <td class="px-4 py-3 font-sans text-xs text-slate-600">
            <div class="font-medium">${r.recurso_tipo} ${r.recurso_id ? `(#${r.recurso_id})` : ''}</div>
            <div class="text-[10px] text-slate-400 font-mono">IP: ${r.ip_address || '127.0.0.1'}</div>
          </td>
          <td class="px-4 py-3 text-xs">
            <div class="text-emerald-700 font-bold" title="${hashTooltip}">${hashCurto}</div>
            <div class="text-[10px] text-slate-400">Anterior: ${hashPrevCurto}</div>
          </td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("Erro na trilha de auditoria:", err);
    tabela.innerHTML = `<tr><td colspan="4" class="px-4 py-8 text-center text-rose-500 font-sans">Falha na conexão com o servidor de auditoria.</td></tr>`;
  }
}
