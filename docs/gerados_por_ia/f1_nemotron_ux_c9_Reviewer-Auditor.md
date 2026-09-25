 ```html
<!-- Arquivo: backend/app/static/cockpit_clinico.html -->
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MedIA — Cockpit Clínico Unificado</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Ajustes personalizados para melhor experiência médica */
        .soap-textarea {
            resize: none;
            min-height: 120px;
            line-height: 1.5;
        }
        .section-title {
            @apply text-sm font-semibold text-gray-600 uppercase tracking-wide;
        }
        .btn-icon {
            @apply p-2 rounded-full hover:bg-gray-200 transition-colors;
        }
        .modal-overlay {
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(4px);
        }
        .video-placeholder {
            background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
        }
        .badge {
            @apply px-2 py-0.5 rounded-full text-xs font-medium;
        }
    </style>
</head>
<body class="bg-gray-100 h-screen flex flex-col overflow-hidden">

    <!-- Header -->
    <header class="bg-white shadow-md px-4 py-2 flex items-center justify-between z-10">
        <div class="flex items-center gap-3">
            <span class="text-2xl font-bold text-blue-700">Med<span class="text-blue-500">IA</span></span>
            <span class="text-gray-400 border-l pl-3 text-sm">Cockpit Clínico</span>
        </div>
        <div class="flex items-center gap-4">
            <div class="text-right">
                <p class="text-sm font-medium text-gray-700">Paciente: Maria da Silva</p>
                <p class="text-xs text-gray-400">42 anos · Feminino · 12/03/2025 14:30</p>
            </div>
            <button id="btn-fechar-atendimento" class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg shadow transition-colors">
                <i class="fas fa-check-circle mr-2"></i>Fechar Atendimento
            </button>
        </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 p-4 overflow-hidden">

        <!-- ========== VÍDEO WEBRTC ========== -->
        <section class="bg-white rounded-xl shadow-lg p-4 flex flex-col min-h-0">
            <h2 class="section-title mb-3 flex items-center gap-2">
                <span class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span> Teleconsulta
            </h2>
            <div class="flex-1 grid grid-rows-2 gap-3 min-h-0">
                <!-- Vídeo remoto -->
                <div class="relative rounded-lg overflow-hidden bg-gray-800 video-placeholder flex items-center justify-center">
                    <video id="remoteVideo" class="w-full h-full object-cover" autoplay playsinline></video>
                    <div id="remotePlaceholder" class="absolute inset-0 flex flex-col items-center justify-center text-white">
                        <svg class="w-16 h-16 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        <p class="text-sm mt-2">Aguardando conexão...</p>
                    </div>
                </div>
                <!-- Vídeo local -->
                <div class="relative rounded-lg overflow-hidden bg-gray-700">
                    <video id="localVideo" class="w-full h-full object-cover" autoplay muted playsinline></video>
                    <span class="absolute bottom-2 left-2 bg-black/50 text-white text-xs px-2 py-1 rounded">Você</span>
                </div>
            </div>
            <!-- Controles -->
            <div class="flex justify-center gap-2 mt-4">
                <button id="btn-toggle-camera" class="btn-icon bg-gray-100 text-gray-700" title="Ligar/Desligar câmera">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                </button>
                <button id="btn-toggle-mic" class="btn-icon bg-gray-100 text-gray-700" title="Ligar/Desligar microfone">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11a7 7 0 01-14 0M12 4a3 3 0 00-3 3v4a3 3 0 006 0V7a3 3 0 00-3-3zM5 19h14" />
                    </svg>
                </button>
                <button id="btn-share-screen" class="btn-icon bg-gray-100 text-gray-700" title="Compartilhar tela">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                </button>
                <button id="btn-end-call" class="btn-icon bg-red-100 text-red-600" title="Encerrar chamada">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M4 16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-2c0-1.1-.9-2-2-2H6c-1.1 0-2 .9-2 2v2z" />
                    </svg>
                </button>
            </div>
        </section>

        <!-- ========== EDITOR SOAP ========== -->
        <section class="bg-white rounded-xl shadow-lg p-4 flex flex-col min-h-0">
            <div class="flex items-center justify-between mb-3">
                <h2 class="section-title">Prontuário SOAP</h2>
                <span id="soap-status" class="text-xs text-gray-400">Salvando...</span>
            </div>
            <div class="flex-1 grid grid-rows-4 gap-3 min-h-0">
                <!-- S -->
                <div class="flex flex-col">
                    <label class="text-xs font-medium text