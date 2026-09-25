```html:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="min-h-screen">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmacia Dispensação - UBS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {
            font-family: 'Inter', sans-serif;
        }
        body {
            background: #0f172a;
            color: #e2e8f0;
        }
        .scan-ring {
            animation: pulse-ring 2s infinite;
        }
        @keyframes pulse-ring {
            0% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.05); opacity: 1; }
            100% { transform: scale(1); opacity: 0.5; }
        }
        .scan-ring::after {
            content: '';
            position: absolute;
            inset: -4px;
            border: 2px solid #3b82f6;
            border-radius: 50%;
            animation: pulse-ring 2s infinite;
        }
        .scan-ring::before {
            content: '';
            position: absolute;
            inset: -8px;
            border: 2px solid #60a5fa;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::before::before {
            content: '';
            position: absolute;
            inset: -12px;
            border: 2px solid #93c5fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::before::after {
            content: '';
            position: absolute;
            inset: -16px;
            border: 2px solid #c7d2fe;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::before::before {
            content: '';
            position: absolute;
            inset: -20px;
            border: 2px solid #d0e6ff;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::before::after {
            content: '';
            position: absolute;
            inset: -24px;
            border: 2px solid #e0f2fe;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after {
            content: '';
            position: absolute;
            inset: -28px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -32px;
            border: 2px solid #e0f2fe;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -36px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -40px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -44px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -48px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -52px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -56px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -60px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -64px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -68px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -72px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -76px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -80px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -84px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -88px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -92px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -96px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -100px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -104px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -108px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -112px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -116px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -120px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -124px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -128px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -132px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -136px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -140px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -144px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -148px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -152px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -156px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -160px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -164px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -168px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -172px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -176px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -180px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -184px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: '';
            position: absolute;
            inset: -188px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::before {
            content: '';
            position: absolute;
            inset: -192px;
            border: 2px solid #e8f4fd;
            border-radius: 50%;
            animation: pulse-ring 2s infinite reverse;
        }
        .scan-ring::after::after {
            content: