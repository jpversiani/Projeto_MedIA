Calendário PNI (simplificado):
- Ao nascer: BCG, Hepatite B
- 2 meses: Penta (1ª), VIP (1ª), PCV10 (1ª), Rotavírus (1ª)
- 3 meses: Meningocócica C (1ª), Penta (2ª)?

class Paciente(Base):
    __tablename__ = "pacientes"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    cns: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    cpf: Mapped[str | None] = mapped_column(String(11), unique=True)
    nome_completo: Mapped[str]
    data_nascimento: Mapped[date]
    telefone_celular: Mapped[str | None]
    telefone_whatsapp: Mapped[bool]  # aceita whatsapp
    opt_out_mensageria: Mapped[bool] = mapped_column(default=False)  # LGPD consent
    ...

class Vacinacao(Base):  # registro de dose aplicada
    __tablename__ = "vacinacoes"
    id, paciente_id, vacina (nome/codigo), dose (1ª/2ª/reforço), data_aplicacao, lote, estrategia
    
class Teleconsulta(Base):
    __tablename__ = "teleconsultas"
    id, paciente_id, profissional_nome, profissional_cns?, data_hora_inicio, data_hora_fim, status (AGENDADA, CONFIRMADA, REALIZADA, CANCELADA, FALTOU), link_sala, motivo_cid10?, ciap2?
    
class MensagemEnviada(Base):
    __tablename__ = "mensagens"
    id, paciente_id, teleconsulta_id?, canal, tipo (LEMBRETE_TELECONSULTA, ...), texto, status_envio (ENVIADA, FALHA, SIMULADA), criada_em, enviada_em
    
class AlertaBuscaAtiva(Base):
    __tablename__ = "alertas_busca_ativa"
    id, paciente_id, tipo (VACINA_ATRASADA, DIABETES_SEM_ACOMPANHAMENTO), prioridade, descricao, detalhe (JSON), status (ABERTO, EM_ATENDIMENTO, RESOLVIDO), responsavel?, criado_em, resolvido_em

soma = sum(digit[i] * (15 - i) for i in range(15))
resto = soma % 11
if resto != 0:
    # recompute: soma += 100? No...

function validaCNS(cns):
    if len(cns) != 15: return false
    if cns has non-digits: return false (or handle with [0-1] for letters? There's a variant with letters but let's keep digits)
    if cns[0] not in "123789": return false
    soma = sum(int(cns[i]) * (15 - i) for i in range(15))
    resto = soma % 11
    if resto == 0: return true
    else: return false

soma = Σ (digit × weight) where weights = 15,14,13,...,1?

function validaCNS(vCNS) {
  // Formatos: 1, 2, 7, 8 ou 9
  if ((vCNS.trim().length != 15) || (vCNS.charAt(0) != '1' && vCNS.charAt(0) != '2' && vCNS.charAt(0) != '7' && vCNS.charAt(0) != '8' && vCNS.charAt(0) != '9')) {
    return false;
  } else {
    var soma;
    var resto;
    ...
    soma = (Number(vCNS.charAt(0)) * 15) + (Number(vCNS.charAt(1)) * 14) + ... + (Number(vCNS.charAt(14)) * 1);
    resto = soma % 11;
    if (resto != 0) {
      soma = soma + (11 - resto) * 100?

soma = (Number(vCNS.charAt(0)) * 15) + (Number(vCNS.charAt(1)) * 14) + (Number(vCNS.charAt(2)) * 13) + (Number(vCNS.charAt(3)) * 12) + (Number(vCNS.charAt(4)) * 11) + (Number(vCNS.charAt(5)) * 10) + (Number(vCNS.charAt(6)) * 9) + (Number(vCNS.charAt(7)) * 8) + (Number(vCNS.charAt(8)) * 7) + (Number(vCNS.charAt(9)) * 6) + (Number(vCNS.charAt(10)) * 5) + (Number(vCNS.charAt(11)) * 4) + (Number(vCNS.charAt(12)) * 3) + (Number(vCNS.charAt(13)) * 2) + (Number(vCNS.charAt(14)) * 1);
resto = soma % 11;
if (resto != 0) {
  soma = soma + (11 - resto) * 100;  // ??? no

resto = soma % 11;
if (resto != 0) {
  soma = soma + (11 - resto) * 100;  // no this doesn't make sense

def valida_cns(cns):
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] not in '123789':
        return False
    soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
    resto = soma % 11
    if resto == 0:
        return True
    # Se resto != 0, soma = soma + (11 - resto) * 100?

soma = Σ digit_i * peso_i (pesos 15..1)
resto = soma % 11
se resto != 0:
    soma = soma + (11 - resto) * 100  # ???

dv = 11 - resto
if dv in (10, 11): dv = 0  # ?

function validaCNS(vCNS) {
  if ((vCNS.trim().length != 15) || ...) return false;
  var soma = 0;
  for (var i = 0; i < 15; i++) {
    soma += Number(vCNS.charAt(i)) * (15 - i);
  }
  var resto = soma % 11;
  if (resto != 0) {
    resto = 11 - resto;
    // recompute with the last digit replaced?
  }
}

resto = soma % 11
if resto != 0:
    soma = soma + (11 - resto) * 100
    resto = soma % 11
    if resto == 0: valid else invalid
