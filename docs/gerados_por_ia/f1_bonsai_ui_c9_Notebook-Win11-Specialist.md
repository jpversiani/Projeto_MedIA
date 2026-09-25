```python:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta - Sistema de Telemedicina</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
        }
        .glass-panel {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(148, 163, 184, 0.08);
        }
        .glass-card:hover {
            border-color: rgba(148, 163, 184, 0.15);
        }
        .video-container {
            position: relative;
            overflow: hidden;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        }
        .video-container .overlay {
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background 0.3s;
        }
        .video-container .overlay:hover {
            background: rgba(0, 0, 0, 0.6);
        }
        .control-bar {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 12px 16px;
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(15, 23, 42, 0.6) 100%);
            backdrop-filter: blur(8px);
            border-top: 1px solid rgba(148, 163, 184, 0.1);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .control-bar .btn-control {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid rgba(148, 163, 184, 0.15);
            background: rgba(30, 41, 59, 0.6);
            color: #e2e8f0;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
            font-weight: 500;
        }
        .btn-control:hover {
            background: rgba(51, 65, 85, 0.8);
            border-color: rgba(148, 163, 184, 0.3);
            transform: translateY(-1px);
        }
        .btn-control.active {
            background: rgba(59, 130, 246, 0.3);
            border-color: rgba(59, 130, 246, 0.5);
            color: #60a5fa;
        }
        .btn-close {
            background: rgba(239, 68, 68, 0.2);
            border-color: rgba(239, 68, 68, 0.4);
            color: #fca5a5;
        }
        .btn-close:hover {
            background: rgba(239, 68, 68, 0.35);
        }
        .chat-panel {
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(8px);
            border-left: 1px solid rgba(148, 163, 184, 0.1);
        }
        .chat-panel .chat-header {
            background: rgba(30, 41, 59, 0.8);
            padding: 12px 16px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .chat-panel .chat-header .title {
            font-size: 14px;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .chat-panel .chat-header .status {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: #64748b;
        }
        .chat-panel .chat-header .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .chat-panel .chat-messages {
            padding: 12px;
            overflow-y: auto;
            max-height: 300px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .chat-panel .chat-messages::-webkit-scrollbar {
            width: 4px;
        }
        .chat-panel .chat-messages::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-panel .chat-messages::-webkit-scrollbar-thumb {
            background: rgba(148, 163, 184, 0.2);
            border-radius: 2px;
        }
        .chat-message {
            max-width: 75%;
            padding: 8px 12px;
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.4;
            word-wrap: break-word;
        }
        .chat-message.sent {
            align-self: flex-end;
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .chat-message.received {
            align-self: flex-start;
            background: rgba(148, 163, 184, 0.1);
            color: #cbd5e1;
            border: 1px solid rgba(148, 163, 184, 0.2);
        }
        .chat-input-area {
            padding: 12px;
            border-top: 1px solid rgba(148, 163, 184, 0.1);
        }
        .chat-input-area .input-wrapper {
            display: flex;
            gap: 8px;
        }
        .chat-input-area .input-wrapper input {
            flex: 1;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            background: rgba(30, 41, 59, 0.5);
            color: #e2e8f0;
            font-size: 13px;
            font-family: 'Inter', sans-serif;
            outline: none;
            transition: border-color 0.2s;
        }
        .chat-input-area .input-wrapper input:focus {
            border-color: rgba(59, 130, 246, 0.5);
        }
        .chat-input-area .input-wrapper button {
            padding: 10px 16px;
            border-radius: 8px;
            border: none;
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .chat-input-area .input-wrapper button:hover {
            background: rgba(59, 130, 246, 0.35);
        }
        .video-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            padding: 16px;
        }
        .video-item {
            position: relative;
            aspect-ratio: 4/3;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        .video-item .video-placeholder {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 12px;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
        }
        .video-item .video-placeholder .icon {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
        }
        .video-item .video-placeholder .label {
            font-size: 14px;
            font-weight: 600;
            color: #94a3b8;
        }
        .video-item .video-placeholder .sublabel {
            font-size: 12px;
            color: #64748b;
        }
        .video-item .video-placeholder .status-badge {
            position: absolute;
            top: 10px;
            left: 10px;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-active {
            background: rgba(34, 197, 94, 0.2);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }
        .status-idle {
            background: rgba(148, 163, 184, 0.1);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.2);
        }
        .header-bar {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .header-bar .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header-bar .logo-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }
        .header-bar .logo-text {
            font-size: 18px;
            font-weight: 700;
            color: #e2e8f0;
        }
        .header-bar .logo-text span {
            color: #60a5fa;
        }
        .header-bar .patient-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header-bar .patient-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #ec4899, #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 600;
            color: white;
        }
        .header-bar .patient-details {
            display: flex;
            flex-direction: column;
        }
        .header-bar .patient-name {
            font-size: 14px;
            font-weight: 600;
            color: #e2e8f0;
        }
        .header-bar .patient-id {
            font-size: 11px;
            color: #64748b;
        }
        .header-bar .header-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .header-bar .header-actions button {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            border: 1px solid rgba(148, 163, 184, 0.15);
            background: rgba(30, 