```python:backend/app/static/telemedicina_sala.html
# Arquivo: backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta — MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; margin: 0; padding: 0; height: 100vh; overflow: hidden; }
        .glass {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .glass-panel {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .glass-card {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.04);
        }
        .btn-primary {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            border: none;
            border-radius: 10px;
            padding: 8px 16px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 13px;
            letter-spacing: 0.3px;
        }
        .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
        .btn-primary:active { transform: translateY(0); }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 8px 16px;
            color: #94a3b8;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 13px;
        }
        .btn-secondary:hover { background: rgba(255, 255, 255, 0.1); color: #e2e8f0; }
        .btn-danger {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 10px;
            padding: 8px 16px;
            color: #fca5a5;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 13px;
        }
        .btn-danger:hover { background: rgba(239, 68, 68, 0.25); }
        .btn-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(30, 41, 59, 0.6);
            color: #94a3b8;
        }
        .btn-icon:hover { background: rgba(30, 41, 59, 0.8); color: #e2e8f0; }
        .btn-icon.active { background: rgba(37, 99, 235, 0.2); border-color: rgba(37, 99, 235, 0.4); color: #60a5fa; }
        .btn-icon.danger { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); color: #fca5a5; }
        .btn-icon.danger:hover { background: rgba(239, 68, 68, 0.25); }

        .video-container {
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background: #000;
        }
        .video-container .video-placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            background: linear-gradient(135deg, #1e293b, #0f172a);
        }
        .video-container .video-placeholder .icon { font-size: 48px; margin-bottom: 12px; }
        .video-container .video-placeholder p { color: #64748b; font-size: 14px; }
        .video-container .video-placeholder .sub { color: #475569; font-size: 12px; }

        .chat-message {
            max-width: 80%;
            border-radius: 16px;
            padding: 10px 14px;
            margin-bottom: 8px;
            animation: fadeIn 0.3s ease;
        }
        .chat-message.sent {
            background: rgba(37, 99, 235, 0.15);
            border: 1px solid rgba(37, 99, 235, 0.2);
            border-bottom-right-radius: 4px;
            align-self: flex-end;
        }
        .chat-message.received {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom-left-radius: 4px;
            align-self: flex-start;
        }
        .chat-message .sender { font-size: 11px; font-weight: 600; color: #94a3b8; margin-bottom: 2px; }
        .chat-message .text { font-size: 13px; color: #e2e8f0; line-height: 1.5; }
        .chat-message .time { font-size: 10px; color: #475569; margin-top: 4px; }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }
        .status-dot.online { background: #22c55e; }
        .status-dot.offline { background: #ef4444; }
        .status-dot.pending { background: #f59e0b; }

        .room-info {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 12px 16px;
        }
        .room-info .title { font-size: 13px; font-weight: 600; color: #e2e8f0; }
        .room-info .subtitle { font-size: 11px; color: #64748b; }

        .toggle-switch {
            position: relative;
            width: 44px;
            height: 24px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.1);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .toggle-switch.on { background: rgba(37, 99, 235, 0.4); }
        .toggle-switch .slider {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: white;
            transition: all 0.3s ease;
        }
        .toggle-switch.on .slider { left: 22px; }

        .scrollbar-thin::-webkit-scrollbar { width: 4px; }
        .scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
        .scrollbar-thin::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 2px; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .pulse-dot {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .room-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 20px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
            color: #94a3b8;
        }

        .room-badge .badge-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #22c55e;
        }

        .room-badge.pending .badge-dot { background: #f59e0b; }
        .room-badge.pending .room-badge-text { color: #fbbf24; }

        .room-badge.active .room-badge-text { color: #60a5fa; }

        .room-badge.active .badge-dot {
            background: #60a5fa;
            animation: pulse 2s infinite;
        }

        .room-badge.closed .room-badge-text { color: #fca5a5; }
        .room-badge.closed .badge-dot { background: #f87171; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .badge-dot {
            background: #f87171;
        }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5; }

        .room-badge.closed .room-badge-text { color: #fca5a5