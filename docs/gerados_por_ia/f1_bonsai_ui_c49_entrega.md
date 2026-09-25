# Painel Visual de Chamada de Teleconsulta - MedIA

Abaixo está a solução completa com arquivos estruturados conforme as diretrizes SUS/APS, tipagem estrita, e cobertura de testes.

---

## 1. Arquivo Principal: `telemedicina_sala.html`

```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sala de Teleconsulta — MedIA</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    body {
      font-family: 'Inter', sans-serif;
      background: #0f172a;
      color: #e2e8f0;
    }
    .glass-panel {
      background: rgba(30, 41, 59, 0.7);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .glass-panel:hover {
      border-color: rgba(255, 255, 255, 0.15);
    }
    .video-container {
      position: relative;
      overflow: hidden;
      border-radius: 0.5rem;
    }
    .video-container .overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.6);
      border-radius: 0.5rem;
    }
    .video-container .overlay .icon {
      font-size: 3rem;
      opacity: 0.8;
    }
    .control-bar {
      position: sticky;
      top: 0;
      left: 0;
      right: 0;
      z-index: 50;
      padding: 0.5rem 1rem;
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .chat-panel {
      transition: transform 0.3s ease;
    }
    .chat-panel.collapsed {
      transform: translateX(-100%);
    }
    .chat-panel.open {
      transform: translateX(0);
    }
    .msg-bubble {
      max-width: 80%;
      border-radius: 1rem;
      padding: 0.5rem 0.75rem;
      word-wrap: break-word;
    }
    .msg-bubble.sent {
      background: rgba(59, 130, 246, 0.2);
      color: #3b82f6;
      border-bottom-right-radius: 4px;
      margin-bottom: 0.25rem;
    }
    .msg-bubble.received {
      background: rgba(148, 163, 184, 0.2);
      color: #94a3b8;
      border-bottom-left-radius: 4px;
      margin-bottom: 0.25rem;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
    }
    .status-dot.online { background: #10b981; }
    .status-dot.offline { background: #ef4444; }
    .status-dot.connecting { background: #f59e0b; animation: pulse 1.5s infinite; }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }
    .btn-primary {
      background: linear-gradient(135deg, #3b82f6, #2563eb);
      color: white;
      border: none;
      border-radius: 0.5rem;
      padding: 0.5rem 1rem;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.2s;
    }
    .btn-primary:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.08);
      color: #e2e8f0;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 0.5rem;
      padding: 0.5rem 1rem;
      cursor: pointer;
      font-weight: 500;
      transition: all 0.2s;
    }
    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.15);
    }
    .btn-danger {
      background: rgba(239, 68, 68, 0.15);
      color: #ef4444;
      border: 1px solid rgba(239, 68, 68, 0.3);
      border-radius: 0.5rem;
      padding: 0.5rem 1rem;
      cursor: pointer;
      font-weight: 500;
      transition: all 0.2s;
    }
    .btn-danger:hover {
      background: rgba(239, 68, 68, 0.3);
    }
    .scrollbar-thin::-webkit-scrollbar {
      width: 4px;
    }
    .scrollbar-thin::-webkit-scrollbar-track {
      background: transparent;
    }
    .scrollbar-thin::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.2);
      border-radius: 2px;
    }
    .scrollbar-thin::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.35);
    }
    .suspension-badge {
      background: rgba(59, 130, 246, 0.15);
      color: #3b82f6;
      border: 1px solid rgba(59, 130, 246, 0.3);
      border-radius: 0.25rem;
      padding: 0.15rem 0.4rem;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.05em;
    }
    .suspension-badge.cip-2 {
      background: rgba(16, 185, 129, 0.15);
      color: #10b981;
      border-color: rgba(16, 185, 129, 0.3);
    }
    .suspension-badge.cid-10 {
      background: rgba(245, 158, 11, 0.15);
      color: #f59e0b;
      border-color: rgba(245, 158, 11, 0.3);
    }
  </style>
</head>
<body class="h-screen flex flex-col">

  <!-- ======================================== -->
  <!--  BARRA DE CONTROLE (Sticky Top)          -->
  <!-- ======================================== -->
  <header class="control-bar">
    <div class="max-w-7xl mx-auto w-full flex items-center justify-between">
      <!-- Left: Identification & Status -->
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="status-dot online"></span>
          <span class="text-sm font-semibold text-slate-300">
            <span class="text-xs text-slate-500 uppercase tracking-wider">CNS</span>
            <span class="text-sm">123456789</span>
          </span>
        </div>
        <div class="flex gap-1.5">
          <span class="suspension-badge cip-2">CIP-2</span>
          <span class="suspension-badge cid-10">CID-10</span>
        </div>
      </div>

      <!-- Center: Patient Info -->
      <div class="hidden md:flex items-center gap-4">
        <div class="text-center">
          <div class="text-xs text-slate-500 uppercase tracking-wider">Médico</div>
          <div class="text-sm font-semibold text-slate-200">Dr. Silva</div>
        </div>
        <div class="w-px h-8 bg-slate-700"></div>
        <div class="text-center">
          <div class="text-xs text-slate-500 uppercase tracking-wider">Paciente</div>
          <div class="text-sm font-semibold text-slate-200">Maria Santos</div>
        </div>
      </div>

      <!-- Right: Controls -->
      <div class="flex items-center gap-2">
        <button
          id="btn-mute"
          class="btn-secondary flex items-center gap-1.5"
          title="Mutar / Desmutar"
        >
          <svg id="icon-mute" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15.536 8.464a5 5 0 010 7.072" />
            <path d="M17 14a1 1 0 01-1 1v6a1 1 0 01-1-1V7a1 1 0 011-1h2a1 1 0 011 1v7a1 1 0 01-1 1z" />
          </svg>
          <span id="label-mute">Mutar</span>
        </button>
        <button
          id="btn-video"
          class="btn-secondary flex items-center gap-1.5"
          title="Ativar / Desativar Vídeo"
        >
          <svg id="icon-video" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <polygon points="9 9 15 9 15 15 9 15" />
            <circle cx="12" cy="12" r="2" />
          </svg>
          <span id="label-video">Vídeo</span>
        </button>
        <button
          id="btn-chat"
          class="btn-secondary flex items-center gap-1.5"
          title="Abrir Chat"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17.5 21v-2a9 9 0 00-5.5-8.5H5.5a9 9 0 00-5.5 8.5v2" />
            <path d="M17.5 21h2.5" />
            <path d="M12 15v2" />
            <path d="M15 15v2" />
            <path d="M17.5 21h2.5" />
          </svg>
          <span id="label-chat">Chat</span>
        </button>
        <button
          id="btn-close"
          class="btn-danger flex items-center gap-1.5"
          title="Encerrar Sessão"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
          <span>Encerrar</span>
        </button>
      </div>
    </div>
  </header>

  <!-- ======================================== -->
  <!--  PRINCIPAL: GRID VÍDEO + CHAT            -->
  <!-- ======================================== -->
  <main class="flex-1 flex overflow-hidden">
    <!-- Left: Video Grid -->
    <section class="flex-1 flex flex-col md:flex-row relative">
      <!-- Doctor Panel -->
      <div class="flex-1 flex flex-col md:w-1/2 md:h-auto">
        <div class="flex items-center justify-between p-3 border-b border-slate-700/50">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold text-white">
              D
            </div>
            <div>
              <div class="text-xs font-semibold text-slate-200">Médico</div>
              <div class="text-xs text-slate-500">Dr. Silva — Cardiorespiratório</div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="status-dot online"></span>
            <span class="text-xs text-slate-400">CNS: 123456789</span>
          </div>
