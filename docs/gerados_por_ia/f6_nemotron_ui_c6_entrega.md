```html
<!-- Arquivo: backend/app/static/copiloto_card.html -->
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Copiloto IA - Prontuário</title>
    <!-- Tailwind CSS via CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Estilos adicionais para melhorar a aparência */
        body {
            background-color: #f3f4f6;
            font-family: 'Inter', sans-serif;
        }
        .card-shadow {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">
    <!-- Card principal -->
    <div class="bg-white rounded-lg card-shadow w-full max-w-2xl p-6">
        <!-- Cabeçalho -->
        <div class="flex items-center justify-between mb-6">
            <div class="flex items-center space-x-2">
                <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.674M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0012 18.5a3.374 3.374 0 00-2.475-1.02l-.548-.547z"></path>
                    </svg>
                </div>
                <h2 class="text-xl font-bold text-gray-800">Copiloto IA</h2>
            </div>
            <button id="refreshBtn" class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm font-medium">
                Atualizar
            </button>
        </div>

        <!-- Conteúdo dinâmico -->
        <div id="cardContent">
            <!-- Hipóteses Diagnósticas -->
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-700 mb-3">Hipóteses Diagnósticas</h3>
                <ul id="hypothesesList" class="space-y-3">
                    <!-- Itens serão preenchidos via JavaScript -->
                </ul>
            </div>

            <!-- Interações Farmacológicas -->
            <div>
                <h3 class="text-lg font-semibold text-gray-700 mb-3">Interações Farmacológicas</h3>
                <ul id="interactionsList" class="space-y-3">
                    <!-- Itens serão preenchidos via JavaScript -->
                </ul>
            </div>
        </div>

        <!-- Rodapé informativo -->
        <div class="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-500">
            <p>Baseado no método clínico de Atenção Primária / Saúde da Família.</p>
            <p>Dados de exemplo - integração com API em desenvolvimento.</p>
        </div>
    </div>

    <script>
        // Dados de exemplo (simulando resposta da API)
        const sampleData = [
            {
                hypotheses: [
                    { name: "Pneumonia adquirida na comunidade", probability: 85 },
                    { name: "Bronquite aguda", probability: 70 },
                    { name: "Asma exacerbada", probability: 60 }
                ],
                interactions: [
                    { drugs: "Ibuprofeno + Losartana", description: "Redução do efeito anti-hipertensivo, risco de elevação da pressão arterial." },
                    { drugs: "Amoxicilina + Varfarina", description: "Potencialização do efeito anticoagulante, risco de sangramento." },
                    { drugs: "Salbutamol + Propranolol", description: "Antagonismo farmacológico, redução da eficácia broncodilatadora." }
                ]
            },
            {
                hypotheses: [
                    { name: "Infecção do trato urinário", probability: 90 },
                    { name: "Pielonefrite aguda", probability: 75 },
                    { name: "Cistite intersticial", probability: 55 }
                ],
                interactions: [
                    { drugs: "Ciprofloxacino + Sucralfato", description: "Diminuição da absorção do antibiótico, reduzindo eficácia." },
                    { drugs: "Nitrofurantoína + Antiácidos", description: "Aumento da absorção da nitrofurantoína, risco de toxicidade." },
                    { drugs: "Fosfomicina + Metoclopramida", description: "Redução da concentração da fosfomicina no trato urinário." }
                ]
            },
            {
                hypotheses: [
                    { name: "Diabetes mellitus tipo 2", probability: 80 },
                    { name: "Síndrome metabólica", probability: 65 },
                    { name: "Hipotireoidismo", probability: 45 }
                ],
                interactions: [
                    { drugs: "Metformina + Contraste iodado", description: "Risco de acidose láctica em pacientes com função renal comprometida." },
                    { drugs: "Glibenclamida + Álcool", description: "Reação dissulfiram-like e risco de hipoglicemia grave." },
                    { drugs: "Levotiroxina + Omeprazol", description: "Redução da absorção da levotiroxina, necessitando ajuste de dose." }
                ]
            }
        ];

        // Função para renderizar os dados no card
        function renderCard(data) {
            // Hipóteses
            const hypothesesList = document.getElementById('hypothesesList');
            hypothesesList.innerHTML = '';
            data.hypotheses.forEach(h => {
                const li = document.createElement('li');
                li.className = 'flex items-center justify-between bg-gray-50 p-3 rounded-md';
                li.innerHTML = `
                    <div class="flex items-center space-x-3">
                        <span class="text-sm font-medium text-gray-800">${h.name}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div class="h-full bg-blue-500 rounded-full" style="width: ${h.probability}%"></div>
                        </div>
                        <span class="text-sm font-semibold text-gray-700">${h.probability}%</span>
                    </div>
                `;
                hypothesesList.appendChild(li);
            });

            // Interações
            const interactionsList = document.getElementById('interactionsList');
            interactionsList.innerHTML = '';
            data.interactions.forEach(inter => {
                const li = document.createElement('li');
                li.className = 'bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded-md';
                li.innerHTML = `
                    <div class="flex items-start">
                        <div class="flex-1">
                            <p class="text-sm font-semibold text-gray-800">${inter.drugs}</p>
                            <p class="text-sm text-gray-600 mt-1">${inter.description}</p>
                        </div>
                    </div>
                `;
                interactionsList.appendChild(li);
            });
        }

        // Inicialização com o primeiro conjunto de dados
        let currentIndex = 0;
        renderCard(sampleData[currentIndex]);

        // Evento de atualização (simula nova chamada à API)
        document.getElementById('refreshBtn').addEventListener('click', () => {
            currentIndex = (currentIndex + 1) % sampleData.length;
            renderCard(sampleData[currentIndex]);
        });
    </script>
</body>
</html>
```