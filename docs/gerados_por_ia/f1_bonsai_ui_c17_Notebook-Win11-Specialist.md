```python
# Arquivo: backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta - MedIA</title>
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
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .glass-panel-light {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .video-container {
            position: relative;
            overflow: hidden;
            border-radius: 8px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
        }
        .video-container::after {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(0,0,0,0.1) 0%, transparent 50%);
            pointer-events: none;
        }
        .control-bar {
            position: absolute;
            bottom: 12px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 10;
        }
        .control-btn {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            position: relative;
        }
        .control-btn:hover { transform: scale(1.05); }
        .control-btn.active { background: rgba(59, 130, 246, 0.9); }
        .control-btn:active { transform: scale(0.95); }
        .control-btn.mute-btn:hover { background: rgba(248, 113, 113, 0.9); }
        .control-btn.mute-btn.active { background: rgba(248, 113, 113, 0.9); }
        .control-btn.video-btn:hover { background: rgba(59, 130, 246, 0.9); }
        .control-btn.video-btn.active { background: rgba(59, 130, 246, 0.9); }
        .control-btn.close-btn:hover { background: rgba(248, 113, 113, 0.9); }
        .control-btn.close-btn.active { background: rgba(248, 113, 113, 0.9); }
        .chat-panel {
            position: absolute;
            right: 0;
            top: 0;
            bottom: 0;
            width: 340px;
            max-width: 90vw;
            background: rgba(15, 23, 42, 0.95);
            border-left: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            flex-direction: column;
            z-index: 20;
            transition: transform 0.3s ease;
        }
        .chat-panel.hidden { transform: translateX(100%); }
        .chat-header {
            padding: 16px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .chat-header h3 {
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
        }
        .chat-header .close-chat {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            border: none;
            background: rgba(255, 255, 255, 0.05);
            color: #94a3b8;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 12px 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .chat-message {
            max-width: 80%;
            padding: 8px 12px;
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.4;
            animation: fadeIn 0.2s ease;
        }
        .chat-message.sent {
            align-self: flex-end;
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border-bottom-right-radius: 4px;
        }
        .chat-message.received {
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.05);
            color: #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        .chat-message .timestamp {
            font-size: 11px;
            color: #64748b;
            margin-top: 2px;
        }
        .chat-input-area {
            padding: 12px 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }
        .chat-input {
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.05);
            color: #e2e8f0;
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }
        .chat-input:focus { border-color: rgba(59, 130, 246, 0.5); }
        .chat-send-btn {
            width: 100%;
            padding: 10px;
            margin-top: 8px;
            border-radius: 8px;
            border: none;
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }
        .chat-send-btn:hover { background: rgba(59, 130, 246, 0.35); }
        .chat-send-btn:disabled { background: rgba(255, 255, 255, 0.05); color: #64748b; cursor: not-allowed; }
        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
        }
        .status-indicator.active { background: #22c55e; box-shadow: 0 0 6px rgba(34, 197, 94, 0.5); }
        .status-indicator.inactive { background: #64748b; }
        .status-indicator.pending { background: #f59e0b; box-shadow: 0 0 6px rgba(245, 158, 11, 0.5); }
        .user-info {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            color: white;
        }
        .user-avatar.doctor { background: linear-gradient(135deg, #6366f1, #a855f7); }
        .user-avatar.patient { background: linear-gradient(135deg, #06b6d4, #22d3ee); }
        .user-avatar.system { background: linear-gradient(135deg, #f59e0b, #f97316); }
        .user-name {
            font-size: 13px;
            font-weight: 600;
        }
        .user-role {
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .patient-info {
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        .patient-info h4 {
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }
        .patient-detail {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #cbd5e1;
            margin-bottom: 4px;
        }
        .patient-detail .label { color: #64748b; }
        .patient-detail .value { color: #e2e8f0; font-weight: 500; }
        .patient-detail .value.cns { color: #60a5fa; }
        .patient-detail .value.cpf { color: #f472b6; }
        .patient-detail .value.cid10 { color: #34d399; }
        .patient-detail .value.ciap2 { color: #fbbf24; }
        .patient-detail .value.soap { color: #a78bfa; }
        .patient-detail .value.cns { color: #fbbf24; }
        .patient-detail .value.cpf { color: #f472b6; }
        .patient-detail .value.cid10 { color: #34d399; }
        .patient-detail .value.ciap2 { color: #fbbf24; }
        .patient-detail .value.soap { color: #a78bfa; }
        .patient-detail .value.cns { color: #fbbf24; }
        .patient-detail .value.cpf { color: #f472b6; }
        .patient-detail .value.cid10 { color: #34d399; }
        .patient-detail .value.ciap2 { color: #fbbf24; }
        .patient-detail .value.soap { color: #a78bfa; }
        .patient-detail .value.cns { color: #fbbf24; }
        .patient-detail .value.cpf { color: #f472b6; }
        .patient-detail .value.cid10 { color: #34d399; }
        .patient-detail .value.ciap2 { color: #fbbf24; }
        .patient-detail .value.soap { color: #a78bfa; }
        .patient-detail .value.cns { color: #fbbf24; }
        .patient-detail .value.cpf { color: #f472b6; }
        .patient-detail .value.cid10 { color: #34d399; }
        .patient-detail .value.ciap2 { color: #fbbf24; }
        .patient-detail .value.soap { color: #a78bfa; }
        .patient-detail .value.cns { color: #fbbf24; }
        .patient-detail .value.cpf { color: #f472b6; }
        .patient-detail .value.cid10 { color: #34d399; }
        .patient-detail .value.ciap2 { color: #fbbf24; }
        .patient-detail .value.soap { color: #a78bfa; }
        .patient-detail .value.cns { color: #fbbf24; }
        .patient-detail .value.cpf { color: #f472b6; }
        .patient-detail .value.cid10 { color: #34d399; }
        .patient-detail .value.ciap2 { color: #fbbf24; }
        .patient-detail .value.so