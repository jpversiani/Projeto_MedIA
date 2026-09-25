```python
# Arquivo: backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS (C5) - Atenção Domicilar</title>
    <style>
        :root {
            --color-primary: #0056b3;
            --color-primary-dark: #003d80;
            --color-success: #2e7d32;
            --color-warning: #f57c00;
            --color-error: #c62828;
            --color-info: #1976d2;
            --color-bg: #f5f5f5;
            --color-card: #ffffff;
            --color-text: #212121;
            --color-text-light: #757575;
            --color-border: #e0e0e0;
            --color-accent: #42a5f5;
            --radius: 8px;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
            --shadow-hover: 0 4px 16px rgba(0,0,0,0.15);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
            background-color: var(--color-bg);
            color: var(--color-text);
            line-height: 1.6;
            min-height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header h1 .icon {
            font-size: 1.8rem;
        }

        .header .meta {
            display: flex;
            gap: 20px;
            font-size: 0.9rem;
        }

        .header .meta span {
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 500;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px 30px;
        }

        .controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 12px;
        }

        .btn {
            padding: 10px 24px;
            border: none;
            border-radius: var(--radius);
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-family: inherit;
        }

        .btn-primary {
            background: var(--color-primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--color-primary-dark);
            transform: translateY(-1px);
            box-shadow: var(--shadow-hover);
        }

        .btn-success {
            background: var(--color-success);
            color: white;
        }

        .btn-success:hover {
            background: #1b5e20;
            transform: translateY(-1px);
            box-shadow: var(--shadow-hover);
        }

        .btn-warning {
            background: var(--color-warning);
            color: white;
        }

        .btn-warning:hover {
            background: #e65100;
            transform: translateY(-1px);
            box-shadow: var(--shadow-hover);
        }

        .btn-error {
            background: var(--color-error);
            color: white;
        }

        .btn-error:hover {
            background: #b71c1c;
            transform: translateY(-1px);
            box-shadow: var(--shadow-hover);
        }

        .btn-outline {
            background: transparent;
            border: 2px solid var(--color-border);
            color: var(--color-text);
        }

        .btn-outline:hover {
            border-color: var(--color-primary);
            color: var(--color-primary);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-sm {
            padding: 6px 16px;
            font-size: 0.85rem;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .status-card {
            background: var(--color-card);
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
            border-left: 4px solid var(--color-primary);
        }

        .status-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-hover);
        }

        .status-card.success {
            border-left-color: var(--color-success);
        }

        .status-card.warning {
            border-left-color: var(--color-warning);
        }

        .status-card.error {
            border-left-color: var(--color-error);
        }

        .status-card.info {
            border-left-color: var(--color-info);
        }

        .status-card .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .status-card .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--color-text);
        }

        .status-card .card-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-card.success .card-status {
            background: rgba(46, 125, 50, 0.1);
            color: var(--color-success);
        }

        .status-card.warning .card-status {
            background: rgba(245, 124, 0, 0.1);
            color: var(--color-warning);
        }

        .status-card.error .card-status {
            background: rgba(198, 40, 40, 0.1);
            color: var(--color-error);
        }

        .status-card.info .card-status {
            background: rgba(25, 118, 210, 0.1);
            color: var(--color-info);
        }

        .status-card .card-body {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .status-card .stat-item {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .status-card .stat-label {
            font-size: 0.8rem;
            color: var(--color-text-light);
            font-weight: 500;
        }

        .status-card .stat-value {
            font-size: 1.2rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
        }

        .status-card .stat-value.success {
            color: var(--color-success);
        }

        .status-card .stat-value.warning {
            color: var(--color-warning);
        }

        .status-card .stat-value.error {
            color: var(--color-error);
        }

        .status-card .stat-value.info {
            color: var(--color-info);
        }

        .progress-section {
            background: var(--color-card);
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow);
            margin-bottom: 20px;
        }

        .progress-section h2 {
            font-size: 1.2rem;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .progress-section h2 .badge {
            background: var(--color-primary);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .batch-progress {
            margin-bottom: 16px;
        }

        .batch-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .batch-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .batch-info .batch-id {
            background: var(--color-bg);
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--color-text);
        }

        .batch-info .batch-type {
            font-size: 0.8rem;
            color: var(--color-text-light);
        }

        .batch-info .batch-date {
            font-size: 0.8rem;
            color: var(--color-text-light);
        }

        .progress-bar-container {
            width: 100%;
            height: 24px;
            background: var(--color-bg);
            border-radius: 12px;
            overflow: hidden;
            position: relative;
        }

        .progress-bar {
            height: 100%;
            border-radius: 12px;
            transition: width 0.5s ease;
            position: relative;
        }

        .progress-bar.active {
            background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
        }

        .progress-bar.completed {
            background: linear-gradient(90deg, var(--color-success), #4caf50);
        }

        .progress-bar.error {
            background: linear-gradient(90deg, var(--color-error), #e53935);
        }

        .progress-bar.warning {
            background: linear-gradient(90deg, var(--color-warning), #ff9800);
        }

        .progress-bar .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.75rem;
            font-weight: 700;
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }

        .progress-bar.completed .progress-text {
            color: white;
        }

        .progress-bar.error .progress-text {
            color: white;
        }

        .progress-bar.warning .progress-text {
            color: white;
        }

        .progress-bar .bar-stats {
            display: flex;
            justify-content: space-between;
            margin-top: 6px;
            font-size: 0.8rem;
            color: var(--color-text-light);
        }

        .batch-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .batch-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: var(--color-bg);
            border-radius: var(--radius);
            transition: all 0.3s ease;
        }

        .batch-item:hover {
            background: #f0f0f0;
        }

        .batch-item .batch-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            flex-shrink: 0;
        }

        .batch-item .batch-icon.success {
            background: rgba(46, 125, 50, 0.1);
            color: var(--color-success);
        }

        .batch-item .batch-icon.warning {
            background: rgba(245, 124, 0, 0.1);
            color: var(--color-warning);
        }

        .batch-item .batch-icon.error {
            background: rgba(198, 40, 40, 0.1);
            color: var(--color-error);
        }

        .batch-item .batch-icon.info {
            background: rgba(25, 118, 210, 0.1);
            color: var(--color-info);
        }

        .batch-item .batch-details {
            flex: 1;
            min-width: 0;
        }

        .batch-item .batch-name {
            font-weight: 600;
            font-size: 0.95rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .batch-item .batch-meta {
            font-size: 0.8rem;
            color: var(--color-text-light);
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        .batch-item .batch-meta span {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .batch-item .batch-status {
            padding: 4px 12px;
            border-radius: