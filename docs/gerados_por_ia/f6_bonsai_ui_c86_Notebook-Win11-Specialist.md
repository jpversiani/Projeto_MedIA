```html:backend/app/static/copiloto_card.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card Copiloto - Prontuário Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #f0f4f8; }
        .card-glow { box-shadow: 0 4px 24px rgba(0,0,0,0.08); }
        .hypothesis-card { transition: transform 0.2s ease, box-shadow 0.2s ease; }
        .hypothesis-card:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.12); }
        .interaction-badge { border-radius: 9999px; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
        .status-dot.high { background: #ef4444; box-shadow: 0 0 6px #ef4444; }
        .status-dot.medium { background: #f59e0b; box-shadow: 0 0 6px #f59e0b; }
        .status-dot.low { background: #10b981; box-shadow: 0 0 6px #10b981; }
        .status-dot.info { background: #3b82f6; box-shadow: 0 0 6px #3b82f6; }
        .patient-badge { background: linear-gradient(135deg, #1e293b 0%, #334155 100%); }
        .diagnosis-bar { height: 4px; border-radius: 2px; background: #e2e8f0; }
        .diagnosis-bar.fill { border-radius: 2px; }
        .diagnosis-bar.high { background: #ef4444; }
        .diagnosis-bar.medium { background: #f59e0b; }
        .diagnosis-bar.low { background: #10b981; }
        .diagnosis-bar.info { background: #3b82f6; }
        .tab-btn { transition: all 0.2s ease; }
        .tab-btn.active { background: #1e293b; color: white; }
        .tab-btn:not(.active) { background: #f1f5f9; color: #334155; }
        .tab-btn:hover:not(.active) { background: #e2e8f0; }
        .tab-content { display: none; animation: fadeIn 0.3s ease; }
        .tab-content.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        .confidence-ring { position: relative; width: 48px; height: 48px; }
        .confidence-ring svg { transform: rotate(-90deg); }
        .confidence-ring .bg { fill: none; stroke: #e2e8f0; stroke-width: 4; }
        .confidence-ring .progress { fill: none; stroke-width: 4; stroke-linecap: round; transition: stroke-dashoffset 0.5s ease; }
        .patient-card { background: #ffffff; border-radius: 16px; padding: 24px; }
        .section-title { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; }
        .medication-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 500; }
        .med-pill-red { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .med-pill-yellow { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-green { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .med-pill-blue { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
        .med-pill-purple { background: #ede9fe; color: #7c3aed; border: 1px solid #e0e7ff; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-cyan { background: #cffafe; color: #0891b2; border: 1px solid #a5f3fc; }
        .med-pill-pink { background: #fce7f3; color: #9c27b0; border: 1px solid #fbcfe8; }
        .med-pill-gray { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
        .med-pill-navy { background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }
        .med-pill-brown { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-teal { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
        .med-pill-rose { background: #fce7f3; color: #9c27b0; border: 1px solid #fbcfe8; }
        .med-pill-sky { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
        .med-pill-emerald { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .med-pill-amber { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-indigo { background: #ede9fe; color: #7c3aed; border: 1px solid #e0e7ff; }
        .med-pill-violet { background: #fce7f3; color: #9c27b0; border: 1px solid #fbcfe8; }
        .med-pill-slate { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
        .med-pill-stone { background: #e2e8f0; color: #334155; border: 1px solid #cbd5e1; }
        .med-pill-rose { background: #fce7f3; color: #9c27b0; border: 1px solid #fbcfe8; }
        .med-pill-cyan { background: #cffafe; color: #0891b2; border: 1px solid #a5f3fc; }
        .med-pill-pink { background: #fce7f3; color: #9c27b0; border: 1px solid #fbcfe8; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-red { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .med-pill-yellow { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-green { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .med-pill-blue { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
        .med-pill-purple { background: #ede9fe; color: #7c3aed; border: 1px solid #e0e7ff; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-cyan { background: #cffafe; color: #0891b2; border: 1px solid #a5f3fc; }
        .med-pill-pink { background: #fce7f3; color: #9c27b0; border: 1px solid #fbcfe8; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-red { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .med-pill-yellow { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-green { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .med-pill-blue { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
        .med-pill-purple { background: #ede9fe; color: #7c3aed; border: 1px solid #e0e7ff; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-cyan { background: #cffafe; color: #0891b2; border: 1px solid #a5f3fc; }
        .med-pill-pink { background: #fce7f3; color: #9c27b0; border: 1px solid #fbcfe8; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-red { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .med-pill-yellow { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-green { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .med-pill-blue { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
        .med-pill-purple { background: #ede9fe; color: #7c3aed; border: 1px solid #e0e7ff; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-cyan { background: #cffafe; color: #0891b2; border: 1px solid #a5f3fc; }
        .med-pill-pink { background: #fce7f3; color: #9c27b0; border: 1px solid #fbcfe8; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-red { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .med-pill-yellow { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-green { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .med-pill-blue { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
        .med-pill-purple { background: #ede9fe; color: #7c3aed; border: 1px solid #e0e7ff; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-cyan { background: #cffafe; color: #0891b2; border: 1px solid #a5f3fc; }
        .med-pill-pink { background: #fce7f3; color: #9c27b0; border: 1px solid #fbcfe8; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-red { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .med-pill-yellow { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-green { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .med-pill-blue { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
        .med-pill-purple { background: #ede9fe; color: #7c3aed; border: 1px solid #e0e7ff; }
        .med-pill-orange { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .med-pill-cyan { background: #cffafe; color: #0891b2; border: 1px solid #a5f