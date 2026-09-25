```python:backend/app/static/monitor_sisab.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor SISAB - Dashboard de Remessas</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #0056b3;
            --secondary: #2c3e50;
            --success: #27ae60;
            --danger: #e74c3c;
            --bg: #f8f9fa;
            --text: #333;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: var(--primary);
            border-bottom: 2px solid var(--primary);
            padding-bottom: 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #fff;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-top: 0;
            color: var(--secondary);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: var(--primary);
            color: white;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        .status-success { color: var(--success); font-weight: bold; }
        .status-error { color: var(--danger); font-weight: bold; }
        .btn {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 5px;
        }
        .btn:hover {
            background-color: #004494;
        }
        .btn-error {
            background-color: var(--danger);
        }
        .btn-error:hover {
            background-color: #c0392b;
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        .controls {
            margin-bottom: 20px;
        }
        .controls button {
            background-color: var(--success);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
        }
        .controls button:hover {
            background-color: #219a52;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: var(--secondary);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Monitor SISAB - Remessas (C28)</h1>
        
        <div class="controls">
            <button onclick="fetchDashboard()">Atualizar Dashboard</button>
            <span id="last-update">Última atualização: --</span>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Gráficos Mensais</h3>
                <div class="chart-container">
                    <canvas id="monthlyChart"></canvas>
                </div>
            </div>
            <div class="card">
                <h3>Remessas Recentes</h3>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>CNPJ/CNPJ</th>
                            <th>CNS/CPF</th>
                            <th>CID-10</th>
                            <th>CIAP-2</th>
                            <th>Valor</th>
                            <th>Estato</th>
                            <th>Ação</th>
                        </tr>
                    </thead>
                    <tbody id="remittanceTable">
                        <tr>
                            <td colspan="8" class="loading">Carregando dados...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div class="card">
                <h3>Reenvio de Lotes com Erro</h3>
                <table>
                    <thead>
                        <tr>
                            <th>ID do Lote</th>
                            <th>Estato</th>
                            <th>Ação</th>
                        </tr>
                    </thead>
                    <tbody id="failedBatchesTable">
                        <tr>
                            <td colspan="3" class="loading">Carregando dados...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        async function fetchDashboard() {
            const tableBody = document.getElementById('remittanceTable');
            const failedBody = document.getElementById('failedBatchesTable');
            const chartCtx = document.getElementById('monthlyChart').getContext('2d');
            
            // Limpar gráficos antigos
            if (window.monthlyChart) window.monthlyChart.destroy();

            try {
                const [remittances, failedBatches, monthlyData] = await Promise.all([
                    fetch('/api/remittances').then(r => r.json()),
                    fetch('/api/failed_batches').then(r => r.json()),
                    fetch('/api/monthly_data').then(r => r.json())
                ]);

                // Renderizar Remessas
                tableBody.innerHTML = '';
                remittances.forEach(r => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${r.id}</td>
                        <td>${r.cnpj}</td>
                        <td>${r.cns}</td>
                        <td>${r.cid10}</td>
                        <td>${r.ciap2}</td>
                        <td>R$ ${r.valor.toFixed(2)}</td>
                        <td class="${r.status === 'SUCCESS' ? 'status-success' : 'status-error'}">${r.status}</td>
                        <td>${r.status === 'SUCCESS' ? '' : `<button class="btn btn-error" onclick="retransmitBatch('${r.batchId}')">Reenviar</button>`}</td>
                    `;
                    tableBody.appendChild(row);
                });

                // Renderizar Lotes Falhados
                failedBody.innerHTML = '';
                failedBatches.forEach(b => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${b.id}</td>
                        <td>${b.status}</td>
                        <td><button class="btn btn-error" onclick="retransmitBatch('${b.id}')">Reenviar Lote</button></td>
                    `;
                    failedBody.appendChild(row);
                });

                // Renderizar Gráfico Mensual
                if (monthlyData) {
                    const labels = monthlyData.labels;
                    const datasets = monthlyData.datasets;
                    const ctx = document.getElementById('monthlyChart').getContext('2d');
                    
                    window.monthlyChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: datasets
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: { beginAtZero: true }
                            }
                        }
                    });
                }

                document.getElementById('last-update').textContent = new Date().toLocaleString();
            } catch (error) {
                console.error('Erro ao carregar dashboard:', error);
                alert('Erro ao carregar dados do dashboard.');
            }
        }

        async function retransmitBatch(batchId) {
            try {
                const response = await fetch('/api/retransmit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ batchId })
                });
                const data = await response.json();
                if (response.ok) {
                    alert(`Lote ${batchId} reenviado com sucesso.`);
                    fetchDashboard();
                } else {
                    alert(`Erro ao reenviar lote: ${data.message}`);
                }
            } catch (error) {
                alert('Erro ao reenviar lote.');
            }
        }

        // Inicializar ao carregar
        window.onload = fetchDashboard;
    </script>
</body>
</html>
```

```python:backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pydantic import BaseModel, Field
from typing import List, Optional