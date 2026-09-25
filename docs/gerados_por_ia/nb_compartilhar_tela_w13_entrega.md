O projeto principal possui os arquivos de referência. Vou estudar o `webrtc_manager.js` existente e o `screen_share.js` atual para seguir as convenções do projeto.
O projeto de referência já contém convenções estabelecidas. Vou criar o arquivo no sandbox de trabalho com a implementação completa, seguindo as diretrizes (ES Module, mensagens em pt-BR, Tailwind CSS, integração com o WebRTCManager existente).
Verificando a sintaxe do módulo ES com Node:
Node indisponível — farei uma verificação estática leve (balanceamento e estrutura) com Python:
Arquivo criado e verificado — `backend/app/static/js/screen_share.js` (609 linhas, sintaxe balanceada, estrutura íntegra).

**Implementação — classe `ScreenShareManager` (ES Module):**

| Requisito | Como foi atendido |
|---|---|
| `getDisplayMedia` com preferência de tela/janela | `#capturarTela()` com `displaySurface: monitor/window/browser` + `selfBrowserSurface: "exclude"` (privacidade LGPD — oculta a própria aba do prontuário) |
| `replaceTrack` sem renegociação | `#substituirTrilhaVideo()` localiza o enviador de vídeo (`getSenders` → fallback `getTransceivers`) e chama `replaceTrack` — sem offer/answer, sem `negotiationneeded` |
| Alternância câmera ↔ tela | `alternarCompartilhamento()` em um comando; restaura a trilha original da câmera (tela → câmera) também sem renegociar |
| Indicador de transmissão ativa | Selo pulsante Tailwind (`bg-emerald-600` + `animate-pulse`) com a fonte compartilhada, gerenciado via `aria-live="polite"` |
| Erro de permissão negada amigável | `NotAllowedError` → código `PERMISSAO_NEGADA` com mensagem orientando o médico a liberar no cadeado da barra de endereço; demais falhas mapeadas (`SEM_FONTE`, `FONTE_OCUPADA`, `NAO_SUPORTADO`, cancelamento do diálogo) |

**Integração com o `WebRTCManager` existente:** `definirPeerConnection(pc)` + `definirTrilhaCamera(trilha)`; eventos `compartilhamento:{iniciado,encerrado,alternado,cancelado,erro}` emitem-se na instância e no indicador (com bubbling) para a sala de teleconsulta; `destruir()` encerra trilhas e remove listeners.

Destaques adicionais: `contentHint = "detail"` para nitidez de laudos/receitas, 15 fps ideal (economia de banda em redes da APS), áudio do sistema desativado (evita eco), e tratamento do "Parar compartilhamento" da barra do navegador com restauração automática da câmera.