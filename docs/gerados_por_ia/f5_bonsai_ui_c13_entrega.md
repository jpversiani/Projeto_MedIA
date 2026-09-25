```html:backend/app/static/sync_status.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sincronização ACS — MedIA | Status de Conexão</title>
    <style>
        /* ============================================
           CSS RESET & VARIABLES
           ============================================ */
        *, *::before, *::after {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --color-primary: #0056b3;
            --color-primary-dark: #003d80;
            --color-primary-light: #e3f2fd;
            --color-success: #2e7d32;
            --color-success-light: #e8f5e9;
            --color-warning: #f57c00;
            --color-warning-light: #fff3e0;
            --color-error: #c62828;
            --color-error-light: #ffebee;
            --color-info: #1976d2;
            --color-info-light: #e3f2fd;
            --color-neutral: #757575;
            --color-neutral-light: #e0e0e0;
            --color-surface: #ffffff;
            --color-border: #d0d0d0;
            --color-text: #1a1a2e;
            --color-text-secondary: #555555;
            --color-card-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            --color-card-shadow-hover: 0 4px 16px rgba(0, 0, 0, 0.12);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --transition-fast: 0.2s ease;
            --transition-normal: 0.3s ease;
            --transition-slow: 0.5s ease;
            --font-main: 'Segoe UI', system-ui, -apple-system, sans-serif;
            --font-mono: 'Courier New', monospace;
        }

        body {
            font-family: var(--font-main);
            background: linear-gradient(135deg, #f0f4f8 0%, #e8ecf1 100%);
            color: var(--color-text);
            min-height: 100vh;
            line-height: 1.6;
        }

        /* ============================================
           LAYOUT
           ============================================ */
        .app-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px 16px;
        }

        /* ============================================
           HEADER
           ============================================ */
        .app-header {
            background: var(--color-surface);
            border-radius: var(--radius-lg);
            box-shadow: var(--color-card-shadow);
            padding: 28px 32px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 16px;
        }

        .app-header__brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .app-header__logo {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
            font-weight: 700;
        }

        .app-header__title {
            font-size: 22px;
            font-weight: 700;
            color: var(--color-text);
        }

        .app-header__title span {
            color: var(--color-primary);
        }

        .app-header__subtitle {
            font-size: 13px;
            color: var(--color-text-secondary);
            margin-top: 2px;
        }

        .app-header__actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 18px;
            border: none;
            border-radius: var(--radius-sm);
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all var(--transition-fast);
            font-family: var(--font-main);
        }

        .btn--primary {
            background: var(--color-primary);
            color: white;
        }

        .btn--primary:hover {
            background: var(--color-primary-dark);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 86, 179, 0.3);
        }

        .btn--secondary {
            background: var(--color-surface);
            color: var(--color-text);
            border: 1px solid var(--color-border);
        }

        .btn--secondary:hover {
            background: var(--color-primary-light);
            border-color: var(--color-primary);
        }

        .btn--danger {
            background: var(--color-error);
            color: white;
        }

        .btn--danger:hover {
            background: #b71c1c;
        }

        .btn--success {
            background: var(--color-success);
            color: white;
        }

        .btn--success:hover {
            background: #266700;
        }

        .btn--sm {
            padding: 6px 12px;
            font-size: 12px;
        }

        .btn--icon {
            width: 36px;
            height: 36px;
            padding: 0;
            border-radius: 50%;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-badge--online {
            background: var(--color-success-light);
            color: var(--color-success);
        }

        .status-badge--online::before {
            content: '';
            width: 8px;
            height: 8px;
            background: var(--color-success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .status-badge--offline {
            background: var(--color-error-light);
            color: var(--color-error);
        }

        .status-badge--offline::before {
            content: '';
            width: 8px;
            height: 8px;
            background: var(--color-error);
            border-radius: 50%;
        }

        .status-badge--syncing {
            background: var(--color-warning-light);
            color: var(--color-warning);
        }

        .status-badge--syncing::before {
            content: '';
            width: 8px;
            height: 8px;
            background: var(--color-warning);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }

        .status-badge--error {
            background: var(--color-error-light);
            color: var(--color-error);
        }

        .status-badge--error::before {
            content: '';
            width: 8px;
            height: 8px;
            background: var(--color-error);
            border-radius: 50%;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
        }

        .header-meta {
            font-size: 12px;
            color: var(--color-text-secondary);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-meta__item {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .header-meta__item svg {
            width: 14px;
            height: 14px;
        }

        /* ============================================
           MAIN GRID
           ============================================ */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 320px;
            gap: 24px;
        }

        @media (max-width: 1024px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 640px) {
            .app-header {
                padding: 16px 12px;
            }
            .app-header__title {
                font-size: 18px;
            }
        }

        /* ============================================
           STATUS CARDS GRID
           ============================================ */
        .status-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }

        .status-card {
            background: var(--color-surface);
            border-radius: var(--radius-md);
            box-shadow: var(--color-card-shadow);
            padding: 24px;
            transition: all var(--transition-normal);
            border-left: 4px solid transparent;
        }

        .status-card:hover {
            box-shadow: var(--color-card-shadow-hover);
            transform: translateY(-2px);
        }

        .status-card--online {
            border-left-color: var(--color-success);
        }

        .status-card--syncing {
            border-left-color: var(--color-warning);
        }

        .status-card--error {
            border-left-color: var(--color-error);
        }

        .status-card--info {
            border-left-color: var(--color-primary);
        }

        .status-card__header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }

        .status-card__icon {
            width: 48px;
            height: 48px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
        }

        .status-card__icon--success {
            background: var(--color-success-light);
            color: var(--color-success);
        }

        .status-card__icon--warning {
            background: var(--color-warning-light);
            color: var(--color-warning);
        }

        .status-card__icon--error {
            background: var(--color-error-light);
            color: var(--color-error);
        }

        .status-card__icon--info {
            background: var(--color-primary-light);
            color: var(--color-primary);
        }

        .status-card__title {
            font-size: 16px;
            font-weight: 700;
            color: var(--color-text);
        }

        .status-card__subtitle {
            font-size: 13px;
            color: var(--color-text-secondary);
            margin-top: 2px;
        }

        .status-card__body {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .status-card__metric {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            background: var(--color-surface);
            border-radius: var(--radius-sm);
            border: 1px solid var(--color-border);
        }

        .status-card__metric__label {
            font-size: 12px;
            color: var(--color-text-secondary);
            font-weight: 500;
        }

        .status-card__metric__value {
            font-size: 14px;
            font-weight: 700;
            font-family: var(--font-mono);
        }

        .status-card__metric--success {
            color: var(--color-success);
        }

        .status-card__metric--warning {
            color: var(--color-warning);
        }

        .status-card__metric--error {
            color: var(--color-error);
        }

        .status-card__metric--info {
            color: var(--color-primary);
        }

        .status-card__timestamp {
            font-size: 11px;
            color: var(--color-text-secondary);
            text-align: right;
        }

        /* ============================================
           UPLOAD PROGRESS SECTION
           ============================================ */
        .upload-section {
            background: var(--color-surface);
            border-radius: var(--radius-md);
            box-shadow: var(--color-card-shadow);
            padding: 24px;
            margin-bottom: 24px;
        }

        .upload-section__header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }

        .upload-section__title {
            font-size: 18px;
            font-weight: 700;
            color: var(--color-text);
        }

        .upload-section__title span {
            color: var(--color-primary);
        }

        .upload-section__actions {
            display: flex;
            gap: 8px;
        }

        .upload-list {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .upload-item {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 14px 16px;
            background: var(--color-surface);
            border-radius: var(--radius-sm);
            border: 1px solid var(--color-border);
            transition: all var(--transition-fast);
        }

        .upload-item:hover {
            border-color: var(--color-primary);
            background: var(--color-primary-light);
        }

        .upload-item__icon {
            width: 40px;
            height: 40px;
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font