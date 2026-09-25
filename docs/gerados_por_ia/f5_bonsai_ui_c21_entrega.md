```html:backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS - MedIA</title>
    <style>
        :root {
            --color-primary: #1a73e8;
            --color-primary-dark: #1557b0;
            --color-success: #2ecc71;
            --color-warning: #f39c12;
            --color-danger: #e74c3c;
            --color-info: #3498db;
            --color-bg: #f5f7fa;
            --color-card: #ffffff;
            --color-text: #2c3e50;
            --color-text-light: #7f8c8d;
            --color-border: #e0e0e0;
            --color-header: #1a1a2e;
            --color-header-text: #e0e0e0;
            --radius: 12px;
            --shadow: 0 4px 6px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 25px rgba(0,0,0,0.15);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
            min-height: 100vh;
        }

        .app-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header */
        .app-header {
            background: var(--color-header);
            color: var(--color-header-text);
            padding: 24px 32px;
            border-radius: var(--radius);
            box-shadow: var(--shadow-lg);
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 16px;
        }

        .app-header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .app-header h1 .icon {
            font-size: 1.8rem;
        }

        .header-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: var(--color-primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--color-primary-dark);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: var(--color-bg);
            color: var(--color-text);
            border: 1px solid var(--color-border);
        }

        .btn-secondary:hover {
            background: var(--color-card);
            border-color: var(--color-primary);
        }

        .btn-danger {
            background: var(--color-danger);
            color: white;
        }

        .btn-danger:hover {
            background: #c0392b;
        }

        .btn-sm {
            padding: 6px 14px;
            font-size: 0.8rem;
        }

        .btn-icon {
            width: 40px;
            height: 40px;
            padding: 0;
            border-radius: 50%;
        }

        /* Status Bar */
        .status-bar {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: var(--color-card);
            border-radius: 50px;
            border: 1px solid var(--color-border);
            font-size: 0.85rem;
            font-weight: 500;
            box-shadow: var(--shadow);
        }

        .status-indicator .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .status-indicator.connected .dot {
            background: var(--color-success);
        }

        .status-indicator.disconnected .dot {
            background: var(--color-danger);
        }

        .status-indicator.syncing .dot {
            background: var(--color-warning);
            animation: pulse 1s infinite;
        }

        .status-indicator.error .dot {
            background: var(--color-danger);
            animation: pulse 0.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Main Grid */
        .main-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }

        /* Cards */
        .card {
            background: var(--color-card);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .card-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--color-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .card-header h2 {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--color-text);
        }

        .card-header .badge {
            padding: 4px 10px;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .badge-connected {
            background: #d4edda;
            color: #155724;
        }

        .badge-syncing {
            background: #fff3cd;
            color: #856404;
        }

        .badge-error {
            background: #f8d7da;
            color: #721c24;
        }

        .badge-info {
            background: #d1ecf1;
            color: #0c5460;
        }

        .card-body {
            padding: 24px;
        }

        /* Connection Status Card */
        .connection-status {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .connection-item {
            padding: 16px;
            background: var(--color-bg);
            border-radius: 8px;
            border: 1px solid var(--color-border);
        }

        .connection-item .label {
            font-size: 0.8rem;
            color: var(--color-text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .connection-item .value {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--color-text);
        }

        .connection-item .value.connected {
            color: var(--color-success);
        }

        .connection-item .value.disconnected {
            color: var(--color-danger);
        }

        .connection-item .value.syncing {
            color: var(--color-warning);
        }

        .connection-item .value.error {
            color: var(--color-danger);
        }

        /* Progress Card */
        .progress-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .progress-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: var(--color-bg);
            border-radius: 8px;
            border: 1px solid var(--color-border);
        }

        .progress-item .progress-label {
            flex: 1;
            min-width: 0;
        }

        .progress-item .progress-label .batch-name {
            font-weight: 600;
            font-size: 0.9rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .progress-item .progress-label .batch-id {
            font-size: 0.75rem;
            color: var(--color-text-light);
            margin-top: 2px;
        }

        .progress-item .progress-bar-container {
            flex: 1;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            min-width: 80px;
        }

        .progress-item .progress-bar {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        .progress-item .progress-bar.uploading {
            background: linear-gradient(90deg, var(--color-primary), var(--color-primary-dark));
        }

        .progress-item .progress-bar.uploading::after {
            content: '';
            position: absolute;
            right: 0;
            top: 0;
            width: 10px;
            height: 100%;
            background: rgba(255,255,255,0.3);
            animation: shimmer 1.5s infinite;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .progress-item .progress-bar.completed {
            background: var(--color-success);
        }

        .progress-item .progress-bar.error {
            background: var(--color-danger);
        }

        .progress-item .progress-text {
            font-size: 0.8rem;
            font-weight: 600;
            min-width: 60px;
            text-align: right;
        }

        .progress-item .progress-text.uploading {
            color: var(--color-primary);
        }

        .progress-item .progress-text.completed {
            color: var(--color-success);
        }

        .progress-item .progress-text.error {
            color: var(--color-danger);
        }

        /* Batch Summary */
        .batch-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 12px;
            margin-top: 16px;
        }

        .batch-summary .summary-item {
            text-align: center;
            padding: 12px 8px;
            background: var(--color-bg);
            border-radius: 8px;
            border: 1px solid var(--color-border);
        }

        .batch-summary .summary-item .number {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--color-primary);
        }

        .batch-summary .summary-item .label {
            font-size: 0.75rem;
            color: var(--color-text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Log Card */
        .log-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .log-entry {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 16px;
            background: var(--color-bg);
            border-radius: 8px;
            border: 1px solid var(--color-border);
            transition: background 0.2s ease;
        }

        .log-entry:hover {
            background: #f0f4f8;
        }

        .log-entry .log-icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
            flex-shrink: 0;
        }

        .log-entry .log-icon.success {
            background: #d4edda;
            color: #155724;
        }

        .log-entry .log-icon.error {
            background: #f8d7da;
            color: #721c24;
        }

        .log-entry .log-icon.warning {
            background: #fff3cd;
            color: #856404;
        }

        .log-entry .log-icon.info {
            background: #d1ecf1;
            color: #0c5460;
        }

        .log-entry .log-body {
            flex: 1;
            min-width: 0;
        }

        .log-entry .log-text {
            font-size: 0.85rem;
            line-height: 1.4;
            color: var(--color-text);
        }

        .log-entry .log-text .timestamp {
            font-size: 0.75rem;
            color: var(--color-text-light);
            margin-top: 4px;
            display: block;
        }

        .log-entry .log-text .cns {
            font-weight: 600;
            color: var(--color-primary);
            font-family: monospace;
        }

        .log-entry .log-text .status {
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
        }

        .log-entry .log-text .status.success {
            background: #d4edda;
