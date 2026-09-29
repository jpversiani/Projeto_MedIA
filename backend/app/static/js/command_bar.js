/**
 * MedIA Practice OS — Command Bar & Global Shortcuts (⌘K / Ctrl+K)
 * Sistema de navegação global e atalhos clínicos rápidos.
 */

class CommandBar {
  constructor() {
    this.isOpen = false;
    this.actions = [
      { id: "nova_consulta", titulo: "Agendar Nova Consulta", icone: "fa-calendar-plus text-blue-400", kbd: "N", categoria: "Ações Clínicas" },
      { id: "emitir_receita", titulo: "Emitir Prescrição com QR Code (CFM)", icone: "fa-file-prescription text-emerald-400", kbd: "P", categoria: "Ações Clínicas" },
      { id: "emitir_atestado", titulo: "Emitir Atestado Médico Digital", icone: "fa-file-medical text-indigo-400", kbd: "A", categoria: "Ações Clínicas" },
      { id: "alternar_modo", titulo: "Alternar Consultório Presencial / Telemedicina", icone: "fa-repeat text-purple-400", kbd: "M", categoria: "Ações Clínicas" },
      { id: "alternar_tema", titulo: "Alternar Tema Escuro / Claro", icone: "fa-circle-half-stroke text-amber-400", kbd: "Ctrl J", categoria: "Preferências" },
      { id: "exportar_dmed", titulo: "Gerar Arquivo Magnético DMED (Receita Federal)", icone: "fa-file-invoice text-rose-400", kbd: "D", categoria: "Financeiro" },
      { id: "exportar_tiss", titulo: "Exportar Lote XML TISS 4.01 (ANS)", icone: "fa-file-code text-cyan-400", kbd: "X", categoria: "Financeiro" },
      { id: "trilha_auditoria", titulo: "Trilha de Auditoria Criptográfica (SHA-256)", icone: "fa-shield-halved text-emerald-400", kbd: "L", categoria: "Segurança" },
      { id: "guia_atalhos", titulo: "Ver Guia de Atalhos de Teclado", icone: "fa-keyboard text-slate-400", kbd: "?", categoria: "Ajuda" },
      
      // Navegação
      { id: "nav_agenda", titulo: "Ir para Agenda de Consultas", icone: "fa-calendar-day text-blue-400", kbd: "Alt 1", categoria: "Navegação" },
      { id: "nav_telemedicina", titulo: "Ir para Sala de Telemedicina WebRTC", icone: "fa-video text-teal-400", kbd: "Alt 2", categoria: "Navegação" },
      { id: "nav_prontuario", titulo: "Ir para Prontuário Eletrônico & SOAP", icone: "fa-notes-medical text-indigo-400", kbd: "Alt 3", categoria: "Navegação" },
      { id: "nav_pacientes", titulo: "Ir para Gestão de Pacientes", icone: "fa-users text-cyan-400", kbd: "Alt 4", categoria: "Navegação" },
      { id: "nav_convenios", titulo: "Ir para Convênios & Guias TISS", icone: "fa-file-invoice-dollar text-blue-400", kbd: "Alt 5", categoria: "Navegação" },
      { id: "nav_farmacia", titulo: "Ir para Farmácia & Dispensação", icone: "fa-pills text-emerald-400", kbd: "Alt 6", categoria: "Navegação" },
      { id: "nav_analytics", titulo: "Ir para Painel de Analytics & KPIs", icone: "fa-chart-line text-amber-400", kbd: "Alt 7", categoria: "Navegação" },
      { id: "nav_honorarios", titulo: "Ir para Honorários & DMED", icone: "fa-receipt text-rose-400", kbd: "Alt 8", categoria: "Navegação" },
    ];
    this.initDOM();
    this.initEvents();
  }

  initDOM() {
    let modal = document.getElementById("command-bar-modal");
    if (modal) modal.remove();

    modal = document.createElement("div");
    modal.id = "command-bar-modal";
    modal.className = "fixed inset-0 bg-slate-950/75 backdrop-blur-md z-50 flex items-start justify-center pt-20 hidden p-4";
    modal.innerHTML = `
      <div class="bg-[#0b1220] border border-slate-700/80 rounded-2xl shadow-2xl max-w-xl w-full overflow-hidden flex flex-col text-slate-100">
        <div class="flex items-center px-4 py-3.5 border-b border-slate-800 gap-3">
          <i class="fa-solid fa-magnifying-glass text-blue-400 text-sm"></i>
          <input type="text" id="cmd-input" placeholder="Buscar comando, aba ou atalho clínico... (Esc para fechar)" class="bg-transparent flex-1 text-sm text-slate-100 focus:outline-none placeholder-slate-500 font-sans">
          <kbd class="text-[10px] font-mono bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">ESC</kbd>
        </div>
        
        <div class="max-h-96 overflow-y-auto p-2 space-y-1 text-xs" id="cmd-results">
          <!-- Renderizado dinamicamente -->
        </div>

        <div class="px-4 py-2.5 border-t border-slate-800/80 bg-slate-950/60 flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span class="flex items-center gap-1.5"><i class="fa-solid fa-bolt text-amber-400"></i> MedIA Practice Command Engine</span>
          <span>Navegue com clique ou atalho</span>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  renderResults(query = "") {
    const container = document.getElementById("cmd-results");
    if (!container) return;

    const q = query.trim().toLowerCase();
    const filtradas = this.actions.filter(a => 
      !q || a.titulo.toLowerCase().includes(q) || a.categoria.toLowerCase().includes(q) || a.id.includes(q)
    );

    if (filtradas.length === 0) {
      container.innerHTML = `
        <div class="py-8 text-center text-slate-500">
          <i class="fa-solid fa-ghost text-2xl mb-2"></i>
          <p>Nenhuma ação encontrada para "${query}"</p>
        </div>
      `;
      return;
    }

    let html = "";
    let ultimaCat = "";

    filtradas.forEach(a => {
      if (a.categoria !== ultimaCat) {
        ultimaCat = a.categoria;
        html += `<div class="px-3 pt-2 pb-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">${ultimaCat}</div>`;
      }
      html += `
        <button onclick="CommandBar.exec('${a.id}')" class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-800/80 text-left transition-colors group">
          <span class="flex items-center gap-2.5 font-medium text-slate-200 group-hover:text-white">
            <i class="fa-solid ${a.icone} w-4 text-center"></i> ${a.titulo}
          </span>
          <kbd class="text-[9px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 group-hover:border-slate-700">${a.kbd}</kbd>
        </button>
      `;
    });

    container.innerHTML = html;
  }

  initEvents() {
    window.addEventListener("keydown", (e) => {
      const tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : "";
      const isInput = tag === "input" || tag === "textarea" || tag === "select";

      // ⌘K ou Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        this.toggle();
        return;
      }

      // Ctrl+J: alternar tema
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "j") {
        e.preventDefault();
        alternarTema?.();
        return;
      }

      // Ctrl+S: Concluir consulta / Salvar SOAP
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        concluirConsulta?.();
        return;
      }

      // ?: Abrir atalhos se não estiver digitando
      if (e.key === "?" && !isInput) {
        e.preventDefault();
        abrirModalAtalhos?.();
        return;
      }

      // Alt + 1..8: Navegação de abas direta
      if (e.altKey && e.key >= "1" && e.key <= "8") {
        e.preventDefault();
        const abas = ["agenda", "telemedicina", "prontuario", "pacientes", "convenios", "farmacia", "analytics", "honorarios"];
        const idx = parseInt(e.key, 10) - 1;
        if (abas[idx]) trocarAba(abas[idx]);
        return;
      }

      // ESC: Fechar Command Bar ou Modais
      if (e.key === "Escape") {
        if (this.isOpen) {
          this.close();
          return;
        }
        fecharModaisAbertos?.();
      }
    });

    const modal = document.getElementById("command-bar-modal");
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) this.close();
      });
    }

    const input = document.getElementById("cmd-input");
    if (input) {
      input.addEventListener("input", (e) => {
        this.renderResults(e.target.value);
      });
    }
  }

  toggle() {
    this.isOpen ? this.close() : this.open();
  }

  open() {
    this.isOpen = true;
    const modal = document.getElementById("command-bar-modal");
    if (!modal) return;
    modal.classList.remove("hidden");
    this.renderResults("");
    const input = document.getElementById("cmd-input");
    if (input) {
      input.value = "";
      input.focus();
    }
  }

  close() {
    this.isOpen = false;
    const modal = document.getElementById("command-bar-modal");
    if (modal) modal.classList.add("hidden");
  }

  static exec(action) {
    window.medIACommandBar?.close();

    switch (action) {
      case "nova_consulta":
        abrirModalNovoAgendamento?.();
        break;
      case "emitir_receita":
        abrirModalPrescricaoDigital?.("SIMPLES");
        break;
      case "emitir_atestado":
        abrirModalAtestadoDigital?.();
        break;
      case "alternar_modo":
        const proxModo = (modoTrabalhoAtual === "CONSULTORIO") ? "TELEMEDICINA" : "CONSULTORIO";
        alternarModoTrabalho?.(proxModo);
        break;
      case "alternar_tema":
        alternarTema?.();
        break;
      case "exportar_dmed":
        gerarLoteDMED?.();
        break;
      case "exportar_tiss":
        exportarLoteXMLTISS?.();
        break;
      case "trilha_auditoria":
        abrirModalAuditoria?.();
        break;
      case "guia_atalhos":
        abrirModalAtalhos?.();
        break;
      case "nav_agenda":
        trocarAba?.("agenda");
        break;
      case "nav_telemedicina":
        trocarAba?.("telemedicina");
        break;
      case "nav_prontuario":
        trocarAba?.("prontuario");
        break;
      case "nav_pacientes":
        trocarAba?.("pacientes");
        break;
      case "nav_convenios":
        trocarAba?.("convenios");
        break;
      case "nav_farmacia":
        trocarAba?.("farmacia");
        break;
      case "nav_analytics":
        trocarAba?.("analytics");
        break;
      case "nav_honorarios":
        trocarAba?.("honorarios");
        break;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.medIACommandBar = new CommandBar();
});
