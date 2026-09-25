```html
<!-- Arquivo: backend/app/static/cockpit_clinico.html -->
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cockpit Clínico Unificado - MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        /* Estilos adicionais para melhorar a experiência */
        .auto-save-indicator {
            transition: opacity 0.3s;
        }
        .soap-textarea {
            min-height: 120px;
            resize: vertical;
        }
        .copilot-suggestion {
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .copilot-suggestion:hover {
            background-color: #f0f9ff;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto p-4">
        <!-- Cabeçalho -->
        <header class="bg-white shadow rounded-lg p-4 mb-4 flex items-center justify-between">
            <div class="flex items-center space-x-4">
                <h1 class="text-2xl font-bold text-blue-800">Cockpit Clínico</h1>
                <span class="text-sm text-gray-500">Paciente: Maria da Silva</span>
            </div>
            <div class="flex items-center space-x-2">
                <button id="btn-fechamento" class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg shadow">
                    <i class="fas fa-file-medical mr-2"></i>Fechamento Rápido
                </button>
                <button id="btn-sair" class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-2 px-4 rounded-lg">
                    <i class="fas fa-sign-out-alt mr-2"></i>Sair
                </button>
            </div>
        </header>

        <!-- Grid principal: 3 colunas -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <!-- Coluna 1: Vídeo WebRTC -->
            <div class="bg-white shadow rounded-lg p-4">
                <h2 class="text-lg font-semibold mb-3 text-gray-800"><i class="fas fa-video mr-2 text-blue-600"></i>Vídeo Consulta</h2>
                <div class="aspect-w-16 aspect-h-9 bg-gray-200 rounded-lg overflow-hidden mb-3">
                    <!-- Área de vídeo -->
                    <video id="remote-video" autoplay playsinline class="w-full h-full object-cover"></video>
                    <div id="video-placeholder" class="flex items-center justify-center h-full text-gray-500">
                        <i class="fas fa-user-circle text-6xl"></i>
                    </div>
                </div>
                <!-- Controles -->
                <div class="flex justify-center space-x-2">
                    <button id="btn-toggle-camera" class="bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-full shadow" title="Ligar/Desligar câmera">
                        <i class="fas fa-video"></i>
                    </button>
                    <button id="btn-toggle-mic" class="bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-full shadow" title="Ligar/Desligar microfone">
                        <i class="fas fa-microphone"></i>
                    </button>
                    <button id="btn-end-call" class="bg-red-500 hover:bg-red-600 text-white p-3 rounded-full shadow" title="Encerrar chamada">
                        <i class="fas fa-phone-slash"></i>
                    </button>
                </div>
                <div class="mt-3 text-sm text-gray-600">
                    <p><i class="fas fa-info-circle mr-1"></i>Status: <span id="call-status">Em espera</span></p>
                </div>
            </div>

            <!-- Coluna 2: Editor SOAP -->
            <div class="bg-white shadow rounded-lg p-4">
                <div class="flex items-center justify-between mb-3">
                    <h2 class="text-lg font-semibold text-gray-800"><i class="fas fa-notes-medical mr-2 text-green-600"></i>Prontuário SOAP</h2>
                    <span id="auto-save-indicator" class="text-xs text-gray-500 auto-save-indicator"><i class="fas fa-save mr-1"></i>Salvo</span>
                </div>
                <form id="soap-form" class="space-y-4">
                    <div>
                        <label for="subjetivo" class="block text-sm font-medium text-gray-700">S (Subjetivo)</label>
                        <textarea id="subjetivo" name="subjetivo" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 soap-textarea" placeholder="Queixa principal, história da doença atual..."></textarea>
                    </div>
                    <div>
                        <label for="objetivo" class="block text-sm font-medium text-gray-700">O (Objetivo)</label>
                        <textarea id="objetivo" name="objetivo" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 soap-textarea" placeholder="Exame físico, sinais vitais, resultados..."></textarea>
                    </div>
                    <div>
                        <label for="avaliacao" class="block text-sm font-medium text-gray-700">A (Avaliação)</label>
                        <textarea id="avaliacao" name="avaliacao" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 soap-textarea" placeholder="Diagnóstico, hipóteses, CIAP-2/CID-10..."></textarea>
                    </div>
                    <div>
                        <label for="plano" class="block text-sm font-medium text-gray-700">P (Plano)</label>
                        <textarea id="plano" name="plano" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 soap-textarea" placeholder="Conduta, medicações, encaminhamentos..."></textarea>
                    </div>
                </form>
            </div>

            <!-- Coluna 3: Copiloto IA -->
            <div class="bg-white shadow rounded-lg p-4">
                <h2 class="text-lg font-semibold mb-3 text-gray-800"><i class="fas fa-robot mr-2 text-purple-600"></i>Copiloto IA</h2>
                <div class="space-y-4">
                    <div>
                        <h3 class="text-sm font-medium text-gray-700 mb-2">Sugestões de Classificação</h3>
                        <div id="sugestoes-ciap" class="space-y-2">
                            <!-- Sugestões serão preenchidas via JS -->
                        </div>
                    </div>
                    <div>
                        <h3 class="text-sm font-medium text-gray-700 mb-2">Condutas Recomendadas</h3>
                        <div id="sugestoes-conduta" class="space-y-2">
                            <!-- Sugestões de conduta -->
                        </div>
                    </div>
                    <div class="border-t pt-3">
                        <button id="btn-gerar-sugestoes" class="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg">
                            <i class="fas fa-magic mr-2"></i>Gerar Sugestões
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal de Fechamento Rápido -->
        <div id="modal-fechamento" class="hidden fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Fechamento Rápido</h3>
                    <div class="space-y-3">
                        <button id="btn-gerar-tiss" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg">
                            <i class="fas fa-file-invoice mr-2"></i>Gerar Guia TISS
                        </button>
                        <button id="btn-gerar-dmed" class="w-full bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-2 px-4 rounded-lg">
                            <i class="fas fa-receipt mr-2"></i>Gerar Recibo DMED
                        </button>
                        <button id="btn-fechar-modal" class="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-2 px-4 rounded-lg">
                            Cancelar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // ====== Lógica do Cockpit ======

        // Auto-save no navegador (localStorage)
        const soapFields = ['subjetivo', 'objetivo', 'avaliacao', 'plano'];
        const autoSaveIndicator = document.getElementById('auto-save-indicator');
        let saveTimeout;

        // Carregar dados salvos
        function loadSavedData() {
            const saved = localStorage.getItem('soapData');
            if (saved) {
                const data = JSON.parse(saved);
                soapFields.forEach(field => {
                    if (data[field]) {
                        document.getElementById(field).value = data[field];
                    }
                });
            }
        }

        // Salvar dados
        function saveData() {
            const data = {};
            soapFields.forEach(field => {
                data[field] = document.getElementById(field).value;
            });
            localStorage.setItem('soapData', JSON.stringify(data));
            autoSaveIndicator.innerHTML = '<i class="fas fa-check mr-1"></i>Salvo';
            autoSaveIndicator.classList.remove('text-gray-500');
            autoSaveIndicator.classList.add('text-green-600');
            setTimeout(() => {
                autoSaveIndicator.classList.add('text-gray-500');
                autoSaveIndicator.classList.remove('text-green-600');
            }, 2000);
        }

        // Evento de input para auto-save
        soapFields.forEach(field => {
            document.getElementById(field).addEventListener('input', () => {
                clearTimeout(saveTimeout);
                autoSaveIndicator.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Salvando...';
                autoSaveIndicator.classList.remove('text-gray-500');
                autoSaveIndicator.classList.add('text-blue-600');
                saveTimeout = setTimeout(saveData, 1000);
            });
        });

        // Carregar dados ao iniciar
        loadSavedData();

        // ====== Vídeo WebRTC (simulação) ======
        const remoteVideo = document.getElementById('remote-video');
        const videoPlaceholder = document.getElementById('video-placeholder');
        const callStatus = document.getElementById('call-status');
        let isCameraOn = false;
        let isMicOn = false;

        // Simular conexão WebRTC (apenas para demonstração)
        document.getElementById('btn-toggle-camera').addEventListener('click', () => {
            isCameraOn = !isCameraOn;
            if (isCameraOn) {
                // Simular ativação da câmera
                videoPlaceholder.classList.add('hidden');
                remoteVideo.classList.remove('hidden');
                // Em produção, usar getUserMedia
                callStatus.textContent = 'Câmera ligada';
            } else {
                videoPlaceholder.classList.remove('hidden');
                remoteVideo.classList.add('hidden');
                callStatus.textContent = 'Câmera desligada';
            }
        });

        document.getElementById('btn-toggle-mic').addEventListener('click', () => {
            isMicOn = !isMicOn;
            callStatus.textContent = isMicOn ? 'Microfone ligado' : 'Microfone desligado';
        });

        document.getElementById('btn-end-call').addEventListener('click', () => {
            callStatus.textContent = 'Chamada encerrada';
            // Em produção, encerrar stream
        });

        // ====== Copiloto IA (simulação) ======
        const sugestoesCiap = document.getElementById('sugestoes-ciap');
        const sugestoesConduta = document.getElementById('sugestoes-conduta');

        // Dados simulados de sugestões
        const mockSugestoes = {
            ciap: [
                { codigo: 'A01', descricao: 'Dor generalizada' },
                { codigo: 'R05', descricao: 'Tosse' },
                { codigo: 'K86', descricao: 'Hipertensão não complicada' }
            ],
            conduta: [
                'Prescrever analgésico simples',
                'Orientar repouso e hidratação',
                'Encaminhar para avaliação cardiológica'
            ]
        };

        function renderSugestoes() {
            sugestoesCiap.innerHTML = '';
            mockSugestoes.ciap.forEach(item => {
                const div = document.createElement('div');
                div.className = 'copilot-suggestion bg-blue-50 rounded p-2 flex justify-between items-center';
                div.innerHTML = `
                    <span class="text-sm"><strong>${item.codigo}</strong> - ${item.descricao}</span>
                    <button class="text-blue-600 hover:text-blue-800" onclick="adicionarSugestao('${item.codigo} - ${item.descricao}')">
                        <i class="fas fa-plus"></i>
                    </button>
                `;
                sugestoesCiap.appendChild(div);
            });

            sugestoesConduta.innerHTML = '';
            mockSugestoes.conduta.forEach(item => {
                const div = document.createElement('div');
                div.className = 'copilot-suggestion bg-green-50 rounded p-2 flex justify-between items-center';
                div.innerHTML = `
                    <span class="text-sm">${item}</span>
                    <button class="text-green-600 hover:text-green-800" onclick="adicionarSugestao('${item}')">
                        <i class="fas fa-plus"></i>
                    </button>
                `;
                sugestoesConduta.appendChild(div);
            });
        }

        // Função para adicionar sugestão ao campo de avaliação ou plano
        function adicionarSugestao(texto) {
            const avaliacao = document.getElementById('avaliacao');
            const plano = document.getElementById('plano');
            // Adiciona à avaliação se for código, senão ao plano
            if (texto.includes('-')) {
                avaliacao.value += (avaliacao.value ? '\n' : '') + texto;
            } else {
                plano.value += (plano.value ? '\n' : '') + texto;
            }
            // Disparar evento de input para auto-save
            avaliacao.dispatchEvent(new Event('input'));
            plano.dispatchEvent(new Event('input'));
        }

        document.getElementById('btn-gerar-sugestoes').addEventListener('click', () => {
            renderSugestoes();
        });

        // Renderizar sugestões iniciais
        renderSugestoes();

        // ====== Fechamento Rápido ======
        const modalFechamento = document.getElementById('modal-fechamento');
        const btnFechamento = document.getElementById('btn-fechamento');
        const btnFecharModal = document.getElementById('btn-fechar-modal');

        btnFechamento.addEventListener