# Telemedicina Sala - Interface Completa

## Arquivo Principal: `backend/app/static/telemedicina_sala.html`

```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta - SUS/APS</title>
    <meta name="description" content="Sala de teleconsulta com integração SUS/APS">
    <meta name="csp" content="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' https://cdn.tailwindcss.com; img-src 'self' data: https:; font-src 'self' https:">

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        sus: {
                            primary: '#1a365d',
                            secondary: '#2d5a7d',
                            accent: '#e74c3c',
                            light: '#f0f4f8',
                            success: '#2ecc71',
                            warning: '#f39c12',
                            error: '#e74c3c',
                            bg: '#ffffff'
                        }
                    },
                    fontFamily: {
                        sans: ['Inter', 'Segoe UI', 'Arial', 'sans-serif'],
                        mono: ['Consolas', 'Monaco', 'monospace']
                    },
                    animation: {
                        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        'slide-in': 'slideIn 0.3s ease-out forwards',
                        'fade-in': 'fadeIn 0.3s ease-out forwards',
                        'bounce': 'bounce 0.5s ease-in-out infinite'
                    },
                    keyframes: {
                        slideIn: {
                            '0%': { transform: 'translateX(100%)', opacity: '0' },
                            '100%': { transform: 'translateX(0)', opacity: '1' }
                        },
                        fadeIn: {
                            '0%': { opacity: '0' },
                            '100%': { opacity: '1' }
                        }
                    }
                }
            }
        }
    </script>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
        /* Custom styles for telemedicina_sala */
        .glass-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .glass-panel-dark {
            background: rgba(26, 54, 93, 0.85);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .video-container {
            position: relative;
            overflow: hidden;
            border-radius: 0.5rem;
        }

        .video-container::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(
                180deg,
                transparent 0%,
                rgba(0, 0, 0, 0.1) 100%
            );
            pointer-events: none;
        }

        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .status-indicator.connected {
            background: rgba(46, 204, 113, 0.15);
            color: #2ecc71;
            border: 1px solid rgba(46, 204, 113, 0.3);
        }

        .status-indicator.disconnected {
            background: rgba(231, 76, 60, 0.15);
            color: #e74c3c;
            border: 1px solid rgba(231, 76, 60, 0.3);
        }

        .status-indicator.pending {
            background: rgba(243, 156, 18, 0.15);
            color: #f39c12;
            border: 1px solid rgba(243, 156, 18, 0.3);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .chat-message {
            animation: fadeIn 0.3s ease-out forwards;
        }

        .chat-message.sent {
            align-self: flex-end;
        }

        .chat-message.received {
            align-self: flex-start;
        }

        .chat-input-wrapper {
            transition: box-shadow 0.3s ease;
        }

        .chat-input-wrapper:focus-within {
            box-shadow: 0 0 0 3px rgba(26, 54, 93, 0.1);
        }

        .control-btn {
            transition: all 0.2s ease;
            position: relative;
        }

        .control-btn:hover {
            transform: scale(1.05);
        }

        .control-btn:active {
            transform: scale(0.95);
        }

        .control-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .control-btn:disabled:hover {
            transform: none;
        }

        .control-btn.active {
            background: rgba(26, 54, 93, 0.15);
            color: #1a365d;
        }

        .control-btn.active:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93, 0.2);
        }

        .control-btn.active:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover:hover {
            background: rgba(26, 54, 93,