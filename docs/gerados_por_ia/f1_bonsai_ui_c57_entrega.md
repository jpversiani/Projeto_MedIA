```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta — MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            overflow: hidden;
        }
        .glass-panel {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(148, 163, 184, 0.08);
            border-radius: 12px;
        }
        .glass-card:hover {
            border-color: rgba(148, 163, 184, 0.2);
        }
        .video-container {
            position: relative;
            overflow: hidden;
            border-radius: 8px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
        }
        .video-container .video-overlay {
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background 0.3s;
        }
        .video-container .video-overlay:hover {
            background: rgba(0, 0, 0, 0.5);
        }
        .control-bar {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
            padding: 12px 20px;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(12px);
            border-top: 1px solid rgba(148, 163, 184, 0.1);
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }
        .control-btn {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: none;
            background: rgba(148, 163, 184, 0.1);
            color: #94a3b8;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            position: relative;
        }
        .control-btn:hover {
            background: rgba(148, 163, 184, 0.2);
            color: #e2e8f0;
            transform: scale(1.05);
        }
        .control-btn.active {
            background: rgba(59, 130, 246, 0.3);
            color: #60a5fa;
        }
        .control-btn.active svg {
            stroke: #60a5fa;
        }
        .chat-panel {
            width: 320px;
            max-width: 45vw;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(12px);
            border-left: 1px solid rgba(148, 163, 184, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            padding: 16px 20px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .chat-header h3 {
            font-size: 14px;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            scroll-behavior: smooth;
        }
        .chat-message {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.5;
            animation: fadeIn 0.3s ease;
        }
        .chat-message.sent {
            align-self: flex-end;
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border-bottom-right-radius: 4px;
        }
        .chat-message.received {
            align-self: flex-start;
            background: rgba(148, 163, 184, 0.08);
            color: #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        .chat-message .timestamp {
            font-size: 11px;
            opacity: 0.6;
            margin-top: 4px;
            text-align: right;
        }
        .chat-input-area {
            padding: 12px 20px;
            border-top: 1px solid rgba(148, 163, 184, 0.1);
        }
        .chat-input {
            width: 100%;
            padding: 10px 14px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 8px;
            color: #e2e8f0;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        .chat-input:focus {
            border-color: rgba(59, 130, 246, 0.5);
        }
        .chat-input::placeholder {
            color: #64748b;
        }
        .chat-send-btn {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: none;
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-left: 10px;
            transition: all 0.2s;
        }
        .chat-send-btn:hover {
            background: rgba(59, 130, 246, 0.35);
        }
        .user-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-doctor {
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
        }
        .badge-patient {
            background: rgba(244, 114, 182, 0.15);
            color: #f472b6;
        }
        .status-dot {
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
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .info-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 500;
        }
        .badge-ciap2 {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
        }
        .badge-cid10 {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
        }
        .badge-soap {
            background: rgba(168, 85, 247, 0.15);
            color: #c084fc;
        }
        .info-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }
        .info-bar .label {
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .info-bar .value {
            font-size: 13px;
            font-weight: 600;
        }
        .info-bar .value.cns {
            color: #60a5fa;
        }
        .info-bar .value.cpf {
            color: #f472b6;
        }
        .info-bar .value.ciap2 {
            color: #34d399;
        }
        .info-bar .value.cid10 {
            color: #fbbf24;
        }
        .info-bar .value.soap {
            color: #c084fc;
        }
        .info-bar .value.status {
            color: #22c55e;
        }
        .info-bar .value.time {
            color: #94a3b8;
        }
        .video-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .video-grid .video-item {
            position: relative;
            aspect-ratio: 4/3;
            background: #1e293b;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.08);
        }
        .video-grid .video-item .video-placeholder {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            background: linear-gradient(135deg, #1e293b, #0f172a);
        }
        .video-grid .video-item .video-placeholder .avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
        }
        .video-grid .video-item .video-placeholder .name {
            font-size: 14px;
            font-weight: 600;
            color: #e2e8f0;
        }
        .video-grid .video-item .video-placeholder .role {
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .video-grid .video-item .video-placeholder .status-indicator {
            position: absolute;
            bottom: 12px;
            right: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
            border-radius: 20px;
            font-size: 11px;
            color: #22c55e;
        }
        .video-grid .video-item .video-placeholder .status-indicator .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #22c55e;
            animation: pulse 2s infinite;
        }
        .video-grid .video-item .video-placeholder .status-indicator .dot.off {
            background: #ef4444;
        }
        .video-grid .video-item .video-placeholder .status-indicator .dot.on {
            background: #22c5