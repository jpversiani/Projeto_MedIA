"""
Catálogo de Especialidades Médicas e Templates Clínicos Estruturados
Suporte a atendimento presencial e telemedicina para diversas especialidades médicas.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class EspecialidadeTemplate:
    codigo: str
    nome: str
    icone: str
    descricao: str
    queixa_sugestoes: List[str]
    anamnese_guia: str
    exame_fisico_template: str
    principais_ciap2_cid10: List[Dict[str, str]]
    alertas_seguranca_telemedicina: List[str]


CATALOGO_ESPECIALIDADES: Dict[str, EspecialidadeTemplate] = {
    "clinica_medica": EspecialidadeTemplate(
        codigo="clinica_medica",
        nome="Clínica Médica / Geral",
        icone="fa-stethoscope",
        descricao="Acompanhamento ambulatorial geral, manejo de condições crônicas e check-up.",
        queixa_sugestoes=[
            "Revisão de exames de rotina / check-up",
            "Controle de Hipertensão Arterial e Diabetes",
            "Cefaleia e mal-estar geral",
            "Fadiga crônica e fraqueza",
            "Sintomas respiratórios agudos (tosse, coriza, febre)"
        ],
        anamnese_guia="HDA cronológica, fatores desencadeantes, comorbidades (HAS, DM, dislipidemia), medicações em uso, hábitos de vida e histórico familiar.",
        exame_fisico_template="Bom estado geral, lúcido e orientado, corado, hidratado, anictérico, acianótico. PA: __/__ mmHg, FC: __ bpm. ACV: BNF em 2T sem sopros. AR: MVF sem ruídos adventícios. Abdome: flácido, indolor, RHA presentes.",
        principais_ciap2_cid10=[
            {"codigo": "I10", "tipo": "CID-10", "descricao": "Hipertensão essencial (primária)"},
            {"codigo": "E11", "tipo": "CID-10", "descricao": "Diabetes mellitus não-insulino-dependente (Tipo 2)"},
            {"codigo": "E78.0", "tipo": "CID-10", "descricao": "Hipercolesterolemia pura"},
            {"codigo": "R51", "tipo": "CID-10", "descricao": "Cefaleia"}
        ],
        alertas_seguranca_telemedicina=[
            "Dor torácica súbita ou dispneia intensa exigem conversão presencial / pronto atendimento imediato.",
            "Febre alta persistente (> 39°C) com rigidez de nuca contraindica teleatendimento isolado."
        ]
    ),
    "cardiologia": EspecialidadeTemplate(
        codigo="cardiologia",
        nome="Cardiologia",
        icone="fa-heart-pulse",
        descricao="Prevenção, diagnóstico e tratamento de doenças cardiovasculares e hipertensão complexa.",
        queixa_sugestoes=[
            "Palpitações paroxísticas e taquicardia",
            "Dor torácica atípica / opressão precordial aos esforços",
            "Dispneia aos esforços / ortopneia (Classe funcional NYHA)",
            "Acompanhamento pós-angioplastia ou infarto prévio",
            "Síncope e episódios pré-sincopais"
        ],
        anamnese_guia="Caracterização da dor (tipo, irradiação, alívio com repouso), tolerância a esforço físico (NYHA I-IV), histórico de DAC precoce em familiares de 1º grau, tabagismo (anos-maço).",
        exame_fisico_template="Ictus cordis palpável no 5º EIC na LHC, sem impulsões paraesternais. Ausculta cardíaca: bulhas rítmicas e normofonéticas em 2T, sem sopros ou estalidos audíveis. Ausência de turgência jugular a 45º. Pulsos periféricos simétricos e amplos. MMII sem edema ou sinais de estase.",
        principais_ciap2_cid10=[
            {"codigo": "I20.9", "tipo": "CID-10", "descricao": "Angina pectoris, não especificada"},
            {"codigo": "I48.9", "tipo": "CID-10", "descricao": "Fibrilação atrial e flutter atrial não especificado"},
            {"codigo": "I50.9", "tipo": "CID-10", "descricao": "Insuficiência cardíaca não especificada"},
            {"codigo": "I25.1", "tipo": "CID-10", "descricao": "Doença aterosclerótica do coração"}
        ],
        alertas_seguranca_telemedicina=[
            "Dor torácica típica com irradiação para mandíbula/braço esquerdo em repouso: suspeita de SCA (encaminhar imediatamente para emergência com ECG em < 10min).",
            "Síncope de repouso ou durante esforço físico requer investigação presencial urgente."
        ]
    ),
    "psiquiatria": EspecialidadeTemplate(
        codigo="psiquiatria",
        nome="Psiquiatria & Saúde Mental",
        icone="fa-brain",
        descricao="Transtornos do humor, ansiedade, insônia, TDAH e psicofarmacologia.",
        queixa_sugestoes=[
            "Crises de ansiedade, angústia e ataques de pânico",
            "Humor deprimido, anedonia e desânimo persistente",
            "Insônia inicial/intermediária e alteração do ciclo sono-vigília",
            "Dificuldade de concentração e suspeita de TDAH em adultos",
            "Ajuste e manejo de psicotrópicos em uso crônico"
        ],
        anamnese_guia="Início e evolução dos sintomas afetivos e cognitivos, histórico psiquiátrico prévio e internações, histórico de uso de substâncias, suporte sociofamiliar, avaliação formal de risco de auto/heteroagressividade.",
        exame_fisico_template="Exame do Estado Mental (EEM): Paciente asseado, cooperativo, contato visual preservado. Psicomotricidade adequada sem lentificação ou agitação. Consciência clara, orientado no tempo e espaço. Atenção concentrada. Pensamento com curso regular, forma lógica, sem delírios evidentes. Humor normotímico/deprimido, afeto modulado. Sem alucinações auditivas ou visuais. Crítica e juízo da realidade preservados.",
        principais_ciap2_cid10=[
            {"codigo": "F41.1", "tipo": "CID-10", "descricao": "Transtorno de ansiedade generalizada (TAG)"},
            {"codigo": "F32.1", "tipo": "CID-10", "descricao": "Episódio depressivo moderado"},
            {"codigo": "F41.0", "tipo": "CID-10", "descricao": "Transtorno de pânico (ansiedade paroxística episódica)"},
            {"codigo": "F51.0", "tipo": "CID-10", "descricao": "Insônia não-orgânica"},
            {"codigo": "F90.0", "tipo": "CID-10", "descricao": "Distúrbios da atividade e da atenção (TDAH)"}
        ],
        alertas_seguranca_telemedicina=[
            "Ideação suicida estruturada com planejamento ou agitação psicomotora intensa contraindica teleconsulta ambulatorial (acionar rede de apoio e emergência psiquiátrica).",
            "Prescrições de receitas controladas (Notificação de Receita A/B) devem respeitar as diretrizes da Anvisa e portaria 344/98 com certificado digital ICP-Brasil."
        ]
    ),
    "dermatologia": EspecialidadeTemplate(
        codigo="dermatologia",
        nome="Dermatologia",
        icone="fa-hand-dots",
        descricao="Afecções cutâneas, acne, dermatites, queda de cabelo e lesões pigmentadas.",
        queixa_sugestoes=[
            "Lesão pigmentada ou nevos com alteração recente (Regra ABCDE)",
            "Acne vulgar facial/tronco persistente",
            "Dermatite atópica / eczemas e prurido cutâneo",
            "Queda capilar acentuada (eflúvio telógeno / alopecia)",
            "Descamação e lesões eritematosas em placas (psoríase)"
        ],
        anamnese_guia="Tempo de evolução da lesão, sintomas associados (prurido, dor, sangramento), exposições solares, uso de cosméticos e tratamentos tópicos prévios.",
        exame_fisico_template="Ectoscopia dermatológica dirigida via teletransmissão HD ou presencial: Fototipo cutâneo Fitzpatrick II-IV. Distribuição das lesões, morfologia primária (mácula, pápula, placa, nódulo), bordas, coloração homogênea ou heterogênea.",
        principais_ciap2_cid10=[
            {"codigo": "L70.0", "tipo": "CID-10", "descricao": "Acne vulgar"},
            {"codigo": "L20.9", "tipo": "CID-10", "descricao": "Dermatite atópica não especificada"},
            {"codigo": "L40.0", "tipo": "CID-10", "descricao": "Psoríase vulgar"},
            {"codigo": "L65.0", "tipo": "CID-10", "descricao": "Eflúvio telógeno"}
        ],
        alertas_seguranca_telemedicina=[
            "Lesões suspeitas de melanoma com alta assimetria e policromia exigem dermatoscopia presencial e biópsia excisional.",
            "Erupções cutâneas agudas com descolamento epidérmico (suspeita de Stevens-Johnson / NET) são emergências médicas presenciais."
        ]
    ),
    "pediatria": EspecialidadeTemplate(
        codigo="pediatria",
        nome="Pediatria",
        icone="fa-child",
        descricao="Puericultura, desenvolvimento infantil, infecções da infância e orientação aos pais.",
        queixa_sugestoes=[
            "Consulta de puericultura e acompanhamento de crescimento",
            "Febre sem foco e irritabilidade na infância",
            "Tosse noturna, coriza e chiado no peito",
            "Dificuldade alimentar e introdução da dieta sólida",
            "Avaliação do calendário vacinal e marcos do desenvolvimento"
        ],
        anamnese_guia="Idade gestacional ao nascer, peso de nascimento, histórico alimentar (aleitamento materno exclusivo vs fórmula), vacinação em dia, marcos de desenvolvimento (sustentar cabeça, sentar, falar).",
        exame_fisico_template="Criança em bom estado geral, reativa, ativa ao colo materno. Sem tiragem intercostal ou batimento de asa nasal. Boa hidratação das mucosas, turgor cutâneo preservado. Peso: __ kg (Percentil __), Estatura: __ cm.",
        principais_ciap2_cid10=[
            {"codigo": "Z00.1", "tipo": "CID-10", "descricao": "Exame de rotina de saúde da criança"},
            {"codigo": "J00", "tipo": "CID-10", "descricao": "Nasofaringite aguda [resfriado comum]"},
            {"codigo": "J20.9", "tipo": "CID-10", "descricao": "Bronquite aguda não especificada"},
            {"codigo": "R50.9", "tipo": "CID-10", "descricao": "Febre não especificada"}
        ],
        alertas_seguranca_telemedicina=[
            "Lactente < 3 meses com febre requer avaliação médica presencial mandatória.",
            "Sinais de desconforto respiratório (tiragem, gemência) ou sonolência excessiva exigem atendimento imediato em pronto-socorro infantil."
        ]
    ),
    "endocrinologia": EspecialidadeTemplate(
        codigo="endocrinologia",
        nome="Endocrinologia & Metabologia",
        icone="fa-dna",
        descricao="Diabetes, tireoidopatias, obesidade e distúrbios hormonais.",
        queixa_sugestoes=[
            "Manejo e titulação de insulina em Diabetes Tipo 1 ou Tipo 2",
            "Hipotireoidismo e ajuste de levotiroxina (TSH/T4L)",
            "Tratamento clínico da obesidade e acompanhamento metabólico",
            "Nódulos tireoidianos e ultrassonografia de tireoide",
            "Osteopenia / Osteoporose e densitometria óssea"
        ],
        anamnese_guia="Histórico glicêmico, mapa de glicemias capilares ou relatório de sensor (Freestyle Libre / Dexcom), dosagem e horário exato de medicações hormonais, ganho ou perda ponderal involuntária.",
        exame_fisico_template="IMC: __ kg/m², Circunferência abdominal: __ cm. Tireoide não palpável ou palpável sem nódulos evidentes, indolor, móvel à deglutição. Ausência de edema de membros inferiores ou estrias violáceas.",
        principais_ciap2_cid10=[
            {"codigo": "E10.9", "tipo": "CID-10", "descricao": "Diabetes mellitus insulino-dependente"},
            {"codigo": "E03.9", "tipo": "CID-10", "descricao": "Hipotireoidismo não especificado"},
            {"codigo": "E66.0", "tipo": "CID-10", "descricao": "Obesidade devida a excesso de calorias"},
            {"codigo": "E04.1", "tipo": "CID-10", "descricao": "Nódulo tireoidiano atóxico único"}
        ],
        alertas_seguranca_telemedicina=[
            "Glicemias capilares > 350 mg/dL com náuseas/vômitos (suspeita de Cetoacidose Diabética) exigem pronto atendimento presencial imediato.",
            "Sintomas de crise tireotóxica (febre alta, taquicardia severa, delírio) contraindicam teleconsulta."
        ]
    )
}


def obter_especialidade(codigo: str) -> EspecialidadeTemplate:
    """Retorna o template da especialidade ou o padrão da clínica médica."""
    return CATALOGO_ESPECIALIDADES.get(codigo, CATALOGO_ESPECIALIDADES["clinica_medica"])


def listar_todas_especialidades() -> List[Dict[str, Any]]:
    """Lista as especialidades disponíveis com seus metadados."""
    return [
        {
            "codigo": esp.codigo,
            "nome": esp.nome,
            "icone": esp.icone,
            "descricao": esp.descricao,
            "queixas": esp.queixa_sugestoes,
            "anamnese_guia": esp.anamnese_guia,
            "exame_fisico_template": esp.exame_fisico_template,
            "codigos_frequentes": esp.principais_ciap2_cid10,
            "alertas_seguranca": esp.alertas_seguranca_telemedicina,
        }
        for esp in CATALOGO_ESPECIALIDADES.values()
    ]
