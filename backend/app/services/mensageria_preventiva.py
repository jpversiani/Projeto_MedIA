# backend/app/services/mensageria_preventiva.py
"""Regras de busca ativa e lembretes preventivos (C16).

Este módulo nasceu como um esqueleto de integração com um provedor de
mensageria (WhatsApp/SMS). A parte que dependia de modelos ORM inexistentes
(`Paciente`, `Consulta`, `Vacina`, `Diagnostico`) foi removida: ela nunca era
importada por nenhuma rota e falharia com `NameError` se fosse executada.

O que permanece são as funções puras usadas pelos testes de regra de negócio:

* ``filtrar_pacientes_hipertensos_vencidos`` — seleção para busca ativa;
* ``verificar_janela_horario`` — evita contato fora do horário comercial;
* ``enviar_lembrete`` — fluxo idempotente de envio.

A entrega real de mensagens continua fora de escopo (mock); quando um gateway
for integrado, substitua ``enviar_notificacao`` e ``notificacao_ja_enviada``
por chamadas ao provedor e ao registro persistido.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Sequence


def filtrar_pacientes_hipertensos_vencidos(
    consultas: Sequence[Any], data_referencia: date
) -> list[int]:
    """Lista pacientes com consulta de hipertensão estritamente vencida.

    Uma consulta do próprio dia de referência não conta como vencida, e cada
    paciente aparece uma única vez no resultado.
    """
    vencidos: list[int] = []
    for consulta in consultas:
        tipo = getattr(consulta, "tipo", None)
        data = getattr(consulta, "data", None)
        paciente_id = getattr(consulta, "paciente_id", None)
        if tipo == "hipertensao" and data is not None and data < data_referencia:
            if paciente_id is not None and paciente_id not in vencidos:
                vencidos.append(paciente_id)
    return vencidos


def verificar_janela_horario(horario: datetime) -> bool:
    """Informa se o horário está dentro da janela permitida (08:00–19:59)."""
    return time(8, 0) <= horario.time() < time(20, 0)


def notificacao_ja_enviada(paciente_id: int, consulta_id: int) -> bool:
    """Verifica a idempotência do envio de notificação.

    O mock não consulta persistência e assume que a notificação ainda não
    existe. A integração real deve consultar a tabela ``mensagens_preventivas``
    pela chave de idempotência.
    """
    return False


def enviar_notificacao(paciente_id: int, consulta_id: int) -> None:
    """Ponto de extensão para o gateway de WhatsApp/SMS."""
    return None


def registrar_notificacao(paciente_id: int, consulta_id: int) -> None:
    """Ponto de extensão para registrar a notificação enviada no banco."""
    return None


def enviar_lembrete(paciente_id: int, consulta_id: int) -> None:
    """Executa o fluxo idempotente de envio de lembrete preventivo."""
    if not notificacao_ja_enviada(paciente_id=paciente_id, consulta_id=consulta_id):
        enviar_notificacao(paciente_id=paciente_id, consulta_id=consulta_id)
        registrar_notificacao(paciente_id=paciente_id, consulta_id=consulta_id)
