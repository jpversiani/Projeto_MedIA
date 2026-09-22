let pacienteAtivo = null;
let filaAtivaId = null;
let problemasSelecionados = [];
let cidadaosCache = [];

document.addEventListener("DOMContentLoaded", () => {
  carregarFila();
  carregarCidadaos();
});

function trocarAba(aba) {
  document.getElementById("aba-fila").classList.add("hidden");
  document.getElementById("aba-cidadaos").classList.add("hidden");
  document.getElementById("aba-soap").classList.add("hidden");

  document.getElementById("btn-menu-fila").className = "w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50";
  document.getElementById("btn-menu-cidadaos").className = "w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50";
  document.getElementById("btn-menu-soap").className = "w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50";

  if (aba === 'fila') {
    document.getElementById("aba-fila").classList.remove("hidden");
    document.getElementById("btn-menu-fila").className = "w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium bg-blue-50 text-blue-800";
    carregarFila();
  } else if (aba === 'cidadaos') {
    document.getElementById("aba-cidadaos").classList.remove("hidden");
    document.getElementById("btn-menu-cidadaos").className = "w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium bg-blue-50 text-blue-800";
  } else if (aba === 'soap') {
    document.getElementById("aba-soap").classList.remove("hidden");
    document.getElementById("btn-menu-soap").className = "w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium bg-blue-50 text-blue-800";
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
        'VERMELHO': 'badge-vermelho',
        'AMARELO': 'badge-amarelo',
        'VERDE': 'badge-verde',
        'AZUL': 'badge-azul'
      };
      const badgeCls = riscoCores[item.classificacao_risco] || 'badge-verde';
      const vitais = `PA: ${item.pressao_sistolica || '--'}/${item.pressao_diastolica || '--'} | FC: ${item.frequencia_cardiaca || '--'} | Temp: ${item.temperatura ? item.temperatura + '°C' : '--'}`;
      const hora = new Date(item.data_hora_entrada).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      tr.innerHTML = `
        <td class="px-5 py-3.5">
          <span class="px-2.5 py-1 rounded text-xs font-bold ${badgeCls}">${item.classificacao_risco}</span>
        </td>
        <td class="px-5 py-3.5">
          <div class="font-semibold text-slate-800">${cid ? cid.nome_completo : 'Paciente sem cadastro'}</div>
          <div class="text-xs text-slate-400">${item.motivo_acolhimento || 'Sem queixa informada'}</div>
        </td>
        <td class="px-5 py-3.5 text-xs text-slate-600">
          <div>CNS: ${cid && cid.cns ? cid.cns : '--'}</div>
          <div>CPF: ${cid && cid.cpf ? cid.cpf : '--'}</div>
        </td>
        <td class="px-5 py-3.5 text-xs text-slate-600">
          <span class="bg-slate-100 px-2 py-0.5 rounded">${item.tipo_demanda}</span>
        </td>
        <td class="px-5 py-3.5 text-xs text-slate-600">${vitais}</td>
        <td class="px-5 py-3.5 text-xs text-slate-500 font-mono">${hora}</td>
        <td class="px-5 py-3.5 text-right">
          <button onclick="iniciarAtendimento(${item.id})" class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm flex items-center space-x-1 ml-auto">
            <i class="fa-solid fa-stethoscope"></i>
            <span>Atender (SOAP)</span>
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
      select.innerHTML = cidadaosCache.map(c => `<option value="${c.id}">${c.nome_completo} (CPF: ${c.cpf || 'Sem CPF'} | CNS: ${c.cns || '--'})</option>`).join("");
    }

    // Atualizar cards
    const container = document.getElementById("cards-cidadaos");
    if (!container) return;
    container.innerHTML = "";

    cidadaosCache.forEach(c => {
      const card = document.createElement("div");
      card.className = "bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2";
      card.innerHTML = `
        <div class="flex items-start justify-between">
          <div>
            <h4 class="font-bold text-slate-800">${c.nome_completo}</h4>
            <div class="text-xs text-slate-400">Nasc: ${c.data_nascimento} | Sexo: ${c.sexo}</div>
          </div>
          <span class="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-mono">ID ${c.id}</span>
        </div>
        <div class="text-xs text-slate-600 space-y-0.5 pt-1">
          <div><span class="font-medium">CPF:</span> ${c.cpf || '--'} | <span class="font-medium">CNS:</span> ${c.cns || '--'}</div>
          <div><span class="font-medium">Mãe:</span> ${c.nome_mae || '--'}</div>
          <div><span class="font-medium">Endereço:</span> ${c.logradouro || ''}, ${c.numero || ''} - ${c.bairro || ''}</div>
        </div>
        <div class="flex flex-wrap gap-1 pt-2">
          ${c.hipertenso ? '<span class="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded">Hipertenso</span>' : ''}
          ${c.diabetico ? '<span class="text-[10px] bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded">Diabético</span>' : ''}
          ${c.alergias ? `<span class="text-[10px] bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">Alergia: ${c.alergias}</span>` : ''}
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

async function acionarCopilotIA() {
  const relato = document.getElementById("copilot-input-relato").value.trim();
  if (!relato) {
    alert("Digite ou cole um relato clínico para a IA analisar.");
    return;
  }

  const btn = document.getElementById("btn-copilot-ia");
  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i><span>Analisando...</span>`;
  btn.disabled = true;

  try {
    const payload = {
      relato_clinico: relato,
      cidadao_id: pacienteAtivo ? pacienteAtivo.id : null,
      pressao_aferida: document.getElementById("soap-pa").textContent !== '--' ? document.getElementById("soap-pa").textContent : null
    };

    const res = await fetch("/api/v1/copilot/gerar-soap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      alert("Erro ao comunicar com o Copilot IA.");
      return;
    }

    const data = await res.json();

    // Preencher campos do SOAP
    document.getElementById("soap-motivo").value = data.subjetivo_motivo || "";
    document.getElementById("soap-subjetivo-notas").value = data.subjetivo_notas || "";
    document.getElementById("soap-exame-fisico").value = data.objetivo_exame_fisico || "";
    document.getElementById("soap-avaliacao-notas").value = data.avaliacao_notas || "";
    document.getElementById("soap-conduta").value = data.plano_conduta || "";
    document.getElementById("soap-prescricao").value = data.plano_prescricoes || "";
    document.getElementById("soap-exames").value = data.plano_exames || "";

    // Anexar problemas CIAP-2 e CID-10 sugeridos
    if (data.problemas_sugeridos && data.problemas_sugeridos.length > 0) {
      data.problemas_sugeridos.forEach(p => {
        adicionarProblema(p.tipo_codigo, p.codigo, p.descricao);
      });
    }

    // Exibir alertas de segurança se houver
    const alertasContainer = document.getElementById("copilot-alertas-container");
    alertasContainer.innerHTML = "";
    if (data.alertas_seguranca && data.alertas_seguranca.length > 0) {
      alertasContainer.classList.remove("hidden");
      data.alertas_seguranca.forEach(a => {
        const div = document.createElement("div");
        div.className = "bg-amber-500/20 border border-amber-400 text-amber-200 text-xs px-3 py-1.5 rounded-lg flex items-center gap-2";
        div.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-amber-300"></i><span>${a}</span>`;
        alertasContainer.appendChild(div);
      });
    } else {
      alertasContainer.classList.add("hidden");
    }

  } catch (err) {
    console.error("Erro no Copilot:", err);
    alert("Falha ao processar com IA.");
  } finally {
    btn.innerHTML = originalHtml;
    btn.disabled = false;
  }
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
