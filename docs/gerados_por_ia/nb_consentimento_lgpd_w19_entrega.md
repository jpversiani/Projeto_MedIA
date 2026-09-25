O sandbox está vazio, então vou criar o arquivo alvo do zero, seguindo as diretrizes (ES Module, Tailwind, pt-BR, POST `/api/v1/consentimento`).
Corrigindo um erro de digitação que notei no método `destruir()` e validando a sintaxe:
Não há Node no ambiente; aplico dois ajustes finos (escala da velocidade do traço e limpeza do redesenho) e valido a estrutura com um cheque estático em Python:
Criado: `backend/app/static/js/consentimento_lgpd.js` (875 linhas, ES Module sem efeitos colaterais na importação).

Implementação conforme solicitado:

- **Modal (Tailwind)**: termo de sigilo e consentimento com referência à Resolução CFM 2.314/2022 e à LGPD, dois aceites obrigatórios (checkbox), área rolável, `role="dialog"` com trap de foco, ESC para cancelar e exibição de paciente/CPF/CNS/profissional.
- **Assinatura em canvas**: Pointer Events (mouse/touch/caneta) com `setPointerCapture`, eventos coalescidos, suavização por curvas quadráticas nos pontos médios, espessura dinâmica pela velocidade, suporte a DPR e redesenho preservado via `ResizeObserver` (`AssinaturaCanvas` em `consentimento_lgpd.js:231`).
- **Hash SHA-256**: `calcularHashSha256` via Web Crypto API sobre payload canônico de chaves fixas (inclui assinatura, aceites, IP, UA e timestamp) — `consentimento_lgpd.js:76`; o hash viaja como `hash_integridade` com `algoritmo_hash: 'SHA-256'`.
- **Auditoria e POST**: IP público (ipify, best-effort com fallback, pois o IP autoritativo deve vir do servidor), `navigator.userAgent`, `new Date().toISOString()` e `POST /api/v1/consentimento` com CSRF opcional via `meta[name="csrf-token"]`, estado de envio e mensagens de erro em pt-BR.

Integração: `import abrirModalConsentimento from '/static/js/consentimento_lgpd.js'` → `const r = await abrirModalConsentimento({ cpf, cns, nomePaciente, idAgendamento, profissional: { nome, registro } })`; retorna `null` se o paciente cancelar. Observação: o hash exige contexto seguro (HTTPS/localhost), com mensagem clara quando indisponível.