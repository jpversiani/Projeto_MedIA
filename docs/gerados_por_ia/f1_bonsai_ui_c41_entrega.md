```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta — SUS/APS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; margin: 0; height: 100vh; overflow: hidden; }
        .glass {
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.06);
        }
        .glass-panel {
            background: rgba(30, 41, 59, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.08);
        }
        .glass-panel-dark {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.06);
        }
        .btn-icon {
            width: 44px; height: 44px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: all 0.2s ease;
            border: none; background: rgba(255,255,255,0.08);
            color: #e2e8f0; font-size: 18px;
        }
        .btn-icon:hover { background: rgba(255,255,255,0.15); transform: scale(1.05); }
        .btn-icon.active { background: rgba(59, 130, 246, 0.25); color: #60a5fa; }
        .btn-close {
            width: 44px; height: 44px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: all 0.2s ease;
            border: none; background: rgba(239, 68, 68, 0.15);
            color: #fca5a5; font-size: 18px;
        }
        .btn-close:hover { background: rgba(239, 68, 68, 0.35); }
        .video-container {
            position: relative;
            width: 100%; aspect-ratio: 4/3;
            background: #020617;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.06);
        }
        .video-container .video-placeholder {
            width: 100%; height: 100%;
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            background: linear-gradient(135deg, #0f172a, #1e293b);
        }
        .video-container .video-placeholder .avatar {
            width: 120px; height: 120px; border-radius: 50%;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            display: flex; align-items: center; justify-content: center;
            font-size: 48px; margin-bottom: 12px;
        }
        .video-container .video-placeholder .label {
            color: #94a3b8; font-size: 14px; font-weight: 500;
        }
        .video-container .video-placeholder .status-dot {
            width: 10px; height: 10px; border-radius: 50%;
            background: #22c55e; margin-top: 8px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        .video-container .video-overlay {
            position: absolute; bottom: 0; left: 0; right: 0;
            padding: 12px 16px;
            background: linear-gradient(to top, rgba(15,23,42,0.9), transparent);
            display: flex; gap: 8px;
        }
        .chat-panel {
            width: 340px; min-width: 340px;
            display: flex; flex-direction: column;
        }
        .chat-header {
            padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.06);
            display: flex; align-items: center; gap: 10px;
        }
        .chat-header .patient-icon {
            width: 36px; height: 36px; border-radius: 10px;
            background: rgba(59,130,246,0.2);
            display: flex; align-items: center; justify-content: center;
            font-size: 16px;
        }
        .chat-header .patient-info {
            flex: 1; min-width: 0;
        }
        .chat-header .patient-info .name {
            font-size: 14px; font-weight: 600; color: #e2e8f0;
        }
        .chat-header .patient-info .role {
            font-size: 11px; color: #64748b;
        }
        .chat-header .patient-info .cns {
            font-size: 11px; color: #64748b;
        }
        .chat-messages {
            flex: 1; overflow-y: auto; padding: 12px 16px;
            display: flex; flex-direction: column; gap: 8px;
        }
        .chat-messages::-webkit-scrollbar { width: 4px; }
        .chat-messages::-webkit-scrollbar-track { background: transparent; }
        .chat-messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }
        .chat-message {
            max-width: 75%; padding: 10px 14px; border-radius: 12px;
            font-size: 13px; line-height: 1.5;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        .chat-message.sent {
            align-self: flex-end;
            background: rgba(59,130,246,0.15);
            border: 1px solid rgba(59,130,246,0.25);
            color: #e2e8f0;
        }
        .chat-message.received {
            align-self: flex-start;
            background: rgba(30,41,59,0.5);
            border: 1px solid rgba(255,255,255,0.06);
            color: #cbd5e1;
        }
        .chat-message .time {
            font-size: 10px; color: #475569; margin-top: 4px;
            text-align: right;
        }
        .chat-input-area {
            padding: 12px 16px; border-top: 1px solid rgba(255,255,255,0.06);
        }
        .chat-input-area input {
            width: 100%; padding: 10px 14px; border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(15,23,42,0.5);
            color: #e2e8f0; font-size: 13px;
            outline: none; transition: border-color 0.2s;
        }
        .chat-input-area input:focus { border-color: rgba(59,130,246,0.5); }
        .chat-input-area button {
            margin-left: 8px; padding: 10px 20px; border-radius: 10px;
            border: none; background: rgba(59,130,246,0.2);
            color: #60a5fa; font-size: 13px; font-weight: 600;
            cursor: pointer; transition: background 0.2s;
        }
        .chat-input-area button:hover { background: rgba(59,130,246,0.35); }
        .control-bar {
            position: fixed; top: 0; left: 0; right: 0;
            height: 64px; display: flex; align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            background: rgba(15,23,42,0.95);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255,255,255,0.06);
            z-index: 100;
        }
        .control-bar .info {
            display: flex; align-items: center; gap: 12px;
        }
        .control-bar .info .patient-avatar {
            width: 36px; height: 36px; border-radius: 10px;
            background: rgba(59,130,246,0.2);
            display: flex; align-items: center; justify-content: center;
            font-size: 14px;
        }
        .control-bar .info .patient-info {
            flex: 1; min-width: 0;
        }
        .control-bar .info .patient-info .name {
            font-size: 14px; font-weight: 600; color: #e2e8f0;
        }
        .control-bar .info .patient-info .cns {
            font-size: 11px; color: #64748b;
        }
        .control-bar .info .patient-info .role {
            font-size: 11px; color: #64748b;
        }
        .control-bar .controls {
            display: flex; align-items: center; gap: 8px;
        }
        .control-bar .controls .btn-icon {
            width: 40px; height: 40px; border-radius: 10px;
        }
        .control-bar .controls .btn-close {
            width: 40px; height: 40px; border-radius: 10px;
        }
        .video-grid {
            display: grid;
            grid-template-columns: 1fr 340px;
            grid-template-rows: 64px 1fr;
            grid-template-rows: 64px 1fr;
            gap: 16px;
            padding: 16px;
            height: calc(100vh - 64px);
        }
        .video-main {
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            gap: 16px;
        }
        .video-main .video-container {
            width: 100%; max-width: 640px;
        }
        .video-main .controls {
            display: flex; align-items: center; gap: 8px;
            margin-top: 8px;
        }
        .video-main .controls .btn-icon {
            width: 40px; height: 40px; border-radius: 10px;
        }
        .video-main .controls .btn-close {
            width: 40px; height: 40px; border-radius: 10px;
        }
        .video-main .controls .btn-icon {
            width: 40px; height: 40px; border-radius: 10px;
        }
        .video-main .controls .btn-close {
            width: 40px; height: 40px; border-radius: 10px;
        }
        .video-main .controls .btn-icon {
            width: 40px; height: 40px; border-radius: 10px;
        }
        .video-main .controls .btn-close {
            width: 40px; height: 40px; border-radius: 10px;
        }
        @media (max-width: 900px) {
            .video-grid {
                grid-template-columns: 1fr;
                grid-template-rows: 64px 1fr;
            }
            .chat-panel {
                width: 100%;
                min-width: unset;
                max-width: 100%;
            }
        }
        .status-badge {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 2px 8px; border-radius: 12px;
            font-size: 11px; font-weight: 600;
        }
        .status-active {
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
        }
        .status-idle {
            background: rgba(99, 102, 241, 0.15);
            color: #a5b4fc;
        }
        .status-queued {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
        }
        .status-canceled {
            background: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
        }
        .status-badge .dot {
            width: 6px; height: 6px; border-radius: 50%;
        }
        .