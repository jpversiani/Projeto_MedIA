```python:backend/app/static/dashboard_analytics.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Executivo - MedIA</title>
    <style>
        :root {
            --primary: #0056b3;
            --primary-dark: #003d80;
            --secondary: #28a745;
            --danger: #dc3545;
            --warning: #ffc107;
            --info: #17a2b8;
            --light: #f8f9fa;
            --dark: #212529;
            --card-bg: #ffffff;
            --border: #dee2e6;
            --text: #343a40;
            --text-light: #6c757d;
            --gradient-primary: linear-gradient(135deg, #0056b3 0%, #003d80 100%);
            --gradient-success: linear-gradient(135deg, #28a745 0%, #1f8734 100%);
            --gradient-danger: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            --gradient-info: linear-gradient(135deg, #17a2b8 0%, #0d6efd 100%);
            --shadow-sm: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.05);
            --shadow-md: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            --shadow-xl: 0 1rem 2rem rgba(0, 0, 0, 0.2);
            --radius-sm: 0.25rem;
            --radius-md: 0.5rem;
            --radius-lg: 1rem;
            --radius-xl: 1.5rem;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--light);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* Header */
        .app-header {
            background: var(--gradient-primary);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--shadow-md);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .app-header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .app-header h1 .logo {
            font-size: 1.8rem;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .header-actions .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: white;
            color: var(--primary);
        }

        .btn-primary:hover {
            background: var(--light);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.875rem;
            color: var(--primary);
        }

        .user-info span {
            font-size: 0.875rem;
            font-weight: 500;
        }

        /* Main Layout */
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* Sidebar */
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            bottom: 0;
            width: 260px;
            background: white;
            border-right: 1px solid var(--border);
            padding: 1.5rem 1rem;
            z-index: 90;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .sidebar-nav {
            flex: 1;
        }

        .sidebar-nav .nav-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 1rem;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-light);
        }

        .sidebar-nav .nav-item:hover {
            background: var(--light);
            color: var(--text);
        }

        .sidebar-nav .nav-item.active {
            background: var(--primary);
            color: white;
        }

        .nav-icon {
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.125rem;
        }

        .sidebar-footer {
            padding: 1rem;
            border-top: 1px solid var(--border);
        }

        .sidebar-footer .user-card {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: background 0.2s;
        }

        .sidebar-footer .user-card:hover {
            background: var(--light);
        }

        /* Dashboard Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 280px;
            gap: 2rem;
            margin-top: 2rem;
        }

        /* KPI Cards */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
        }

        .kpi-card {
            background: var(--card-bg);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border);
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .kpi-card .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }

        .kpi-card .card-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .kpi-card .card-status {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.25rem 0.5rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .card-status.up {
            background: rgba(40, 167, 69, 0.1);
            color: #28a745;
        }

        .card-status.down {
            background: rgba(220, 53, 69, 0.1);
            color: #dc3545;
        }

        .card-status.stable {
            background: rgba(255, 193, 7, 0.1);
            color: #ffc107;
        }

        .card-status .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
        }

        .kpi-card .card-value {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .kpi-card .card-change {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }

        .kpi-card .card-change.up {
            color: #28a745;
        }

        .kpi-card .card-change.down {
            color: #dc3545;
        }

        .kpi-card .card-change.stable {
            color: #6c757d;
        }

        .kpi-card .card-chart {
            height: 60px;
            position: relative;
        }

        .kpi-card .card-chart canvas {
            width: 100%;
            height: 100%;
        }

        .kpi-card .card-label {
            font-size: 0.75rem;
            color: var(--text-light);
            margin-top: 0.5rem;
        }

        /* Heatmap Section */
        .heatmap-section {
            background: var(--card-bg);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border);
        }

        .heatmap-section h2 {
            font-size: 1.125rem;
            font-weight: 700;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .heatmap-section h2 .heatmap-icon {
            font-size: 1.25rem;
        }

        .heatmap-controls {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .heatmap-controls .filter-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .heatmap-controls .filter-group label {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text);
        }

        .heatmap-controls .filter-group select {
            padding: 0.375rem 0.75rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            font-size: 0.875rem;
            background: white;
            cursor: pointer;
        }

        .heatmap-controls .btn-small {
            padding: 0.375rem 0.75rem;
            border: none;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 600;
            transition: all 0.2s;
        }

        .heatmap-controls .btn-small.primary {
            background: var(--primary);
            color: white;
        }

        .heatmap-controls .btn-small.primary:hover {
            background: var(--primary-dark);
        }

        .heatmap-controls .btn-small.secondary {
            background: var(--light);
            color: var(--text);
        }

        .heatmap-controls .btn-small.secondary:hover {
            background: var(--border);
        }

        .heatmap-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            margin-bottom: 1rem;
        }

        .heatmap-cell {
            aspect-ratio: 1;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.625rem;
            font-weight: 700;
            color: white;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }

        .heatmap-cell:hover {
            transform: scale(1.1);
            z-index: 10;
        }

        .heatmap-cell .tooltip {
            position: absolute;
            bottom: 120%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--dark);
            color: white;
            padding: 0.5rem 0.75rem;
            border-radius: var(--radius-sm);
            font-size: 0.75rem;
            white-space: nowrap;
            opacity: 0;
            transition: opacity 0.2s;
            pointer-events: none;
        }

        .heatmap-cell:hover .tooltip {
            opacity: 1;
        }

        .heatmap-legend {
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .heatmap-legend .legend-item {
            display: flex;
            align-items: center;
            gap: 0.375rem;
            font-size: 0.875rem