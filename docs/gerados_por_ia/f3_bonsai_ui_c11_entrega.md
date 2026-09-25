# Painel Visual da Triage e Monitor de Fila APS (C11)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── triage.py
│   └── static/
│       └── painel_triagem.html
├── tests/
│   ├── __init__.py
│   └── test_triage.py
└── requirements.txt
```

---

## Arquivo: `backend/app/static/painel_triagem.html`

```html
<!-- Arquivo: backend/app/static/painel_triagem.html -->
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Triagem e Monitor de Fila - APS C11</title>
    <style>
        /* ============================================
           PALETA MANCHESTER (SUS/APS)
           ============================================ */
        :root {
            --manc-primary: #0056b3;
            --manc-secondary: #003d80;
            --manc-accent: #ff6b35;
            --manc-success: #28a745;
            --manc-warning: #ffc107;
            --manc-danger: #dc3545;
            --manc-light: #f8f9fa;
            --manc-dark: #212529;
            --manc-card-bg: #ffffff;
            --manc-border: #dee2e6;
            --manc-radius: 12px;
            --manc-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            --manc-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--manc-light);
            color: var(--manc-dark);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ============================================
           CABEÇA DO PAINEL
           ============================================ */
        .panel-header {
            background: linear-gradient(135deg, var(--manc-primary), var(--manc-secondary));
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--manc-shadow);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .panel-header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .panel-header h1 .icon {
            font-size: 1.8rem;
        }

        .panel-header .meta {
            display: flex;
            gap: 20px;
            font-size: 0.9rem;
        }

        .panel-header .meta span {
            background: rgba(255, 255, 255, 0.2);
            padding: 6px 14px;
            border-radius: 20px;
        }

        /* ============================================
           BARRA DE NAVEGAÇÃO
           ============================================ */
        .nav-bar {
            background: white;
            padding: 15px 30px;
            display: flex;
            gap: 5px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }

        .nav-bar a {
            text-decoration: none;
            color: var(--manc-dark);
            padding: 10px 20px;
            border-radius: var(--manc-radius);
            font-weight: 500;
            transition: var(--manc-transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .nav-bar a:hover {
            background: var(--manc-light);
            color: var(--manc-primary);
        }

        .nav-bar a.active {
            background: var(--manc-primary);
            color: white;
        }

        /* ============================================
           CARDS MANCHESTER (SUS/APS)
           ============================================ */
        .card {
            background: var(--manc-card-bg);
            border-radius: var(--manc-radius);
            box-shadow: var(--manc-shadow);
            padding: 20px;
            transition: var(--manc-transition);
            border: 1px solid var(--manc-border);
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--manc-dark);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-title .badge {
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        /* Cards por estado da fila */
        .card-attendezendo {
            border-left: 4px solid var(--manc-warning);
        }
        .card-attendezendo .card-title { color: #856404; }

        .card-chamando {
            border-left: 4px solid var(--manc-accent);
            animation: pulse 1.5s infinite;
        }
        .card-chamando .card-title { color: #854d0e; }

        .card-em-triage {
            border-left: 4px solid var(--manc-primary);
        }
        .card-em-triage .card-title { color: #003d80; }

        .card-em-atendimento {
            border-left: 4px solid var(--manc-success);
        }
        .card-em-atendimento .card-title { color: #155724; }

        .card-em-urgência {
            border-left: 4px solid var(--manc-danger);
            background: #fff5f5;
        }
        .card-em-urgência .card-title { color: #850000; }

        .card-concluída {
            border-left: 4px solid #6c757d;
        }
        .card-concluída .card-title { color: #495057; }

        /* ============================================
           CARDS DE STATÍSTICAS
           ============================================ */
        .stat-card {
            background: linear-gradient(135deg, var(--manc-primary), var(--manc-secondary));
            color: white;
            border-radius: var(--manc-radius);
            padding: 20px;
            text-align: center;
            box-shadow: var(--manc-shadow);
        }

        .stat-card .stat-icon {
            font-size: 2rem;
            margin-bottom: 8px;
        }

        .stat-card .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .stat-card .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }

        .stat-card.warning {
            background: linear-gradient(135deg, var(--manc-warning), #ffc800);
        }
        .stat-card.warning .stat-icon { color: #856404; }

        .stat-card.danger {
            background: linear-gradient(135deg, var(--manc-danger), #dc3545);
        }
        .stat-card.danger .stat-icon { color: #850000; }

        .stat-card.success {
            background: linear-gradient(135deg, var(--manc-success), #28a745);
        }
        .stat-card.success .stat-icon { color: #155724; }

        /* ============================================
           LISTA DE PACIENTES (FILA)
           ============================================ */
        .patient-card {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 8px;
            transition: var(--manc-transition);
        }

        .patient-card:hover {
            background: var(--manc-light);
        }

        .patient-card.em-urgência {
            background: #fff5f5;
            border: 1px solid #f5c6cb;
        }

        .patient-card .patient-photo {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--manc-primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
            flex-shrink: 0;
        }

        .patient-card .patient-info {
            flex: 1;
        }

        .patient-card .patient-name {
            font-weight: 600;
            font-size: 0.95rem;
        }

        .patient-card .patient-cns {
            color: var(--manc-dark);
            font-size: 0.8rem;
            opacity: 0.8;
        }

        .patient-card .patient-age {
            color: var(--manc-dark);
            font-size: 0.85rem;
        }

        .patient-card .patient-position {
            font-size: 0.8rem;
            color: var(--manc-dark);
        }

        .patient-card .patient-position span {
            background: var(--manc-light);
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 600;
        }

        .patient-card .patient-wait {
            color: var(--manc-dark);
            font-weight: 600;
            font-size: 0.9rem;
        }

        .patient-card .patient-wait .wait-time {
            color: var(--manc-accent);
        }

        /* ============================================
           PANEL DE EQUIPA DE ERMENGAEM (C11)
           ============================================ */
        .team-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
        }

        .team-member {
            background: var(--manc-light);
            border-radius: var(--manc-radius);
            padding: 15px;
            text-align: center;
            border: 1px solid var(--manc-border);
            transition: var(--manc-transition);
        }

        .team-member:hover {
            background: white;
            box-shadow: var(--manc-shadow);
        }

        .team-member .member-photo {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--manc-primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.2rem;
            margin: 0 auto 10px;
        }

        .team-member .member-name {
            font-weight: 600;
            font-size: 0.9rem;
            color: var(--manc-dark);
        }

        .team-member .member-role {
            font-size: 0.8rem;
            color: var(--manc-dark);
            opacity: 0.7;
        }

        .team-member .member-status {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 8px;
        }

        .team-member .member-status.on-call {
            background: #d4edda;
            color: #155724;
        }

        .team-member .member-status.on-leave {
            background: #fff3cd;
            color: #856404;
        }

        .team-member .member-status.on-leave {
            background: #fff3cd;
            color: #856404;
        }

        .team-member .member-status.on-leave {
            background: #fff3cd;
            color: #856404;
        }

        /* ============================================
           BLOCO DE AUDIO (CHAMADA SONORA)
           ============================================ */
        .audio-block {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: var(--manc-radius);
            padding: 20px;
            text-align: center;
            box-shadow: var(--manc-shadow);
        }

        .audio-block .audio-icon {
            font-size: 3rem;
            margin-bottom: 10px;
        }

        .audio-block .audio-patient {
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .audio-block .audio-cns {
            font-size