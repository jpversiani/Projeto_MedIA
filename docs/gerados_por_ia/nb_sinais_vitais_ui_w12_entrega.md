O arquivo já existe com uma implementação completa. Vou verificar a sintaxe e a validade do módulo:
Chamada de API errada da minha parte — `esprima` tem `parseModule` separado:
O esprima do Python é antigo (não suporta `??`, `?.` e campos privados `#` do ES2020+). Vou procurar outro runtime JS disponível:
Node instalado. Agora valido a sintaxe ESM e executo um teste funcional do componente:
Agora um teste funcional em ambiente com DOM simulado, cobrindo todos os requisitos da tarefa:
Conflito de versão do jsdom com Node 20. Instalo versão compatível:
14/15 — a falha é bug no meu teste (pego o primeiro evento `alteracao`, emitido quando a PAM ainda era nula, antes da PAD ser definida). Corrijo o teste para usar o último evento:
15/15 testes aprovados. Verificação final de integração com as telas existentes:
Concluído. O arquivo `backend/app/static/js/sinais_vitais_input.js` (ES Module, 841 linhas) está implementado e validado com testes funcionais (15/15 aprovados via Node + jsdom).

**Requisitos atendidos:**
- **7 sinais vitais**: PA sistólica/diastólica, FC, FR, Temp, SpO₂ e glicemia capilar (backend/app/static/js/sinais_vitais_input.js:39)
- **Steppers touch**: botões de 64px (`h-16 w-16`) com repetição acelerada, Pointer Events e suporte a teclado (:242)
- **Validação instantânea**: vermelho fora dos limites vitais, âmbar em zona de atenção, verde na faixa de referência (severidade calculada por `#validarValor`, :514)
- **PAM**: `calcularPam()` = (PAS + 2×PAD)/3 com destaque de hipoperfusão quando PAM < 65 (:279)
- **Alerta de choque**: SpO₂ < 92% + FC > 120 bpm → banner pulsante + evento dedicado (:290)
- **Regra extra de consistência**: PAS ≤ PAD marcada inválida (:555)
- **CustomEvents**: `sinaisvitais:alteracao`, `sinaisvitais:alerta-choque` e `sinaisvitais:confirmado` (com bubbling no contêiner e na instância `EventTarget`, :231)

Validação cobriu sintaxe ESM (`node --check`), limites clínicos, entrada pt-BR com vírgula decimal, acessibilidade ARIA e API pública defensiva.