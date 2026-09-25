"""
Gerador de População Sintética de Pacientes SUS / APS (Norte de Minas e Vale do Jequitinhonha)
Cria 300 pacientes realistas distribuídos epidemiologicamente segundo a pirâmide do PSF/ESF:
- Montes Claros (Polo principal)
- Cidades do Vale do Jequitinhonha: Capelinha, Diamantina, Turmalina, Veredinha, Água Boa
- Outras do Norte de Minas: Bocaiúva, Janaúba, Januária, Salinas, Taiobeiras
- Referências da Capital: Belo Horizonte

Perfil demográfico epidemiológico:
- Crianças (0-11 anos): ~15%
- Adolescentes / Jovens (12-24 anos): ~15%
- Adultos (25-59 anos): ~45% (incluindo ~6% de gestantes em idade fértil)
- Idosos (60+ anos): ~25%
- Prevalência de Hipertensão (~28%) e Diabetes (~10%)
- Alergias comuns na prática médica ambulatorial (Penicilina, Dipirona, AINEs, Sulfa)
"""

import random
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.cidadao import Cidadao
from app.core.database import SessionLocal

# Listas de Nomes Reais Brasileiros
NOMES_MASCULINOS = [
    "João", "José", "Antônio", "Francisco", "Carlos", "Paulo", "Pedro", "Lucas", "Luiz", "Marcos",
    "Gabriel", "Rafael", "Daniel", "Marcelo", "Bruno", "Eduardo", "Felipe", "Raimundo", "Rodrigo", "Manoel",
    "Mateus", "André", "Fernando", "Fábio", "Leonardo", "Gustavo", "Guilherme", "Leandro", "Tiago", "Anderson",
    "Sebastião", "Geraldo", "Vicente", "Otávio", "Bernardo", "Enzo", "Arthur", "Davi", "Heitor", "Miguel",
    "Bento", "Joaquim", "Valdir", "Ailton", "Aparecido", "Edilson", "Ademir", "Cleber", "Ronaldo", "Valdemar"
]

NOMES_FEMININOS = [
    "Maria", "Ana", "Francisca", "Antônia", "Adriana", "Juliana", "Márcia", "Fernanda", "Patrícia", "Aline",
    "Camila", "Amanda", "Bruna", "Jéssica", "Letícia", "Julia", "Luciana", "Vanessa", "Mariana", "Gabriela",
    "Vitória", "Larissa", "Daniela", "Beatriz", "Rita", "Aparecida", "Cleuza", "Lourdes", "Sônia", "Elizete",
    "Helena", "Alice", "Laura", "Manuela", "Sophia", "Isabella", "Valentina", "Lorena", "Giovanna", "Lívia",
    "Tereza", "Raimunda", "Conceição", "Socorro", "Fátima", "Ivone", "Neuza", "Marlene", "Nilza", "Zilda"
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes",
    "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa",
    "Rocha", "Dias", "Nascimento", "Andrade", "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas",
    "Cardoso", "Ramos", "Gonçalves", "Santana", "Teixeira", "Macedo", "Guimarães", "Neves", "Versiani", "Quadros",
    "Figueiredo", "Dutra", "Barreto", "Pinto", "Correia", "Siqueira", "Magalhães", "Cunha", "Borges", "Mota"
]

CIDADES_NORTE_MINAS_JEQUITINHONHA = [
    # Polo
    {"nome": "Montes Claros", "ibge": "3143302", "cep_base": "39400", "peso": 45, "bairros": ["Major Prates", "Independência", "Maracanã", "Morada do Parque", "Cidade Cristo Rei", "Delfino Magalhães", "Vila Regina", "Ibituruna", "Santos Reis", "Vila Mauricéia"]},
    # Vale do Jequitinhonha
    {"nome": "Capelinha", "ibge": "3112307", "cep_base": "39680", "peso": 10, "bairros": ["Centro", "Aparecida", "Planalto", "Maria Lúcia", "Piedade", "São Geraldo"]},
    {"nome": "Diamantina", "ibge": "3121605", "cep_base": "39100", "peso": 8, "bairros": ["Centro", "Palha", "Largo Dom João", "Consolação", "Rio Grande"]},
    {"nome": "Turmalina", "ibge": "3169703", "cep_base": "39660", "peso": 7, "bairros": ["Centro", "Campo", "Pau D'Óleo", "Nova Turmalina"]},
    {"nome": "Veredinha", "ibge": "3171154", "cep_base": "39665", "peso": 5, "bairros": ["Centro", "Planalto", "Zona Rural Veredinha"]},
    {"nome": "Água Boa", "ibge": "3100609", "cep_base": "39790", "peso": 5, "bairros": ["Centro", "Vila Nova", "Bairro das Flores"]},
    # Outras do Norte de Minas
    {"nome": "Bocaiúva", "ibge": "3107307", "cep_base": "39390", "peso": 5, "bairros": ["Centro", "Alto da Boa Vista", "Nossa Senhora Aparecida"]},
    {"nome": "Janaúba", "ibge": "3135100", "cep_base": "39440", "peso": 5, "bairros": ["Centro", "Rio Novo", "Barbosa", "Dente Grande"]},
    {"nome": "Januária", "ibge": "3135209", "cep_base": "39480", "peso": 3, "bairros": ["Centro", "Brejo do Amparo", "Cerâmica"]},
    {"nome": "Salinas", "ibge": "3157005", "cep_base": "39560", "peso": 3, "bairros": ["Centro", "Santo Antônio", "São Geraldo"]},
    {"nome": "Taiobeiras", "ibge": "3168002", "cep_base": "39550", "peso": 2, "bairros": ["Centro", "Sagrada Família", "Nossa Senhora de Fátima"]},
    # Capital (Referência de Regulação)
    {"nome": "Belo Horizonte", "ibge": "3106200", "cep_base": "30100", "peso": 2, "bairros": ["Savassi", "Barro Preto", "Santa Efigênia", "Centro"]},
]

ALERGIAS_COMUNS = [
    None, None, None, None, None,  # Maioria sem alergia
    "Dipirona",
    "Penicilina / Amoxicilina",
    "Anti-inflamatórios Não Esteroidais (AINEs / Ibuprofeno)",
    "Sulfas (Sulfametoxazol)",
    "Iodo / Frutos do Mar",
    "Aspirina (AAS)",
    "Dipirona e Paracetamol"
]

LOGRADOUROS = [
    "Rua Minas Gerais", "Avenida Afonso Pena", "Rua Santa Maria", "Rua São Pedro",
    "Avenida Santos Dumont", "Rua Tiradentes", "Rua Marechal Deodoro", "Rua Bahia",
    "Avenida Deputado Esteves Rodrigues", "Rua Dr. Santos", "Rua Coronel Altino de Freitas",
    "Avenida Geraldo Athayde", "Rua Padre Augusto", "Rua Bocaiúva", "Rua Diamantina"
]


def gerar_cpf_valido() -> str:
    """Gera um CPF sintético com dígitos verificadores matematicamente válidos."""
    nove_digitos = [random.randint(0, 9) for _ in range(9)]
    
    # 1º dígito
    soma1 = sum(d * peso for d, peso in zip(nove_digitos, range(10, 1, -1)))
    resto1 = soma1 % 11
    d1 = 0 if resto1 < 2 else 11 - resto1
    
    # 2º dígito
    dez_digitos = nove_digitos + [d1]
    soma2 = sum(d * peso for d, peso in zip(dez_digitos, range(11, 1, -1)))
    resto2 = soma2 % 11
    d2 = 0 if resto2 < 2 else 11 - resto2
    
    return "".join(map(str, dez_digitos + [d2]))


def gerar_cns_valido() -> str:
    """Gera número de Cartão Nacional de Saúde (CNS) no padrão de 15 dígitos."""
    prefixo = random.choice(["1", "2", "7", "8"])
    meio = "".join(str(random.randint(0, 9)) for _ in range(13))
    raw = prefixo + meio
    # Ajuste de dígito verificador
    soma = sum(int(raw[i]) * (15 - i) for i in range(14))
    resto = soma % 11
    dv = (11 - resto) % 11
    if dv == 10:
        dv = 0
    return raw + str(dv)


def gerar_pacientes_sinteticos(quantidade: int = 300) -> list[Cidadao]:
    pacientes = []
    hoje = date.today()
    
    # Pool de cidades ponderado
    cidades_pool = []
    for c in CIDADES_NORTE_MINAS_JEQUITINHONHA:
        cidades_pool.extend([c] * c["peso"])

    for _ in range(quantidade):
        cidade = random.choice(cidades_pool)
        
        # Perfil etário conforme PSF
        faixa = random.choices(["crianca", "jovem", "adulto", "idoso"], weights=[15, 15, 45, 25])[0]
        if faixa == "crianca":
            idade = random.randint(0, 11)
        elif faixa == "jovem":
            idade = random.randint(12, 24)
        elif faixa == "adulto":
            idade = random.randint(25, 59)
        else:
            idade = random.randint(60, 92)
            
        data_nasc = hoje - timedelta(days=idade * 365 + random.randint(0, 364))
        sexo = random.choice(["M", "F"])
        
        if sexo == "M":
            nome = f"{random.choice(NOMES_MASCULINOS)} {random.choice(SOBRENOMES)} {random.choice(SOBRENOMES)}"
        else:
            nome = f"{random.choice(NOMES_FEMININOS)} {random.choice(SOBRENOMES)} {random.choice(SOBRENOMES)}"
            
        nome_mae = f"{random.choice(NOMES_FEMININOS)} {random.choice(SOBRENOMES)} {random.choice(SOBRENOMES)}"
        
        # Prevalências clínicas SUS
        hipertenso = False
        diabetico = False
        gestante = False
        fumante = False
        
        if idade >= 35:
            hipertenso = random.random() < (0.45 if idade >= 60 else 0.22)
            diabetico = random.random() < (0.22 if idade >= 60 else 0.08)
            fumante = random.random() < 0.14
        
        if sexo == "F" and 16 <= idade <= 42:
            gestante = random.random() < 0.08
            if gestante:
                fumante = False
                
        raca = random.choices(["Parda", "Preta", "Branca", "Indígena", "Amarela"], weights=[65, 18, 15, 1, 1])[0]
        
        # Endereço
        bairro = random.choice(cidade["bairros"])
        cep = f"{cidade['cep_base']}{random.randint(100, 999)}"
        logradouro = random.choice(LOGRADOUROS)
        num = str(random.randint(10, 1850)) if random.random() > 0.1 else "S/N"
        ddd = "38" if cidade["nome"] != "Belo Horizonte" else "31"
        tel = f"({ddd}) 9{random.randint(8000, 9999)}-{random.randint(1000, 9999)}"
        
        alergia = random.choice(ALERGIAS_COMUNS)
        
        cidadao = Cidadao(
            cns=gerar_cns_valido(),
            cpf=gerar_cpf_valido(),
            nome_completo=nome,
            nome_social=None,
            nome_mae=nome_mae,
            data_nascimento=data_nasc,
            sexo=sexo,
            raca_cor=raca,
            telefone=tel,
            email=f"{nome.lower().replace(' ', '.')[:20]}@gmail.com",
            cep=cep,
            logradouro=logradouro,
            numero=num,
            complemento="Apto " + str(random.randint(101, 404)) if random.random() < 0.2 else None,
            bairro=bairro,
            municipio_ibge=cidade["ibge"],
            hipertenso=hipertenso,
            diabetico=diabetico,
            gestante=gestante,
            fumante=fumante,
            alergias=alergia,
        )
        pacientes.append(cidadao)
        
    return pacientes


def popular_pacientes(db: Session, total: int = 300):
    novos = gerar_pacientes_sinteticos(total)
    
    # Filtra potenciais duplicidades acidentais
    inseridos = 0
    for p in novos:
        existe_cpf = db.query(Cidadao).filter(Cidadao.cpf == p.cpf).first()
        existe_cns = db.query(Cidadao).filter(Cidadao.cns == p.cns).first()
        if not existe_cpf and not existe_cns:
            db.add(p)
            inseridos += 1
            
    db.commit()
    print(f"✔ Sucesso: {inseridos} pacientes brasileiros (Montes Claros / Vale do Jequitinhonha) inseridos no banco.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        popular_pacientes(db, 300)
    finally:
        db.close()
