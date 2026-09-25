```python:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card Copiloto - Prontuário Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f0f2f5;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.08);
        }
        .stat-bar {
            height: 6px;
            border-radius: 3px;
            background: linear-gradient(90deg, #3b82f6, #2563eb);
            transition: width 0.5s ease;
        }
        .hypothesis-card {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .hypothesis-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }
        .drug-interaction {
            transition: transform 0.2s ease;
        }
        .drug-interaction:hover {
            transform: scale(1.02);
        }
        .pulse-dot {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .suspense-bar {
            width: 0%;
            transition: width 1.5s ease;
        }
        .suspense-bar.active {
            width: 100%;
        }
        .suspense-bar.active:nth-child(1) { transition-delay: 0.1s; }
        .suspense-bar.active:nth-child(2) { transition-delay: 0.3s; }
        .suspense-bar.active:nth-child(3) { transition-delay: 0.5s; }
        .suspense-bar.active:nth-child(4) { transition-delay: 0.7s; }
        .suspense-bar.active:nth-child(5) { transition-delay: 0.9s; }
        .suspense-bar.active:nth-child(6) { transition-delay: 1.1s; }
        .suspense-bar.active:nth-child(7) { transition-delay: 1.3s; }
        .suspense-bar.active:nth-child(8) { transition-delay: 1.5s; }
        .suspense-bar.active:nth-child(9) { transition-delay: 1.7s; }
        .suspense-bar.active:nth-child(10) { transition-delay: 1.9s; }
        .suspense-bar.active:nth-child(11) { transition-delay: 2.1s; }
        .suspense-bar.active:nth-child(12) { transition-delay: 2.3s; }
        .suspense-bar.active:nth-child(13) { transition-delay: 2.5s; }
        .suspense-bar.active:nth-child(14) { transition-delay: 2.7s; }
        .suspense-bar.active:nth-child(15) { transition-delay: 2.9s; }
        .suspense-bar.active:nth-child(16) { transition-delay: 3.1s; }
        .suspense-bar.active:nth-child(17) { transition-delay: 3.3s; }
        .suspense-bar.active:nth-child(18) { transition-delay: 3.5s; }
        .suspense-bar.active:nth-child(19) { transition-delay: 3.7s; }
        .suspense-bar.active:nth-child(20) { transition-delay: 3.9s; }
        .suspense-bar.active:nth-child(21) { transition-delay: 4.1s; }
        .suspense-bar.active:nth-child(22) { transition-delay: 4.3s; }
        .suspense-bar.active:nth-child(23) { transition-delay: 4.5s; }
        .suspense-bar.active:nth-child(24) { transition-delay: 4.7s; }
        .suspense-bar.active:nth-child(25) { transition-delay: 4.9s; }
        .suspense-bar.active:nth-child(26) { transition-delay: 5.1s; }
        .suspense-bar.active:nth-child(27) { transition-delay: 5.3s; }
        .suspense-bar.active:nth-child(28) { transition-delay: 5.5s; }
        .suspense-bar.active:nth-child(29) { transition-delay: 5.7s; }
        .suspense-bar.active:nth-child(30) { transition-delay: 5.9s; }
        .suspense-bar.active:nth-child(31) { transition-delay: 6.1s; }
        .suspense-bar.active:nth-child(32) { transition-delay: 6.3s; }
        .suspense-bar.active:nth-child(33) { transition-delay: 6.5s; }
        .suspense-bar.active:nth-child(34) { transition-delay: 6.7s; }
        .suspense-bar.active:nth-child(35) { transition-delay: 6.9s; }
        .suspense-bar.active:nth-child(36) { transition-delay: 7.1s; }
        .suspense-bar.active:nth-child(37) { transition-delay: 7.3s; }
        .suspense-bar.active:nth-child(38) { transition-delay: 7.5s; }
        .suspense-bar.active:nth-child(39) { transition-delay: 7.7s; }
        .suspense-bar.active:nth-child(40) { transition-delay: 7.9s; }
        .suspense-bar.active:nth-child(41) { transition-delay: 8.1s; }
        .suspense-bar.active:nth-child(42) { transition-delay: 8.3s; }
        .suspense-bar.active:nth-child(43) { transition-delay: 8.5s; }
        .suspense-bar.active:nth-child(44) { transition-delay: 8.7s; }
        .suspense-bar.active:nth-child(45) { transition-delay: 8.9s; }
        .suspense-bar.active:nth-child(46) { transition-delay: 9.1s; }
        .suspense-bar.active:nth-child(47) { transition-delay: 9.3s; }
        .suspense-bar.active:nth-child(48) { transition-delay: 9.5s; }
        .suspense-bar.active:nth-child(49) { transition-delay: 9.7s; }
        .suspense-bar.active:nth-child(50) { transition-delay: 9.9s; }
        .suspense-bar.active:nth-child(51) { transition-delay: 10.1s; }
        .suspense-bar.active:nth-child(52) { transition-delay: 10.3s; }
        .suspense-bar.active:nth-child(53) { transition-delay: 10.5s; }
        .suspense-bar.active:nth-child(54) { transition-delay: 10.7s; }
        .suspense-bar.active:nth-child(55) { transition-delay: 10.9s; }
        .suspense-bar.active:nth-child(56) { transition-delay: 11.1s; }
        .suspense-bar.active:nth-child(57) { transition-delay: 11.3s; }
        .suspense-bar.active:nth-child(58) { transition-delay: 11.5s; }
        .suspense-bar.active:nth-child(59) { transition-delay: 11.7s; }
        .suspense-bar.active:nth-child(60) { transition-delay: 11.9s; }
        .suspense-bar.active:nth-child(61) { transition-delay: 12.1s; }
        .suspense-bar.active:nth-child(62) { transition-delay: 12.3s; }
        .suspense-bar.active:nth-child(63) { transition-delay: 12.5s; }
        .suspense-bar.active:nth-child(64) { transition-delay: 12.7s; }
        .suspense-bar.active:nth-child(65) { transition-delay: 12.9s; }
        .suspense-bar.active:nth-child(66) { transition-delay: 13.1s; }
        .suspense-bar.active:nth-child(67) { transition-delay: 13.3s; }
        .suspense-bar.active:nth-child(68) { transition-delay: 13.5s; }
        .suspense-bar.active:nth-child(69) { transition-delay: 13.7s; }
        .suspense-bar.active:nth-child(70) { transition-delay: 13.9s; }
        .suspense-bar.active:nth-child(71) { transition-delay: 14.1s; }
        .suspense-bar.active:nth-child(72) { transition-delay: 14.3s; }
        .suspense-bar.active:nth-child(73) { transition-delay: 14.5s; }
        .suspense-bar.active:nth-child(74) { transition-delay: 14.7s; }
        .suspense-bar.active:nth-child(75) { transition-delay: 14.9s; }
        .suspense-bar.active:nth-child(76) { transition-delay: 15.1s; }
        .suspense-bar.active:nth-child(77) { transition-delay: 15.3s; }
        .suspense-bar.active:nth-child(78) { transition-delay: 15.5s; }
        .suspense-bar.active:nth-child(79) { transition-delay: 15.7s; }
        .suspense-bar.active:nth-child(80) { transition-delay: 15.9s; }
        .suspense-bar.active:nth-child(81) { transition-delay: 16.1s; }
        .suspense-bar.active:nth-child(82) { transition-delay: 16.3s; }
        .suspense-bar.active:nth-child(83) { transition-delay: 16.5s; }
        .suspense-bar.active:nth-child(84) { transition-delay: 16.7s; }
        .suspense-bar.active:nth-child(85) { transition-delay: 16.9s; }
        .suspense-bar.active:nth-child(86) { transition-delay: 17.1s; }
        .suspense-bar.active:nth-child(87) { transition-delay: 17.3s; }
        .suspense-bar.active:nth-child(88) { transition-delay: 17.5s; }
        .suspense-bar.active:nth-child(89) { transition-delay: 17.7s; }
        .suspense-bar.active:nth-child(90) { transition-delay: 17.9s; }
        .suspense-bar.active:nth-child(91) { transition-delay: 18.1s; }
        .suspense-bar.active:nth-child(92) { transition-delay: 18.3s; }
        .suspense-bar.active:nth-child(93) { transition-delay: 18.5s; }
        .suspense-bar.active:nth-child(94) { transition-delay: 18.7s; }
        .suspense-bar.active:nth-child(95) { transition-delay: 18.9s; }
        .suspense-bar.active:nth-child(96) { transition-delay: 19.1s; }
        .suspense-bar.active:nth-child(97) { transition-delay: 19.3s; }
        .suspense-bar.active:nth-child(98) { transition-delay: 19.5s; }
        .suspense-bar.active:nth-child(99) { transition-delay: 19.7s; }
        .suspense-bar.active:nth-child(100) { transition-delay: 19.9s; }
        .suspense-bar.active:nth-child(101) { transition-delay: 20.1s; }
        .suspense-bar.active:nth-child(102) { transition-delay: 20.3s; }
        .suspense-bar.active:nth-child(103) { transition-delay: 20.5s; }
        .suspense-bar.active:nth-child(104) { transition-delay: 20.7s; }
        .suspense-bar.active:nth-child(105) { transition-delay: 20.9s; }
        .suspense-bar.active:nth-child(106) { transition-delay: 21.1s; }
        .suspense-bar.active:nth-child(107) { transition-delay: 21.3s; }
        .suspense-bar.active:nth-child(108) { transition-delay: 21.5s; }
        .suspense-bar.active:nth-child(109) { transition-delay: 21.7s; }
        .suspense-bar.active:nth-child(110) { transition-delay: 21.9s; }
        .suspense-bar.active:nth-child(111) { transition-delay: 22.1s; }
        .suspense-bar.active:nth-child(112) { transition-delay: 22.3s; }
        .suspense-bar.active:nth-child(113) { transition-delay: 22.5s; }
        .suspense-bar.active:nth-child(114) { transition-delay: 22.7s; }
        .suspense-bar.active:nth-child(115) { transition-delay: 22.9s; }
        .suspense-bar.active:nth-child(116) { transition-delay: 23.1s; }
        .suspense-bar.active:nth-child(117) { transition-delay: 23.3s; }
        .suspense-bar.active:nth-child(118) { transition-delay: 23.5s; }
        .suspense-bar.active:nth-child(119) { transition-delay: 2