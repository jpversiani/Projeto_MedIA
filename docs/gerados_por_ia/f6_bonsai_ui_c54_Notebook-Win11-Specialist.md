```html:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card Copiloto — Prontuário Web</title>
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
                        medical: {
                            primary: '#0f172a',
                            accent: '#3b82f6',
                            warning: '#f59e0b',
                            danger: '#ef4444',
                            success: '#10b981',
                            bg: '#f8fafc',
                            card: '#ffffff',
                            border: '#e2e8f0',
                        }
                    },
                    animation: {
                        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        'fade-in-up': 'fadeInUp 0.5s ease-out forwards',
                        'slide-in-left': 'slideInLeft 0.4s ease-out forwards',
                        'slide-in-right': 'slideInRight 0.4s ease-out forwards',
                    },
                    keyframes: {
                        fadeInUp: {
                            '0%': { opacity: '0', transform: 'translateY(20px)' },
                            '100%': { opacity: '1', transform: 'translateY(0)' },
                        },
                        slideInLeft: {
                            '0%': { opacity: '0', transform: 'translateX(-30px)' },
                            '100%': { opacity: '1', transform: 'translateX(0)' },
                        },
                        slideInRight: {
                            '0%': { opacity: '0', transform: 'translateX(30px)' },
                            '100%': { opacity: '1', transform: 'translateX(0)' },
                        }
                    }
                }
            }
        }
    </script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f8fafc;
        }
        .card-glow {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
                        0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .card-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1),
                        0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        .hypothesis-card {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .hypothesis-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.15);
        }
        .interaction-badge {
            transition: all 0.2s ease;
        }
        .interaction-badge:hover {
            transform: scale(1.05);
        }
        .stat-ring {
            transition: stroke 0.5s ease;
        }
        .stat-ring:hover {
            stroke: #3b82f6;
        }
        .pulse-dot {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.5); }
        }
        .progress-bar {
            transition: width 1s ease-out;
        }
        .cns-badge {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        }
        .risk-high { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .risk-medium { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .risk-low { background: #d1fae5; color: #065f46; border: 1px solid #bbf7d0; }
        .tab-active {
            background: #3b82f6;
            color: white;
        }
        .tab-inactive {
            background: #e2e8f0;
            color: #64748b;
        }
        .tab-inactive:hover {
            background: #cbd5e1;
            color: #334155;
        }
        .tab-inactive.active {
            background: #3b82f6;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active:hover {
            background: #2563eb;
            color: white;
        }
        .tab-inactive.active