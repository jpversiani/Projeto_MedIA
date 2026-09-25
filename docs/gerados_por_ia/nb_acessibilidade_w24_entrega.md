Entendido. O workspace (sandbox) está vazio, então vou criar o arquivo alvo no caminho relativo `backend/app/static/js/acessibilidade_widget.js` seguindo as convenções do projeto MedIA (módulos ES com cabeçalho JSDoc em pt-BR, `'use strict'`, constantes congeladas, integração por eventos customizados como em `fila_espera.js`).
Agora vou corrigir dois problemas identificados (referência a método inexistente e bloco de exportação redundante) e tratar o `Escape` sem exigir `Alt`:
Verificação de sintaxe e estrutura:
Node não está disponível no ambiente. Farei uma verificação estática estrutural do arquivo:
Estrutura íntegra. Corrigindo um último detalhe: o interruptor de narração precisa re-registrar o ouvinte de eventos para refletir o novo estado (o `falar` estava capturado apenas na inicialização):
Arquivo criado: `backend/app/static/js/acessibilidade_widget.js` (1.220 linhas, ES Module, sem efeitos colaterais na importação), conforme as convenções do projeto MedIA.

**Cobertura dos requisitos (WCAG 2.1 AA / e-MAG):**

| Requisito | Implementação |
|---|---|
| Widget flutuante | `WidgetAcessibilidade` (botão FAB `role=dialog` com `aria-expanded`, foco gerenciado, `destruir()` para SPA) |
| Fonte até 200% (passos de 10%) | `aumentarFonte()/diminuirFonte()/redefinirFonte()` em `document.documentElement.style.fontSize`, limites 100–200% (`ESCALA_FONTE_MAXIMA`) |
| Alto contraste (filter + classes) | `filter: contrast(1.35) saturate(1.15)` em `<html>` + classe `media-alto-contraste` com overrides das utilidades Tailwind (bg-*, text-*, shadow-*, border-*) |
| Skip links / teclado | `<nav id="media-ac-skip">` focável no primeiro TAB; atalhos e-MAG/gov.br: Alt+A, Alt+1 (contraste), Alt+2/3/0 (fonte), Alt+4/5 (leitura), Alt+C/M (conteúdo/menu), Esc fecha painel |
| aria-live chamada de sala | `anunciarChamadaSala()` + `escutarChamadasDeSala()` consumindo o evento `media:chamada-sala` (integração direta com `fila_espera.js`), região `role="alert"`/polite singleton |
| Termo via SpeechSynthesis | `LeitorTermo`: voz pt-BR automática, divisão em blocos de ≤220 caracteres (bug do Chromium), Ler/Pausar/Retomar/Parar, degradação grácil sem suporte |

Extras: persistência em `localStorage` (`media:acessibilidade:v1`), respeito a `prefers-contrast: more` e `prefers-reduced-motion`, alvos táteis ≥44px, região de status `aria-live` no painel, e integração opcional via callback `aoAplicarPreferencias`.