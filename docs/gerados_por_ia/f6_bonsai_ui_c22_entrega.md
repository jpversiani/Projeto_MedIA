```python:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card do Copiloto - Prontuário Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Inter+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f0f2f5;
        }
        .mono {
            font-family: 'Inter Mono', monospace;
        }
        .card-hypothesis {
            transition: all 0.3s ease;
        }
        .card-hypothesis:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        }
        .drug-interaction {
            transition: all 0.3s ease;
        }
        .drug-interaction:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        }
        .status-badge {
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            font-weight: 600;
        }
        .badge-critical {
            background-color: #fee2e2;
            color: #991b1b;
        }
        .badge-warning {
            background-color: #fef3c7;
            color: #92400e;
        }
        .badge-info {
            background-color: #dbeafe;
            color: #1e40af;
        }
        .badge-safe {
            background-color: #d1fae5;
            color: #065f46;
        }
        .cns-code {
            font-family: 'Inter Mono', monospace;
            color: #6b7280;
            font-size: 0.875rem;
        }
        .soap-section {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e5e7eb;
        }
        .ai-confidence {
            width: 100%;
            height: 6px;
            background-color: #e5e7eb;
            border-radius: 9999px;
            overflow: hidden;
        }
        .ai-confidence-bar {
            height: 100%;
            border-radius: 9999px;
            transition: width 0.5s ease;
        }
        .ai-confidence-bar.high {
            background-color: #10b981;
        }
        .ai-confidence-bar.medium {
            background-color: #f59e0b;
        }
        .ai-confidence-bar.low {
            background-color: #ef4444;
        }
        .diagnostic-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        .diagnostic-icon.critical {
            background-color: #fee2e2;
            color: #ef4444;
        }
        .diagnostic-icon.warning {
            background-color: #fef3c7;
            color: #f59e0b;
        }
        .diagnostic-icon.info {
            background-color: #dbeafe;
            color: #1e40af;
        }
        .diagnostic-icon.safe {
            background-color: #d1fae5;
            color: #065f46;
        }
        .patient-info {
            background: linear-gradient(135deg, #1e3a8a 0%, #2d52a7 100%);
            color: white;
        }
        .patient-info .cns-code {
            color: #93c5fd;
        }
        .patient-info .cpf-code {
            color: #93c5fd;
        }
        .soap-text {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
        }
        .soap-text h4 {
            font-size: 0.875rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .soap-text p {
            font-size: 0.875rem;
            color: #6b7280;
            line-height: 1.6;
        }
        .ai-disclaimer {
            background: #fef3c7;
            border: 1px solid #fde047;
            color: #92400e;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-size: 0.875rem;
            margin-top: 1rem;
        }
        .ai-disclaimer strong {
            color: #78350f;
        }
        .ai-disclaimer span {
            color: #92400e;
        }
        .ai-disclaimer ul {
            margin-top: 0.5rem;
            padding-left: 1.25rem;
        }
        .ai-disclaimer li {
            margin-bottom: 0.25rem;
        }
        .ai-disclaimer li::before {
            content: "• ";
        }
        .ai-disclaimer li span {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(2) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(3) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(4) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(5) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(6) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(7) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(8) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(9) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(10) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(11) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(12) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(13) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(14) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(15) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(16) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(17) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(18) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(19) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(20) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(21) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(22) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(23) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(24) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(25) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(26) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(27) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(28) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(29) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(30) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(31) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(32) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(33) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(34) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(35) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(36) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(37) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(38) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(39) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(40) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(41) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(42) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(43) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(44) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(45) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(46) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(47) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(48) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(49) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(50) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(51) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(52) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(53) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(54) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(55) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(56) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(57) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(58) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(59) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(60) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(61) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(62) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(63) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(64) {
            color: #92400e;
        }
        .ai-disclaimer li span:nth-child(65) {
            color: #78350f;
        }
        .ai-disclaimer li span:nth-child(66) {
            color: #92400e;
        }