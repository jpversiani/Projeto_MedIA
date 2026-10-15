"""
Repositório de Convênios, Guias TISS e Lançamentos Financeiros.
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.convenios import (
    GuiaStatus,
    GuiaTISS,
    LancamentoFinanceiro,
    LancamentoStatus,
    LancamentoTipo,
    Operadora,
    Plano,
    TipoGuia,
)
from app.services.tiss_generator import TISSGenerator, gerar_numero_guia

class ConveniosRepository:
    """Repositório de acesso e persistência para Convênios e Faturamento TISS."""

    @staticmethod
    def criar_operadora(
        db: Session,
        nome: str,
        registro_ans: str,
        cnpj: str,
        contato_email: str | None = None,
    ) -> Operadora:
        operadora = Operadora(
            nome=nome,
            registro_ans=registro_ans,
            cnpj=cnpj,
            contato_email=contato_email,
            ativo=True,
        )
        db.add(operadora)
        db.commit()
        db.refresh(operadora)
        return operadora

    @staticmethod
    def obter_operadora(db: Session, operadora_id: int) -> Operadora | None:
        return db.scalar(select(Operadora).where(Operadora.id == operadora_id))

    @staticmethod
    def listar_operadoras(db: Session, apenas_ativas: bool = True) -> list[Operadora]:
        query = select(Operadora)
        if apenas_ativas:
            query = query.where(Operadora.ativo.is_(True))
        return list(db.scalars(query).all())

    @staticmethod
    def criar_plano(
        db: Session,
        operadora_id: int,
        nome: str,
        codigo_plano: str,
        tipo: str = "AMBULATORIAL",
    ) -> Plano:
        plano = Plano(
            operadora_id=operadora_id,
            nome=nome,
            codigo_plano=codigo_plano,
            tipo=tipo,
            ativo=True,
        )
        db.add(plano)
        db.commit()
        db.refresh(plano)
        return plano

    @staticmethod
    def listar_planos(db: Session, operadora_id: int | None = None) -> list[Plano]:
        query = select(Plano)
        if operadora_id:
            query = query.where(Plano.operadora_id == operadora_id)
        return list(db.scalars(query).all())

    @staticmethod
    def emitir_guia_consulta_tiss(
        db: Session,
        plano_id: int,
        paciente_nome: str,
        numero_carteira: str,
        paciente_cpf: str | None = None,
        paciente_cns: str | None = None,
        ciap2: str | None = None,
        cid10: str | None = None,
        procedimento_tuss: str = "10101012",
        valor: float = 150.0,
        atendimento_id: int | None = None,
    ) -> GuiaTISS:
        plano = db.scalar(select(Plano).where(Plano.id == plano_id))
        registro_ans = plano.operadora.registro_ans if plano and plano.operadora else "000000"
        
        num_guia = gerar_numero_guia()
        xml_conteudo = TISSGenerator.gerar_guia_consulta_xml(
            numero_guia=num_guia,
            operadora_registro_ans=registro_ans,
            paciente_nome=paciente_nome,
            numero_carteira=numero_carteira,
            paciente_cpf=paciente_cpf,
            paciente_cns=paciente_cns,
            cid10=cid10,
            ciap2=ciap2,
            procedimento_tuss=procedimento_tuss,
            valor_procedimento=valor,
        )

        guia = GuiaTISS(
            numero_guia=num_guia,
            tipo_guia=TipoGuia.CONSULTA,
            plano_id=plano_id,
            atendimento_id=atendimento_id,
            paciente_cns=paciente_cns,
            paciente_cpf=paciente_cpf,
            paciente_nome=paciente_nome,
            numero_carteira=numero_carteira,
            status=GuiaStatus.GERADA,
            ciap2_codigo=ciap2,
            cid10_codigo=cid10,
            procedimento_tuss=procedimento_tuss,
            valor_total=valor,
            xml_tiss=xml_conteudo,
        )
        db.add(guia)
        db.commit()
        db.refresh(guia)

        # Registra lançamento financeiro atrelado
        lancamento = LancamentoFinanceiro(
            guia_id=guia.id,
            atendimento_id=atendimento_id,
            paciente_cpf=paciente_cpf or "00000000000",
            paciente_nome=paciente_nome,
            tipo=LancamentoTipo.CONVENIO,
            valor=valor,
            descricao=f"Guia TISS Consulta {num_guia}",
            status=LancamentoStatus.PENDENTE,
        )
        db.add(lancamento)
        db.commit()

        return guia

    @staticmethod
    def obter_guia(db: Session, guia_id: int) -> GuiaTISS | None:
        return db.scalar(select(GuiaTISS).where(GuiaTISS.id == guia_id))

    @staticmethod
    def atualizar_status_guia(
        db: Session,
        guia_id: int,
        novo_status: GuiaStatus,
    ) -> GuiaTISS | None:
        guia = db.scalar(select(GuiaTISS).where(GuiaTISS.id == guia_id))
        if guia:
            guia.status = novo_status
            if novo_status == GuiaStatus.PAGA:
                for lanc in guia.lancamentos:
                    lanc.status = LancamentoStatus.PAGO
            elif novo_status == GuiaStatus.GLOSADA:
                for lanc in guia.lancamentos:
                    lanc.status = LancamentoStatus.GLOSADO
            db.commit()
            db.refresh(guia)
        return guia

    @staticmethod
    def registrar_recibo_particular_dmed(
        db: Session,
        paciente_nome: str,
        paciente_cpf: str,
        valor: float,
        descricao: str = "Consulta Médica Particular",
        atendimento_id: int | None = None,
    ) -> LancamentoFinanceiro:
        recibo_num = f"REC-{datetime.now(datetime.UTC).strftime('%Y%m')}-{gerar_numero_guia()[-6:]}"
        lancamento = LancamentoFinanceiro(
            atendimento_id=atendimento_id,
            paciente_cpf=paciente_cpf,
            paciente_nome=paciente_nome,
            tipo=LancamentoTipo.PARTICULAR,
            valor=valor,
            descricao=descricao,
            status=LancamentoStatus.PAGO,
            recibo_numero=recibo_num,
            cpf_cnpj_pagador=paciente_cpf,
            nome_pagador=paciente_nome,
        )
        db.add(lancamento)
        db.commit()
        db.refresh(lancamento)
        return lancamento

    @staticmethod
    def listar_lancamentos(
        db: Session,
        status: LancamentoStatus | None = None,
    ) -> list[LancamentoFinanceiro]:
        query = select(LancamentoFinanceiro)
        if status:
            query = query.where(LancamentoFinanceiro.status == status)
        return list(db.scalars(query).all())
