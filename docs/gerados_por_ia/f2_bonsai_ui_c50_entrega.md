```html:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="min-h-screen bg-gray-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia UBS - Consulta Prescrição Digital</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        .scan-container {
            position: relative;
            overflow: hidden;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            background: #ffffff;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .scan-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.9) 100%);
            pointer-events: none;
        }
        .scan-container::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.9) 100%);
            pointer-events: none;
        }
        .scan-container .scan-content {
            position: relative;
            z-index: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 300px;
            padding: 20px;
        }
        .scan-content .scan-label {
            color: #6b7280;
            font-size: 0.875rem;
            margin-bottom: 15px;
            font-weight: 500;
        }
        .scan-content .scan-placeholder {
            color: #9ca3af;
            font-size: 1.125rem;
            font-weight: 500;
            text-align: center;
            padding: 20px;
            border: 2px dashed #e5e7eb;
            border-radius: 8px;
            min-height: 150px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .scan-content .scan-placeholder .scan-icon {
            font-size: 3rem;
            margin-bottom: 10px;
        }
        .scan-content .scan-placeholder .scan-text {
            font-size: 0.875rem;
            color: #9ca3af;
        }
        .scan-content .scan-placeholder .scan-text span {
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint {
            font-size: 0.75rem;
            color: #9ca3af;
            margin-top: 5px;
        }
        .scan-content .scan-placeholder .scan-text .hint span {
            color: #6b7280;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #6b7280;
            font-weight: 600;
        }
        .scan-content .scan-placeholder .scan-text .hint .key {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;