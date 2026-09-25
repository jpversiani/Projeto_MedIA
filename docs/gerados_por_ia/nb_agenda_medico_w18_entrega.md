Corrigindo a lógica de construção da grade (células de hora com rowspan) e a altura dos cards de 30 min:
Arquivo criado: `backend/app/static/agenda_medico.html` (26 KB), verificado (estrutura HTML, sintaxe JS balanceada, todos os marcos funcionais presentes).

**Funcionalidades implementadas:**
- **Grade APS 07h–19h** — 48 slots de 15 min em tabela com rowspan nas horas cheias e linha vermelha do horário atual
- **Drag-and-drop (HTML5 DnD)** — cards arrastáveis com `dragstart`/`dragover`/`drop`, destaque visual do slot-alvo, validação de conflito de horário (respeitando durações de 15/30 min) e aviso de confirmação
- **Telemedicina** — ícone de vídeo SVG nos cards, contagem no KPI, cor/ícone distintos e acesso à sala virtual via modal
- **Absenteísmo do dia** — percentual + detalhamento (faltas/total) no painel de indicadores, com card de "Falta" riscado
- **Sala virtual** — botão de chamada direta no cabeçalho e por consulta (telemedicina)
- **Conformidade SUS/APS** — CNS nos detalhes, CID-10, referência a CIAP-2, método SOAP, legendas e ARIA em pt-BR, paleta verde SUS com Tailwind