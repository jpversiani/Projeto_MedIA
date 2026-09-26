"""
Serviço de Terminologia Médica - CID-11 (Classificação Internacional de Doenças - 11ª Revisão)
Padrão Global OMS (WHO - ICD-11 MMS / Mortality and Morbidity Statistics)

Fornece:
1. Catálogo estruturado de códigos Stem (códigos-tronco) e extensão da CID-11
2. Mapeamento cruzado bidirecional (Cross-walk / Dual-Coding) CID-10 <-> CID-11
3. Busca fonética/textual por código, título e sinônimos clínicos
4. Apoio à transição regulatória (CFM / ANS / OMS)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ItemCID11:
    codigo: str
    titulo: str
    capitulo: str
    capitulo_numero: str
    cid10_equivalente: Optional[str] = None
    sinonimos: List[str] = field(default_factory=list)
    definicao: Optional[str] = None


# Catálogo clínico representativo de alta prevalência da CID-11 para Consultórios e Telemedicina
CATALOGO_CID11: List[ItemCID11] = [
    # Capítulo 05: Doenças do sistema endócrino, nutricionais ou metabólicas
    ItemCID11(
        codigo="5A11",
        titulo="Diabetes mellitus tipo 2",
        capitulo="Doenças do sistema endócrino, nutricionais ou metabólicas",
        capitulo_numero="05",
        cid10_equivalente="E11",
        sinonimos=["DM2", "Diabetes não insulino-dependente", "Diabetes do adulto"],
        definicao="Transtorno metabólico caracterizado por hiperglicemia resultante de defeitos na secreção ou na ação da insulina."
    ),
    ItemCID11(
        codigo="5A10",
        titulo="Diabetes mellitus tipo 1",
        capitulo="Doenças do sistema endócrino, nutricionais ou metabólicas",
        capitulo_numero="05",
        cid10_equivalente="E10",
        sinonimos=["DM1", "Diabetes insulino-dependente", "Diabetes autoimune"],
        definicao="Destruição autoimune das células beta pancreáticas levando à deficiência absoluta de insulina."
    ),
    ItemCID11(
        codigo="5A00",
        titulo="Hipotireoidismo primário",
        capitulo="Doenças do sistema endócrino, nutricionais ou metabólicas",
        capitulo_numero="05",
        cid10_equivalente="E03.9",
        sinonimos=["Hipotireoidismo", "Tireoidite de Hashimoto", "Insuficiência tireoidiana"],
        definicao="Deficiência na produção dos hormônios tireoidianos pela própria glândula tireoide."
    ),
    ItemCID11(
        codigo="5B81",
        titulo="Obesidade",
        capitulo="Doenças do sistema endócrino, nutricionais ou metabólicas",
        capitulo_numero="05",
        cid10_equivalente="E66.0",
        sinonimos=["Excesso de peso", "IMC elevado", "Obesidade clínica"],
        definicao="Acúmulo anormal ou excessivo de gordura corporal que apresenta risco à saúde (IMC >= 30 kg/m²)."
    ),
    ItemCID11(
        codigo="5C80",
        titulo="Hipercolesterolemia pura",
        capitulo="Doenças do sistema endócrino, nutricionais ou metabólicas",
        capitulo_numero="05",
        cid10_equivalente="E78.0",
        sinonimos=["Dislipidemia", "Colesterol alto", "Hiperlipidemia"],
        definicao="Elevação isolada das frações de colesterol sérico (LDL ou colesterol total)."
    ),

    # Capítulo 06: Transtornos mentais, comportamentais ou do neurodesenvolvimento
    ItemCID11(
        codigo="6B00",
        titulo="Transtorno de ansiedade generalizada",
        capitulo="Transtornos mentais, comportamentais ou do neurodesenvolvimento",
        capitulo_numero="06",
        cid10_equivalente="F41.1",
        sinonimos=["TAG", "Ansiedade generalizada", "Ansiedade crônica"],
        definicao="Ansiedade e preocupação excessivas, persistentes (meses), de difícil controle sobre diversos eventos ou atividades."
    ),
    ItemCID11(
        codigo="6B01",
        titulo="Transtorno de pânico",
        capitulo="Transtornos mentais, comportamentais ou do neurodesenvolvimento",
        capitulo_numero="06",
        cid10_equivalente="F41.0",
        sinonimos=["Síndrome do pânico", "Crises de pânico", "Ataque de pânico recorrente"],
        definicao="Ataques de pânico recorrentes e inesperados com preocupação persistente sobre novas crises."
    ),
    ItemCID11(
        codigo="6A70",
        titulo="Transtorno depressivo, episódio único",
        capitulo="Transtornos mentais, comportamentais ou do neurodesenvolvimento",
        capitulo_numero="06",
        cid10_equivalente="F32",
        sinonimos=["Depressão", "Episódio depressivo maior", "Transtorno depressivo unipolar"],
        definicao="Humor deprimido persistente ou anedonia quase diária por pelo menos 2 semanas."
    ),
    ItemCID11(
        codigo="6A71",
        titulo="Transtorno depressivo recorrente",
        capitulo="Transtornos mentais, comportamentais ou do neurodesenvolvimento",
        capitulo_numero="06",
        cid10_equivalente="F33",
        sinonimos=["Depressão recorrente", "Transtorno depressivo maior recorrente"],
        definicao="História de pelo menos dois episódios depressivos com intervalos livres de sintomas."
    ),
    ItemCID11(
        codigo="6A05",
        titulo="Transtorno de déficit de atenção e hiperatividade",
        capitulo="Transtornos mentais, comportamentais ou do neurodesenvolvimento",
        capitulo_numero="06",
        cid10_equivalente="F90.0",
        sinonimos=["TDAH", "Déficit de atenção", "Hiperatividade infantil ou no adulto"],
        definicao="Padrão persistente de desatenção e/ou hiperatividade-impulsividade que interfere no funcionamento."
    ),
    ItemCID11(
        codigo="6B40",
        titulo="Transtorno de estresse pós-traumático",
        capitulo="Transtornos mentais, comportamentais ou do neurodesenvolvimento",
        capitulo_numero="06",
        cid10_equivalente="F43.1",
        sinonimos=["TEPT", "Estresse pós-traumático"],
        definicao="Reação de estresse prolongada e desadaptativa a um evento extraordinariamente ameaçador ou catastrófico."
    ),
    ItemCID11(
        codigo="QD85",
        titulo="Síndrome de Burnout (Esgotamento profissional)",
        capitulo="Fatores que influenciam o estado de saúde ou o contato com serviços de saúde",
        capitulo_numero="24",
        cid10_equivalente="Z73.0",
        sinonimos=["Burnout", "Esgotamento no trabalho", "Estresse ocupacional crônico"],
        definicao="Síndrome conceituada como resultante de estresse crônico no local de trabalho não gerenciado com sucesso."
    ),

    # Capítulo 08: Doenças do sistema nervoso
    ItemCID11(
        codigo="8A80",
        titulo="Enxaqueca (Migrânea)",
        capitulo="Doenças do sistema nervoso",
        capitulo_numero="08",
        cid10_equivalente="G43",
        sinonimos=["Migrânea", "Enxaqueca com aura", "Enxaqueca sem aura"],
        definicao="Cefaleia primária caracterizada por episódios recorrentes de dor pulsátil, frequentemente unilateral."
    ),
    ItemCID11(
        codigo="8A81",
        titulo="Cefaleia do tipo tensional",
        capitulo="Doenças do sistema nervoso",
        capitulo_numero="08",
        cid10_equivalente="G44.2",
        sinonimos=["Cefaleia tensional", "Dor de cabeça por tensão"],
        definicao="Cefaleia em pressão ou aperto bilateral, de intensidade leve a moderada, sem náuseas importantes."
    ),
    ItemCID11(
        codigo="8A00",
        titulo="Doença de Parkinson",
        capitulo="Doenças do sistema nervoso",
        capitulo_numero="08",
        cid10_equivalente="G20",
        sinonimos=["Parkinsonismo idiopático", "Parkinson"],
        definicao="Doença neurodegenerativa progressiva com tremor de repouso, rigidez, bradicinesia e instabilidade postural."
    ),

    # Capítulo 11: Doenças do aparelho circulatório
    ItemCID11(
        codigo="BA00",
        titulo="Hipertensão essencial",
        capitulo="Doenças do aparelho circulatório",
        capitulo_numero="11",
        cid10_equivalente="I10",
        sinonimos=["HAS", "Hipertensão arterial primária", "Pressão alta"],
        definicao="Elevação crônica e sustentada da pressão arterial sistêmica (PA >= 140/90 mmHg) sem causa secundária identificável."
    ),
    ItemCID11(
        codigo="BA01",
        titulo="Hipertensão secundária",
        capitulo="Doenças do aparelho circulatório",
        capitulo_numero="11",
        cid10_equivalente="I15",
        sinonimos=["HAS secundária", "Hipertensão renovascular", "Hipertensão endócrina"],
        definicao="Hipertensão arterial decorrente de condição médica subjacente identificável."
    ),
    ItemCID11(
        codigo="BA41",
        titulo="Angina de peito (Angina pectoris)",
        capitulo="Doenças do aparelho circulatório",
        capitulo_numero="11",
        cid10_equivalente="I20",
        sinonimos=["Angina estável", "Angina instável", "Dor precordial isquêmica"],
        definicao="Desconforto ou dor torácica retroesternal causada por isquemia miocárdica transitória."
    ),
    ItemCID11(
        codigo="BD10",
        titulo="Insuficiência cardíaca congestiva",
        capitulo="Doenças do aparelho circulatório",
        capitulo_numero="11",
        cid10_equivalente="I50.0",
        sinonimos=["ICC", "Insuficiência cardíaca crônica", "Falência cardíaca"],
        definicao="Síndrome clínica complexa na qual o coração não bombeia sangue suficiente para atender às demandas metabólicas."
    ),
    ItemCID11(
        codigo="BC40",
        titulo="Fibrilação ou flutter atrial",
        capitulo="Doenças do aparelho circulatório",
        capitulo_numero="11",
        cid10_equivalente="I48",
        sinonimos=["FA", "Fibrilação atrial", "Arritmia supraventricular"],
        definicao="Taquiarritmia supraventricular com ativação atrial desorganizada e contrações ventriculares irregulares."
    ),

    # Capítulo 12: Doenças do aparelho respiratório
    ItemCID11(
        codigo="CA23",
        titulo="Asma",
        capitulo="Doenças do aparelho respiratório",
        capitulo_numero="12",
        cid10_equivalente="J45",
        sinonimos=["Asma brônquica", "Bronquite asmática", "Hiper-reatividade brônquica"],
        definicao="Doença inflamatória crônica das vias aéreas com hiper-responsividade e obstrução variável do fluxo aéreo expiratório."
    ),
    ItemCID11(
        codigo="CA22",
        titulo="Doença pulmonar obstrutiva crônica",
        capitulo="Doenças do aparelho respiratório",
        capitulo_numero="12",
        cid10_equivalente="J44",
        sinonimos=["DPOC", "Enfisema pulmonar", "Bronquite crônica tabágica"],
        definicao="Condição respiratória caracterizada por sintomas respiratórios crônicos e limitação persistente do fluxo aéreo."
    ),
    ItemCID11(
        codigo="CA01",
        titulo="Rinite alérgica",
        capitulo="Doenças do aparelho respiratório",
        capitulo_numero="12",
        cid10_equivalente="J30.4",
        sinonimos=["Rinite", "Febre do feno", "Rinite alérgica sazonal ou perene"],
        definicao="Inflamação das mucosas nasais mediada por IgE após exposição a alérgenos."
    ),
    ItemCID11(
        codigo="CA40",
        titulo="Pneumonia bacteriana",
        capitulo="Doenças do aparelho respiratório",
        capitulo_numero="12",
        cid10_equivalente="J15.9",
        sinonimos=["Pneumonia comunitária", "Infecção pulmonar aguda"],
        definicao="Infecção aguda do parênquima pulmonar caracterizada por infiltrado inflamatório alveolar."
    ),

    # Capítulo 13: Doenças do aparelho digestivo
    ItemCID11(
        codigo="DA22",
        titulo="Doença do refluxo gastroesofágico",
        capitulo="Doenças do aparelho digestivo",
        capitulo_numero="13",
        cid10_equivalente="K21.9",
        sinonimos=["DRGE", "Refluxo gastroesofágico", "Pirose / Azia crônica"],
        definicao="Condição que se desenvolve quando o refluxo do conteúdo gástrico causa sintomas incômodos ou lesão da mucosa."
    ),
    ItemCID11(
        codigo="DA60",
        titulo="Gastrite e duodenite",
        capitulo="Doenças do aparelho digestivo",
        capitulo_numero="13",
        cid10_equivalente="K29.7",
        sinonimos=["Gastrite", "Dispepsia", "Inflamação gástrica"],
        definicao="Processo inflamatório da mucosa gástrica ou duodenal, frequentemente associado a H. pylori ou AINEs."
    ),
    ItemCID11(
        codigo="DD91",
        titulo="Síndrome do intestino irritável",
        capitulo="Doenças do aparelho digestivo",
        capitulo_numero="13",
        cid10_equivalente="K58.9",
        sinonimos=["SII", "Cólon irritável", "Distúrbio funcional gastrointestinal"],
        definicao="Transtorno funcional caracterizado por dor abdominal recorrente associada a alterações na evacuação."
    ),

    # Capítulo 14: Doenças da pele
    ItemCID11(
        codigo="EA80",
        titulo="Dermatite atópica",
        capitulo="Doenças da pele",
        capitulo_numero="14",
        cid10_equivalente="L20",
        sinonimos=["Eczema atópico", "Dermatite eczematosa"],
        definicao="Doença inflamatória crônica e recidivante da pele com prurido intenso e lesões eczematosas típicas."
    ),
    ItemCID11(
        codigo="ED80",
        titulo="Acne vulgar",
        capitulo="Doenças da pele",
        capitulo_numero="14",
        cid10_equivalente="L70.0",
        sinonimos=["Acne", "Espinhas", "Acne inflamatória"],
        definicao="Afecção inflamatória crônica da unidade pilossebácea com comedões, pápulas, pústulas ou nódulos."
    ),
    ItemCID11(
        codigo="EA90",
        titulo="Psoríase",
        capitulo="Doenças da pele",
        capitulo_numero="14",
        cid10_equivalente="L40.0",
        sinonimos=["Psoríase vulgar", "Psoríase em placas"],
        definicao="Doença inflamatória sistêmica crônica imunomediada com placas eritemato-descamativas pruriginosas."
    ),

    # Capítulo 15: Doenças do sistema musculoesquelético ou do tecido conjuntivo
    ItemCID11(
        codigo="FA00",
        titulo="Osteoartrite (Artrose)",
        capitulo="Doenças do sistema musculoesquelético ou do tecido conjuntivo",
        capitulo_numero="15",
        cid10_equivalente="M19.9",
        sinonimos=["Artrose", "Osteoartrose", "Doença articular degenerativa"],
        definicao="Degradação progressiva da cartilagem articular associada a neoformação óssea (osteófitos) e dor mecânica."
    ),
    ItemCID11(
        codigo="FA20",
        titulo="Artrite reumatoide",
        capitulo="Doenças do sistema musculoesquelético ou do tecido conjuntivo",
        capitulo_numero="15",
        cid10_equivalente="M06.9",
        sinonimos=["AR", "Artrite autoimune", "Poliartrite crônica"],
        definicao="Doença autoimune inflamatória crônica que atinge primariamente a membrana sinovial articular."
    ),
    ItemCID11(
        codigo="ME84",
        titulo="Dor lombar baixa (Lombalgia)",
        capitulo="Sintomas, sinais ou achados clínicos não classificados em outra parte",
        capitulo_numero="21",
        cid10_equivalente="M54.5",
        sinonimos=["Lombalgia mecânica", "Lumbago", "Dor nas costas"],
        definicao="Dor ou desconforto muscular localizado abaixo da margem costal e acima das pregas glúteas inferiores."
    ),
    ItemCID11(
        codigo="NC32",
        titulo="Fibromialgia",
        capitulo="Doenças do sistema musculoesquelético ou do tecido conjuntivo",
        capitulo_numero="15",
        cid10_equivalente="M79.7",
        sinonimos=["Síndrome fibromiálgica", "Dor crônica generalizada"],
        definicao="Síndrome clínica de dor musculoesquelética crônica generalizada acompanhada de fadiga, sono não reparador e pontos sensíveis."
    ),

    # Capítulo 16: Doenças do sistema geniturinário
    ItemCID11(
        codigo="GC08",
        titulo="Infecção não complicada do trato urinário",
        capitulo="Doenças do sistema geniturinário",
        capitulo_numero="16",
        cid10_equivalente="N39.0",
        sinonimos=["ITU", "Cistite aguda", "Infecção urinária"],
        definicao="Infecção bacteriana da bexiga urinária em hospedeiro sem anormalidades estruturais ou funcionais do trato urinário."
    ),
    ItemCID11(
        codigo="GB61",
        titulo="Doença renal crônica (DRC)",
        capitulo="Doenças do sistema geniturinário",
        capitulo_numero="16",
        cid10_equivalente="N18.9",
        sinonimos=["DRC", "Insuficiência renal crônica", "Nefropatia crônica"],
        definicao="Anormalidades na estrutura ou função renal presentes por mais de 3 meses, com implicações para a saúde."
    ),

    # Capítulo 01: Doenças infecciosas
    ItemCID11(
        codigo="1C60",
        titulo="Dengue",
        capitulo="Certas doenças infecciosas ou parasitárias",
        capitulo_numero="01",
        cid10_equivalente="A90",
        sinonimos=["Febre dengue", "Dengue clássica"],
        definicao="Doença febril aguda causada por flavivírus transmitido por mosquitos Aedes."
    ),
    ItemCID11(
        codigo="RA01",
        titulo="COVID-19 (Doença por coronavírus 2019)",
        capitulo="Códigos para situações especiais",
        capitulo_numero="25",
        cid10_equivalente="U07.1",
        sinonimos=["Coronavírus", "SARS-CoV-2", "Infecção por COVID-19"],
        definicao="Doença infecciosa aguda respiratória e multissistêmica causada pelo SARS-CoV-2."
    ),
]


class CID11Service:
    """
    Motor central de inteligência para CID-11 (OMS - 11ª Revisão).
    Fornece busca rápida e resolução de equivalências para transição CID-10 <-> CID-11.
    """

    def __init__(self, catalogo: Optional[List[ItemCID11]] = None):
        self._catalogo = catalogo or CATALOGO_CID11
        # Mapeamentos indexados para O(1) lookup
        self._por_codigo_cid11: Dict[str, ItemCID11] = {}
        self._por_codigo_cid10: Dict[str, ItemCID11] = {}

        for item in self._catalogo:
            code_clean = item.codigo.strip().upper()
            self._por_codigo_cid11[code_clean] = item
            if item.cid10_equivalente:
                cid10_clean = item.cid10_equivalente.strip().upper()
                self._por_codigo_cid10[cid10_clean] = item

    def buscar(
        self,
        termo: Optional[str] = None,
        capitulo: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Pesquisa códigos CID-11 por código exato, parte do código, título ou sinônimos clínicos.
        Suporta busca insensível a acentuação e caixa.
        """
        import unicodedata

        def normalizar(t: str) -> str:
            return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c)).lower().strip()

        resultados: List[ItemCID11] = []
        termo_limpo = normalizar(termo) if termo else None

        for item in self._catalogo:
            # Filtro por capítulo se fornecido
            if capitulo:
                cap_limpo = normalizar(capitulo)
                if cap_limpo not in normalizar(item.capitulo) and cap_limpo != item.capitulo_numero:
                    continue

            # Se não houver termo de busca, traz os registros
            if not termo_limpo:
                resultados.append(item)
                if len(resultados) >= limit:
                    break
                continue

            # Busca por código CID-11 (prefixo ou correspondência)
            if termo_limpo in item.codigo.lower():
                resultados.append(item)
            # Busca por código CID-10 correspondente
            elif item.cid10_equivalente and termo_limpo in item.cid10_equivalente.lower():
                resultados.append(item)
            # Busca por título (sem acento)
            elif termo_limpo in normalizar(item.titulo):
                resultados.append(item)
            # Busca por sinônimos (sem acento)
            elif any(termo_limpo in normalizar(sin) for sin in item.sinonimos):
                resultados.append(item)

            if len(resultados) >= limit:
                break

        return [self._formatar_item(it) for it in resultados]

    def obter_por_codigo(self, codigo_cid11: str) -> Optional[Dict[str, Any]]:
        """Retorna detalhes completos de um código CID-11 específico."""
        code_clean = codigo_cid11.strip().upper()
        item = self._por_codigo_cid11.get(code_clean)
        return self._formatar_item(item) if item else None

    def converter_cid10_para_cid11(self, codigo_cid10: str) -> Optional[Dict[str, Any]]:
        """
        Converte um código legado CID-10 para a correspondência oficial CID-11.
        Suporta códigos truncados (ex: I10 ou E11).
        """
        if not codigo_cid10:
            return None

        clean = codigo_cid10.strip().upper()
        # Busca exata
        item = self._por_codigo_cid10.get(clean)
        if item:
            return {
                "origem": "CID-10",
                "codigo_origem": clean,
                "destino": "CID-11",
                "codigo_cid11": item.codigo,
                "titulo_cid11": item.titulo,
                "capitulo": item.capitulo,
                "equivalencia_direta": True
            }

        # Busca por prefixo (ex: I10.9 buscando I10)
        prefixo = clean.split(".")[0]
        item_prefixo = self._por_codigo_cid10.get(prefixo)
        if item_prefixo:
            return {
                "origem": "CID-10",
                "codigo_origem": clean,
                "destino": "CID-11",
                "codigo_cid11": item_prefixo.codigo,
                "titulo_cid11": item_prefixo.titulo,
                "capitulo": item_prefixo.capitulo,
                "equivalencia_direta": False,
                "observacao": f"Mapeado por aproximação pelo prefixo do grupo {prefixo}"
            }

        return None

    def converter_cid11_para_cid10(self, codigo_cid11: str) -> Optional[Dict[str, Any]]:
        """
        Converte um código CID-11 para o código legado CID-10 (essencial para faturamento TISS e CFM).
        """
        if not codigo_cid11:
            return None

        clean = codigo_cid11.strip().upper()
        item = self._por_codigo_cid11.get(clean)
        if item and item.cid10_equivalente:
            return {
                "origem": "CID-11",
                "codigo_origem": clean,
                "destino": "CID-10",
                "codigo_cid10": item.cid10_equivalente,
                "titulo": item.titulo,
                "capitulo": item.capitulo
            }
        return None

    def total_codigos(self) -> int:
        return len(self._catalogo)

    def listar_capitulos(self) -> List[Dict[str, str]]:
        """Lista os capítulos OMS da CID-11 presentes no catálogo."""
        vistos = set()
        capitulos = []
        for it in self._catalogo:
            if it.capitulo_numero not in vistos:
                vistos.add(it.capitulo_numero)
                capitulos.append({
                    "numero": it.capitulo_numero,
                    "nome": it.capitulo
                })
        return sorted(capitulos, key=lambda x: x["numero"])

    @staticmethod
    def _formatar_item(item: ItemCID11) -> Dict[str, Any]:
        return {
            "codigo": item.codigo,
            "titulo": item.titulo,
            "capitulo": item.capitulo,
            "capitulo_numero": item.capitulo_numero,
            "cid10_equivalente": item.cid10_equivalente,
            "sinonimos": item.sinonimos,
            "definicao": item.definicao,
            "padrao_oms": "ICD-11 MMS (Mortality and Morbidity Statistics)"
        }


# Instância Singleton global para reuso eficiente em toda a aplicação
cid11_service = CID11Service()
