import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from app.models.atendimento import AtendimentoSOAP

def gerar_fai_ledi_payload(atendimento: AtendimentoSOAP) -> Dict[str, Any]:
    """
    Gera o payload da Ficha de Atendimento Individual (FAI) no formato do LEDI (Layout e-SUS APS de Dados e Interface).
    Estrutura compatível com as regras de validação do SISAB / Ministério da Saúde.
    """
    cidadao = atendimento.cidadao
    uuid_ficha = str(uuid.uuid4())
    
    problemas_ciap2 = [p.codigo for p in atendimento.problemas if p.tipo_codigo == "CIAP2"]
    problemas_cid10 = [p.codigo for p in atendimento.problemas if p.tipo_codigo == "CID10"]

    data_atendimento_str = (atendimento.created_at or datetime.now(timezone.utc)).strftime("%Y-%m-%d")

    payload = {
        "cabecalho": {
            "uuidDadoSerializado": uuid_ficha,
            "tipoDadoSerializado": 7, # 7 = Ficha de Atendimento Individual (FAI)
            "cnesDadoSerializado": "3180115",
            "ineDadoSerializado": "0001452361",
            "codIbge": "3143302", # Montes Claros - MG
            "versao": "5.3.0",
            "dataEnvio": datetime.now(timezone.utc).isoformat()
        },
        "fichaAtendimentoIndividualMaster": {
            "headerTransport": {
                "profissionalCNS": "700123456789012",
                "cboCodigo_2002": "225142", # Médico de Família
                "cnes": "3180115",
                "ine": "0001452361",
                "dataAtendimento": data_atendimento_str
            },
            "atendimentosIndividuais": [
                {
                    "numeroProntuario": f"PRONT-{atendimento.cidadao_id}",
                    "cnsCidadao": cidadao.cns if cidadao else None,
                    "cpfCidadao": cidadao.cpf if cidadao else None,
                    "dataNascimento": cidadao.data_nascimento.strftime("%Y-%m-%d") if (cidadao and cidadao.data_nascimento) else None,
                    "sexo": 0 if (cidadao and cidadao.sexo == "M") else 1, # 0 = Masc, 1 = Fem
                    "localDeAtendimento": 1, # 1 = UBS
                    "turno": 1, # 1 = Manhã, 2 = Tarde
                    "tipoAtendimento": 1, # 1 = Consulta agendada / espontânea
                    "problemaCondicaoAvaliada": {
                        "ciap2": problemas_ciap2,
                        "cid10": problemas_cid10,
                        "notas": atendimento.avaliacao_notas
                    },
                    "exame": [
                        {"codigoExame": ex.strip()} for ex in (atendimento.plano_exames or "").split(",") if ex.strip()
                    ],
                    "medicamentos": [
                        {"nome": med.strip()} for med in (atendimento.plano_prescricoes or "").split("\n") if med.strip()
                    ],
                    "condutas": [
                        {"conduta": 1} # 1 = Retorno para consulta agendada / cuidado continuado
                    ],
                    "statusAtendimento": "FINALIZADO"
                }
            ]
        }
    }
    return payload
