```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telemedicina – Sala de Consulta</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            height: 100vh;
            overflow: hidden;
        }
        .glass-panel {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.08);
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(148, 163, 184, 0.06);
        }
        .video-slot {
            position: relative;
            overflow: hidden;
            border-radius: 12px;
            aspect-ratio: 4/3;
            background: #1e293b;
            cursor: pointer;
        }
        .video-slot .video-placeholder {
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            transition: opacity 0.3s;
        }
        .video-slot .video-placeholder .avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: 700;
            color: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        .video-slot .video-placeholder .name {
            font-size: 13px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .video-slot .video-placeholder .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            animation: pulse 2s infinite;
        }
        .video-slot .video-placeholder .status-dot.off {
            background: #ef4444;
            animation: none;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        .video-slot .overlay {
            position: absolute;
            inset: 0;
            background: rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .video-slot:hover .overlay { opacity: 1; }
        .control-bar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 64px;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid rgba(148, 163, 184, 0.06);
        }
        .control-bar .brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .control-bar .brand .logo {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 16px;
            color: white;
        }
        .control-bar .brand .brand-text {
            font-weight: 600;
            font-size: 16px;
            color: #e2e8f0;
        }
        .control-bar .brand .brand-text span {
            color: #22c55e;
        }
        .control-bar .controls {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .control-btn {
            width: 44px;
            height: 44px;
            border-radius: 10px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            background: rgba(30, 41, 59, 0.5);
            color: #94a3b8;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 18px;
        }
        .control-btn:hover {
            background: rgba(51, 65, 85, 0.6);
            color: #e2e8f0;
            border-color: rgba(148, 163, 184, 0.2);
        }
        .control-btn.active {
            background: rgba(34, 197, 94, 0.15);
            border-color: rgba(34, 197, 94, 0.3);
            color: #22c55e;
        }
        .control-btn.mute-active {
            background: rgba(239, 68, 68, 0.15);
            border-color: rgba(239, 68, 68, 0.3);
            color: #ef4444;
        }
        .control-btn.mute-active:hover {
            background: rgba(239, 68, 68, 0.2);
        }
        .control-bar .info {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .control-bar .info-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: #64748b;
        }
        .control-bar .info-item .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #22c55e;
        }
        .control-bar .info-item .dot.warning {
            background: #f59e0b;
        }
        .control-bar .info-item .dot.danger {
            background: #ef4444;
        }
        .main-content {
            position: relative;
            z-index: 1;
            display: flex;
            flex: 1;
            height: calc(100vh - 64px);
        }
        .video-grid {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 16px;
            padding: 24px;
            overflow: hidden;
        }
        .video-grid .slot {
            position: relative;
        }
        .video-grid .slot .video-slot {
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.3);
        }
        .video-grid .slot .video-slot .video-placeholder .avatar {
            width: 100px;
            height: 100px;
            font-size: 36px;
        }
        .video-grid .slot .video-slot .video-placeholder .name {
            font-size: 14px;
        }
        .chat-sidebar {
            width: 360px;
            min-width: 360px;
            background: rgba(15, 23, 42, 0.6);
            border-left: 1px solid rgba(148, 163, 184, 0.06);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            padding: 16px 20px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.06);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .chat-header h3 {
            font-size: 14px;
            font-weight: 600;
            color: #e2e8f0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .chat-header h3 .chat-icon {
            color: #22c55e;
        }
        .chat-header .close-chat {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            border: none;
            background: rgba(148, 163, 184, 0.08);
            color: #64748b;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            transition: all 0.2s;
        }
        .chat-header .close-chat:hover {
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            scroll-behavior: smooth;
        }
        .chat-messages::-webkit-scrollbar {
            width: 4px;
        }
        .chat-messages::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-messages::-webkit-scrollbar-thumb {
            background: rgba(148, 163, 184, 0.2);
            border-radius: 2px;
        }
        .chat-message {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.5;
            word-wrap: break-word;
            animation: fadeIn 0.2s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .chat-message.sent {
            align-self: flex-end;
            background: rgba(34, 197, 94, 0.15);
            color: #22c55e;
            border: 1px solid rgba(34, 197, 94, 0.2);
            border-bottom-right-radius: 4px;
        }
        .chat-message.received {
            align-self: flex-start;
            background: rgba(148, 163, 184, 0.1);
            color: #e2e8f0;
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-bottom-left-radius: 4px;
        }
        .chat-message .sender {
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 2px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .chat-message.sent .sender { color: #22c55e; }
        .chat-message.received .sender { color: #94a3b8; }
        .chat-message .timestamp {
            font-size: 10px;
            color: #475569;
            margin-top: 4px;
            text-align: right;
        }
        .chat-input-area {
            padding: 12px 20px;
            border-top: 1px solid rgba(148, 163, 184, 0.06);
        }
        .chat-input-area input {
            width: 100%;
            padding: 10px 14px;
            border-radius: 10px;
            border: 1px solid rgba(148, 163, 184, 0.15);
            background: rgba(30, 41, 59, 0.5);
            color: #e2e8f0;
            font-size: 13px;
            font-family: 'Inter', sans-serif;
            outline: none;
            transition: border-color 0.2s;
        }
        .chat-input-area input:focus {
            border-color: rgba(34, 197, 94, 0.4);
        }
        .chat-input-area input::placeholder {
            color: #475569;
        }
        .chat-send-btn {
            width: 100%;
            padding: 10px;
            margin-top: 8px;
            border-radius: 10px;
            border: none;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            font-size: 13px;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            cursor: pointer;
            transition: all 0.