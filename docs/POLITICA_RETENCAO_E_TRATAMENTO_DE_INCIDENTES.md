# Política de retenção de dados e resposta a incidentes

**Base legal:** LGPD (Lei 13.709/2018) Arts. 15, 16, 18, 37, 46, 48; Resoluções
CFM nº 1.821/2007 e nº 2.314/2022; Marco Civil da Internet (Lei 12.965/2014) Art. 15.

Este documento é a referência para o encarregado de dados (DPO) e para quem
opera o sistema. Ele descreve o que o **código** já faz e o que depende de
decisão humana. Onde os dois divergem, o código é a verdade — e a divergência é
um defeito a corrigir.

---

## 1. Princípios aplicados

1. **Finalidade:** cada tabela existe para uma finalidade declarada. Quando ela
   termina, o dado sai (Art. 15/16).
2. **Minimização:** cópia de contingência já sincronizada não fica guardada
   "por garantia"; mensagem de campanha antiga perde o telefone.
3. **Guarda clínica obrigatória:** registro de prontuário **não** é apagado por
   rotina automática. A guarda mínima é de **20 anos** (CFM 1.821/2007).
4. **Rastreabilidade:** toda execução destrutiva é registrada na trilha de
   auditoria encadeada (`EXECUTAR_RETENCAO_DADOS`).
5. **Decisão humana no que é irreversível:** anonimizar registro clínico é ato
   jurídico, não um cron.

---

## 2. Tabela de retenção em vigor

Implementada em `backend/app/services/retencao_dados.py`. Os prazos são contados
a partir da data indicada em cada linha.

| Regra | Dado | Prazo | Ação | Base legal |
|---|---|---|---|---|
| `refresh_tokens_expirados` | Token de sessão | 30 dias após expirar/revogar | **Expurgar** | LGPD Art. 15/16 |
| `salas_virtuais_expiradas` | Link de teleconsulta | 7 dias após expirar | **Encerrar** (sala permanece, link é inutilizado) | LGPD Art. 15/16 |
| `atendimentos_offline_sincronizados` | Cópia de contingência | 90 dias após sincronizar | **Expurgar** (conteúdo já está no prontuário) | LGPD Art. 16, II |
| `mensagens_preventivas_antigas` | Telefone, nome, CNS, CPF | 365 dias | **Anonimizar** (linha fica para estatística) | LGPD Art. 16 |
| `alertas_busca_ativa_antigos` | Nome, CNS, CPF | 730 dias | **Anonimizar** | LGPD Art. 16 |
| `cidadaos_sem_movimento_20_anos` | Cadastro completo | 20 anos sem atendimento | **Revisar** (relatório; nada é alterado) | CFM 1.821/2007 |
| `trilha_auditoria_antiga` | Eventos de auditoria | 5 anos | **Revisar** (relatório) | LGPD Art. 37 |

**Marcador de anonimização:** `[anonimizado]`. É intencionalmente visível: quem
ler o banco precisa saber que a remoção foi deliberada, não uma falha de carga.

### Como operar

```bash
# 1) Ver o plano (não altera nada — é o padrão)
python -m app.tools.retencao

# 2) Aplicar (irreversível; grava evento na auditoria)
python -m app.tools.retencao --executar

# 3) Aplicar uma regra específica
python -m app.tools.retencao --executar --regra mensagens_preventivas_antigas

# 4) Para automação/monitoramento
python -m app.tools.retencao --json
```

Pela API (perfil **ADMIN**):

- `GET /api/v1/conformidade/retencao` — plano com prazos, base legal e volume.
- `POST /api/v1/conformidade/retencao/executar` — exige `{"confirmar": true}`.

Cadência recomendada: **mensal**, com o relatório arquivado como evidência.

---

## 3. Dados tratados e finalidade

| Categoria | Exemplos | Finalidade | Onde |
|---|---|---|---|
| Identificação | Nome, CPF, CNS, data de nascimento | Atender, prescrever, faturar | `cidadaos`, `documentos_clinicos`, `receitas` |
| Contato | Telefone, WhatsApp, e-mail | Aviso de consulta e busca ativa | `cidadaos`, `mensagens_preventivas` |
| Clínico | SOAP, diagnósticos, prescrições | Assistência e continuidade do cuidado | `atendimentos_soap`, `documentos_clinicos` |
| Sessão | Tokens, IP, user agent | Autenticar e detectar abuso | `refresh_tokens`, `audit_trail` |
| Auditoria | Eventos de acesso a PHI | Provar conformidade e investigar incidente | `audit_trail` |

Dados **sensíveis** (Art. 5º, II): os clínicos, tratados com base no Art. 11 —
tutela da saúde, por profissional de saúde.

---

## 4. Direitos do titular (Art. 18)

