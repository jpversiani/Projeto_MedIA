"""
Seed de Multi-Clínica, Multi-Médico e Usuários de Demonstração para Teste do MVP.
"""
from app.core.database import SessionLocal, Base, engine
from app.models.estabelecimento import Estabelecimento, Equipe
from app.models.profissional import Profissional
from app.models.usuario import Usuario, VinculoClinica, PapelUsuarioEnum
from app.services.auth_service import hash_password


def seed_multiclinica():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Estabelecimentos / Clínicas
        clinica1 = db.query(Estabelecimento).filter(Estabelecimento.cnes == "3180115").first()
        if not clinica1:
            clinica1 = Estabelecimento(
                cnes="3180115",
                nome_fantasia="Consultório Particular MedIA",
                razao_social="MedIA Saúde Inteligente Ltda",
                municipio_ibge="3143302",
                logradouro="Avenida Afonso Pena",
                numero="1020",
                bairro="Ibituruna"
            )
            db.add(clinica1)
            db.commit()
            db.refresh(clinica1)

        clinica2 = db.query(Estabelecimento).filter(Estabelecimento.cnes == "3112307").first()
        if not clinica2:
            clinica2 = Estabelecimento(
                cnes="3112307",
                nome_fantasia="Centro Integrado de Saúde da Família",
                razao_social="CISF Capelinha Serviços Médicos",
                municipio_ibge="3112307",
                logradouro="Rua Tiradentes",
                numero="450",
                bairro="Centro"
            )
            db.add(clinica2)
            db.commit()
            db.refresh(clinica2)

        # 2. Profissionais Médicos
        med1 = db.query(Profissional).filter(Profissional.cpf == "09876543211").first()
        if not med1:
            med1 = Profissional(
                cns="702000123456789",
                cpf="09876543211",
                nome="Dr. João Paulo Versiani",
                cbo="225142",
                cbo_descricao="Médico de Família e Comunidade (CRM/MG 65432)"
            )
            db.add(med1)
            db.commit()
            db.refresh(med1)

        med2 = db.query(Profissional).filter(Profissional.cpf == "12312312399").first()
        if not med2:
            med2 = Profissional(
                cns="803000987654321",
                cpf="12312312399",
                nome="Dra. Letícia Mendes",
                cbo="225125",
                cbo_descricao="Clínica Médica / Atenção Primária (CRM/MG 78910)"
            )
            db.add(med2)
            db.commit()
            db.refresh(med2)

        # 3. Usuários e Vínculos Multi-Clínica
        users_data = [
            ("dr.versiani@media-saude.com.br", "Dr. João Paulo Versiani", PapelUsuarioEnum.MEDICO, med1.id, True),
            ("dra.leticia@media-saude.com.br", "Dra. Letícia Mendes", PapelUsuarioEnum.MEDICO, med2.id, False),
            ("recepcao@media-saude.com.br", "Maria Auxiliadora (Recepção)", PapelUsuarioEnum.RECEPCAO, None, False),
            ("admin@media-saude.com.br", "Carlos Eduardo (Gestor)", PapelUsuarioEnum.ADMIN, None, True),
        ]

        for email, nome, papel, prof_id, is_super in users_data:
            user = db.query(Usuario).filter(Usuario.email == email).first()
            if not user:
                user = Usuario(
                    email=email,
                    nome=nome,
                    hashed_password=hash_password("media123"), # Senha padrão para testes locais
                    sso_provider="local",
                    is_active=True,
                    is_superuser=is_super
                )
                db.add(user)
                db.commit()
                db.refresh(user)

                # Vincula à Clínica 1 (Consultório Particular) como padrão
                v1 = VinculoClinica(
                    usuario_id=user.id,
                    estabelecimento_id=clinica1.id,
                    papel=papel,
                    profissional_id=prof_id,
                    is_default=True
                )
                db.add(v1)

                # Vincula também à Clínica 2 (Capelinha) para demonstrar multi-tenancy!
                v2 = VinculoClinica(
                    usuario_id=user.id,
                    estabelecimento_id=clinica2.id,
                    papel=papel,
                    profissional_id=prof_id,
                    is_default=False
                )
                db.add(v2)
                db.commit()

        print("✔ Seed de Multi-Clínica, Médicos e Usuários concluído com sucesso!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_multiclinica()
