```html:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="min-h-screen">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia UBS — Consulta e Baixa de Prescrição</title>

    <!-- Tailwind CSS via CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        sus: {
                            blue: '#003366',
                            light: '#e0f0ff',
                            accent: '#007acc',
                            warning: '#f59e0b',
                            danger: '#dc2626',
                            success: '#16a34a',
                            gray: '#6b7280'
                        }
                    },
                    fontFamily: {
                        sans: ['Inter', 'Segoe UI', 'Arial', 'sans-serif'],
                        mono: ['Courier New', 'monospace'],
                    },
                    animation: {
                        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        'slide-in': 'slideIn 0.3s ease-out forwards',
                        'fade-in': 'fadeIn 0.3s ease-out forwards',
                    },
                    keyframes: {
                        slideIn: {
                            '0%': { transform: 'translateY(20px)', opacity: '0' },
                            '100%': { transform: 'translateY(0)', opacity: '1' },
                        },
                        fadeIn: {
                            '0%': { opacity: '0' },
                            '100%': { opacity: '1' },
                        }
                    }
                }
            }
        }
    </script>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

    <style>
        /* Custom scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #007acc; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #005588; }

        /* Barcode scanner overlay */
        #barcode-scan-area {
            position: relative;
            overflow: hidden;
        }

        /* Scan line animation */
        .scan-line {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, transparent, #007acc, transparent);
            animation: scanLine 2s linear infinite;
            pointer-events: none;
        }

        @keyframes scanLine {
            0% { top: -100%; }
            100% { top: 100%; }
        }

        /* Barcode grid overlay */
        .barcode-grid {
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(rgba(0, 122, 204, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 122, 204, 0.05) 1px, transparent 1px);
            background-size: 20px 20px;
            pointer-events: none;
        }

        /* Prescription card */
        .prescription-card {
            transition: all 0.3s ease;
        }
        .prescription-card:hover {
            box-shadow: 0 10px 40px rgba(0, 122, 204, 0.15);
        }

        /* Status badges */
        .badge-sus {
            background: linear-gradient(135deg, #003366, #007acc);
            color: white;
            font-weight: 600;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .badge-cip {
            background: linear-gradient(135deg, #16a34a, #059669);
            color: white;
            font-weight: 600;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .badge-cip-expiry {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            font-weight: 600;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .badge-cip-expired {
            background: linear-gradient(135deg, #dc2626, #b91c1c);
            color: white;
            font-weight: 600;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        /* Prescription status */
        .status-prescription {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.375rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }

        .status-prescription-ativa {
            background: #dcfce7;
            color: #166534;
        }
        .status-prescription-expira {
            background: #fef3c7;
            color: #92400e;
        }
        .status-prescription-expirada {
            background: #fee2e2;
            color: #991b1b;
        }
        .status-prescription-rejeitada {
            background: #fef2f2;
            color: #991b1b;
        }

        /* Prescription form */
        .prescription-form {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        /* Prescription item */
        .prescription-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-bottom: 1px solid #f1f5f9;
            transition: background 0.2s;
        }
        .prescription-item:last-child { border-bottom: none; }
        .prescription-item:hover { background: #f8fafc; }

        /* Quantity input */
        .qty-input {
            width: 60px;
            text-align: center;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 0.875rem;
            font-weight: 600;
            text-align: center;
            background: white;
        }

        /* Prescription summary */
        .prescription-summary {
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
        }

        /* Alert messages */
        .alert {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        .alert-info { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
        .alert-warning { background: #fef3c7; color: #92400e; border: 1px solid #fde047; }
        .alert-danger { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .alert-success { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }

        /* Prescription hash input */
        .hash-input-wrapper {
            position: relative;
        }
        .hash-input-wrapper i {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #9ca3af;
        }

        /* Prescription detail modal */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 50;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        .modal-overlay.active {
            opacity: 1;
            visibility: visible;
        }
        .modal-content {
            background: white;
            border-radius: 16px;
            max-width: 600px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            transform: scale(0.9);
            transition: transform 0.3s ease;
        }
        .modal-overlay.active .modal-content {
            transform: scale(1);
        }

        /* Prescription table */
        .prescription-table {
            width: 100%;
            border-collapse: collapse;
        }
        .prescription-table th {
            background: #f8fafc;
            font-weight: 600;
            color: #374151;
            text-align: left;
            padding: 12px 16px;
            border-bottom: 2px solid #e5e7eb;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .prescription-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #f1f5f9;
            font-size: 0.875rem;
        }
        .prescription-table tr:hover td {
            background: #f8fafc;
        }

        /* Prescription history */
        .history-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: 8px;
            transition: background 0.2s;
        }
        .history-item:hover { background: #f8fafc; }
        .history-item.completed { opacity: 0.7; }
        .history-item.completed .status-icon { color: #9ca3af; }

        /* Prescription status indicator */
        .status-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            flex-shrink: 0;
        }
        .status-icon-ativa { background: #dcfce7; color: #166534; }
        .status-icon-expira { background: #fef3c7; color: #92400e; }
        .status-icon-expirada { background: #fee2e2; color: #991b1b; }
        .status-icon-rejeitada { background: #fef2f2; color: #991b1b; }
        .status-icon-baixa { background: #dbeafe; color: #1e40af; }

        /* Prescription details */
        .detail-section {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .detail-section h3 {
            font-size: 0.875rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .detail-section h3 i { color: #007acc; }

        /* Prescription table */
        .prescription-table {
            width: 100%;
            border-collapse: collapse;
        }
        .prescription-table th {
            background: #f8fafc;
            font-weight: 600;
            color: #374151;
            text-align: left;
            padding: 12px 16px;
            border-bottom: 2px solid #e5e7eb;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .prescription-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #f1f5f9;
            font-size: 0.875rem;
        }
        .prescription-table tr:hover td {
            background: #f8fafc;
        }

        /* Prescription summary */
        .prescription-summary {
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            border: 1px solid #e5e7eb;
            border-radius: 1