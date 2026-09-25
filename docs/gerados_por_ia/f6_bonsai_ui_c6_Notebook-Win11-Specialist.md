```python
# Arquivo: backend/app/static/copiloto_card.html
"""
Card Dinâmico do Copiloto - Interface Web Prontuário
Projeto MedIA - Sistema de Assistência Clínica Inteligente
Padrões: SUS/APS, CIAP-2, CID-10, Método SOAP, Identificação por CNS/CPF
"""

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card Copiloto - Prontuário Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f0f1f5;
        }
        .card-header {
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 16px 16px 0 0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .card-body {
            background: white;
            border-radius: 0 0 16px 16px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            padding: 2rem;
        }
        .diagnostic-hypothesis {
            background: #f8fafc;
            border-left: 4px solid #3b82f6;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            padding: 1.25rem;
            transition: all 0.3s ease;
        }
        .diagnostic-hypothesis:hover {
            background: #eff6ff;
            transform: translateX(4px);
        }
        .drug-interaction {
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            padding: 1.25rem;
        }
        .drug-interaction.warning {
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
        }
        .drug-interaction.critical {
            background: #fee2e2;
            border-left: 4px solid #dc2626;
        }
        .patient-info {
            background: #f1f5f9;
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.5rem;
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
        }
        .patient-info .info-item {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        .patient-info .info-label {
            font-size: 0.75rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }
        .patient-info .info-value {
            font-weight: 600;
            color: #1e293b;
        }
        .soap-section {
            background: #f8fafc;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .soap-section h3 {
            font-size: 0.875rem;
            color: #334155;
            margin-bottom: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .soap-section p {
            color: #475569;
            line-height: 1.6;
            font-size: 0.9375rem;
        }
        .diagnostic-hypothesis .hypothesis-number {
            font-size: 0.75rem;
            color: #3b82f6;
            font-weight: 700;
            margin-right: 0.5rem;
        }
        .diagnostic-hypothesis .hypothesis-title {
            font-size: 1.125rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
        }
        .diagnostic-hypothesis .hypothesis-description {
            color: #475569;
            font-size: 0.9375rem;
            line-height: 1.6;
        }
        .diagnostic-hypothesis .hypothesis-evidence {
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px solid #e2e8f0;
            font-size: 0.8125rem;
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence strong {
            color: #1e293b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .code {
            background: #e0e7ff;
            color: #1e3a8a;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability {
            color: #10b981;
            font-weight: 600;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.low {
            color: #f59e0b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.medium {
            color: #3b82f6;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.high {
            color: #10b981;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #059669;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-low {
            color: #dc2626;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-medium {
            color: #64748b;
        }
        .diagnostic-hypothesis .hypothesis-evidence .probability.very-high {
            color: #05966