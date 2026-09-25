```python
# Arquivo: backend/app/static/painel_triagem.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Triagem — MedIA C3</title>
    <style>
        /* ============================================
           PALETA MANCHESTER — C3
           ============================================ */
        :root {
            --m-cream:    #F8F5F0;
            --m-cream-l:  #FAF9F6;
            --m-blue:     #003366;
            --m-blue-l:   #005588;
            --m-blue-m:   #0077B3;
            --m-blue-l:   #0099D4;
            --m-teal:     #00A896;
            --m-teal-l:   #00CCBB;
            --m-teal-m:   #00D4CC;
            --m-teal-l:   #00E8D4;
            --m-green:    #007A5F;
            --m-green-l:  #00997A;
            --m-green-m:  #00BB96;
            --m-green-l:  #00CCB0;
            --m-orange:   #D47A3A;
            --m-orange-l: #E88A4A;
            --m-orange-m: #F09A5A;
            --m-orange-l: #F8A86A;
            --m-red:      #C44A3A;
            --m-red-l:    #D45A4A;
            --m-red-m:    #E46A4A;
            --m-red-l:    #E87A5A;
            --m-purple:   #5A3A8A;
            --m-purple-l: #6A4A9A;
            --m-purple-m: #7A5AB3;
            --m-purple-l: #8A6AC3;
            --m-gray:     #888888;
            --m-gray-l:   #A8A8A8;
            --m-gray-m:   #B8B8B8;
            --m-gray-l:   #C8C8C8;
            --m-gray-d:   #E8E8E8;
            --m-gray-dl:  #F0F0F0;
            --m-white:    #FFFFFF;
            --m-shadow:   0 2px 8px rgba(0,0,0,0.08);
            --m-shadow-l: 0 4px 16px rgba(0,0,0,0.12);
            --m-radius:   12px;
            --m-radius-sm: 8px;
            --m-transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--m-cream);
            color: var(--m-blue);
            min-height: 100vh;
            line-height: 1.6;
        }

        /* ============================================
           HEADER
           ============================================ */
        .c3-header {
            background: linear-gradient(135deg, var(--m-blue) 0%, var(--m-blue-m) 50%, var(--m-blue-l) 100%);
            color: var(--m-white);
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--m-shadow-l);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .c3-header__logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .c3-header__logo-icon {
            width: 40px;
            height: 40px;
            background: var(--m-teal);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: 700;
            color: var(--m-white);
        }

        .c3-header__logo-text {
            font-size: 1.3rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .c3-header__logo-text span {
            color: var(--m-teal-l);
        }

        .c3-header__info {
            display: flex;
            align-items: center;
            gap: 24px;
        }

        .c3-header__status {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.15);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .c3-header__status-dot {
            width: 10px;
            height: 10px;
            background: var(--m-green-l);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(0,170,150,0.4); }
            50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(0,170,150,0); }
        }

        .c3-header__time {
            font-size: 0.85rem;
            font-weight: 600;
            background: rgba(255,255,255,0.15);
            padding: 6px 14px;
            border-radius: 20px;
        }

        .c3-header__actions {
            display: flex;
            gap: 10px;
        }

        .c3-header__btn {
            background: var(--m-white);
            color: var(--m-blue);
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: var(--m-transition);
        }

        .c3-header__btn:hover {
            transform: translateY(-1px);
            box-shadow: var(--m-shadow);
        }

        .c3-header__btn--call {
            background: var(--m-red);
            color: var(--m-white);
        }

        .c3-header__btn--call:hover {
            background: var(--m-red-m);
        }

        /* ============================================
           MAIN LAYOUT
           ============================================ */
        .c3-main {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px 32px;
        }

        .c3-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        @media (max-width: 1024px) {
            .c3-grid {
                grid-template-columns: 1fr;
            }
        }

        /* ============================================
           CARDS
           ============================================ */
        .c3-card {
            background: var(--m-white);
            border-radius: var(--m-radius);
            box-shadow: var(--m-shadow);
            overflow: hidden;
            transition: var(--m-transition);
        }

        .c3-card:hover {
            box-shadow: var(--m-shadow-l);
            transform: translateY(-2px);
        }

        .c3-card__header {
            padding: 20px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--m-gray-d);
        }

        .c3-card__title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--m-blue);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .c3-card__title-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }

        .c3-card__title--teal { background: var(--m-teal); color: var(--m-white); }
        .c3-card__title--blue { background: var(--m-blue); color: var(--m-white); }
        .c3-card__title--green { background: var(--m-green); color: var(--m-white); }
        .c3-card__title--orange { background: var(--m-orange); color: var(--m-white); }
        .c3-card__title--red { background: var(--m-red); color: var(--m-white); }
        .c3-card__title--purple { background: var(--m-purple); color: var(--m-white); }

        .c3-card__badge {
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .c3-card__badge--active {
            background: var(--m-teal);
            color: var(--m-white);
        }

        .c3-card__badge--urgent {
            background: var(--m-red);
            color: var(--m-white);
        }

        .c3-card__badge--normal {
            background: var(--m-blue);
            color: var(--m-white);
        }

        .c3-card__badge--stable {
            background: var(--m-green);
            color: var(--m-white);
        }

        .c3-card__body {
            padding: 24px;
        }

        /* ============================================
           KPI CARDS (TOP ROW)
           ============================================ */
        .c3-kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }

        @media (max-width: 768px) {
            .c3-kpi-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        .c3-kpi-card {
            background: var(--m-white);
            border-radius: var(--m-radius);
            box-shadow: var(--m-shadow);
            padding: 20px;
            text-align: center;
            transition: var(--m-transition);
        }

        .c3-kpi-card:hover {
            box-shadow: var(--m-shadow-l);
            transform: translateY(-2px);
        }

        .c3-kpi-card__icon {
            width: 56px;
            height: 56px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 12px;
            font-size: 24px;
        }

        .c3-kpi-card__icon--teal { background: var(--m-teal); color: var(--m-white); }
        .c3-kpi-card__icon--blue { background: var(--m-blue); color: var(--m-white); }
        .c3-kpi-card__icon--green { background: var(--m-green); color: var(--m-white); }
        .c3-kpi-card__icon--orange { background: var(--m-orange); color: var(--m-white); }

        .c3-kpi-card__value {
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1;
            margin-bottom: 4px;
        }

        .c3-kpi-card__label {
            font-size: 0.8rem;
            color: var(--m-gray);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .c3-kpi-card__value--teal { color: var(--m-teal); }
        .c3-kpi-card__value--blue { color: var(--m-blue); }
        .c3-kpi-card__value--green { color: var(--m-green); }
        .c3-kpi-card__value--orange { color: var(--m-orange); }

        /* ============================================
           TRIAGE CARDS
           ============================================ */
        .c3-triage-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }

        @media (max-width: 768px) {
            .c3-triage-grid {
                grid-template-columns: 1fr;
            }
        }

        .c3-triage-card {
            background: var(--m-white);
            border-radius: var(--m-radius);
            box-shadow: var(--m-shadow);
            overflow: hidden;
            transition: var(--m-transition);
        }

        .c3-triage-card:hover {
            box-shadow: var(--m-shadow-l);
            transform: translateY(-2px);
        }

        .c3-triage-card__header {
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--m-gray-d);
        }

        .c3-triage-card__title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--m-blue);
            display: flex;
            align-items: center;
            gap: 1