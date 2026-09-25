```html:backend/app/static/campanhas_saude.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Campanhas de Busca Ativa da Comunidade (C8) - ACS</title>
    <meta name="description" content="Dashboard para Agente Comunitário de Saúde (ACS) para gerenciar visitas domiciliares e teleatendimentos.">
    
    <!-- Bootstrap 5.3.1 for UI Components -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome for Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --primary-color: #0056b3;
            --secondary-color: #007bff;
            --accent-color: #28a745;
            --bg-color: #f8f9fa;
        }

        body {
            background-color: var(--bg-color);
            color: #333;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .header {
            background-color: var(--primary-color);
            color: white;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .sidebar {
            background-color: white;
            border-right: 1px solid #ddd;
            padding: 1rem;
            position: sticky;
            top: 60px;
            height: calc(100vh - 60px);
        }

        .filter-card {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .table-responsive {
            margin-bottom: 2rem;
        }

        .badge-status {
            font-weight: bold;
            padding: 0.25rem 0.5rem;
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #f1f1f1; 
        }
        ::-webkit-scrollbar-thumb {
            background: #c1c1c1; 
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8; 
        }

        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1050;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
        }

        .loading-overlay.active {
            opacity: 1;
            pointer-events: auto;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--primary-color);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .alert-custom {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 5px;
        }
        
        .alert-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .alert-info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
    </style>
</head>
<body>

    <!-- Loading Overlay -->
    <div id="loading-overlay" class="loading-overlay">
        <div class="spinner"></div>
    </div>

    <!-- Header -->
    <div class="header">
        <div class="container-fluid">
            <div class="d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-2">
                    <i class="fas fa-heart text-white text-2d"></i>
                    <h1 class="h4 mb-0">Projeto MedIA - Panel ACS</h1>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <span class="badge bg-light text-dark">C8 - Busca Ativa</span>
                    <span id="user-info">ACS: <strong id="acs-name"></strong></span>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Layout -->
    <div class="container-fluid mt-4">
        <div class="row g-4">
            <!-- Sidebar Filters -->
            <div class="col-md-3">
                <div class="card sidebar">
                    <div class="card-header bg-primary text-white">
                        <i class="fas fa-filter me-2"></i> Filtros
                    </div>
                    <div class="card-body">
                        <div class="filter-card">
                            <h5 class="card-title mb-3">Visitas Domiciliares</h5>
                            <div class="mb-3">
                                <label class="form-label">Região</label>
                                <select id="filter-region" class="form-select">
                                    <option value="">Todas</option>
                                    <option value="regiao_1">Região 1</option>
                                    <option value="regiao_2">Região 2</option>
                                    <option value="regiao_3">Região 3</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Data</label>
                                <input type="date" id="filter-date" class="form-control">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Prioridade</label>
                                <select id="filter-priority" class="form-select">
                                    <option value="">Todas</option>
                                    <option value="alta">Alta</option>
                                    <option value="media">Média</option>
                                    <option value="baixa">Baixa</option>
                                </select>
                            </div>
                            <button id="btn-filter-visitas" class="btn btn-primary w-100">
                                <i class="fas fa-sync-alt me-2"></i> Atualizar Lista
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Content -->
            <div class="col-md-9">
                <!-- Stats Cards -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card text-white bg-primary shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title mb-1">Visitas Pendentes</h5>
                                <h2 class="card-text display-5" id="stat-visitas-pendentes">0</h2>
                                <small class="text-muted">Próximas agendadas</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-white bg-success shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title mb-1">Teleatendidos Confirmados</h5>
                                <h2 class="card-text display-5" id="stat-tele-confirmados">0</h2>
                                <small class="text-muted">Atendidos remotamente</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-white bg-warning shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title mb-1">Total de Pacientes</h5>
                                <h2 class="card-text display-5" id="stat-total-pacientes">0</h2>
                                <small class="text-muted">Em campanha ativa</small>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Visits Table -->
                <div class="card shadow-sm">
                    <div class="card-header bg-light">
                        <h5 class="card-title mb-0"><i class="fas fa-house me-2"></i> Lista de Visitas Domiciliares Prioritárias</h5>
                    </div>
                    <div class="card-body table-responsive">
                        <table class="table table-hover table-striped align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th>Paciente</th>
                                    <th>Região</th>
                                    <th>Prioridade</th>
                                    <th>Agendamento</th>
                                    <th>Status</th>
                                    <th>Ação</th>
                                </tr>
                            </thead>
                            <tbody id="table-visitas">
                                <!-- Data will be inserted here -->
                                <tr>
                                    <td colspan="6" class="text-center text-muted">
                                        <i class="fas fa-spinner fa-spin"></i> Carregando dados...
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Teleconsultations Table -->
                <div class="card shadow-sm mt-4">
                    <div class="card-header bg-light">
                        <h5 class="card-title mb-0"><i class="fas fa-video me-2"></i> Confirmações de Teleatendimento</h5>
                    </div>
                    <div class="card-body table-responsive">
                        <table class="table table-hover table-striped align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th>Paciente</th>
                                    <th>Região</th>