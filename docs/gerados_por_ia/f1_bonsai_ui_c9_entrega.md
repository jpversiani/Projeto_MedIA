```python:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta — SUS / APS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0a0f;
            color: #e2e8f0;
            height: 100vh;
            overflow: hidden;
        }
        /* ── Video Grid ── */
        .video-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 12px;
            padding: 12px;
            background: #111827;
            border-radius: 16px;
            overflow: hidden;
        }
        .video-cell {
            position: relative;
            aspect-ratio: 4 / 3;
            background: #0f172a;
            border-radius: 12px;
            overflow: hidden;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s ease;
        }
        .video-cell:hover { transform: scale(1.02); }
        .video-cell.active {
            border: 2px solid #3b82f6;
            z-index: 10;
        }
        .video-cell .placeholder {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            background: linear-gradient(135deg, #1e293b, #0f172a);
        }
        .video-cell .placeholder .avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            color: white;
            font-weight: 700;
            box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
        }
        .video-cell .placeholder .label {
            font-size: 13px;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .video-cell .placeholder .label .cns {
            font-size: 11px;
            color: #64748b;
            margin-top: 2px;
        }
        .video-cell .overlay {
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.2s;
        }
        .video-cell:hover .overlay { opacity: 1; }
        .video-cell .overlay .icon {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: rgba(59, 130, 246, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
        }

        /* ── Control Bar ── */
        .control-bar {
            position: fixed;
            bottom: 16px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 24px;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 100px;
            z-index: 100;
        }
        .control-btn {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: 1px solid rgba(59, 130, 246, 0.3);
            background: rgba(15, 23, 42, 0.8);
            color: #94a3b8;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .control-btn:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #3b82f6;
            border-color: #3b82f6;
        }
        .control-btn.active {
            background: rgba(59, 130, 246, 0.3);
            color: #3b82f6;
            border-color: #3b82f6;
        }
        .control-btn .icon { font-size: 18px; }

        /* ── Chat Panel ── */
        .chat-panel {
            position: fixed;
            top: 0;
            right: 0;
            width: 360px;
            max-width: 90vw;
            height: 100vh;
            background: #0f172a;
            border-left: 1px solid rgba(59, 130, 246, 0.2);
            z-index: 50;
            display: flex;
            flex-direction: column;
            transition: transform 0.3s ease;
        }
        .chat-panel.hidden {
            transform: translateX(100%);
        }
        .chat-header {
            padding: 16px 20px;
            border-bottom: 1px solid rgba(59, 130, 246, 0.2);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .chat-header h3 {
            font-size: 16px;
            font-weight: 700;
            color: #e2e8f0;
        }
        .chat-header .status {
            font-size: 12px;
            color: #34d399;
            font-weight: 600;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .chat-message {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.5;
            animation: fadeIn 0.2s ease;
        }
        .chat-message.sent {
            align-self: flex-end;
            background: rgba(59, 130, 246, 0.15);
            color: #3b82f6;
        }
        .chat-message.received {
            align-self: flex-start;
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
        }
        .chat-message .meta {
            font-size: 11px;
            color: #64748b;
            margin-top: 4px;
        }
        .chat-input-area {
            padding: 12px 20px;
            border-top: 1px solid rgba(59, 130, 246, 0.2);
        }
        .chat-input-area input {
            width: 100%;
            padding: 10px 14px;
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 8px;
            color: #e2e8f0;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        .chat-input-area input:focus {
            border-color: #3b82f6;
        }
        .chat-input-area button {
            margin-top: 8px;
            width: 100%;
            padding: 10px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .chat-input-area button:hover { opacity: 0.9; }

        /* ── Overlay ── */
        .overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.6);
            z-index: 40;
            display: none;
            align-items: center;
            justify-content: center;
        }
        .overlay.active { display: flex; }
        .overlay-content {
            background: #1e293b;
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            max-width: 400px;
            width: 90%;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .overlay-content h2 {
            font-size: 24px;
            font-weight: 800;
            color: #e2e8f0;
            margin-bottom: 8px;
        }
        .overlay-content p {
            color: #94a3b8;
            font-size: 14px;
            margin-bottom: 24px;
        }
        .overlay-content .btn {
            padding: 12px 32px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .overlay-content .btn:hover { opacity: 0.9; }

        /* ── Notification Badge ── */
        .notification-badge {
            position: absolute;
            top: 8px;
            right: 8px;
            width: 18px;
            height: 18px;
            background: #ef4444;
            border-radius: 50%;
            border: 2px solid #111827;
        }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* ── Responsive ── */
        @media (max-width: 768px) {
            .video-grid {
                grid-template-columns: 1fr;
                grid-template-rows: 1fr;
                gap: 8px;
                padding: 8px;
            }
            .chat-panel {
                width: 100%;
                max-width: none;
                border-left: none;
                border-top: 1px solid rgba(59, 130, 246, 0.2);
            }
            .chat-panel.hidden {
                transform: none;
                display: none;
            }
            .control-bar {
                bottom: 8px;
                left: 8px;
                right: 8px;
                padding: 8px 16px;
                gap: 8px;
            }
            .chat-panel {
                top: 0;
                right: 0;
                border-left: none;
                border-top: 1px solid rgba(59, 130, 246, 0.2);
            }
        }

        /* ── Loading Skeleton ── */
        .skeleton {
            background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        /* ── Medical Badge ── */
        .medical-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 8px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 100px;
            font-size: 11px;
            color: #34d399;
            font-weight: 600;
       