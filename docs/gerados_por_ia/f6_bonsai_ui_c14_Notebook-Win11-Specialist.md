# Card Dinâmico do Copiloto no Prontuário Web (C14)

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── schemas.py
│   ├── api.py
│   ├── static/
│   │   └── copiloto_card.html
│   └── config.py
├── tests/
│   ├── __init__.py
│   └── test_api.py
└── requirements.txt
```

---

## Arquivo: `backend/app/static/copiloto_card.html`

```html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card Copiloto — Prontuário Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }

        /* ── Card Base ── */
        .copiloto-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 20px;
            box-shadow: 0 25px 60px -12px rgba(0,0,0,0.5);
        }

        /* ── Gradient Accent ── */
        .accent-gradient {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        }

        .accent-gradient-light {
            background: linear-gradient(135deg, #60a5fa 0%, #c084fc 50%, #f472b6 100%);
        }

        /* ── Card Header ── */
        .card-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }

        /* ── Hypothesis Card ── */
        .hypothesis-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .hypothesis-card:hover {
            background: rgba(255,255,255,0.07);
            border-color: rgba(255,255,255,0.12);
            transform: translateY(-2px);
        }

        /* ── Interaction Card ── */
        .interaction-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            transition: all 0.3s ease;
        }
        .interaction-card:hover {
            background: rgba(255,255,255,0.07);
            border-color: rgba(255,255,255,0.12);
            transform: translateY(-2px);
        }

        /* ── Confidence Badge ── */
        .confidence-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }

        .confidence-high {
            background: rgba(16,185,129,0.15);
            color: #34d399;
            border: 1px solid rgba(34,211,149,0.25);
        }

        .confidence-medium {
            background: rgba(245,158,11,0.15);
            color: #fbbf24;
            border: 1px solid rgba(251,191,36,0.25);
        }

        .confidence-low {
            background: rgba(248,113,113,0.15);
            color: #f87171;
            border: 1px solid rgba(248,113,113,0.25);
        }

        /* ── Risk Level ── */
        .risk-high {
            background: rgba(248,113,113,0.15);
            color: #f87171;
            border: 1px solid rgba(248,113,113,0.25);
        }
        .risk-medium {
            background: rgba(245,158,11,0.15);
            color: #fbbf24;
            border: 1px solid rgba(251,191,36,0.25);
        }
        .risk-low {
            background: rgba(16,185,129,0.15);
            color: #34d399;
            border: 1px solid rgba(34,211,149,0.25);
        }

        /* ── Pulse Animation ── */
        @keyframes pulse-ring {
            0% { box-shadow: 0 0 0 0 rgba(59,130,246,0.4); }
            70% { box-shadow: 0 0 0 10px rgba(59,130,246,0); }
            100% { box-shadow: 0 0 0 0 rgba(59,130,246,0); }
        }

        .pulse-ring::before {
            content: '';
            position: absolute;
            inset: -4px;
            border-radius: inherit;
            background: conic-gradient(from 0deg, transparent 0deg, rgba(59,130,246,0.3) 30deg, transparent 30deg);
            animation: pulse-ring 2s linear infinite;
            z-index: -1;
        }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.25); }

        /* ── Toggle ── */
        .toggle-switch {
            position: relative;
            width: 44px;
            height: 24px;
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .toggle-switch.active { background: rgba(59,130,246,0.4); }
        .toggle-switch::after {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 18px;
            height: 18px;
            background: white;
            border-radius: 50%;
            transition: transform 0.3s;
        }
        .toggle-switch.active::after { transform: translateX(20px); }

        /* ── Tooltip ── */
        .tooltip-trigger {
            position: relative;
        }
        .tooltip-trigger::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%) translateY(8px);
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.7rem;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s;
            z-index: 10;
        }
        .tooltip-trigger:hover::after { opacity: 1; }

        /* ── Card Number ── */
        .card-number {
            font-variant-numeric: tabular-nums;
        }

        /* ── Responsive ── */
        @media (max-width: 640px) {
            .copiloto-card { border-radius: 16px; }
            .hypothesis-card, .interaction-card { border-radius: 12px; }
        }
    </style>
</head>
<body class="bg-slate-900 min-h-screen flex items-center justify-center p-4">

    <!-- ═══════════════════════════════════════════════════════ -->
    <!--  HEADER / HEADER BAR                                 -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <div class="copiloto-card w-full max-w-4xl">

        <!-- Header -->
        <div class="card-header px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl accent-gradient flex items-center justify-center text-white font-bold text-lg">
                    <i class="fas fa-brain"></i>
                </div>
                <div>
                    <h1 class="text-lg font-bold text-white">Card Copiloto</h1>
                    <p class="text-xs text-slate-400">Prontuário Web — IA Assistida</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                    <span class="text-xs font-medium text-slate-300">Sistema Ativo</span>
                </div>
                <button class="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center text-slate-400 hover:bg-white/10 transition">
                    <i class="fas fa-share-alt text-sm"></i>
                </button>
            </div>
        </div>

        <!-- Patient Info Bar -->
        <div class="px-6 py-3 bg-white/5 border-b border-white/5">
            <div class="flex items-center gap-4">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                        <i class="fas fa-user"></i>
                    </div>
                    <div>
                        <div class="text-xs font-medium text-white">
                            <span id="patientName">—</span>
                        </div>
                        <div class="text-[10px] text-slate-500">CNPJ: <span id="patientCNPJ">—</span></div>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-[10px] text-slate-500">CNS</span>
                    <span class="text-xs font-medium text-slate-300" id="patientCNS">—</span>
                </div>
                <div class="ml-auto">
                    <span class="text-[10px] text-slate-500">Data:</span>
                    <span class="text-xs font-medium text-slate-300" id="patientDate">—</span>
                </div>
            </div>
        </div>

        <!-- ═══════════════════════════════════════════════════ -->
        <!--  DIAGNOSTIC HYPOTHESES                              -->
        <!-- ═══════════════════════════════════════════════════ -->
        <div class="px-6 py-4">
            <div class="flex items-center justify-between mb-3">
                <h2 class="text-sm font-semibold text-white flex items-center gap-2">
                    <i class="fas fa-microscope text-blue-400"></i>
                    Hipóteses Diagnósticas
                </h2>
                <span class="text-[10px] text-slate-500" id="hypothesisCount">0</span>
            </div>

            <!-- Hypothesis 1 -->
            <div class="hypothesis-card mb-3" data-hypothesis="1">
                <div class="flex items-center gap-3 px-4 py-3">
                    <div class="w-10 h-10 rounded-lg bg-blue-500/15 flex items-center justify-center text-blue-400">
                        <i class="fas fa-lungs"></i>
                    </div>
                    <div class="flex-1">
                        <div class="flex items-center gap-2">
                            <span class="card-number text-[10px] font-bold text-blue-400">H-01</span>
                            <h3 class="text-sm font-medium text-white">Pneumonia Comunitária (PCN)</h3>
                        </div>
                        <p class="text-xs text-slate-400 mt-1">
                            Sintomas: febre ≥38°C, tosse cavitária, respiração rápida,
                            ausência de sintonia pulmonar.
                        </p>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="confidence-badge confidence-high">
                            <i class="fas fa-check-circle text-[10px]"></i>
                            87%
                        </span>
                        <button class