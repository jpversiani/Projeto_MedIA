```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta — SUS / APS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                    colors: {
                        sus: {
                            blue: '#0057a3',
                            dark: '#003d7a',
                            light: '#e8f4f8',
                            accent: '#00b894',
                            warning: '#f5a623',
                            error: '#e74c3c',
                            success: '#2ecc71',
                        },
                        medical: {
                            header: '#0f172a',
                            card: '#ffffff',
                            border: '#e2e8f0',
                            muted: '#94a3b8',
                        }
                    },
                    animation: {
                        'fade-in': 'fadeIn 0.3s ease-out',
                        'slide-up': 'slideUp 0.4s ease-out',
                        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        'spin-slow': 'spin 8s linear infinite',
                    },
                    keyframes: {
                        fadeIn: {
                            '0%': { opacity: '0' },
                            '100%': { opacity: '1' },
                        },
                        slideUp: {
                            '0%': { opacity: '0', transform: 'translateY(20px)' },
                            '100%': { opacity: '1', transform: 'translateY(0)' },
                        }
                    }
                }
            }
        }
    </script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #f1f5f9;
            color: #1e293b;
        }
        .glass-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(226, 232, 240, 0.6);
        }
        .video-container {
            position: relative;
            overflow: hidden;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
        }
        .video-container::after {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(0,87,163,0.05) 0%, transparent 60%);
            pointer-events: none;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: 700;
            color: white;
        }
        .status-dot.live { background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.4); }
        .status-dot.ready { background: #f59e0b; box-shadow: 0 0 8px rgba(245,158,11,0.4); }
        .status-dot.idle { background: #94a3b8; }
        .chat-message {
            animation: slideUp 0.3s ease-out;
        }
        .chat-message.sent {
            align-self: flex-end;
        }
        .chat-message.received {
            align-self: flex-start;
        }
        .chat-message .avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            color: white;
            margin-right: 8px;
            flex-shrink: 0;
        }
        .chat-input-wrapper {
            position: relative;
        }
        .chat-input-wrapper input:focus {
            outline: none;
            border-color: #0057a3;
            box-shadow: 0 0 0 3px rgba(0,87,163,0.1);
        }
        .btn-control {
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        }
        .btn-control:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .btn-control:active {
            transform: translateY(0);
        }
        .btn-control:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .btn-control:disabled:hover {
            transform: none;
            box-shadow: none;
        }
        .control-bar {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid #e2e8f0;
        }
        .scrollbar-thin::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        .scrollbar-thin::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 3px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 3px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
        .cns-badge {
            font-family: 'Courier New', monospace;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
        }
        .badge-consultation {
            background: linear-gradient(135deg, #0057a3, #003d7a);
            color: white;
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        .badge-specialty {
            background: #f0f9ff;
            color: #0057a3;
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 600;
        }
        .badge-appointment {
            background: #fef3c7;
            color: #92400e;
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 600;
        }
        .video-overlay {
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            padding: 16px;
            background: linear-gradient(to top, rgba(0,0,0,0.5) 0%, transparent 60%);
            pointer-events: none;
        }
        .video-overlay .info {
            color: white;
            pointer-events: auto;
        }
        .video-overlay .name {
            font-size: 1.1rem;
            font-weight: 700;
        }
        .video-overlay .role {
            font-size: 0.8rem;
            font-weight: 500;
            opacity: 0.9;
        }
        .video-overlay .cns {
            font-size: 0.7rem;
            opacity: 0.8;
        }
        .video-overlay .status {
            position: absolute;
            top: 12px;
            right: 12px;
        }
        .video-overlay .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: 700;
            color: white;
        }
        .video-overlay .status-dot.live { background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.4); }
        .video-overlay .status-dot.ready { background: #f59e0b; box-shadow: 0 0 8px rgba(245,158,11,0.4); }
        .video-overlay .status-dot.idle { background: #94a3b8; }
        .video-overlay .status-dot.error { background: #e74c3c; box-shadow: 0 0 8px rgba(231,76,60,0.4); }
        .video-overlay .status-dot .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: white;
        }
        .video-overlay .status-dot .dot::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
            50% { opacity: 0.5; transform: translate(-50%, -50%) scale(1.5); }
        }
        .chat-input {
            transition: all 0.2s ease;
        }
        .chat-input::placeholder {
            color: #94a3b8;
        }
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: 4px;
        }
        .typing-indicator .dots span {
            animation: typing 1.4s infinite;
            animation-delay: 0.32s;
        }
        .typing-indicator .dots span:nth-child(2) { animation-delay: 0.16s; }
        .typing-indicator .dots span:nth-child(3) { animation-delay: 0.08s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
            30% { transform: translateY(-4px); opacity: 1; }
        }
        .notification-toast {
            animation: slideUp 0.4s ease-out;
        }
        .notification-toast.exiting {
            animation: slideDown 0.3s ease-in forwards;
        }
        @keyframes slideDown {
            to { opacity: 0; transform: translateY(-10px); }
        }
        .loading-skeleton {
            background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        .fade-in-section {
            opacity: 0;
            animation: fadeIn 0.5s ease-out forwards;
        }
        .fade-in-section:nth-child(2) { animation-delay: 0.1s; }
        .fade-in-section:nth-child(3) { animation-delay: 0.2s; }
        .fade-in-section:nth-child(4) { animation-delay: 0.3s; }
        .fade-in-section:nth-child(5) { animation-delay: 0.4s; }
        .fade-in-section:nth-child(6) { animation-delay: 0.5s; }
        .fade-in-section:nth-child(7) { animation-delay: 0.6s; }
        .fade-in-section:nth-child(8) { animation-delay: 0.7s; }
        .fade-in-section:nth-child(9) { animation-delay: 0.8s; }
        .fade-in-section:nth-child(10) { animation-delay: 0.9s; }
        .fade-in-section:nth-child(11) { animation-delay: 1s; }
        .fade-in-section:nth-child(12) { animation-delay: 1.1s; }
        .fade-in-section:nth-child(13) { animation-delay: 1.2s; }
        .fade-in-section:nth-child(14) { animation-delay: 1.3s; }
        .fade-in-section:nth-child(15) { animation-delay: 1.4s; }
        .fade-in-section:nth-child(16) { animation-delay: 1.5s; }
        .fade-in-section:nth-child(17) { animation-delay: 1.6s; }
        .fade-in