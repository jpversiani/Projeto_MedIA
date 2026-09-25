```html:backend/app/static/telemedicina_sala.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sala de Teleconsulta - MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            overflow: hidden;
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #1e293b;
        }
        ::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
            50% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
        }

        .animate-fade-in {
            animation: fadeIn 0.5s ease-out forwards;
        }

        .animate-slide-left {
            animation: slideInLeft 0.5s ease-out forwards;
        }

        .animate-slide-right {
            animation: slideInRight 0.5s ease-out forwards;
        }

        .pulse-glow {
            animation: pulse-glow 2s infinite;
        }

        /* Custom cursor for video controls */
        .video-container {
            cursor: default;
        }

        .video-container:hover {
            cursor: pointer;
        }

        /* Custom scrollbar for chat */
        .chat-scroll {
            overflow-y: auto;
            max-height: 100%;
        }

        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .chat-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        .chat-scroll::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Custom scrollbar for chat */
        .chat-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .chat-scroll::-webkit-scrollbar-track {
            background: