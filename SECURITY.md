# Segurança — MedIA Practice

Este documento diz **o que o sistema garante hoje**, **o que ele não garante** e
**como reportar um problema**. A parte mais útil é a segunda: um produto de saúde
que só lista qualidades não ajuda ninguém a decidir se pode usá-lo.

---

## 1. Como reportar uma vulnerabilidade

**Não abra issue pública.** Uma falha de segurança em sistema clínico é, por si,
exposição de dados de paciente.

- Envie um e-mail para o responsável técnico com o assunto `[SEGURANÇA] MedIA`.
- Inclua: versão/commit, passos para reproduzir, impacto observado e, se houver,
  uma prova de conceito mínima. **Não inclua dados de paciente real.**
- Prazo de resposta que nos comprometemos a cumprir:

| Etapa | Prazo |
|---|---|
| Confirmação de recebimento | 2 dias úteis |
| Avaliação inicial (severidade e impacto) | 5 dias úteis |
| Correção de falha crítica (exposição de PHI, bypass de autenticação) | 7 dias corridos |
| Correção de falha alta/média | 30 dias corridos |
| Divulgação coordenada | após a correção, com seu acordo |

Não temos programa de recompensa. Creditamos o relato no `CHANGELOG` se você
quiser.

---

## 2. Versões suportadas

Projeto em desenvolvimento ativo, branch `main`. Apenas o HEAD recebe correção de
segurança; não há branches de manutenção.

| Versão | Suporte |
|---|---|
| `main` (HEAD) | ✅ |
| Qualquer tag/commit anterior | ❌ |

---

## 3. O que está implementado

| Controle | Onde | Observação |
|---|---|---|
| Autenticação JWT com access curto | `app/services/auth_service.py` | Access de **15 min**, refresh de **7 dias** |
| Refresh rotativo com detecção de reuso | `app/services/auth_service.py`, tabela `refresh_tokens` | Reutilizar um refresh revoga **todas** as sessões do usuário |
| Cookies `HttpOnly` para o refresh | `app/api/v1/auth.py` | O JavaScript nunca lê o refresh token |
| Autorização por papel (RBAC) | `app/core/rbac.py` | 19 módulos declaram os papéis aceitos; rota nova nasce protegida |
| Isolamento por estabelecimento | `app/core/rbac.py` (`filtrar_tenant`) | Consulta e escrita cruzada entre clínicas bloqueadas com 403 |
| Auditoria de acesso a PHI encadeada por hash | `app/services/audit_service.py` | `verificar_cadeia()` detecta alteração posterior no banco |
| Sinalização de teleconsulta autenticada | `app/api/v1/telemedicina_ws.py` | Token obrigatório; sala validada no banco; roteamento 1:1 |
| Retenção e anonimização (LGPD Art. 16) | `app/services/retencao_dados.py` | Plano sem efeito colateral; execução exige confirmação e é auditada |
| Backup verificado | `scripts/backup_db.py` | SHA-256 em manifesto + `integrity_check` + restauração confirmada |
| Migrações versionadas | `alembic/versions/` | Sem `create_all` em produção |

---

## 4. O que **não** está implementado (risco conhecido)

Estas lacunas são reais e estão abertas. Não trate o sistema como pronto para
dados de paciente real enquanto elas existirem.

| # | Lacuna | Impacto | Contorno atual |
|---|---|---|---|
| 1 | **CPF e CNS em claro no banco** | Um dump do banco expõe identificadores diretos | Criptografia em repouso no volume + backup cifrado; ver `docs/POLITICA_RETENCAO_E_TRATAMENTO_DE_INCIDENTES.md` §6 |
| 2 | **Assinatura ICP-Brasil é simulada** | Receita/atestado não têm validade jurídica de assinatura | `vidaas_signature_service.py` não faz chamada de rede; ver P0.4 no status |
| 3 | **Access token em `localStorage`** | XSS consegue ler o token (15 min de janela) | CSP e revisão de XSS pendentes; refresh já está em cookie `HttpOnly` |
| 4 | **Sem rate limiting** | Força bruta de senha e abuso de API | Colocar atrás de gateway/WAF com limite por IP |
| 5 | **Hub de sinalização em memória** | Com mais de um worker, os dois lados podem cair em processos diferentes | Rodar **1 worker** ou adicionar backplane Redis |
| 6 | **Sem lockfile** | Build não reprodutível; dependência pode mudar sem revisão | `pip freeze` + `pip install -r` com hashes |
| 7 | **Sem varredura de segredo no CI** | Chave vazada não é detectada antes do merge | Adicionar `gitleaks` ao workflow |
| 8 | **Autenticação de cidadão/paciente é frágil** | Link de teleconsulta é credencial temporária; paciente precisa de conta quando `require_auth` está ligado | Emitir convite assinado de uso único |

---

## 5. Requisitos mínimos para implantação

Nenhum destes itens é opcional em ambiente com dado real:

1. `ENVIRONMENT=production` — isso liga `require_auth`, que aplica o token a
   **todas** as rotas clínicas.
2. `SECRET_KEY` própria, gerada por `secrets.token_urlsafe(64)` e guardada em
   cofre de segredos. **A chave de desenvolvimento no repositório não serve.**
3. HTTPS obrigatório (o WebSocket usa `wss:` automaticamente quando a página é
   HTTPS). Cookies de sessão marcados `Secure`.
4. PostgreSQL em vez de SQLite; `alembic upgrade head` no deploy.
5. `TURN_URL`, `TURN_USERNAME`, `TURN_CREDENTIAL` configurados — sem TURN, a
   teleconsulta falha em rede hospitalar com firewall.
6. Backup diário com `scripts/backup_db.py` e **verificação periódica** com
   `--verificar`; teste de restauração trimestral.
7. Retenção agendada: `python -m app.tools.retencao --executar` (mensal, no
   mínimo) com o relatório arquivado.
8. Um worker do Uvicorn (ou backplane Redis) por causa do hub de sinalização.
9. Logs sem PHI: nunca registre CPF/CNS em log de aplicação.

---

## 6. Escopo

**Dentro do escopo:** autenticação, autorização, isolamento entre clínicas,
auditoria, sinalização de teleconsulta, retenção/anonimização, backup/restauração,
e a aplicação em `backend/app`.

**Fora do escopo:** infraestrutura do provedor de nuvem, segurança física,
dispositivos dos usuários, gateway de WhatsApp/SMS, operadoras de plano de saúde
e o provedor de assinatura digital.
