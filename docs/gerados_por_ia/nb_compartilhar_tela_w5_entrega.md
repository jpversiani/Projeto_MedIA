Sandboxes are empty workspaces; I'll build the file at the relative target path. Let me check more style conventions from the existing modules first.
Now I'll create the module following the project conventions.
Now let me fix several issues I spotted: the no-op listener, the fragile sender lookup, the broken `removeEventListener` in `destruir()`, preview restore via `mediaStream` property (doesn't exist), and privacy options that should be passed to `getDisplayMedia` directly.
Now the private fields section:
Now the sender lookup robustness in `#substituirTrilhaVideo`:
Now let me validate the syntax and run a functional smoke test of the module logic:
No JS runtime available, so I'll verify with a bracket-balance checker and a full manual review:
One bug remains: `alternarCompartilhamento` emits `compartilhamento:alternado` with origem "tela" even when the doctor cancels the picker. Fixing:
Final consistency check of all private member references:
Criado `backend/app/static/js/screen_share.js` (599 linhas, ES Module) com a classe `ScreenShareManager`:

- **Captura**: `getDisplayMedia` com preferência `displaySurface` (`monitor`/`window`/`browser`), `selfBrowserSurface: "exclude"` (impede compartilhar o prontuário por engano), `contentHint: "detail"` para nitidez de laudos e 720p/15fps para redes restritas da APS.
- **Sem renegociação**: `RTCRtpSender.replaceTrack()` no enviador de vídeo existente (fallback ao transceptor de vídeo), sem disparar `negotiationneeded`.
- **Alternância câmera ↔ tela**: `alternarCompartilhamento()` restaura a trilha original no encerramento; encerramento via "Parar compartilhamento" do navegador também é tratado (evento `ended` da trilha).
- **Indicador**: selo pulsante em Tailwind ("Transmitindo tela — Tela inteira/Janela/Aba") + botão de alternância com estados visual/`aria-pressed`.
- **Erros amigáveis**: mapeamento de `NotAllowedError` (instrução passo a passo do cadeado no navegador), `NotFoundError`, `NotReadableError`, ausência de suporte e conexão encerrada — emitidos via eventos `compartilhamento:*` (CustomEvent na instância e no contêiner), prontos para toast ao médico.
- API em português (`iniciarCompartilhamento`, `pararCompartilhamento`, `definirPeerConnection`, `definirTrilhaCamera`, `destruir`), integração documentada por JSDoc com o `WebRTCManager` existente, seguindo as convenções dos módulos `fila_espera.js` e `sinais_vitais_input.js` (campos `#` privados, `Object.freeze`, banners de seção). Sintaxe validada por verificador estrutural (Node indisponível no ambiente).