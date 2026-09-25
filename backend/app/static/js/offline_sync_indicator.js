/**
 * offline_sync_indicator.js
 * Projeto MedIA — C37: Indicador e Armazenamento Local de Sincronização Offline
 * ...
 */

'use strict';

/**
 * ============================================================================
 * Projeto MedIA — C37: Indicador e Armazenamento Local de Sincronização Offline
 * ============================================================================
 * ...
 */

{
  id_local: uuid,           // idempotency key
  cns_profissional: ...,
  cns_paciente / cpf_paciente,
  cid10_cod, ciap2_cod,
  soap: { subjetivo, objetivo, avaliacao, plano },
  data_atendimento,
  ubs_id / unidade_saude_id,
  criado_em: ISO timestamp,
  tentativas_sync: 0,
  status: 'PENDENTE' | 'SINCRONIZADO' | 'ERRO'
}

<div id="media-offline-badge" role="status" aria-live="polite">
  <span class="media-offline-badge__dot"></span>
  <span class="media-offline-badge__text">...</span>
</div>

soma = 0
for i in range(15):
    soma += int(cns[i]) * (15 - i)
if soma % 11 == 0: valid

cns must match: [789] + 11 digits + "0001"?

def valida_cns(cns: str) -> bool:
    cns = re.sub(r'\D', '', cns)
    if len(cns) != 15:
        return False
    if cns[0] in '12':
        # soma ponderada
        soma = sum(int(d) * w for d, w in zip(cns, range(15, 0, -1)))
        return soma % 11 == 0
    elif cns[0] in '789':
        # provisional: 7/8/9 + 11 digits + 0001? 
        # Actually: cns[12:15] must be '000' + check?

soma = sum(int(d) * w for d, w in zip(cns[:11], range(15, 5, -1)))  # weights 15..5
resto = soma % 11
dv = 11 - resto if resto > 1 else 0 - resto?

soma = 0
for i in 0..14:
    soma += cns[i] * (15 - i)
resto = soma % 11
valid if resto == 0

soma = 0
for i in 0..10 (first 11 digits):
    soma += cns[i] * (15 - i)
resto = soma % 11
if resto != 0:
    dv = 11 - resto
else:
    dv = 0
# then: pin = str(dv) + "0001"?

function validaCNS(vetorCNS) {
  var soma = 0;
  if (vetorCNS[0] == '1' || vetorCNS[0] == '2') {
    for (i = 0; i < 15; i++) {
      soma += parseInt(vetorCNS[i]) * (15 - i);
    }
    if ((soma % 11) == 0) return true; else return false;
  } else {
    // 7,8,9
    soma = 0;
    for (i = 0; i < 11; i++) soma += parseInt(vetorCNS[i]) * (15 - i);
    var resto = soma % 11;
    var dv = 11 - resto;
    if (dv > 9) {
      // dv becomes two digits: 1 and dv-10
      var resultado = dv.toString(); // e.g., "10" or "11"
      var pin = resultado.split('');
      var pis = vetorCNS.substring(0, 11) + pin[0] + pin[1]; // 13 digits
      soma = 0;
      for (i = 0; i < 13; i++) soma += parseInt(pis[i]) * (15 - i);
      resto = soma % 11;
      var dvFinal = 11 - resto;
      var resultadoFinal = pis + dvFinal + "01"; // 15 digits? pis is 13, + dv + "01" = 15? 13+1+2 = 16. Hmm.
    }
  }
}

Para CNS iniciando com 1 ou 2:
  soma = Σ (dígito_i × peso_i), pesos de 15 a 1 (posição 0 → peso 15, posição 14 → peso 1)
  válido se soma % 11 == 0

Para CNS iniciando com 7, 8 ou 9:
  soma = Σ (dígito_i × peso_i) para os 11 primeiros dígitos, pesos 15 a 5
  resto = soma % 11
  dv = 11 - resto
  se dv > 9: dv vira dois dígitos (ex: 10 → '1','0'), formando "pis" de 13 dígitos:
      pis = primeiros 11 dígitos + os dois dígitos do dv
      refaz soma com pesos 15 a 3 sobre os 13 dígitos
      resto = soma % 11
      dv = 11 - resto
      resultado = pis + dv + "01"  → 13 + 1 + 2 = 16?

function validaCNS(vetorCNS) {
  var soma = new Number(0);
  var i = new Number(0);
  var dv = new Number(0);
  var pis = new String();
  var resultado = new String();
  var resto = 0;
  var mult = new Array(15);

  if (window.event) { ... }

  if (vetorCNS.trim().length != 15) { return false; }

  // Se os primeiros caracteres são 1 ou 2
  if ((vetorCNS.charAt(0) == '1') || (vetorCNS.charAt(0) == '2')) {
    for (i = 0; i < 15; i++) {
      soma = soma + (parseInt(vetorCNS.substring(i, i + 1)) * (15 - i));
    }
    resto = (soma % 11);
    if (resto != 0) {
      return false;
    } else {
      return true;
    }
  } else {
    // Se os primeiros caracteres são 7, 8 ou 9
    for (i = 0; i < 11; i++) {
      soma = soma + (parseInt(vetorCNS.substring(i, i + 1)) * (15 - i));
    }
    resto = soma % 11;
    dv = 11 - resto;
    if (dv > 9) {
      pis = vetorCNS + '0';  // hmm no
    }
    ...
  }
}

} else {
  soma = 0;
  for (i = 0; i < 11; i++) {
    soma = soma + (parseInt(vetorCNS.substring(i, i + 1)) * (15 - i));
  }
  resto = soma % 11;
  dv = 11 - resto;
  if (dv > 9) {
    pis = vetorCNS.substring(0, 11) + '0' + dv;  // no...
  }
}

if (dv > 9) {
  resultado = dv + '';  // "10" or "11"
  pis = vetorCNS.substring(0, 11) + resultado.substring(0, 1) + resultado.substring(1, 2);
  // pis has 13 digits
  soma = 0;
  for (i = 0; i < 13; i++) {
    soma = soma + (parseInt(pis.substring(i, i + 1)) * (15 - i));
  }
  resto = soma % 11;
  dv = 11 - resto;
  resultado = pis + dv + '01';  // 13 + 1 + 2 = 16?? 
}
