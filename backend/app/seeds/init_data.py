from datetime import date

from sqlalchemy.orm import Session

from app.models.cidadao import Cidadao
from app.models.estabelecimento import Estabelecimento, Equipe
from app.models.profissional import Profissional
from app.models.terminologia import CIAP2, CID10

def seed_database(db: Session):
    # 1. Estabelecimento e Equipe
    est = db.query(Estabelecimento).first()
    if not est:
        est = Estabelecimento(
            cnes="3180115",
            nome_fantasia="ESFSB M1 CIDADE CRISTO REI",
            razao_social="Prefeitura Municipal de Montes Claros - CNPJ 22.678.874/0001-35",
            municipio_ibge="3143302", # Montes Claros - MG
            logradouro="Rua Principal",
            numero="S/N",
            bairro="Cidade Cristo Rei"
        )
        db.add(est)
        db.flush()

        equipe = Equipe(
            ine="0001452361",
            nome="Equipe 01 - Cidade Cristo Rei",
            tipo_equipe="eSF",
            estabelecimento_id=est.id
        )
        db.add(equipe)
    else:
        est.cnes = "3180115"
        est.nome_fantasia = "ESFSB M1 CIDADE CRISTO REI"
        est.razao_social = "Prefeitura Municipal de Montes Claros - CNPJ 22.678.874/0001-35"
        est.bairro = "Cidade Cristo Rei"
        if est.equipes:
            est.equipes[0].nome = "Equipe 01 - Cidade Cristo Rei"


    # 2. Profissionais
    prof_medico = db.query(Profissional).filter(Profissional.cpf == "11122233344").first()
    if not prof_medico:
        prof_medico = Profissional(
            cns="700123456789012",
            cpf="11122233344",
            nome="Dra. Francelli Neves Versiani",
            cbo="225142",
            cbo_descricao="Médica de Família e Comunidade / Clínica Geral"
        )
        db.add(prof_medico)
    else:
        prof_medico.nome = "Dra. Francelli Neves Versiani"
        prof_medico.cbo_descricao = "Médica de Família e Comunidade / Clínica Geral"


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
    # 3. Cidadãos e Pacientes do Consultório
    pacientes_iniciais = [
        {
            "cpf": "12345678900",
            "cns": "898000123456789",
            "nome_completo": "Sebastião Ferreira Santos",
            "nome_mae": "Maria de Lourdes Santos",
            "data_nascimento": date(1968, 5, 14),
            "sexo": "M",
            "raca_cor": "Parda",
            "telefone": "38999887766",
            "logradouro": "Rua Belo Horizonte",
            "numero": "120",
            "bairro": "Major Prates",
            "municipio_ibge": "3143302",
            "hipertenso": True,
            "diabetico": False,
            "fumante": False,
            "alergias": "Dipirona",
        },
        {
            "cpf": "12345678901",
            "cns": "898000123456701",
            "nome_completo": "Mariana Souza Alencar",
            "nome_mae": "Carla Regina Alencar",
            "data_nascimento": date(1992, 8, 22),
            "sexo": "F",
            "raca_cor": "Branca",
            "telefone": "38998765432",
            "logradouro": "Rua Santa Maria",
            "numero": "450",
            "bairro": "Todos os Santos",
            "municipio_ibge": "3143302",
            "hipertenso": False,
            "diabetico": False,
            "fumante": False,
            "alergias": "Penicilina",
        },
        {
            "cpf": "98765432100",
            "cns": "898000123456702",
            "nome_completo": "Roberto Carlos Fagundes",
            "nome_mae": "Aparecida Fagundes",
            "data_nascimento": date(1961, 3, 10),
            "sexo": "M",
            "raca_cor": "Parda",
            "telefone": "38991234567",
            "logradouro": "Avenida Sanitária",
            "numero": "1002",
            "bairro": "Centro",
            "municipio_ibge": "3143302",
            "hipertenso": True,
            "diabetico": True,
            "fumante": False,
            "alergias": "Nenhuma relatada",
        },
        {
            "cpf": "45678912344",
            "cns": "898000123456703",
            "nome_completo": "Juliana Mendes Prado",
            "nome_mae": "Cláudia Mendes",
            "data_nascimento": date(1987, 11, 5),
            "sexo": "F",
            "raca_cor": "Parda",
            "telefone": "38988776655",
            "logradouro": "Rua Dr. Veloso",
            "numero": "310",
            "bairro": "Centro",
            "municipio_ibge": "3143302",
            "hipertenso": False,
            "diabetico": False,
            "fumante": False,
            "alergias": "Sulfa",
        },
        {
            "cpf": "11122233344",
            "cns": "898000123456704",
            "nome_completo": "Carlos Eduardo Pereira",
            "nome_mae": "Helena Pereira",
            "data_nascimento": date(1979, 6, 18),
            "sexo": "M",
            "raca_cor": "Branca",
            "telefone": "38999112233",
            "logradouro": "Rua Simeão Ribeiro",
            "numero": "85",
            "bairro": "Melo",
            "municipio_ibge": "3143302",
            "hipertenso": False,
            "diabetico": False,
            "fumante": False,
            "alergias": "Nenhuma",
        },
        {
            "cpf": "55566677701",
            "cns": "898000123456705",
            "nome_completo": "Camila Guimarães Ribeiro",
            "nome_mae": "Patrícia Guimarães",
            "data_nascimento": date(1995, 1, 30),
            "sexo": "F",
            "raca_cor": "Parda",
            "telefone": "38992345678",
            "logradouro": "Rua Dom Pedro II",
            "numero": "215",
            "bairro": "Ibituruna",
            "municipio_ibge": "3143302",
            "hipertenso": False,
            "diabetico": False,
            "fumante": False,
            "alergias": "AINEs (Ibuprofeno)",
        },
        {
            "cpf": "99988877701",
            "cns": "898000123456706",
            "nome_completo": "Beatriz Viana Santos",
            "nome_mae": "Rosana Viana",
            "data_nascimento": date(2001, 9, 12),
            "sexo": "F",
            "raca_cor": "Branca",
            "telefone": "38999998888",
            "logradouro": "Rua Coronel Altino",
            "numero": "98",
            "bairro": "Funcionários",
            "municipio_ibge": "3143302",
            "hipertenso": False,
            "diabetico": False,
            "fumante": False,
            "alergias": "Nenhuma",
        },
    ]

    for p_data in pacientes_iniciais:
        cid_existente = db.query(Cidadao).filter(
            (Cidadao.cpf == p_data["cpf"]) | (Cidadao.cns == p_data["cns"])
        ).first()
        if not cid_existente:
            db.add(Cidadao(**p_data))
        else:
            for k, v in p_data.items():
                setattr(cid_existente, k, v)
    db.flush()

    # 3.1 Operadoras de Saúde e Planos TISS
    from app.models.convenios import Operadora, Plano, GuiaTISS, GuiaStatus, TipoGuia, LancamentoFinanceiro, LancamentoTipo, LancamentoStatus
    from datetime import datetime, time, UTC
    import uuid

    ops_data = [
        ("Unimed", "305685", "12345678000199", "Unimed Pleno"),
        ("Bradesco Saúde", "005711", "98765432000188", "Bradesco Top Nacional"),
        ("Amil", "326305", "11223344000177", "Amil Fácil S80"),
        ("SulAmérica", "006246", "55667788000166", "SulAmérica Especial"),
    ]

    for op_nome, reg_ans, cnpj_op, plano_nome in ops_data:
        op = db.query(Operadora).filter(Operadora.registro_ans == reg_ans).first()
        if not op:
            op = Operadora(nome=op_nome, registro_ans=reg_ans, cnpj=cnpj_op, ativo=True)
            db.add(op)
            db.flush()
        plano = db.query(Plano).filter(Plano.operadora_id == op.id).first()
        if not plano:
            db.add(Plano(operadora_id=op.id, nome=plano_nome, codigo_plano=f"PL-{op.id:03d}", tipo="AMBULATORIAL", ativo=True))
    db.flush()

    # 3.2 Agendamentos Iniciais do Dia
    from app.models.agendamento import Agendamento, StatusAgendamento, TipoAtendimento

    mariana = db.query(Cidadao).filter(Cidadao.cpf == "12345678901").first()
    roberto = db.query(Cidadao).filter(Cidadao.cpf == "98765432100").first()
    juliana = db.query(Cidadao).filter(Cidadao.cpf == "45678912344").first()
    carlos = db.query(Cidadao).filter(Cidadao.cpf == "11122233344").first()
    camila = db.query(Cidadao).filter(Cidadao.cpf == "55566677701").first()

    agenda_inicial = [
        (mariana, TipoAtendimento.TELEMEDICINA, time(9, 0), "Ansiedade e insônia há 3 semanas", 350.0, "Psiquiatria", StatusAgendamento.AGENDADO),
        (roberto, TipoAtendimento.PRESENCIAL, time(10, 0), "Controle de Hipertensão e retorno de exames", 400.0, "Cardiologia", StatusAgendamento.SALA_DE_ESPERA),
        (juliana, TipoAtendimento.TELEMEDICINA, time(11, 0), "Lesões pruriginosas em membros superiores", 350.0, "Dermatologia", StatusAgendamento.AGENDADO),
        (carlos, TipoAtendimento.PRESENCIAL, time(14, 0), "Check-up preventivo anual e cansaço fácil", 300.0, "Clínica Médica", StatusAgendamento.AGENDADO),
        (camila, TipoAtendimento.TELEMEDICINA, time(15, 30), "Ajuste de dose de levotiroxina", 380.0, "Endocrinologia", StatusAgendamento.AGENDADO),
    ]

    for pac, tipo_at, hora, queixa, val, esp, st in agenda_inicial:
        if pac and not db.query(Agendamento).filter(Agendamento.cidadao_id == pac.id).first():
            ag = Agendamento(
                codigo=f"AG-{uuid.uuid4().hex[:6].upper()}",
                cidadao_id=pac.id,
                profissional_id=prof_medico.id if prof_medico else None,
                estabelecimento_id=est.id if est else None,
                tipo=tipo_at.value,
                status=st.value,
                data_consulta=date.today(),
                horario=hora,
                duracao_minutos=30,
                especialidade=esp,
                motivo_queixa=queixa,
                valor_consulta=val,
                codigo_sala_telemedicina=f"sala_{uuid.uuid4().hex[:10]}" if tipo_at == TipoAtendimento.TELEMEDICINA else None,
            )
            db.add(ag)
    db.flush()

    # 3.3 Guias TISS e Lançamentos Iniciais
    unimed_plano = db.query(Plano).first()
    if unimed_plano and not db.query(GuiaTISS).first():
        guias_iniciais = [
            ("TISS-2026-0001", "Mariana Souza Alencar", "12345678901", "Unimed", 250.0, GuiaStatus.AUTORIZADA),
            ("TISS-2026-0002", "Roberto Carlos Fagundes", "98765432100", "Amil", 180.50, GuiaStatus.ENVIADA),
            ("TISS-2026-0003", "Juliana Mendes Prado", "45678912344", "Bradesco Saúde", 320.0, GuiaStatus.PAGA),
            ("TISS-2026-0004", "Carlos Eduardo Pereira", "11122233344", "SulAmérica", 280.0, GuiaStatus.PAGA),
            ("TISS-2026-0005", "Camila Guimarães Ribeiro", "55566677701", "Unimed", 350.0, GuiaStatus.GERADA),
        ]
        for num, pac_nome, pac_cpf, op_ref, vlr, st_guia in guias_iniciais:
            p_ref = db.query(Plano).join(Operadora).filter(Operadora.nome.ilike(f"%{op_ref}%")).first() or unimed_plano
            g = GuiaTISS(
                numero_guia=num,
                tipo_guia=TipoGuia.CONSULTA,
                plano_id=p_ref.id,
                paciente_nome=pac_nome,
                paciente_cpf=pac_cpf,
                numero_carteira="00192837465",
                status=st_guia,
                procedimento_tuss="10101012",
                valor_total=vlr,
                data_emissao=datetime.now(UTC),
            )
            db.add(g)
            db.flush()

            db.add(LancamentoFinanceiro(
                guia_id=g.id,
                paciente_cpf=pac_cpf,
                paciente_nome=pac_nome,
                tipo=LancamentoTipo.CONVENIO,
                valor=vlr,
                descricao=f"Guia TISS Consulta {num} - {op_ref}",
                status=LancamentoStatus.PAGO if st_guia == GuiaStatus.PAGA else LancamentoStatus.PENDENTE,
                recibo_numero=f"REC-2026-{g.id:03d}",
                data_lancamento=datetime.now(UTC),
            ))
    db.flush()

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
