```html:backend/app/static/telemedicina.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sala de Teleatendimento — MedIA SUS</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: { sans: ['Inter', 'sans-serif'] },
          colors: {
            sus: {
              primary: '#005050',
              secondary: '#007777',
              accent: '#00b894',
              light: '#e8f0f0',
              dark: '#0a1a1a',
              card: '#ffffff',
              border: '#c8d6d9',
              danger: '#dc2626',
              success: '#16a34a',
              warning: '#d97706',
            }
          },
          animation: {
            'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            'fade-in': 'fadeIn 0.3s ease-out',
            'slide-up': 'slideUp 0.3s ease-out',
          },
          keyframes: {
            fadeIn: { '0%': { opacity: 0 }, '100%': { opacity: 1 } },
            slideUp: { '0%': { opacity: 0, transform: 'translateY(10px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
            'spin-slow': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } },
          }
        }
      }
    }
  </script>
  <style>
    body { font-family: 'Inter', sans-serif; }
    .glass {
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }
    .glass-dark {
      background: rgba(10, 26, 26, 0.95);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }
    .glass-card {
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(200, 214, 217, 0.6);
    }
    .glass-panel {
      background: rgba(10, 26, 26, 0.9);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(200, 214, 217, 0.3);
    }
    .video-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      grid-template-rows: 1fr 1fr;
      gap: 12px;
    }
    @media (max-width: 768px) {
      .video-grid {
        grid-template-columns: 1fr;
        grid-template-rows: 1fr;
      }
    }
    .pip-overlay {
      position: absolute;
      top: 12px;
      right: 12px;
      z-index: 10;
    }
    .soap-step {
      transition: all 0.3s ease;
    }
    .soap-step.active {
      border-left: 4px solid #00b894;
      background: rgba(0, 184, 148, 0.08);
    }
    .soap-step.completed {
      border-left: 4px solid #16a34a;
      background: rgba(22, 163, 74, 0.08);
    }
    .soap-step.active .step-icon {
      color: #00b894;
    }
    .soap-step.completed .step-icon {
      color: #16a34a;
    }
    .indicator-card {
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .indicator-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 80, 80, 0.15);
    }
    .timer-bar {
      transition: width 1s linear;
    }
    .fade-in { animation: fadeIn 0.3s ease-out; }
    .slide-up { animation: slideUp 0.3s ease-out; }
    .fade-in-delay-1 { animation-delay: 0.1s; }
    .fade-in-delay-2 { animation-delay: 0.2s; }
    .fade-in-delay-3 { animation-delay: 0.3s; }
    .fade-in-delay-4 { animation-delay: 0.4s; }
    .fade-in-delay-5 { animation-delay: 0.5s; }
    .fade-in-delay-6 { animation-delay: 0.6s; }
    .fade-in-delay-7 { animation-delay: 0.7s; }
    .fade-in-delay-8 { animation-delay: 0.8s; }
    .fade-in-delay-9 { animation-delay: 0.9s; }
    .fade-in-delay-10 { animation-delay: 1.0s; }
    .fade-in-delay-11 { animation-delay: 1.1s; }
    .fade-in-delay-12 { animation-delay: 1.2s; }
    .fade-in-delay-13 { animation-delay: 1.3s; }
    .fade-in-delay-14 { animation-delay: 1.4s; }
    .fade-in-delay-15 { animation-delay: 1.5s; }
    .fade-in-delay-16 { animation-delay: 1.6s; }
    .fade-in-delay-17 { animation-delay: 1.7s; }
    .fade-in-delay-18 { animation-delay: 1.8s; }
    .fade-in-delay-19 { animation-delay: 1.9s; }
    .fade-in-delay-20 { animation-delay: 2.0s; }
    .fade-in-delay-21 { animation-delay: 2.1s; }
    .fade-in-delay-22 { animation-delay: 2.2s; }
    .fade-in-delay-23 { animation-delay: 2.3s; }
    .fade-in-delay-24 { animation-delay: 2.4s; }
    .fade-in-delay-25 { animation-delay: 2.5s; }
    .fade-in-delay-26 { animation-delay: 2.6s; }
    .fade-in-delay-27 { animation-delay: 2.7s; }
    .fade-in-delay-28 { animation-delay: 2.8s; }
    .fade-in-delay-29 { animation-delay: 2.9s; }
    .fade-in-delay-30 { animation-delay: 3.0s; }
    .fade-in-delay-31 { animation-delay: 3.1s; }
    .fade-in-delay-32 { animation-delay: 3.2s; }
    .fade-in-delay-33 { animation-delay: 3.3s; }
    .fade-in-delay-34 { animation-delay: 3.4s; }
    .fade-in-delay-35 { animation-delay: 3.5s; }
    .fade-in-delay-36 { animation-delay: 3.6s; }
    .fade-in-delay-37 { animation-delay: 3.7s; }
    .fade-in-delay-38 { animation-delay: 3.8s; }
    .fade-in-delay-39 { animation-delay: 3.9s; }
    .fade-in-delay-40 { animation-delay: 4.0s; }
    .fade-in-delay-41 { animation-delay: 4.1s; }
    .fade-in-delay-42 { animation-delay: 4.2s; }
    .fade-in-delay-43 { animation-delay: 4.3s; }
    .fade-in-delay-44 { animation-delay: 4.4s; }
    .fade-in-delay-45 { animation-delay: 4.5s; }
    .fade-in-delay-46 { animation-delay: 4.6s; }
    .fade-in-delay-47 { animation-delay: 4.7s; }
    .fade-in-delay-48 { animation-delay: 4.8s; }
    .fade-in-delay-49 { animation-delay: 4.9s; }
    .fade-in-delay-50 { animation-delay: 5.0s; }
    .fade-in-delay-51 { animation-delay: 5.1s; }
    .fade-in-delay-52 { animation-delay: 5.2s; }
    .fade-in-delay-53 { animation-delay: 5.3s; }
    .fade-in-delay-54 { animation-delay: 5.4s; }
    .fade-in-delay-55 { animation-delay: 5.5s; }
    .fade-in-delay-56 { animation-delay: 5.6s; }
    .fade-in-delay-57 { animation-delay: 5.7s; }
    .fade-in-delay-58 { animation-delay: 5.8s; }
    .fade-in-delay-59 { animation-delay: 5.9s; }
    .fade-in-delay-60 { animation-delay: 6.0s; }
    .fade-in-delay-61 { animation-delay: 6.1s; }
    .fade-in-delay-62 { animation-delay: 6.2s; }
    .fade-in-delay-63 { animation-delay: 6.3s; }
    .fade-in-delay-64 { animation-delay: 6.4s; }
    .fade-in-delay-65 { animation-delay: 6.5s; }
    .fade-in-delay-66 { animation-delay: 6.6s; }
    .fade-in-delay-67 { animation-delay: 6.7s; }
    .fade-in-delay-68 { animation-delay: 6.8s; }
    .fade-in-delay-69 { animation-delay: 6.9s; }
    .fade-in-delay-70 { animation-delay: 7.0s; }
    .fade-in-delay-71 { animation-delay: 7.1s; }
    .fade-in-delay-72 { animation-delay: 7.2s; }
    .fade-in-delay-73 { animation-delay: 7.3s; }
    .fade-in-delay-74 { animation-delay: 7.4s; }
    .fade-in-delay-75 { animation-delay: 7.5s; }
    .fade-in-delay-76 { animation-delay: 7.6s; }
    .fade-in-delay-77 { animation-delay: 7.7s; }
    .fade-in-delay-78 { animation-delay: 7.8s; }
    .fade-in-delay-79 { animation-delay: 7.9s; }
    .fade-in-delay-80 { animation-delay: 8.0s; }
    .fade-in-delay-81 { animation-delay: 8.1s; }
    <style>
      .video-grid {
        grid-template-columns: 1fr 1fr;
        grid-template-rows: 1fr 1fr;
        gap: 12px;
      }
      @media (max-width: 768px) {
        .video-grid {
          grid-template-columns: 1fr;
          grid-template-rows: 1fr;
        }
      }
    </style>
  </style>
</head>
<body class="bg-sus-light text-sus-primary min-h-screen flex flex-col">

  <!-- ==================== HEADER / BARRA SUPERIOR ==================== -->
  <header class="glass-dark text-white fixed top-0 left-0 right-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <!-- Logo SUS -->
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-sus-accent rounded-lg flex items-center justify-center">
          <i class="fas fa-heart text-white text-lg"></i>
        </div>
        <div>
          <h1 class="text-lg font-bold tracking-tight">MedIA</h1>
          <p class="text-xs text-sus-accent/70 uppercase tracking-wider">Sistema de Teleatendimento</p>
        </div>
      </div>

      <!-- SUS Indicators -->
      <div class="flex items-center gap-4">
        <!-- CNS -->
        <div class="indicator-card glass-card rounded-xl px-4 py-2 flex items-center gap-2">
          <span class="text-xs font-semibold text-sus-secondary uppercase tracking-wider">CNS</span>
          <span class="font-mono text-sm font-bold text-sus-primary">1234567890</span>
        </div>
        <!-- CPF -->
        <div class="indicator-card glass-card rounded-xl px-4 py-2 flex items-center gap-2">
          <span class="text-xs font-semibold text-sus-secondary uppercase tracking-wider">CPF</span>
          <span class="font-mono text-sm font-bold text-sus-primary">123.456.789-00</span>
        </div>
        <!-- Equipe APS -->
        <div class="indicator-card glass-card rounded-xl px-4 py-2 flex items-center gap-2">
          <span class="text-xs font-semibold text-sus-secondary uppercase tracking-wider">Equipe</span>
          <span class