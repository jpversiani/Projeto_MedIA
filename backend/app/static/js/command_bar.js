/**
 * MedIA Health OS — Command Bar (⌘K / Ctrl+K)
 * Sistema de busca e navegação global rápida no estilo Linear / Superhuman.
 */

class CommandBar {
  constructor() {
    this.isOpen = false;
    this.initDOM();
    this.initEvents();
  }

  initDOM() {
    const modal = document.createElement("div");
    modal.id = "command-bar-modal";
    modal.className = "fixed inset-0 bg-slate-950/70 backdrop-blur-md z-50 flex items-start justify-center pt-24 hidden p-4";
    modal.innerHTML = `
      <div class="bg-[#0b1220] border border-slate-700/80 rounded-2xl shadow-2xl max-w-xl w-full overflow-hidden flex flex-col text-slate-100">
        <div class="flex items-center px-4 py-3 border-b border-slate-800 gap-3">
          <i class="fa-solid fa-magnifying-glass text-slate-400 text-sm"></i>
          <input type="text" id="cmd-input" placeholder="Buscar ação, paciente ou atalho clínico... (Esc para sair)" class="bg-transparent flex-1 text-sm text-slate-100 focus:outline-none placeholder-slate-500 font-sans">
          <kbd class="text-[10px] font-mono bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">ESC</kbd>
        </div>
        
        <div class="max-h-80 overflow-y-auto p-2 space-y-1 text-xs" id="cmd-results">
          <div class="px-3 py-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Ações Rápidas</div>
          
          <button onclick="CommandBar.exec('nova_triagem')" class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-800/80 text-left transition-colors group">
            <span class="flex items-center gap-2.5 font-medium"><i class="fa-solid fa-user-plus text-blue-400 w-4"></i> Novo Acolhimento / Triagem</span>
            <kbd class="text-[9px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">T</kbd>
          </button>

          <button onclick="CommandBar.exec('trilha_lgpd')" class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-800/80 text-left transition-colors group">
            <span class="flex items-center gap-2.5 font-medium"><i class="fa-solid fa-shield-halved text-emerald-400 w-4"></i> Inspecionar Ledger LGPD (SHA-256)</span>
            <kbd class="text-[9px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">L</kbd>
          </button>

          <button onclick="CommandBar.exec('calc_framingham')" class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-800/80 text-left transition-colors group">
            <span class="flex items-center gap-2.5 font-medium"><i class="fa-solid fa-heart-pulse text-rose-400 w-4"></i> Calculadora Cardiovascular Framingham</span>
            <kbd class="text-[9px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">F</kbd>
          </button>

          <button onclick="CommandBar.exec('calc_ckdepi')" class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-800/80 text-left transition-colors group">
            <span class="flex items-center gap-2.5 font-medium"><i class="fa-solid fa-droplet text-cyan-400 w-4"></i> Taxa Filtração Glomerular (CKD-EPI)</span>
            <kbd class="text-[9px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">R</kbd>
          </button>

          <div class="px-3 py-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-wider mt-2">Navegação</div>

          <button onclick="CommandBar.exec('nav_fila')" class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-800/80 text-left transition-colors group">
            <span class="flex items-center gap-2.5 font-medium"><i class="fa-solid fa-list-check text-indigo-400 w-4"></i> Ir para Fila de Atendimento</span>
            <kbd class="text-[9px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">1</kbd>
          </button>

          <button onclick="CommandBar.exec('nav_familia')" class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-800/80 text-left transition-colors group">
            <span class="flex items-center gap-2.5 font-medium"><i class="fa-solid fa-users text-teal-400 w-4"></i> Ir para Saúde da Família (1.501 Cidadãos)</span>
            <kbd class="text-[9px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">2</kbd>
          </button>

          <button onclick="CommandBar.exec('nav_soap')" class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-800/80 text-left transition-colors group">
            <span class="flex items-center gap-2.5 font-medium"><i class="fa-solid fa-wand-magic-sparkles text-amber-400 w-4"></i> Abrir Copiloto SOAP</span>
            <kbd class="text-[9px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">3</kbd>
          </button>
        </div>

        <div class="px-4 py-2 border-t border-slate-800/80 bg-slate-950/60 flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <span>MedIA Command System</span>
          <span>Navegue com ↑ ↓ e Enter</span>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  initEvents() {
    window.addEventListener("keydown", (e) => {
      // ⌘K ou Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        this.toggle();
      }
      if (e.key === "Escape" && this.isOpen) {
        this.close();
      }
    });

    const modal = document.getElementById("command-bar-modal");
    modal.addEventListener("click", (e) => {
      if (e.target === modal) this.close();
    });
  }

  toggle() {
    this.isOpen ? this.close() : this.open();
  }

  open() {
    this.isOpen = true;
    const modal = document.getElementById("command-bar-modal");
    modal.classList.remove("hidden");
    const input = document.getElementById("cmd-input");
    input.value = "";
    input.focus();
  }

  close() {
    this.isOpen = false;
    const modal = document.getElementById("command-bar-modal");
    modal.classList.add("hidden");
  }

  static exec(action) {
    window.medIACommandBar?.close();
    if (action === "nova_triagem") {
      abrirModalAcolhimento?.();
    } else if (action === "trilha_lgpd") {
      abrirModalAuditoria?.();
    } else if (action === "nav_fila") {
      trocarAba?.('fila');
    } else if (action === "nav_familia") {
      trocarAba?.('cidadaos');
    } else if (action === "nav_soap") {
      trocarAba?.('soap');
    } else if (action === "calc_framingham") {
      trocarAba?.('soap');
      alert("Calculadora de Framingham disponível no endpoint POST /api/v1/clinica/framingham.");
    } else if (action === "calc_ckdepi") {
      trocarAba?.('soap');
      alert("Calculadora de Função Renal CKD-EPI disponível no endpoint POST /api/v1/clinica/ckd-epi.");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.medIACommandBar = new CommandBar();
});
