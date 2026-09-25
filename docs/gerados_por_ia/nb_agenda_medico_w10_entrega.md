O sandbox está vazio, então vou criar a estrutura e o arquivo alvo. Vou montar a agenda com grade de 15 min (07h–19h), drag-and-drop HTML5 nativo, destaque de telemedicina, contador de absenteísmo e chamada à sala virtual, com fallback para dados de demonstração quando o backend não responder.
Node indisponível para checagem sintática — vou revisar o módulo manualmente ao final. Criando o arquivo:
Agora vou corrigir alguns problemas estruturais que identifiquei na revisão: a camada de cartões precisa ficar dentro da área rolável da grade, a detecção da pausa de almoço usava índice em vez de hora, e os eventos de drop devem cobrir também a área sobre os cartões.
Agora as correções no módulo JavaScript:
Agora a lógica de arrastar/soltar — eventos na grade inteira (para funcionar também sobre os cartões) e guarda de posição X:
Vou reler o arquivo completo para revisão final de sintaxe e coerência:
Revisão completa. Vou fazer três ajustes finais: documentar o contrato do GET no comentário da API, neutralizar mensagens quanto ao gênero e carregar a fonte Inter referenciada no config do Tailwind:
Verificação final — procurando um interpretador JS disponível para validar a sintaxe do módulo:
Sem motor JS disponível — vou fazer uma checagem estrutural heurística em Python (balanceamento de chaves, parênteses, colchetes e crases no módulo):
O verificador tem falha própria: o regex de comentários apagou `https://` dentro de template literals. Vou corrigir o script para tratar comentários apenas fora de strings:
O verificador precisa rastrear templates aninhados corretamente. Reescrevendo com pilha de contextos:
Sintaxe do módulo validada. Verificando se há navegador headless para um teste visual:
Sem navegador no ambiente. Última checagem — garantir que não restaram textos de interface em inglês:
Concluído. `backend/app/static/agenda_medico.html` (923 linhas) criado e validado.

**Entregas conforme solicitado:**
- **Grade da APS**: 07h–19h em slots de 15 min (48 posições), rótulos de hora, faixa de pausa (12h–13h) e indicador de "agora"
- **Drag-and-drop HTML5 nativo**: cartões arrastáveis com linha fantasma do destino, modal de confirmação, validação de conflitos de agenda (interseção `[início, fim)`) e limites de horário — com `PATCH /api/v1/consultas/{id}` documentado
- **Telemedicina**: destaque com gradiente azul SUS + ícone de vídeo, botão "Sala" por cartão e botão global da próxima teleconsulta
- **Absenteísmo**: contador do dia (`faltas / consultas não canceladas`) com barra colorida por faixa (verde <10%, amarelo <20%, vermelho ≥20%) e registro de falta/atendimento/desfazer nos cartões
- **Padrões SUS/APS**: CNS mascarado (LGPD), chips CIAP-2, CID-10, selo "SOAP ✓", dados de demonstração como fallback quando o backend não responde
- **Stack**: Tailwind CSS (paleta SUS customizada), ES Modules (`type="module"`, `Intl` pt-BR, optional chaining) e comentários/docstrings 100% em português

Verificações: balanceamento estrutural do módulo JS (grupos, strings, templates aninhados, comentários) validado por script próprio — sem Node ou navegador no ambiente para testes de runtime.