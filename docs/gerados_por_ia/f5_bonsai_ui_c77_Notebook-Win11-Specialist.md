```python
# Arquivo: backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sync Status - Atenção Domiciliar (C77)</title>
    <style>
        :root {
            --primary: #0056b3;
            --primary-dark: #003d82;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
            --info: #17a2b8;
            --light: #f8f9fa;
            --dark: #212529;
            --card-bg: #ffffff;
            --border: #dee2e6;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
            --shadow-lg: 0 4px 16px rgba(0,0,0,0.15);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--light);
            color: var(--dark);
            min-height: 100vh;
        }

        .app-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header */
        .app-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 24px 32px;
            border-radius: 12px 12px 0 0;
            box-shadow: var(--shadow-lg);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .app-header h1 {
            font-size: 1.5rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .app-header h1 .icon {
            font-size: 1.8rem;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .status-badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .status-badge.connected {
            background: rgba(40, 167, 69, 0.2);
            color: var(--success);
        }

        .status-badge.disconnected {
            background: rgba(220, 53, 69, 0.2);
            color: var(--danger);
        }

        .status-badge.syncing {
            background: rgba(255, 193, 7, 0.2);
            color: var(--warning);
        }

        .status-badge .pulse {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        /* Main Layout */
        .main-content {
            padding: 24px;
        }

        /* Stats Bar */
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat-card {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            box-shadow: var(--shadow);
            border-left: 4px solid var(--primary);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .stat-card .stat-icon {
            font-size: 1.5rem;
            margin-bottom: 8px;
        }

        .stat-card .stat-label {
            font-size: 0.85rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .stat-card .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
        }

        /* Connection Status Cards */
        .connection-section {
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            box-shadow: var(--shadow);
            margin-bottom: 24px;
        }

        .connection-section h2 {
            font-size: 1.2rem;
            margin-bottom: 16px;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .connection-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
        }

        .connection-card {
            background: var(--light);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
        }

        .connection-card:hover {
            box-shadow: var(--shadow);
            border-color: var(--primary);
        }

        .connection-card .conn-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .connection-card .conn-icon {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .connection-card .conn-icon.success {
            background: rgba(40, 167, 69, 0.15);
            color: var(--success);
        }

        .connection-card .conn-icon.warning {
            background: rgba(255, 193, 7, 0.15);
            color: var(--warning);
        }

        .connection-card .conn-icon.error {
            background: rgba(220, 53, 69, 0.15);
            color: var(--danger);
        }

        .connection-card .conn-info h3 {
            font-size: 0.95rem;
            font-weight: 600;
        }

        .connection-card .conn-info .conn-detail {
            font-size: 0.8rem;
            color: #6c757d;
        }

        .connection-card .conn-status {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .connection-card .conn-status.success {
            background: rgba(40, 167, 69, 0.15);
            color: var(--success);
        }

        .connection-card .conn-status.warning {
            background: rgba(255, 193, 7, 0.15);
            color: var(--warning);
        }

        .connection-card .conn-status.error {
            background: rgba(220, 53, 69, 0.15);
            color: var(--danger);
        }

        /* Upload Progress Section */
        .upload-section {
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            box-shadow: var(--shadow);
            margin-bottom: 24px;
        }

        .upload-section h2 {
            font-size: 1.2rem;
            margin-bottom: 16px;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .upload-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 16px;
        }

        .upload-card {
            background: var(--light);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid var(--border);
        }

        .upload-card .upload-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .upload-card .upload-name {
            font-weight: 600;
            font-size: 0.95rem;
        }

        .upload-card .upload-id {
            font-size: 0.75rem;
            color: #6c757d;
            background: var(--light);
            padding: 2px 8px;
            border-radius: 4px;
        }

        .upload-card .upload-date {
            font-size: 0.8rem;
            color: #6c757d;
        }

        .progress-bar-container {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 12px;
        }

        .progress-bar {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        .progress-bar.success {
            background: linear-gradient(90deg, var(--success), #28a745);
        }

        .progress-bar.warning {
            background: linear-gradient(90deg, var(--warning), #ffc107);
        }

        .progress-bar.error {
            background: linear-gradient(90deg, var(--danger), #dc3545);
        }

        .progress-bar.pending {
            background: linear-gradient(90deg, #6c757d, #6c757d);
        }

        .progress-bar .progress-text {
            position: absolute;
            right: 0;
            top: 0;
            bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            font-weight: 600;
            color: white;
        }

        .upload-card .upload-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: #6c757d;
        }

        .upload-card .upload-status {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .upload-card .upload-status .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
        }

        .upload-card .upload-status .dot.success {
            background: var(--success);
            animation: blink 1s infinite;
        }

        .upload-card .upload-status .dot.error {
            background: var(--danger);
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
        }

        /* Transmission Logs Section */
        .logs-section {
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            box-shadow: var(--shadow);
            margin-bottom: 24px;
        }

        .logs-section h2 {
            font-size: 1.2rem;
            margin-bottom: 16px;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logs-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
        }

        .logs-controls .filter-btn {
            padding: 6px 14px;
            border: 1px solid var(--border);
            background: var(--light);
            border-radius: 20px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
        }

        .logs-controls .filter-btn:hover {
            border-color: var(--primary);
            background: var(--primary);
            color: white;
        }

        .logs-controls .filter-btn.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .logs-controls .search-input {
            padding: 6px 12px;
            border: 1px solid var(--border);
            border-radius: 20px;
            font-size: 0.8rem;
            width: 200px;
        }

        .logs-controls .search-input:focus {
            outline: none;
            border-color: var(--primary);
        }

        .logs-container {
            max-height: 400px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--border) var(--card-bg);
        }

        .logs-container::-webkit-scrollbar {
            width: 6px;
        }

        .logs-container::-webkit-scrollbar-track {
            background: transparent;
        }

        .logs-container::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 3px;
        }

        .log-entry {
            background: var(--light);
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: