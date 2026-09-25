```html:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="min-h-screen">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia - Consulta e Baixa de Prescrição</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; }
        .glass {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .glass-card:hover { border-color: rgba(255, 255, 255, 0.12); }
        .scan-line {
            animation: scan 1.5s infinite linear;
        }
        @keyframes scan {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100%); }
        }
        .pulse-dot {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        .badge {
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
        }
        .badge-active { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
        .badge-pending { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
        .badge-expired { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); }
        .badge-completed { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.3); }
        .scan-box {
            position: relative;
            overflow: hidden;
        }
        .scan-box::after {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 3px;
            background: linear-gradient(90deg, transparent, rgba(52, 211, 153, 0.6), transparent);
            animation: scan 1.5s infinite linear;
        }
        .scan-box:focus-within::after {
            background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.6), transparent);
        }
        .scan-box::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            border: 2px solid rgba(52, 211, 153, 0.2);
            border-radius: 12px;
            pointer-events: none;
        }
        .scan-box::before::after {
            content: '';
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: 200px; height: 200px;
            border: 2px dashed rgba(52, 211, 153, 0.15);
            border-radius: 50%;
        }
        .scan-box::before::before {
            content: '';
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: 100px; height: 100px;
            border: 2px dashed rgba(52, 211, 153, 0.1);
            border-radius: 50%;
        }
        .pill-count {
            transition: all 0.3s ease;
        }
        .pill-count:hover { transform: scale(1.05); }
        .tab-active {
            background: rgba(52, 211, 153, 0.15);
            color: #34d399;
            border-color: rgba(52, 211, 153, 0.3);
        }
        .tab-hover {
            background: rgba(255, 255, 255, 0.05);
            color: #94a3b8;
        }
        .tab-hover:hover {
            background: rgba(255, 255, 255, 0.1);
            color: #e2e8f0;
        }
        .tab-hover.active {
            background: rgba(52, 211, 153, 0.15);
            color: #34d399;
            border-color: rgba(52, 211, 153, 0.3);
        }
        .quantity-input {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #e2e8f0;
            border-radius: 8px;
            padding: 0.5rem 0.75rem;
            font-size: 0.875rem;
            outline: none;
            transition: all 0.2s;
        }
        .quantity-input:focus {
            border-color: rgba(52, 211, 153, 0.5);
            box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.15);
        }
        .btn-dispense {
            transition: all 0.2s;
        }
        .btn-dispense:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(52, 211, 153, 0.3);
        }
        .btn-dispense:active {
            transform: translateY(0);
        }
        .btn-dispense:disabled {
            opacity: 0.4;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .history-row {
            transition: all 0.2s;
        }
        .history-row:hover {
            background: rgba(255, 255, 255, 0.03);
        }
        .history-row.completed {
            opacity: 0.7;
        }
        .history-row.completed .btn-dispense {
            display: none;
        }
        .history-row.completed .btn-dispense.reveal {
            display: inline-flex;
        }
        .modal-overlay {
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(4px);
        }
        .modal-content {
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(12px);
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .tab-content.active + .tab-content {
            display: none;
        }
        .tab-content.active ~ .tab-content {
            display: none;
        }
        .tab-content.active ~ .tab-content.active {
            display: block;
        }
        .progress-bar {
            height: 6px;
            border-radius: 3px;
            background: rgba(255, 255, 255, 0.1);
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        .status-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
        }
        .status-dot.active { background: #34d399; box-shadow: 0 0 8px rgba(52, 211, 153, 0.5); }
        .status-dot.pending { background: #fbbf24; box-shadow: 0 0 8px rgba(251, 191, 36, 0.5); }
        .status-dot.expired { background: #f87171; box-shadow: 0 0 8px rgba(248, 113, 113, 0.5); }
        .status-dot.completed { background: #60a5fa; box-shadow: 0 0 8px rgba(96, 165, 250, 0.5); }
        .search-bar {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 0.75rem 1rem 0.75rem 2.5rem;
            color: #e2e8f0;
            outline: none;
            transition: all 0.2s;
            width: 100%;
        }
        .search-bar:focus {
            border-color: rgba(52, 211, 153, 0.4);
            box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.1);
        }
        .search-bar::placeholder { color: #64748b; }
        .search-icon {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: #64748b;
        }
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
        }
        .empty-state-icon {
            width: 80px; height: 80px;
            border-radius: 50%;
            background: rgba(52, 211, 153, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            font-size: 2rem;
        }
        .notification {
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .notification.error { animation-name: slideInError; }
        @keyframes slideInError {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .notification.success { animation-name: slideInSuccess; }
        @keyframes slideInSuccess {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .notification.warning { animation-name: slideInWarning; }
        @keyframes slideInWarning {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .notification-info { animation-name: slideInInfo; }
        @keyframes slideInInfo {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 500;
            z-index: 9999;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        }
        .toast.success { background: rgba(16, 185, 129, 0.2); border: 1px solid rgba(52, 211, 153, 0.4); color: #34d399; }
        .toast.error { background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(248, 113, 113, 0.4); color: #f871