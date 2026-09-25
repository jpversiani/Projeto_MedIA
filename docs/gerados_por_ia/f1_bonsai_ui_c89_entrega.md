```python
# Arquivo: backend/app/static/telemedicina_sala.html
"""
Painel Visual de Chamada de Teleconsulta
Projeto MedIA - Interface de Consultas por Vídeo
Arquitetura: Tailwind CSS + Vanilla JS (WebRTC-ready)
"""

<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Consultas — MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                    colors: {
                        medical: {
                            50:  '#f0fdf4',
                            100: '#e6f7ff',
                            200: '#bae6fd',
                            300: '#93c5fd',
                            400: '#60a5fa',
                            500: '#3b82f6',
                            600: '#2563eb',
                            700: '#1d4ed8',
                            800: '#1e40af',
                            900: '#1e3a8a',
                            950: '#172554',
                        },
                        clinical: {
                            dark: '#0f172a',
                            surface: '#1e293b',
                            card: '#334155',
                            border: '#475569',
                            accent: '#3b82f6',
                            success: '#10b981',
                            warning: '#f59e0b',
                            danger: '#ef4444',
                        }
                    },
                    animation: {
                        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        'fade-in-up': 'fadeInUp 0.5s ease-out forwards',
                        'slide-in-right': 'slideInRight 0.4s ease-out forwards',
                        'slide-in-left': 'slideInLeft 0.4s ease-out forwards',
                    },
                    keyframes: {
                        fadeInUp: {
                            '0%': { opacity: '0', transform: 'translateY(20px)' },
                            '100%': { opacity: '1', transform: 'translateY(0)' },
                        },
                        slideInRight: {
                            '0%': { opacity: '0', transform: 'translateX(30px)' },
                            '100%': { opacity: '1', transform: 'translateX(0)' },
                        },
                        slideInLeft: {
                            '0%': { opacity: '0', transform: 'translateX(-30px)' },
                            '100%': { opacity: '1', transform: 'translateX(0)' },
                        }
                    }
                }
            }
        }
    </script>
    <style>
        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #1e293b; }
        ::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #64748b; }

        /* Video Grid */
        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            grid-template-rows: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }

        .video-card {
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            background: #0f172a;
            aspect-ratio: 16/9;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .video-card:hover {
            transform: scale(1.02);
            box-shadow: 0 0 30px rgba(59, 130, 246, 0.3);
        }

        .video-card.active {
            border: 2px solid #3b82f6;
            box-shadow: 0 0 40px rgba(59, 130, 246, 0.4);
        }

        .video-card .video-placeholder {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #1e293b, #0f172a);
        }

        .video-card .video-placeholder .avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 12px;
            border: 2px solid #334155;
        }

        .video-card .video-placeholder .name {
            color: #94a3b8;
            font-size: 12px;
            font-weight: 500;
        }

        .video-card .video-placeholder .role {
            color: #64748b;
            font-size: 10px;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Status Indicator */
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
        }
        .status-dot.online { background: #10b981; box-shadow: 0 0 6px #10b981; }
        .status-dot.offline { background: #64748b; }
        .status-dot.pending { background: #f59e0b; }

        /* Chat Styles */
        .chat-message {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 16px;
            font-size: 13px;
            line-height: 1.5;
            margin-bottom: 8px;
            animation: fadeInUp 0.3s ease-out;
        }
        .chat-message.sent {
            background: #3b82f6;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        .chat-message.received {
            background: #1e293b;
            color: #e2e8f0;
            margin-right: auto;
            border-bottom-left-radius: 4px;
        }

        .chat-input {
            background: #1e293b;
            border: 1px solid #475569;
            color: #e2e8f0;
            transition: all 0.2s ease;
        }
        .chat-input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        }

        /* Control Bar */
        .control-btn {
            transition: all 0.2s ease;
        }
        .control-btn:hover {
            transform: scale(1.1);
        }

        /* Participant Badge */
        .participant-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-doctor {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .badge-patient {
            background: rgba(16, 185, 129, 0.2);
            color: #6ee7b7;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .badge-nurse {
            background: rgba(245, 158, 11, 0.2);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        /* Scrollbar for chat */
        .chat-scroll {
            overflow-y: auto;
            max-height: 300px;
        }

        /* Notification Toast */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 12px 20px;
            border-radius: 10px;
            color: white;
            font-size: 13px;
            font-weight: 500;
            z-index: 9999;
            animation: slideInRight 0.3s ease-out, fadeOut 0.3s ease-in 2.7s forwards;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        @keyframes fadeOut {
            to { opacity: 0; transform: translateX(30px); }
        }

        /* Mobile Responsive */
        @media (max-width: 768px) {
            .video-grid {
                grid-template-columns: 1fr;
                grid-template-rows: 1fr;
            }
            .video-card {
                aspect-ratio: 16/9;
            }
        }

        /* Loading Spinner */
        .loader {
            border: 3px solid #334155;
            border-top: 3px solid #3b82f6;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Tab Styles */
        .tab-content {
            display: none;
            animation: fadeInUp 0.3s ease-out;
        }
        .tab-content.active {
            display: block;
        }

        /* Note Card */
        .note-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
        }
        .note-card .note-title {
            color: #60a5fa;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .note-card .note-text {
            color: #94a3b8;
            font-size: 12px;
            line-height: 1.5;
        }
    </style>
</head>
<body class="bg-medical-50 text-slate-800 min-h-screen">
    <!-- ==================== HEADER ==================== -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div class="flex items-center justify-between">
                <!-- Logo -->
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-medical-500 rounded-lg flex items-center justify-center">
                        <i class="fas fa-heart text-white text-lg"></i>
                    </div>
                    <div>
                        <h1 class="text-xl font-bold text-slate-900 tracking-tight">MedIA</h1>
                        <p class="text-xs text-slate-500 font-medium">Medicina Interdisciplinar de Acesso</p>
                    </div>
                </div>

                <!-- Right Side -->
                <div class="flex items-center gap-4">
                    <!-- Notification Bell -->
                    <button class="relative p-2 rounded-lg hover:bg-slate-100 transition-colors" title="Notificações">
                        <i class="fas fa-bell text-slate-600"></i>
                        <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                    </button>

                    <!-- User Profile -->
                    <button class="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-slate-100 transition-colors" title="Perfil">
                        <div class="w-8 h-8 rounded-full bg-medical-500 text-white flex items-center justify-center text-xs font-bold">
                            DR
                        </div>
                        <div class="hidden sm:block">
                            <p class="text-sm font-semibold text-slate-900">Dr. Silva</p>
                            <p class="text-xs text-slate-500">CNS 000.000.000-00</p>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- ==================== MAIN CONTENT ==================== -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex flex-col lg:flex-row gap-4">

            <!-- LEFT: Video Grid -->
            <div class="flex-1 min-h-[400px]">
                <!-- Video Grid Container -->
                <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                    <!-- Video Grid -->
                    <div id="videoGrid" class="video-grid min-h-[400px]">
                        <!-- Video cards will be injected by JS -->
                    </div>
                </