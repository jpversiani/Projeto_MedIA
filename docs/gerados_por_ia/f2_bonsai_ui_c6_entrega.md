```python:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia Dispensação - UBS - Consulta e Baixa de Prescrição</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
        }

        .glass-panel {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .glass-card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .scan-area {
            position: relative;
            overflow: hidden;
            border-radius: 12px;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }

        .scan-area::before {
            content: '';
            position: absolute;
            inset: 0;
            background: repeating-linear-gradient(
                45deg,
                transparent,
                transparent 10px,
                rgba(59, 130, 246, 0.03) 10px,
                rgba(59, 130, 246, 0.03) 20px
            );
            pointer-events: none;
        }

        .scan-area::after {
            content: '';
            position: absolute;
            inset: 0;
            border: 2px dashed rgba(59, 130, 246, 0.3);
            border-radius: 10px;
            pointer-events: none;
        }

        .scan-area .scan-content {
            position: relative;
            z-index: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 16px;
        }

        .scan-area .scan-content .scan-label {
            font-size: 0.8rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .scan-area .scan-content .scan-icon {
            font-size: 4rem;
            color: rgba(59, 130, 246, 0.1);
        }

        .scan-area .scan-content .scan-hint {
            font-size: 0.9rem;
            color: #94a3b8;
        }

        .scan-area .scan-content .scan-hint i {
            margin-right: 8px;
            color: #5982ce;
        }

        .scan-area .scan-content .scan-hint .pulse {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .scan-area .scan-content .scan-hint .bar {
            display: inline-block;
            width: 4px;
            height: 16px;
            background: #5982ce;
            border-radius: 2px;
            margin-right: 4px;
        }

        .scan-area .scan-content .scan-hint .bar:nth-child(2) { animation-delay: 0.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(3) { animation-delay: 0.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(4) { animation-delay: 0.6s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(5) { animation-delay: 0.8s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(6) { animation-delay: 1.0s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(7) { animation-delay: 1.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(8) { animation-delay: 1.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(9) { animation-delay: 1.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(10) { animation-delay: 1.8s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(11) { animation-delay: 2.0s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(12) { animation-delay: 2.2s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(13) { animation-delay: 2.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(14) { animation-delay: 2.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(15) { animation-delay: 2.8s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(16) { animation-delay: 3.0s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(17) { animation-delay: 3.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(18) { animation-delay: 3.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(19) { animation-delay: 3.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(20) { animation-delay: 3.8s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(21) { animation-delay: 4.0s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(22) { animation-delay: 4.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(23) { animation-delay: 4.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(24) { animation-delay: 4.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(25) { animation-delay: 4.8s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(26) { animation-delay: 5.0s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(27) { animation-delay: 5.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(28) { animation-delay: 5.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(29) { animation-delay: 5.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(30) { animation-delay: 5.8s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(31) { animation-delay: 6.0s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(32) { animation-delay: 6.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(33) { animation-delay: 6.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(34) { animation-delay: 6.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(35) { animation-delay: 6.8s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(36) { animation-delay: 7.0s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(37) { animation-delay: 7.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(38) { animation-delay: 7.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(39) { animation-delay: 7.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(40) { animation-delay: 7.8s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(41) { animation-delay: 8.0s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(42) { animation-delay: 8.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(43) { animation-delay: 8.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(44) { animation-delay: 8.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(45) { animation-delay: 8.8s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(46) { animation-delay: 9.0s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(47) { animation-delay: 9.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(48) { animation-delay: 9.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(49) { animation-delay: 9.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(50) { animation-delay: 9.8s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(51) { animation-delay: 10.0s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(52) { animation-delay: 10.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(53) { animation-delay: 10.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(54) { animation-delay: 10.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(55) { animation-delay: 10.8s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(56) { animation-delay: 11.0s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(57) { animation-delay: 11.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(58) { animation-delay: 11.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(59) { animation-delay: 11.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(60) { animation-delay: 11.8s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(61) { animation-delay: 12.0s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(62) { animation-delay: 12.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(63) { animation-delay: 12.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(64) { animation-delay: 12.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(65) { animation-delay: 12.8s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(66) { animation-delay: 13.0s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(67) { animation-delay: 13.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(68) { animation-delay: 13.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(69) { animation-delay: 13.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(70) { animation-delay: 13.8s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(71) { animation-delay: 14.0s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(72) { animation-delay: 14.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(73) { animation-delay: 14.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(74) { animation-delay: 14.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(75) { animation-delay: 14.8s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(76) { animation-delay: 15.0s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(77) { animation-delay: 15.2s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(78) { animation-delay: 15.4s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(79) { animation-delay: 15.6s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(80) { animation-delay: 15.8s; }

        .scan-area .scan-content .scan-hint .bar:nth-child(81) { animation-delay: 16.0s; }
        .scan-area .scan-content .scan-hint .bar:nth-child(82) { animation-delay: 16.2s; }
        .scan-area .scan-content .scan-h