| Direito | Como é atendido hoje |
|---|---|
| Confirmação e acesso | Exportação do prontuário pelo profissional responsável |
| Correção | Edição do cadastro em `cidadaos` (com registro em auditoria) |
| Anonimização/eliminação de dado desnecessário | Rotina de retenção (§2) |
| Portabilidade | Exportação em PDF/JSON pelo próprio sistema |
| Informação sobre compartilhamento | Trilha de auditoria (`GET /api/v1/auth/audit-trail`) |
| Revogação de consentimento | Registro de consentimento de teleconsulta é auditado |

**Eliminação de registro clínico** não é automática: exige parecer do
responsável técnico, porque a guarda de 20 anos é obrigação legal que prevalece
sobre o pedido. O pedido e a decisão devem ser registrados.

---

## 5. Segurança dos dados

| Controle | Estado |
|---|---|
| TLS em trânsito | Obrigatório no deploy (HTTPS/WSS) |
| Senhas | Hash com bcrypt/argon (ver `auth_service.py`) |
| Acesso | RBAC por papel + isolamento por estabelecimento |
| Trilha de auditoria | Encadeada por hash; `verificar_cadeia()` detecta alteração |
| Backup | `scripts/backup_db.py` com SHA-256 + `integrity_check` |
| Criptografia em repouso do banco | **Não implementada** — use volume cifrado (§6) |

---

## 6. Contorno obrigatório enquanto não houver criptografia de campo

CPF e CNS ficam em claro nas colunas. Até isso mudar:

1. **Volume/disco cifrado** (LUKS, BitLocker, EBS criptografado).
2. **Backup cifrado em repouso** e em bucket com acesso restrito.
3. **Acesso ao banco por rede privada**, sem exposição pública.
4. **Proibição de exportar dump para estação de trabalho** — use apenas as rotas
   da API, que aplicam RBAC e auditoria.
5. **Logs sem PHI:** nenhum CPF/CNS em log de aplicação.

O desenho da solução definitiva está em §9.

---

## 7. Resposta a incidentes (Art. 48)

### 7.1 Classificação

| Severidade | Critério | Prazo de contenção |
|---|---|---|
| **Crítica** | PHI exposto, acesso não autorizado confirmado, banco copiado | Imediata (≤ 2 h) |
| **Alta** | Credencial comprometida, bypass de autenticação possível, backup perdido | ≤ 24 h |
| **Média** | Falha sem exposição confirmada, erro de configuração | ≤ 72 h |
| **Baixa** | Divergência de política, ausência de registro | Próximo ciclo |

### 7.2 Runbook

1. **Detectar e registrar** — abrir registro com data/hora, quem detectou, o que
   foi observado. Não presumir causa ainda.
2. **Conter** — revogar sessões (`/auth/logout-all`), rotacionar `SECRET_KEY`,
   bloquear acesso ao banco, remover a exposição.
3. **Preservar evidência** — **não** apagar logs nem o banco. Copiar
   `audit_trail` e o backup mais recente para local isolado. A cadeia de hash
   permite provar que a trilha não foi alterada.
4. **Avaliar** — quais titulares, quais dados, qual volume (usar
   `GET /conformidade/retencao` e a trilha para dimensionar).
5. **Comunicar** — à ANPD e aos titulares afetados quando houver risco relevante
   (Art. 48), em prazo razoável, com: dados afetados, medidas técnicas adotadas,
   riscos e canal de contato. O responsável técnico assina a comunicação.
6. **Corrigir** — corrigir a causa, não só o sintoma. Registrar no `CHANGELOG`.
7. **Aprender** — revisar este documento em até 30 dias após o incidente.

### 7.3 Quem faz o quê

| Papel | Responsabilidade |
|---|---|
| Responsável técnico | Decisão de comunicação, assinatura, contato com a ANPD |
| DPO / encarregado | Atendimento ao titular, registro do incidente |
| Engenharia | Contenção técnica, análise de causa, correção |
| Clínica usuária | Informar o paciente quando a comunicação couber a ela |

---

## 8. Revisão

Revisar esta política **anualmente** e sempre que: mudar a legislação, entrar
nova categoria de dado, ocorrer incidente, ou mudar o prazo de guarda. A última
revisão deve constar no rodapé do arquivo (data + autor).

---

## 9. Próximo passo técnico (desenho da criptografia de campo)

Para eliminar a lacuna de CPF/CNS em claro sem quebrar busca:

1. Adicionar coluna `cpf_hash` = HMAC-SHA256(CPF, chave dedicada) com índice
   único — é por ela que se busca, não pelo valor.
2. Guardar `cpf_cifrado` = AES-256-GCM(CPF) com nonce por registro; decifrar
   apenas na borda (PDF, TISS, tela) e nunca em listagem.
3. Migração em duas etapas: popular `cpf_hash`/`cpf_cifrado` com o dado atual,
   trocar as leituras, depois remover a coluna em claro.
4. Chave em KMS/cofre, com rotação versionada (`key_id` na linha).
5. Testes obrigatórios: busca por CPF continua funcionando; dump do banco não
   revela CPF; rotação de chave não quebra registros antigos.

Enquanto os passos 1–4 não estiverem concluídos, vale o contorno de §6.
