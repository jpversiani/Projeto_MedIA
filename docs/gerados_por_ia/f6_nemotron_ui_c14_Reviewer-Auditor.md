```html
<!-- Arquivo: backend/app/static/copiloto_card.html -->
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Copiloto Clínico – Prontuário Web</title>
    <!-- Tailwind CSS (CDN de desenvolvimento) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Heroicons (ícones) -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        /* Transições suaves para o card dinâmico */
        .fade-in {
            animation: fadeIn 0.5s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .progress-bar {
            transition: width 0.8s ease-in-out;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">
    <!-- Card principal -->
    <div id="copiloto-card" class="bg-white rounded-2xl shadow-xl max-w-2xl w-full overflow-hidden border border-gray-200">
        <!-- Cabeçalho -->
        <div class="bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="bg-white/20 rounded-full p-2">
                    <i class="fas fa-robot text-white text-xl"></i>
                </div>
                <div>
                    <h1 class="text-white font-bold text-lg leading-tight">Copiloto Clínico</h1>
                    <p class="text-blue-100 text-xs">Análise em tempo real · Atenção Primária</p>
                </div>
            </div>
            <span class="bg-green-400 text-green-900 text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1">
                <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                Ativo
            </span>
        </div>

        <!-- Corpo -->
        <div class="p-6 space-y-6">
            <!-- Seção: Hipóteses Diagnósticas -->
            <section>
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-gray-800 font-semibold text-md flex items-center gap-2">
                        <i class="fas fa-stethoscope text-blue-600"></i>
                        Hipóteses Diagnósticas
                    </h2>
                    <span class="text-xs text-gray-500">3 principais</span>
                </div>

                <!-- Lista de hipóteses -->
                <div id="hipoteses-container" class="space-y-4">
                    <!-- Item 1 -->
                    <div class="bg-gray-50 rounded-lg p-4 border-l-4 border-blue-500 fade-in">
                        <div class="flex justify-between items-center">
                            <span class="font-medium text-gray-800">Pneumonia Adquirida na Comunidade</span>
                            <span class="text-sm font-bold text-blue-700" id="conf-1">85%</span>
                        </div>
                        <div class="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div id="bar-1" class="progress-bar h-full bg-blue-500 rounded-full" style="width: 85%"></div>
                        </div>
                        <p class="text-xs text-gray-500 mt-2">Sugere-se radiografia de tórax e hemograma completo.</p>
                    </div>

                    <!-- Item 2 -->
                    <div class="bg-gray-50 rounded-lg p-4 border-l-4 border-yellow-400 fade-in">
                        <div class="flex justify-between items-center">
                            <span class="font-medium text-gray-800">Bronquite Aguda</span>
                            <span class="text-sm font-bold text-yellow-700" id="conf-2">10%</span>
                        </div>
                        <div class="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div id="bar-2" class="progress-bar h-full bg-yellow-400 rounded-full" style="width: 10%"></div>
                        </div>
                        <p class="text-xs text-gray-500 mt-2">Considerar se tosse produtiva sem febre alta.</p>
                    </div>

                    <!-- Item 3 -->
                    <div class="bg-gray-50 rounded-lg p-4 border-l-4 border-red-400 fade-in">
                        <div class="flex justify-between items-center">
                            <span class="font-medium text-gray-800">Insuficiência Cardíaca Congestiva</span>
                            <span class="text-sm font-bold text-red-700" id="conf-3">5%</span>
                        </div>
                        <div class="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div id="bar-3" class="progress-bar h-full bg-red-400 rounded-full" style="width: 5%"></div>
                        </div>
                        <p class="text-xs text-gray-500 mt-2">Avaliar BNP e ecocardiograma se dispneia aos esforços.</p>
                    </div>
                </div>
            </section>

            <!-- Divisor -->
            <hr class="border-gray-200">

            <!-- Seção: Interações Farmacológicas -->
            <section>
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-gray-800 font-semibold text-md flex items-center gap-2">
                        <i class="fas fa-pills text-purple-600"></i>
                        Interações Farmacológicas
                    </h2>
                    <span class="text-xs text-gray-500">2 alertas</span>
                </div>

                <div id="interacoes-container" class="space-y-3">
                    <!-- Interação 1 -->
                    <div class="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-200 fade-in">
                        <i class="fas fa-exclamation-triangle text-red-500 mt-1"></i>
                        <div class="flex-1">
                            <p class="text-sm font-semibold text-red-800">
                                Losartana + Espironolactona
                            </p>
                            <p class="text-xs text-red-700 mt-1">
                                Risco de hipercalemia. Monitorar potássio sérico em 7 dias.
                            </p>
                            <span class="inline-block mt-2 text-xs font-medium text-red-700 bg-red-100 px-2 py-0.5 rounded-full">Severidade: Alta</span>
                        </div>
                    </div>

                    <!-- Interação 2 -->
                    <div class="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200 fade-in">
                        <i class="fas fa-info-circle text-yellow-500 mt-1"></i>
                        <div class="flex-1">
                            <p class="text-sm font-semibold text-yellow-800">
                                Sinvastatina + Claritromicina
                            </p>
                            <p class="text-xs text-yellow-700 mt-1">
                                Aumento do risco de miopatia/rabdomiólise. Considerar suspensão temporária da estatina.
                            </p>
                            <span class="inline-block mt-2 text-xs font-medium text-yellow-700 bg-yellow-100 px-2 py-0.5 rounded-full">Severidade: Moderada</span>
                        </div>
                    </div>
                </div>
            </section>
        </div>

        <!-- Rodapé -->
        <div class="bg-gray-50 px-6 py-3 flex items-center justify-between border-t border-gray-200">
            <p class="text-xs text-gray-500">
                <i class="fas fa-shield-alt text-gray-400 mr-1"></i>
                Dados processados localmente · TISS ANS 4.01
            </p>
            <button id="btn-atualizar" class="text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors flex items-center gap-1">
                <i class="fas fa-sync-alt"></i>
                Atualizar
            </button>
        </div>
    </div>

    <!-- Script para simular atualização dinâmica (substituir por chamada real à API) -->
    <script>
        document.getElementById('btn-atualizar').addEventListener('click', function() {
            // Simula novos dados vindos do backend
            const novasConfiancas = [
                { id: 1, valor: Math.floor(Math.random() * 30) + 60, cor: 'bg-blue-500' },
                { id: 2, valor: Math.floor(Math.random() * 20) + 10, cor: 'bg-yellow-400' },
                { id: 3, valor: Math.floor(Math.random() * 10) + 1, cor: 'bg-red-400' }
            ];

            novasConfiancas.forEach(item => {
                const confEl = document.getElementById(`conf-${item.id}`);
                const barEl = document.getElementById(`bar-${item.id}`);
                if (confEl && barEl) {
                    confEl.textContent = item.valor + '%';
                    barEl.style.width = item.valor + '%';
                    barEl.className = `progress-bar h-full ${item.cor} rounded-full`;
                }
            });

            // Feedback visual
            const btn = document.getElementById('btn-atualizar');
            btn.innerHTML = '<i class="fas fa-check"></i> Atualizado';
            setTimeout(() => {
                btn.innerHTML = '<i class="fas fa-sync-alt"></i> Atualizar';
            }, 2000);
        });
    </script>
</body>
</html>
```