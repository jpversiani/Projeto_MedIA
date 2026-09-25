```html:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia Dispensação - UBS - Sistema MEDIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Roboto+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #0052a3;
            --primary-dark: #003d80;
            --primary-light: #3069a8;
            --accent: #e74c3c;
            --accent-light: #f39c12;
            --success: #2ecc71;
            --warning: #f39c12;
            --danger: #e74c3c;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border-color: #334155;
            --border-light: #475569;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1);
            --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1);
            --shadow-2xl: 0 25px 50px -12px rgba(0,0,0,0.25), 0 10px 15px -7px rgba(0,0,0,0.2);
            --shadow-glow: 0 0 30px rgba(0,82,163,0.3);
            --glass: rgba(30, 41, 59, 0.7);
            --glass-border: rgba(51, 65, 85, 0.3);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        .font-mono {
            font-family: 'Roboto Mono', 'Courier New', monospace;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-dark);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--border-light);
        }

        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes slideInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slideInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }

        @keyframes bounceIn {
            0% { transform: scale(0.9); opacity: 0; }
            50% { transform: scale(1.05); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }

        @keyframes flashRed {
            0% { background: var(--bg-card); }
            50% { background: rgba(231, 76, 60, 0.1); }
            100% { background: var(--bg-card); }
        }

        @keyframes flashGreen {
            0% { background: var(--bg-card); }
            50% { background: rgba(46, 204, 113, 0.1); }
            100% { background: var(--bg-card); }
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .animate-fade-in {
            animation: fadeIn 0.3s ease-out forwards;
        }

        .animate-slide-left {
            animation: slideInLeft 0.3s ease-out forwards;
        }

        .animate-slide-right {
            animation: slideInRight 0.3s ease-out forwards;
        }

        .animate-slide-down {
            animation: slideInDown 0.3s ease-out forwards;
        }

        .animate-slide-up {
            animation: slideInUp 0.3s ease-out forwards;
        }

        .animate-bounce-in {
            animation: bounceIn 0.4s ease-out forwards;
        }

        .animate-shake {
            animation: shake 0.5s ease-in-out;
        }

        .animate-pulse-slow {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        .animate-spin-slow {
            animation: spin 10s linear infinite;
        }

        .animate-flash-red {
            animation: flashRed 0.5s ease-in-out;
        }

        .animate-flash-green {
            animation: flashGreen 0.5s ease-in-out;
        }

        /* Glassmorphism */
        .glass {
            background: var(--glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
        }

        .glass-strong {
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(30px);
            -webkit-backdrop-filter: blur(30px);
            border: 1px solid var(--glass-border);
        }

        .glass-card {
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            transition: all 0.3s ease;
        }

        .glass-card:hover {
            background: rgba(51, 65, 85, 0.9);
            border-color: var(--border-light);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        /* Input styles */
        .input-field {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            transition: all 0.3s ease;
            outline: none;
        }

        .input-field:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(0, 82, 163, 0.2);
        }

        .input-field::placeholder {
            color: var(--text-muted);
        }

        .input-field.error {
            border-color: var(--danger);
            box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.2);
        }

        .input-field.success {
            border-color: var(--success);
            box-shadow: 0 0 0 3px rgba(46, 204, 113, 0.2);
        }

        /* Button styles */
        .btn-primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 82, 163, 0.4);
        }

        .btn-primary:active {
            transform: translateY(0);
        }

        .btn-secondary {
            background: rgba(51, 65, 85, 0.8);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }

        .btn-secondary:hover {
            background: rgba(67, 79, 101, 0.8);
            border-color: var(--border-light);
            transform: translateY(-1px);
        }

        .btn-danger {
            background: linear-gradient(135deg, var(--danger) 0%, #c0392b 100%);
            color: white;
            border: none;
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }

        .btn-danger:hover {
            background: linear-gradient(135deg, #e85d5d 0%, var(--danger) 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(231, 76, 60, 0.4);
        }

        .btn-success {
            background: linear-gradient(135deg, var(--success) 0%, #22c55e 100%);
            color: white;
            border: none;
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }

        .btn-success:hover {
            background: linear-gradient(135deg, #34d399 0%, var(--success) 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(46, 204, 113, 0.4);
        }

        .btn-outline {
            background: transparent;
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 