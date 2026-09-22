from datetime import date
from sqlalchemy.orm import Session
from app.models.estabelecimento import Estabelecimento, Equipe
from app.models.profissional import Profissional
from app.models.cidadao import Cidadao
from app.models.terminologia import CIAP2, CID10

def seed_database(db: Session):
    # 1. Estabelecimento e Equipe
    est = db.query(Estabelecimento).filter(Estabelecimento.cnes == "2761234").first()
    if not est:
        est = Estabelecimento(
            cnes="2761234",
            nome_fantasia="ESF Santos Reis - Montes Claros",
            razao_social="Prefeitura Municipal de Montes Claros - Secretaria de Saúde",
            municipio_ibge="3143302", # Montes Claros - MG
            logradouro="Rua Dr. Santos",
            numero="500",
            bairro="Santos Reis"
        )
        db.add(est)
        db.flush()

        equipe = Equipe(
            ine="0001452361",
            nome="Equipe 01 - Santos Reis",
            tipo_equipe="eSF",
            estabelecimento_id=est.id
        )
        db.add(equipe)

    # 2. Profissionais
    prof_medico = db.query(Profissional).filter(Profissional.cpf == "11122233344").first()
    if not prof_medico:
        prof_medico = Profissional(
            cns="700123456789012",
            cpf="11122233344",
            nome="Dra. Ana Paula Medeiros",
            cbo="225142",
            cbo_descricao="Médica de Família e Comunidade"
        )
        db.add(prof_medico)

    prof_enf = db.query(Profissional).filter(Profissional.cpf == "22233344455").first()
    if not prof_enf:
        prof_enf = Profissional(
            cns="700987654321098",
            cpf="22233344455",
            nome="Enf. Marcos Vinícius Souza",
            cbo="223505",
            cbo_descricao="Enfermeiro da Estratégia de Saúde da Família"
        )
        db.add(prof_enf)

    # 3. Cidadão de Exemplo
    cidadao_exemplo = db.query(Cidadao).filter(Cidadao.cpf == "12345678900").first()
    if not cidadao_exemplo:
        cidadao_exemplo = Cidadao(
            cns="898000123456789",
            cpf="12345678900",
            nome_completo="Sebastião Ferreira Santos",
            nome_mae="Maria de Lourdes Santos",
            data_nascimento=date(1968, 5, 14),
            sexo="M",
            raca_cor="Parda",
            telefone="38999887766",
            logradouro="Rua Belo Horizonte",
            numero="120",
            bairro="Major Prates",
            municipio_ibge="3143302",
            hipertenso=True,
            diabetico=False,
            fumante=False,
            alergias="Dipirona"
        )
        db.add(cidadao_exemplo)

    # 4. Terminologias CIAP-2 (Atenção Primária à Saúde)
    ciap2_lista = [
        ("A03", "Febre", "Geral e inespecífico"),
        ("A80", "Traumatismo / acidente não especificado", "Geral e inespecífico"),
        ("A97", "Sem doença / exame preventivo", "Geral e inespecífico"),
        ("D01", "Dor abdominal generalizada / cólica", "Aparelho digestivo"),
        ("D08", "Flatulência / gases / eructação", "Aparelho digestivo"),
        ("D11", "Diarreia", "Aparelho digestivo"),
        ("K86", "Hipertensão arterial sem complicações", "Aparelho circulatório"),
        ("K87", "Hipertensão arterial com complicações", "Aparelho circulatório"),
        ("L03", "Sintoma/queixa da lombar", "Aparelho musculoesquelético"),
        ("L04", "Sintoma/queixa torácica", "Aparelho musculoesquelético"),
        ("P76", "Transtorno depressivo", "Psicológico"),
        ("P01", "Sensação de ansiedade / nervosismo / tensão", "Psicológico"),
        ("R05", "Tosse", "Aparelho respiratório"),
        ("R21", "Sintoma/queixa da garganta", "Aparelho respiratório"),
        ("R74", "Infecção aguda das vias aéreas superiores (IVAS)", "Aparelho respiratório"),
        ("R96", "Asma", "Aparelho respiratório"),
        ("S06", "Erupção cutânea", "Pele"),
        ("T90", "Diabetes não insulino-dependente", "Endócrino, metabólico e nutricional"),
        ("T91", "Deficiência vitamínica / nutricional", "Endócrino, metabólico e nutricional"),
        ("U71", "Cistite / outra infecção urinária", "Aparelho urinário"),
        ("W78", "Gravidez confirmada", "Gravidez, parto, planejamento familiar"),
    ]
    for cod, desc, cap in ciap2_lista:
        if not db.query(CIAP2).filter(CIAP2.codigo == cod).first():
            db.add(CIAP2(codigo=cod, descricao=desc, capitulo=cap, ativo=True))

    # 5. Terminologias CID-10 mais prevalentes na APS
    cid10_lista = [
        ("I10", "Hipertensão essencial (primária)"),
        ("I11", "Doença cardíaca hipertensiva"),
        ("E11", "Diabetes mellitus não-insulino-dependente"),
        ("E10", "Diabetes mellitus insulino-dependente"),
        ("E66", "Obesidade"),
        ("J00", "Nasofaringite aguda [resfriado comum]"),
        ("J01", "Sinusite aguda"),
        ("J03", "Amigdalite aguda"),
        ("J06", "Infecções agudas das vias aéreas superiores de localizações múltiplas e não especificadas"),
        ("J20", "Bronquite aguda"),
        ("J45", "Asma"),
        ("F32", "Episódios depressivos"),
        ("F41", "Outros transtornos ansiosos"),
        ("K29", "Gastrite e duodenite"),
        ("M54", "Dorsalgia (inclui lombalgia)"),
        ("N39.0", "Infecção do trato urinário de localização não especificada"),
        ("Z00", "Exame geral e investigação de pessoas sem queixas ou diagnóstico relatado"),
        ("Z34", "Supervisão de gravidez normal"),
    ]
    for cod, desc in cid10_lista:
        if not db.query(CID10).filter(CID10.codigo == cod).first():
            db.add(CID10(codigo=cod, descricao=desc, ativo=True))

    db.commit()
