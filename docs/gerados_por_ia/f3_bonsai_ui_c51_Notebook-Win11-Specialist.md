```python
# Arquivo: backend/app/static/painel_triagem.html
"""
Painel Visual de Triagem e Monitor de Fila APS (C51)
Projeto MedIA - Sistema de Monitoramento de Fila de Atender
Conformidade: SUS / APS (CIAP-2, CID-10, SOAP, CNS/CPF)
"""

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Triagem C51 - Sistema MedIA</title>
    <style>
        /* ============================================
           CSS CUSTOM PROPERTIES - PALETA MANCHESTER
           ============================================ */
        :root {
            --color-manchester-blue: #003366;
            --color-manchester-dark: #0a1628;
            --color-manchester-red: #c0392b;
            --color-manchester-orange: #e67e22;
            --color-manchester-green: #27ae60;
            --color-manchester-yellow: #f1c40f;
            --color-manchester-white: #ffffff;
            --color-manchester-gray: #7f8c8d;
            --color-manchester-light: #ecf0f1;
            --color-manchester-accent: #1abc9c;
            --radius: 12px;
            --shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            --shadow-hover: 0 8px 30px rgba(0, 0, 0, 0.25);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* ============================================
           RESET & BASE STYLES
           ============================================ */
        *, *::before, *::after {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--color-manchester-dark);
            color: var(--color-manchester-white);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* ============================================
           HEADER / BARRA DE NAVEGAÇÃO
           ============================================ */
        .header {
            background: linear-gradient(135deg, var(--color-manchester-blue), var(--color-manchester-dark));
            padding: 15px 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            position: sticky;
            top: 0;
            z-index: 1000;
            border-bottom: 3px solid var(--color-manchester-red);
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-brand-icon {
            width: 42px;
            height: 42px;
            background: linear-gradient(135deg, var(--color-manchester-red), var(--color-manchester-orange));
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            font-weight: 800;
            color: white;
            box-shadow: 0 2px 10px rgba(192, 57, 43, 0.4);
        }

        .header-brand-text h1 {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 0.5px;
        }

        .header-brand-text h1 span {
            color: var(--color-manchester-red);
        }

        .header-brand-text p {
            font-size: 11px;
            color: var(--color-manchester-gray);
            margin-top: 2px;
            letter-spacing: 0.3px;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-actions button {
            background: var(--color-manchester-red);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: var(--transition);
        }

        .header-actions button:hover {
            background: #a93226;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(192, 57, 43, 0.4);
        }

        .header-actions button.active {
            background: var(--color-manchester-green);
        }

        .header-actions button.active:hover {
            background: #219a52;
        }

        .header-actions .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--color-manchester-green);
            animation: pulse 2s infinite;
        }

        .header-actions .status-dot.off {
            background: var(--color-manchester-red);
            animation: pulse-off 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(39, 174, 96, 0.7); }
            50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(39, 174, 96, 0); }
        }

        @keyframes pulse-off {
            0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(192, 57, 43, 0.7); }
            50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(192, 57, 43, 0); }
        }

        /* ============================================
           MAIN CONTENT AREA
           ============================================ */
        .main-content {
            padding: 25px 30px;
            max-width: 1400px;
            margin: 0 auto;
        }

        /* ============================================
           BARRA DE METRIKAS (TOP BAR)
           ============================================ */
        .metrics-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }

        .metric-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: var(--radius);
            padding: 18px 20px;
            transition: var(--transition);
            backdrop-filter: blur(10px);
        }

        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-hover);
            border-color: rgba(255, 255, 255, 0.15);
        }

        .metric-card .metric-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }

        .metric-card .metric-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--color-manchester-gray);
            font-weight: 600;
        }

        .metric-card .metric-value {
            font-size: 28px;
            font-weight: 800;
            font-variant-numeric: tabular-nums;
        }

        .metric-card .metric-sub {
            font-size: 12px;
            color: var(--color-manchester-gray);
        }

        .metric-card .metric-change {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            margin-top: 6px;
        }

        .metric-card .metric-change.up {
            color: var(--color-manchester-green);
            background: rgba(39, 174, 96, 0.15);
        }

        .metric-card .metric-change.down {
            color: var(--color-manchester-red);
            background: rgba(192, 57, 43, 0.15);
        }

        /* ============================================
           CARDS DE METRIKAS - COLORED (MANCHESTER)
           ============================================ */
        .metric-card.blue {
            border-left: 4px solid var(--color-manchester-blue);
        }
        .metric-card.blue .metric-value { color: var(--color-manchester-blue); }

        .metric-card.red {
            border-left: 4px solid var(--color-manchester-red);
        }
        .metric-card.red .metric-value { color: var(--color-manchester-red); }

        .metric-card.green {
            border-left: 4px solid var(--color-manchester-green);
        }
        .metric-card.green .metric-value { color: var(--color-manchester-green); }

        .metric-card.orange {
            border-left: 4px solid var(--color-manchester-orange);
        }
        .metric-card.orange .metric-value { color: var(--color-manchester-orange); }

        .metric-card.yellow {
            border-left: 4px solid var(--color-manchester-yellow);
        }
        .metric-card.yellow .metric-value { color: var(--color-manchester-yellow); }

        /* ============================================
           SEÇÃO PRÓXIMO PACIENTE (SOLDA SONORA)
           ============================================ */
        .next-patient-section {
            background: linear-gradient(135deg, rgba(192, 57, 43, 0.15), rgba(230, 126, 34, 0.1));
            border: 1px solid rgba(192, 57, 43, 0.3);
            border-radius: var(--radius);
            padding: 25px 30px;
            margin-bottom: 25px;
            position: relative;
            overflow: hidden;
        }

        .next-patient-section::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(192, 57, 43, 0.1), transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        }

        .next-patient-section::after {
            content: '';
            position: absolute;
            bottom: -50%;
            left: -50%;
            width: 150px;
            height: 150px;
            background: radial-gradient(circle, rgba(230, 126, 34, 0.1), transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        }

        .next-patient-section h2 {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            position: relative;
            z-index: 1;
        }

        .next-patient-section h2 .bell-icon {
            font-size: 20px;
        }

        .next-patient-card {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            position: relative;
            z-index: 1;
        }

        .next-patient-info {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: var(--radius);
            padding: 20px;
        }

        .next-patient-info .patient-id {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--color-manchester-gray);
            font-weight: 600;
            margin-bottom: 4px;
        }

        .next-patient-info .patient-name {
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .next-patient-info .patient-cpf {
            font-size: 13px;
            color: var(--color-manchester-gray);
            margin-bottom: 8px;
        }

        .next-patient-info .patient-cpf::before {
            content: 'CPF: ';
            color: var(--color-manchester-orange);
            font-weight: 600;
        }

        .next-patient-info .patient-cns {
            font-size: 13px;
            color: var(--color-manchester-gray);
            margin-bottom: 8px;
        }

        .next-patient-info .patient-cns::before {
            content: 'CNS: ';
            color: var(--color-manchester-yellow);
            font-weight: 600;
        }

        .next-patient-info .patient-ciap {
            font-size: 12px;
            color: var(--color-manchester-gray);
            margin-bottom: 8px;
        }

        .next-patient-info .patient-ciap::before {
            content: 'CIAP-2: ';
            color: var(--color-manchester-accent);
            font-weight: 600;
        }

        .next-patient-info .patient-cid10 {
            font-size: 12px;
            color: var(--color-manchester-gray);
        }

        .next-patient-info .patient-cid10::before {
            content: 'CID-10: ';
            color: var(--color-manchester-green);
            font-weight: 600;
        }

        .next-patient-info .patient-soap {
            font-size: 12px;
            color: var(--color-manchester-gray);
            margin-top: 4px;
        }

        .next-patient-info .patient-soap::before {
            content: 'SOAP: ';
            color: var(--color-manchester-red);
