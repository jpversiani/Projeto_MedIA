"""Busca de CID-10 por prefixo, termo de descrição e capítulo — Projeto MedIA (SUS/APS).

Serviço de terminologia clínica para a Atenção Primária à Saúde (APS/SUS):
expõe um catálogo consultável da Classificação Estatística Internacional de
Doenças e Problemas Relacionados com a Saúde — 10ª revisão (CID-10, OMS/
DATASUS) com uma amostra representativa dos códigos mais utilizados na APS
(hipertensão, diabetes, DPOC, doença renal crônica, queixas comuns e fatores
de saúde usados no e-SUS AP), destinado ao autocomplete do prontuário
eletrônico (método SOAP) e à codificação de problemas ativos do cidadão.

Recursos:

1. **Busca por prefixo** — digitando "I50" o serviço devolve a família da
   insuficiência cardíaca; aceita "i50", "I50." e "I50.9" (o sufixo com
   ponto é ignorado quando a amostra não contém a subcategoria).
2. **Busca por termo de descrição** — busca livre com normalização de
   acentos (NFKD) e "casefold": "insuficiencia cardiaca", "Insuficiência
   Cardíaca" e "INSUFICIENCIA CARDIACA" localizam o mesmo código.
3. **Busca híbrida** — infere o critério pelo formato da consulta (padrão
   de código CID-10 → prefixo; caso contrário → descrição), ideal para uma
   única caixa de autocomplete na interface (HTML5 + ES Modules).
4. **Agrupamento por capítulo** — organiza os resultados pelos capítulos da
   CID-10 (I a XXI, além do capítulo XXII de códigos especiais U).
5. **Cache em memória** — índices e consultas resolvidos com
   ``functools.lru_cache``: a amostra é indexada uma única vez por processo
   e buscas repetidas não revarrem o catálogo (importante em teleatendimento
   com muitos ajustes de codificação por sessão).
6. **Espelho CIAP-2** — sugestão de código CIAP-2 (WONCA) nas condições
   crônicas e queixas frequentes, como recomenda o padrão de registro da APS.

Referências:

    - OMS. CID-10 — Classificação Estatística Internacional de Doenças e
      Problemas Relacionados com a Saúde, 10ª revisão (1995).
    - DATASUS/MS. CID-10: classificações e códigos (TABNET/RIPSA).
    - Ministério da Saúde. e-Multi/PCDT da Atenção Primária à Saúde.
    - Ministério da Saúde. e-SUS APS: vocabulários controlados (problemas
      de saúde, incluindo os códigos U de uso nacional).
    - WONCA. CIAP-2 — Classificação Internacional de Atenção Primária (2008).

Limitações: a amostra cobre cerca de 110 códigos de uso corrente na APS e
não substitui a CID-10 completa — refine a codificação nas subcategorias
oficiais quando necessário. As sugestões de CIAP-2 são auxiliares e não
eliminam a responsabilidade do profissional pelo código registrado.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
from types import MappingProxyType
from typing import Final, Literal, NamedTuple

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CapituloCID10",
    "CatalogoCID10",
    "ConsultaCID10InvalidaError",
    "GrupoCapituloCID10",
    "ItemCID10",
    "LIMITE_MAXIMO",
    "LIMITE_PADRAO",
    "ResultadoBuscaCID10",
]

# ---------------------------------------------------------------------------
# Constantes do serviço
# ---------------------------------------------------------------------------

#: Limite padrão de resultados por busca.
LIMITE_PADRAO: Final[int] = 20

#: Limite máximo permitido por busca (proteção contra respostas gigantes).
LIMITE_MAXIMO: Final[int] = 100

#: Consulta no formato de código CID-10 completo (ex.: "I50", "J15.9", "u07.1").
_PADRAO_CODIGO: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]\d{1,2}(\.\d{1,2})?$")

#: Consulta com prefixo de código ainda incompleto (ex.: "I", "I5", "I50").
_PADRAO_PREFIXO_PARCIAL: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]\d{0,2}$")

#: Texto de busca de descrição: termos com menos de 2 caracteres são ignorados.
_TAMANHO_MINIMO_TERMO: Final[int] = 2


class ConsultaCID10InvalidaError(ValueError):
    """Erro lançado quando a consulta (termo, prefixo ou limite) é inválida."""


# ---------------------------------------------------------------------------
# Capítulos da CID-10 (OMS/DATASUS)
# ---------------------------------------------------------------------------


class CapituloCID10(str, Enum):
    """Capítulos da CID-10, com faixas de código e títulos oficiais.

    Attributes:
        roman: Numeração romana do capítulo (ex.: "IX").
        faixa_inicial: Código inicial do capítulo (ex.: "I00").
        faixa_final: Código final do capítulo (ex.: "I99").
        titulo: Título oficial do capítulo (OMS/DATASUS).
    """

    def __new__(
        cls,
        roman: str,
        faixa_inicial: str,
        faixa_final: str,
        titulo: str,
    ) -> "CapituloCID10":
        obj = str.__new__(cls, roman)
        obj._value_ = roman
        obj._roman = roman
        obj._faixa_inicial = faixa_inicial
        obj._faixa_final = faixa_final
        obj._titulo = titulo
        return obj

    INFECCIOSAS = ("I", "A00", "B99", "Certas doenças infecciosas e parasitárias")
    NEOPLASIAS = ("II", "C00", "D48", "Neoplasias (tumores)")
    SANGUE = (
        "III",
        "D50",
        "D89",
        "Doenças do sangue e dos órgãos hematopoéticos e certas perturbações do sistema imunitário",
    )
    ENDOCRINAS = ("IV", "E00", "E90", "Doenças endócrinas, nutricionais e metabólicas")
    MENTAIS = ("V", "F00", "F99", "Transtornos mentais e comportamentais")
    SISTEMA_NERVOSO = ("VI", "G00", "G99", "Doenças do sistema nervoso")
    OLHO = ("VII", "H00", "H59", "Doenças do olho e anexos")
    OUVIDO = ("VIII", "H60", "H95", "Doenças do ouvido e da apófise mastoide")
    CIRCULATORIO = ("IX", "I00", "I99", "Doenças do sistema circulatório")
    RESPIRATORIO = ("X", "J00", "J99", "Doenças do sistema respiratório")
    DIGESTIVO = ("XI", "K00", "K93", "Doenças do sistema digestivo")
    PELE = ("XII", "L00", "L99", "Doenças da pele e do tecido subcutâneo")
    OSTEOMUSCULAR = (
        "XIII",
        "M00",
        "M99",
        "Doenças do sistema osteomuscular e do tecido conjuntivo",
    )
    GENITURINARIO = ("XIV", "N00", "N99", "Doenças do sistema geniturinário")
    GRAVIDEZ = ("XV", "O00", "O99", "Gravidez, parto e puerpério")
    PERINATAL = ("XVI", "P00", "P96", "Algumas condições originadas no período perinatal")
    MALFORMACOES = (
        "XVII",
        "Q00",
        "Q99",
        "Malformações congênitas, deformidades e anomalias cromossômicas",
    )
    SINTOMAS = (
        "XVIII",
        "R00",
        "R99",
        "Sintomas, sinais e achados anormais de exames clínicos e de laboratório, não classificados em outra parte",
    )
    LESOES = (
        "XIX",
        "S00",
        "T98",
        "Lesões, envenenamentos e algumas outras consequências de causas externas",
    )
    CAUSAS_EXTERNAS = ("XX", "V01", "Y98", "Causas externas de morbidade e de mortalidade")
    FATORES_SAUDE = (
        "XXI",
        "Z00",
        "Z99",
        "Fatores que influenciam o estado de saúde e o contato com serviços de saúde",
    )
    CODIGOS_ESPECIAIS = (
        "XXII",
        "U00",
        "U99",
        "Códigos para propósitos especiais (códigos provisórios e de uso nacional)",
    )

    @property
    def roman(self) -> str:
        """Numeração romana do capítulo (ex.: "IX")."""
        return self._roman

    @property
    def titulo(self) -> str:
        """Título oficial do capítulo (OMS/DATASUS)."""
        return self._titulo

    @property
    def faixa_inicial(self) -> str:
        """Código inicial do capítulo (ex.: "I00")."""
        return self._faixa_inicial

    @property
    def faixa_final(self) -> str:
        """Código final do capítulo (ex.: "I99")."""
        return self._faixa_final

    @property
    def faixa(self) -> str:
        """Faixa de códigos do capítulo formatada (ex.: "I00–I99")."""
        return f"{self._faixa_inicial}–{self._faixa_final}"

    @property
    def rotulo(self) -> str:
        """Rótulo de exibição (ex.: "Capítulo IX")."""
        return f"Capítulo {self._roman}"

    @property
    def letra_inicial(self) -> str:
        """Letra inicial da faixa do capítulo (ex.: "I")."""
        return self._faixa_inicial[0]

    @property
    def numero_inicial(self) -> int:
        """Número inicial da faixa do capítulo (ex.: 0 para "I00")."""
        return int(self._faixa_inicial[1:])

    @property
    def letra_final(self) -> str:
        """Letra final da faixa do capítulo (ex.: "I")."""
        return self._faixa_final[0]

    @property
    def numero_final(self) -> int:
        """Número final da faixa do capítulo (ex.: 99 para "I99")."""
        return int(self._faixa_final[1:])


def _capitulo_do_codigo(codigo: str) -> CapituloCID10:
    """Localiza o capítulo da CID-10 ao qual o código pertence.

    Args:
        codigo: Código no formato "X99" ou "X99.9" (letra + 2 dígitos).

    Returns:
        O membro de :class:`CapituloCID10` correspondente.

    Raises:
        ConsultaCID10InvalidaError: Se o código não pertence a nenhum capítulo.
    """
    letra = codigo[0]
    numero = int(codigo[1:3])
    for capitulo in CapituloCID10:
        dentro_da_faixa = (
            (letra == capitulo.letra_inicial == capitulo.letra_final and capitulo.numero_inicial <= numero <= capitulo.numero_final)
            or (letra == capitulo.letra_inicial != capitulo.letra_final and numero >= capitulo.numero_inicial)
            or (letra == capitulo.letra_final != capitulo.letra_inicial and numero <= capitulo.numero_final)
            or (capitulo.letra_inicial < letra < capitulo.letra_final)
        )
        if dentro_da_faixa:
            return capitulo
    raise ConsultaCID10InvalidaError(f"Código CID-10 fora dos capítulos conhecidos: {codigo!r}.")


# ---------------------------------------------------------------------------
# Schemas Pydantic v2 (contratos de saída para API e interface)
# ---------------------------------------------------------------------------


class ItemCID10(BaseModel):
    """Item do catálogo CID-10 pronto para a interface e para a API.

    Attributes:
        codigo: Código oficial CID-10 (ex.: "I50", "J15.9", "U07.1").
        descricao: Descrição oficial em português (OMS/DATASUS).
        capitulo: Capítulo da CID-10 a que o código pertence.
        ciap2_sugerido: Código CIAP-2 (WONCA) sugerido para o registro na APS,
            quando a correspondência é direta e consensual.
        observacao: Ressalva de uso no SUS (ex.: códigos U de uso nacional).
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    codigo: str = Field(pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$", description="Código oficial CID-10.")
    descricao: str = Field(min_length=1, max_length=300, description="Descrição oficial (pt-BR).")
    capitulo: CapituloCID10
    ciap2_sugerido: str | None = Field(None, pattern=r"^[A-Z]\d{2}$")
    observacao: str | None = None

    @property
    def rotulo_capitulo(self) -> str:
        """Rótulo do capítulo (ex.: "Capítulo IX")."""
        return f"Capítulo {self.capitulo.roman}"


class GrupoCapituloCID10(BaseModel):
    """Agrupamento de itens por capítulo da CID-10 para exibição hierárquica.

    Attributes:
        capitulo: Membro do enum do capítulo (ex.: Capítulo IX).
        rotulo: Rótulo de exibição (ex.: "Capítulo IX").
        titulo: Título oficial do capítulo.
        faixa: Faixa de códigos do capítulo (ex.: "I00–I99").
        total: Quantidade de itens agrupados no capítulo.
        itens: Itens ordenados por código dentro do capítulo.
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    capitulo: CapituloCID10
    rotulo: str
    titulo: str
    faixa: str
    total: int = Field(ge=0)
    itens: tuple[ItemCID10, ...]


class ResultadoBuscaCID10(BaseModel):
    """Resultado consolidado de uma busca no catálogo CID-10.

    Attributes:
        consulta: Consulta original informada pelo profissional.
        criterio: Critério aplicado ("prefixo", "descricao" ou "hibrida").
        total: Quantidade de itens retornados.
        itens: Itens encontrados, ordenados por relevância e código.
        consultado_em: Data/hora (UTC) da execução da busca.
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    consulta: str
    criterio: Literal["prefixo", "descricao", "hibrida"]
    total: int = Field(ge=0)
    itens: tuple[ItemCID10, ...]
    consultado_em: datetime


# ---------------------------------------------------------------------------
# Amostra representativa — códigos mais usados na APS (SUS/e-SUS AP)
# ---------------------------------------------------------------------------


class _EntradaAmostra(NamedTuple):
    """Registro interno da amostra: código, descrição, CIAP-2 e observação."""

    codigo: str
    descricao: str
    ciap2: str | None = None
    observacao: str | None = None


#: Amostra curada dos códigos de uso corrente na Atenção Primária (SUS/APS):
#: condições crônicas prioritárias, agravos frequentes, queixas comuns e
#: fatores de saúde do e-SUS AP, com espelho CIAP-2 quando consensual.
_AMOSTRA_APS: Final[tuple[_EntradaAmostra, ...]] = (
    # Capítulo I — Certas doenças infecciosas e parasitárias
    _EntradaAmostra("A09", "Diarreia e gastroenterite de origem infecciosa presumível", "D11"),
    _EntradaAmostra("A15", "Tuberculose respiratória, com confirmação bacteriológica e histológica"),
    _EntradaAmostra("A16", "Tuberculose respiratória, sem confirmação bacteriológica ou histológica"),
    _EntradaAmostra("A38", "Escarlatina"),
    _EntradaAmostra("A39", "Meningite meningocócica"),
    _EntradaAmostra("A54", "Gonorreia"),
    _EntradaAmostra("A90", "Dengue"),
    _EntradaAmostra("B05", "Sarampo"),
    _EntradaAmostra("B18", "Hepatite viral crônica"),
    _EntradaAmostra("B20", "Doença pelo vírus da imunodeficiência humana [HIV] resultando em doenças infecciosas e parasitárias"),
    _EntradaAmostra("B24", "Doença pelo vírus da imunodeficiência humana [HIV] não especificada"),
    _EntradaAmostra("B37", "Candidíase"),
    # Capítulo II — Neoplasias (tumores)
    _EntradaAmostra("C50", "Neoplasia maligna da mama"),
    _EntradaAmostra("C53", "Neoplasia maligna do colo do útero"),
    _EntradaAmostra("C61", "Neoplasia maligna da próstata"),
    # Capítulo III — Sangue e órgãos hematopoéticos
    _EntradaAmostra("D50", "Anemia ferropênica", "B80"),
    _EntradaAmostra("D64", "Outras anemias", "B80"),
    # Capítulo IV — Endócrinas, nutricionais e metabólicas
    _EntradaAmostra("E10", "Diabetes mellitus insulino-dependente [tipo 1]", "T89"),
    _EntradaAmostra("E11", "Diabetes mellitus não-insulino-dependente [tipo 2]", "T90"),
    _EntradaAmostra("E14", "Diabetes mellitus não especificado", "T90"),
    _EntradaAmostra("E55", "Deficiência de vitamina D"),
    _EntradaAmostra("E66", "Obesidade", "T82"),
    _EntradaAmostra("E78", "Transtornos do metabolismo das lipoproteínas e outras lipidemias", "T93"),
    # Capítulo V — Transtornos mentais e comportamentais
    _EntradaAmostra("F10", "Transtornos mentais e comportamentais devidos ao uso de álcool", "P15"),
    _EntradaAmostra("F17", "Transtornos mentais e comportamentais devidos ao uso de tabaco", "P17"),
    _EntradaAmostra("F20", "Esquizofrenia", "P71"),
    _EntradaAmostra("F31", "Transtorno afetivo bipolar"),
    _EntradaAmostra("F32", "Episódio depressivo", "P76"),
    _EntradaAmostra("F41", "Transtornos de ansiedade", "P74"),
    # Capítulo VI — Sistema nervoso
    _EntradaAmostra("G43", "Enxaqueca"),
    _EntradaAmostra("G47", "Transtornos do sono"),
    # Capítulo VII — Olho e anexos
    _EntradaAmostra("H10", "Conjuntivite", "F73"),
    _EntradaAmostra("H52", "Transtornos da acomodação e da refração"),
    # Capítulo VIII — Ouvido e apófise mastoide
    _EntradaAmostra("H60", "Otite externa"),
    _EntradaAmostra("H66", "Otite média não supurativa", "H74"),
    # Capítulo IX — Sistema circulatório
    _EntradaAmostra("I10", "Hipertensão essencial (primária)", "K86"),
    _EntradaAmostra("I11", "Doença hipertensiva do coração"),
    _EntradaAmostra("I20", "Angina pectoris", "K74"),
    _EntradaAmostra("I21", "Infarto agudo do miocárdio", "K75"),
    _EntradaAmostra("I25", "Doença isquêmica crônica do coração"),
    _EntradaAmostra("I48", "Fibrilação e flutter atriais", "K78"),
    _EntradaAmostra("I50", "Insuficiência cardíaca", "K77"),
    _EntradaAmostra("I63", "Infarto cerebral", "K90"),
    _EntradaAmostra("I64", "Acidente vascular cerebral, não especificado como hemorrágico ou isquêmico", "K90"),
    _EntradaAmostra("I83", "Varizes dos membros inferiores"),
    # Capítulo X — Sistema respiratório
    _EntradaAmostra("J00", "Rinofaringe aguda [viral] (resfriado comum)"),
    _EntradaAmostra("J02", "Faringite aguda"),
    _EntradaAmostra("J03", "Amigdalite aguda", "R72"),
    _EntradaAmostra("J04", "Laringite e traqueíte agudas"),
    _EntradaAmostra("J06", "Infecções agudas das vias aéreas superiores de localizações múltiplas e não especificadas", "R74"),
    _EntradaAmostra("J11", "Gripe com outras manifestações respiratórias, vírus não identificado", "R80"),
    _EntradaAmostra("J15.9", "Pneumonia bacteriana não especificada", "R81"),
    _EntradaAmostra("J18", "Pneumonia, microrganismo não especificado", "R81"),
    _EntradaAmostra("J20", "Bronquite aguda"),
    _EntradaAmostra("J30", "Rinite alérgica e vasomotora"),
    _EntradaAmostra("J44", "Doença pulmonar obstrutiva crônica [DPOC]", "R95"),
    _EntradaAmostra("J45", "Asma", "R96"),
    _EntradaAmostra("J96.0", "Insuficiência respiratória aguda"),
    # Capítulo XI — Sistema digestivo
    _EntradaAmostra("K02", "Cárie dentária", "D82"),
    _EntradaAmostra("K05", "Gengivite e doenças periodontais"),
    _EntradaAmostra("K21", "Doença do refluxo gastroesofágico"),
    _EntradaAmostra("K25", "Úlcera gástrica"),
    _EntradaAmostra("K26", "Úlcera duodenal"),
    _EntradaAmostra("K29", "Gastrite e duodenite"),
    _EntradaAmostra("K30", "Dispepsia", "D83"),
    _EntradaAmostra("K35", "Apendicite aguda"),
    _EntradaAmostra("K40", "Hérnia inguinal"),
    _EntradaAmostra("K58", "Síndrome do intestino irritável"),
    _EntradaAmostra("K59", "Outros transtornos funcionais intestinais"),
    _EntradaAmostra("K74", "Fibrose e cirrose do fígado"),
    # Capítulo XII — Pele e tecido subcutâneo
    _EntradaAmostra("L02", "Abcesso cutâneo, furúnculo e carbúnculo"),
    _EntradaAmostra("L03", "Celulite e linfangite agudas"),
    _EntradaAmostra("L20", "Dermatite atópica"),
    _EntradaAmostra("L21", "Dermatite seborreica"),
    _EntradaAmostra("L22", "Dermatite das fraldas"),
    _EntradaAmostra("L29", "Prurido"),
    _EntradaAmostra("L40", "Psoríase"),
    _EntradaAmostra("L50", "Urticária"),
    _EntradaAmostra("L70", "Acne"),
    # Capítulo XIII — Sistema osteomuscular
    _EntradaAmostra("M10", "Gota"),
    _EntradaAmostra("M17", "Gonartrose [artrose do joelho]"),
    _EntradaAmostra("M51", "Outros transtornos dos discos intervertebrais"),
    _EntradaAmostra("M54", "Dorsalgia", "L84"),
    _EntradaAmostra("M75.1", "Síndrome do manguito dos rotadores"),
    _EntradaAmostra("M81", "Osteoporose sem fratura patológica"),
    # Capítulo XIV — Sistema geniturinário
    _EntradaAmostra("N18", "Doença renal crônica [DRC]"),
    _EntradaAmostra("N30", "Cistite", "U71"),
    _EntradaAmostra("N39.0", "Infecção do trato urinário, de localização não especificada", "U71"),
    _EntradaAmostra("N40", "Hiperplasia prostática benigna"),
    _EntradaAmostra("N76.0", "Vaginite aguda"),
    _EntradaAmostra("N80", "Endometriose"),
    # Capítulo XVIII — Sintomas, sinais e achados anormais
    _EntradaAmostra("R05", "Tosse", "R05"),
    _EntradaAmostra("R06", "Anormalidades da respiração"),
    _EntradaAmostra("R07", "Dores na garganta e no tórax"),
    _EntradaAmostra("R10", "Dores abdominais e pélvicas"),
    _EntradaAmostra("R11", "Náusea e vômito"),
    _EntradaAmostra("R42", "Tontura e instabilidade"),
    _EntradaAmostra("R50", "Febre de origem desconhecida"),
    _EntradaAmostra("R51", "Cefaleia"),
    _EntradaAmostra("R52", "Dor, não especificada"),
    _EntradaAmostra("R53", "Mal-estar e fadiga"),
    _EntradaAmostra("R55", "Síncope e colapso"),
    _EntradaAmostra("R56", "Convulsões, não especificadas"),
    # Capítulo XIX — Lesões, envenenamentos e causas externas
    _EntradaAmostra("S06", "Lesão intracraniana"),
    _EntradaAmostra("S52", "Fratura do antebraço"),
    _EntradaAmostra("S72", "Fratura do fêmur"),
    _EntradaAmostra("S82", "Fratura da perna, incluindo o tornozelo"),
    _EntradaAmostra("T14", "Lesão traumática de localização múltipla não especificada"),
    _EntradaAmostra("T78.4", "Anafilaxia, não especificada"),
    # Capítulo XXI — Fatores que influenciam o estado de saúde
    _EntradaAmostra("Z00", "Exames gerais de rotina"),
    _EntradaAmostra("Z32", "Exames de gravidez e de contracepção"),
    _EntradaAmostra("Z34", "Supervisão de gravidez normal", "W14"),
    # Capítulo XXII — Códigos para propósitos especiais
    _EntradaAmostra(
        "U07.1",
        "COVID-19, vírus identificado",
        None,
        "Codificação SUS: casos confirmados por exame laboratorial ou critério clínico-epidemiológico.",
    ),
    _EntradaAmostra(
        "U07.2",
        "Tabagismo",
        None,
        "Código de uso nacional no Brasil (SUS); na CID-10 internacional, U07.2 corresponde a COVID-19, vírus não identificado.",
    ),
)


# ---------------------------------------------------------------------------
# Normalização de texto e índices em memória (functools.lru_cache)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=8192)
def _normalizar_texto(texto: str) -> str:
    """Remove acentos (NFKD) e padroniza maiúsculas/minúsculas ("casefold").

    Garante que "Insuficiência Cardíaca", "insuficiencia cardiaca" e
    "INSUFICIENCIA CARDIACA" gerem a mesma chave de busca.

    Args:
        texto: Texto original (descrição ou termo digitado).

    Returns:
        Texto sem acentos, minúsculo e com espaços preservados.
    """
    decomposto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(caractere for caractere in decomposto if not unicodedata.combining(caractere))


@lru_cache(maxsize=2048)
def _normalizar_codigo(codigo: str) -> str:
    """Padroniza um código para comparação (maiúsculas, sem pontos/espaços).

    Args:
        codigo: Código ou prefixo digitado (ex.: "i50.", "I50.9").

    Returns:
        Código normalizado (ex.: "I50", "I509").
    """
    return re.sub(r"[^A-Z0-9]", "", codigo.strip().upper())


def _chave_ordenacao(item: ItemCID10) -> tuple[str, int, tuple[int, ...]]:
    """Chave de ordenação natural: letra, número e subcategorias do código."""
    partes = item.codigo.split(".", 1)
    subcategorias = tuple(int(parte) for parte in partes[1].split(".")) if len(partes) > 1 else ()
    return (partes[0][0], int(partes[0][1:3]), subcategorias)


@lru_cache(maxsize=1)
def _catalogo_ordenado() -> tuple[ItemCID10, ...]:
    """Monta o catálogo completo (amostra APS) ordenado por código CID-10.

    Executa uma única vez por processo; o resultado fica retido no cache do
    interpretador (functools.lru_cache) e é reaproveitado por todas as buscas.

    Returns:
        Tupla imutável com todos os itens do catálogo.
    """
    itens = [
        ItemCID10(
            codigo=entrada.codigo,
            descricao=entrada.descricao,
            capitulo=_capitulo_do_codigo(entrada.codigo),
            ciap2_sugerido=entrada.ciap2,
            observacao=entrada.observacao,
        )
        for entrada in _AMOSTRA_APS
    ]
    itens.sort(key=_chave_ordenacao)
    return tuple(itens)


@lru_cache(maxsize=1)
def _indice_por_codigo() -> Mapping[str, ItemCID10]:
    """Índice por código oficial (somente leitura) para consulta exata."""
    return MappingProxyType({item.codigo: item for item in _catalogo_ordenado()})


@lru_cache(maxsize=1)
def _indice_por_codigo_plano() -> Mapping[str, ItemCID10]:
    """Índice por código sem ponto (somente leitura) para tolerar "J159"."""
    return MappingProxyType({item.codigo.replace(".", ""): item for item in _catalogo_ordenado()})


@lru_cache(maxsize=256)
def _correspondencias_por_prefixo(prefixo_normalizado: str, limite: int) -> tuple[ItemCID10, ...]:
    """Devolve itens cujo código normalizado começa pelo prefixo informado.

    A amostra é pequena (ordem de centenas), portanto a varredura linear no
    índice em memória é suficiente e fica retida no cache (lru_cache).

    Args:
        prefixo_normalizado: Prefixo já normalizado (ex.: "I50", "I509").
        limite: Quantidade máxima de itens retornados (1 a 100).

    Returns:
        Tupla de itens ordenados por código, limitada ao teto informado.
    """
    itens = tuple(
        item
        for item in _catalogo_ordenado()
        if _normalizar_codigo(item.codigo).startswith(prefixo_normalizado)
    )
    return itens[:limite]


@lru_cache(maxsize=512)
def _correspondencias_por_descricao(termo_normalizado: str, limite: int) -> tuple[ItemCID10, ...]:
    """Devolve itens cuja descrição (normalizada) casa com todos os termos.

    Ranking determinístico: correspondência da frase completa primeiro
    (posição 0) e, em seguida, itens que contêm todos os termos; dentro de
    cada nível, ordena por código CID-10.

    Args:
        termo_normalizado: Termo digitado, já normalizado (sem acentos).
        limite: Quantidade máxima de itens retornados (1 a 100).

    Returns:
        Tupla de itens ordenados por relevância e código.

    Raises:
        ConsultaCID10InvalidaError: Se nenhum termo tiver tamanho mínimo.
    """
    termos = tuple(t for t in termo_normalizado.split() if len(t) >= _TAMANHO_MINIMO_TERMO)
    if not termos:
        raise ConsultaCID10InvalidaError(
            f"Informe ao menos um termo de descrição com {_TAMANHO_MINIMO_TERMO} ou mais caracteres."
        )
    frase = " ".join(termos)
    classificadas: list[tuple[int, ItemCID10]] = []
    for item in _catalogo_ordenado():
        descricao_normalizada = _normalizar_texto(item.descricao)
        if frase in descricao_normalizada:
            classificadas.append((0, item))
        elif all(termo in descricao_normalizada for termo in termos):
            classificadas.append((1, item))
    classificadas.sort(key=lambda par: (par[0], par[1].codigo))
    return tuple(item for _, item in classificadas[:limite])


@lru_cache(maxsize=128)
def _agrupar_itens(itens: tuple[ItemCID10, ...]) -> tuple[GrupoCapituloCID10, ...]:
    """Agrupa itens pelos capítulos da CID-10, preservando a ordem oficial.

    Args:
        itens: Itens a agrupar (resultado de uma busca ou o catálogo inteiro).

    Returns:
        Grupos por capítulo, apenas para capítulos com itens.
    """
    por_capitulo: dict[CapituloCID10, list[ItemCID10]] = {}
    for item in itens:
        por_capitulo.setdefault(item.capitulo, []).append(item)
    return tuple(
        GrupoCapituloCID10(
            capitulo=capitulo,
            rotulo=capitulo.rotulo,
            titulo=capitulo.titulo,
            faixa=capitulo.faixa,
            total=len(itens_do_capitulo),
            itens=tuple(itens_do_capitulo),
        )
        for capitulo in CapituloCID10
        if (itens_do_capitulo := por_capitulo.get(capitulo))
    )


@lru_cache(maxsize=1)
def _agrupar_catalogo_completo() -> tuple[GrupoCapituloCID10, ...]:
    """Agrupa o catálogo completo por capítulo (resultado fixo, em cache)."""
    return _agrupar_itens(_catalogo_ordenado())


def _validar_limite(limite: int) -> int:
    """Valida o limite de resultados (inteiro entre 1 e LIMITE_MAXIMO)."""
    if not isinstance(limite, int) or isinstance(limite, bool) or not 1 <= limite <= LIMITE_MAXIMO:
        raise ConsultaCID10InvalidaError(
            f"O limite deve ser um inteiro entre 1 e {LIMITE_MAXIMO} (recebido: {limite!r})."
        )
    return limite


def _validar_consulta(texto: str, campo: str) -> str:
    """Valida que a consulta é um texto não vazio e remove espaços sobrando."""
    if not isinstance(texto, str) or not texto.strip():
        raise ConsultaCID10InvalidaError(f"Informe um {campo} válido para a busca.")
    return texto.strip()


@lru_cache(maxsize=1)
def _instancia_padrao() -> "CatalogoCID10":
    """Instância única do catálogo compartilhada pela aplicação (singleton)."""
    return CatalogoCID10()


# ---------------------------------------------------------------------------
# Serviço principal — CatalogoCID10
# ---------------------------------------------------------------------------


class CatalogoCID10:
    """Catálogo consultável da CID-10 com amostra dos códigos mais usados na APS.

    A classe não mantém estado mutável: os índices (catálogo ordenado,
    índices por código e agrupamentos) residem no cache do módulo construído
    com ``functools.lru_cache``, e as consultas repetidas são servidas
    diretamente da memória.

    Exemplos:
        >>> catalogo = CatalogoCID10.padrao()
        >>> catalogo.buscar_por_prefixo("I50").itens[0].codigo
        'I50'
        >>> catalogo.buscar_por_descricao("insuficiencia cardiaca").itens[0].codigo
        'I50'
        >>> catalogo.buscar("asma").itens[0].codigo
        'J45'
    """

    def __init__(self) -> None:
        """Inicializa a referência ao catálogo indexado em memória."""
        self._tamanho: int = len(_catalogo_ordenado())

    # ------------------------------------------------------------------
    # Propriedades e instância padrão
    # ------------------------------------------------------------------

    @classmethod
    def padrao(cls) -> "CatalogoCID10":
        """Devolve a instância única do catálogo (cache por processo)."""
        return _instancia_padrao()

    @property
    def total_registros(self) -> int:
        """Quantidade de códigos carregados na amostra da APS."""
        return self._tamanho

    # ------------------------------------------------------------------
    # Busca por prefixo (código CID-10)
    # ------------------------------------------------------------------

    def buscar_por_prefixo(self, prefixo: str, *, limite: int = LIMITE_PADRAO) -> ResultadoBuscaCID10:
        """Busca itens por prefixo de código CID-10.

        Aceita códigos incompletos ou com ponto: "i50", "I50.", "I50.9".
        Quando o prefixo com subcategoria ("I50.9" → "I509") não encontra
        nada, a busca é repetida apenas com a categoria ("I50"), devolvendo
        a família do código — comportamento útil no autocomplete.

        Args:
            prefixo: Prefixo de código digitado (ex.: "I50").
            limite: Quantidade máxima de itens (1 a 100).

        Returns:
            Resultado com os itens cujo código começa pelo prefixo.

        Raises:
            ConsultaCID10InvalidaError: Se o prefixo ou o limite forem inválidos.
        """
        limite_validado = _validar_limite(limite)
        consulta = _validar_consulta(prefixo, "prefixo de código")
        normalizado = _normalizar_codigo(consulta)
        if not re.fullmatch(r"[A-Z]\d{0,3}", normalizado):
            raise ConsultaCID10InvalidaError(
                "Prefixo inválido: informe uma letra seguida de até 3 dígitos (ex.: 'I50')."
            )
        itens = _correspondencias_por_prefixo(normalizado, limite_validado)
        if not itens and "." in consulta:
            # Sem subcategoria na amostra: recua para a categoria (I50.9 → I50).
            itens = _correspondencias_por_prefixo(normalizado.split(".")[0], limite_validado)
        return self._montar_resultado(consulta, "prefixo", itens)

    # ------------------------------------------------------------------
    # Busca por termo de descrição (com normalização de acentos)
    # ------------------------------------------------------------------

    def buscar_por_descricao(self, termo: str, *, limite: int = LIMITE_PADRAO) -> ResultadoBuscaCID10:
        """Busca itens pelo texto da descrição, ignorando acentos e caixa.

        Todos os termos digitados (com 2 ou mais caracteres) devem constar
        da descrição normalizada; a frase completa digitada tem prioridade.

        Args:
            termo: Termo de busca (ex.: "insuficiencia cardiaca").
            limite: Quantidade máxima de itens (1 a 100).

        Returns:
            Resultado com os itens cuja descrição casa com o termo.

        Raises:
            ConsultaCID10InvalidaError: Se o termo ou o limite forem inválidos.
        """
        limite_validado = _validar_limite(limite)
        consulta = _validar_consulta(termo, "termo de descrição")
        termo_normalizado = _normalizar_texto(consulta)
        itens = _correspondencias_por_descricao(termo_normalizado, limite_validado)
        return self._montar_resultado(consulta, "descricao", itens)

    # ------------------------------------------------------------------
    # Busca híbrida (para autocomplete único na interface)
    # ------------------------------------------------------------------

    def buscar(self, consulta: str, *, limite: int = LIMITE_PADRAO) -> ResultadoBuscaCID10:
        """Busca híbrida: prefixo quando a consulta é um código, senão descrição.

        Regra de inferência:
            - Código completo ("I50", "j15.9", "U07.1") ou prefixo parcial
              ("I", "I5") → busca por prefixo;
            - Texto ("asma", "dor lombar") → busca por descrição, com
              recaída para prefixo apenas quando o texto é um prefixo
              parcial de código.

        Args:
            consulta: Consulta livre digitada pelo profissional.
            limite: Quantidade máxima de itens (1 a 100).

        Returns:
            Resultado da busca pelo critério inferido.

        Raises:
            ConsultaCID10InvalidaError: Se a consulta ou o limite forem inválidos.
        """
        limite_validado = _validar_limite(limite)
        consulta_normalizada = _validar_consulta(consulta, "consulta")
        consulta_limpa = consulta_normalizada.rstrip(". ").strip()
        if _PADRAO_CODIGO.fullmatch(consulta_limpa) or _PADRAO_PREFIXO_PARCIAL.fullmatch(consulta_limpa):
            itens = _correspondencias_por_prefixo(_normalizar_codigo(consulta_limpa), limite_validado)
            if not itens and _PADRAO_CODIGO.fullmatch(consulta_limpa):
                # Subcategoria ausente na amostra: recua para a categoria.
                itens = _correspondencias_por_prefixo(
                    _normalizar_codigo(consulta_limpa.split(".")[0]), limite_validado
                )
            return self._montar_resultado(consulta_normalizada, "hibrida", itens)
        termo_normalizado = _normalizar_texto(consulta_normalizada)
        itens = _correspondencias_por_descricao(termo_normalizado, limite_validado)
        return self._montar_resultado(consulta_normalizada, "hibrida", itens)

    # ------------------------------------------------------------------
    # Consulta exata, capítulos e estatísticas
    # ------------------------------------------------------------------

    def obter(self, codigo: str) -> ItemCID10 | None:
        """Devolve o item pelo código exato (tolera ponto omitido).

        Args:
            codigo: Código oficial (ex.: "J15.9") ou sem ponto (ex.: "J159").

        Returns:
            Item correspondente, ou ``None`` se não houver correspondência.
        """
        consulta = _validar_consulta(codigo, "código")
        item = _indice_por_codigo().get(consulta.upper())
        if item is None:
            item = _indice_por_codigo_plano().get(_normalizar_codigo(consulta))
        return item

    def agrupar_por_capitulo(
        self, itens: Sequence[ItemCID10] | None = None
    ) -> tuple[GrupoCapituloCID10, ...]:
        """Agrupa itens pelos capítulos da CID-10 para exibição hierárquica.

        Args:
            itens: Itens a agrupar; quando ``None``, agrupa o catálogo
                completo (resultado fixo retido em cache).

        Returns:
            Grupos por capítulo, na ordem oficial I a XXII (só capítulos
            com itens).
        """
        if itens is None:
            return _agrupar_catalogo_completo()
        return _agrupar_itens(tuple(itens))

    def capitulos(self) -> tuple[CapituloCID10, ...]:
        """Devolve os capítulos com itens na amostra, na ordem oficial."""
        return tuple(grupo.capitulo for grupo in _agrupar_catalogo_completo())

    def estatisticas(self) -> Mapping[str, int]:
        """Resumo do catálogo em memória (total de códigos e de capítulos).

        Returns:
            Mapeamento somente leitura com "total_codigos" e "total_capitulos".
        """
        return MappingProxyType(
            {
                "total_codigos": self._tamanho,
                "total_capitulos": len(_agrupar_catalogo_completo()),
            }
        )

    # ------------------------------------------------------------------
    # Utilitários internos
    # ------------------------------------------------------------------

    def _montar_resultado(
        self,
        consulta: str,
        criterio: Literal["prefixo", "descricao", "hibrida"],
        itens: tuple[ItemCID10, ...],
    ) -> ResultadoBuscaCID10:
        """Monta o resultado consolidado com o registro de data/hora (UTC)."""
        return ResultadoBuscaCID10(
            consulta=consulta,
            criterio=criterio,
            total=len(itens),
            itens=itens,
            consultado_em=datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------------
# Demonstração local (python -m app.services.busca_cid10)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    catalogo = CatalogoCID10.padrao()
    print(f"Catálogo CID-10 (amostra APS): {catalogo.total_registros} códigos")
    print(f"Capítulos com itens: {', '.join(c.roman for c in catalogo.capitulos())}")

    print("\nBusca por prefixo 'I50':")
    for item in catalogo.buscar_por_prefixo("I50").itens:
        print(f"  {item.codigo} — {item.descricao}")

    print("\nBusca por descrição 'insuficiencia cardiaca' (sem acento):")
    for item in catalogo.buscar_por_descricao("insuficiencia cardiaca").itens:
        print(f"  {item.codigo} — {item.descricao}")

    print("\nBusca híbrida por 'asma':")
    for item in catalogo.buscar("asma").itens:
        print(f"  {item.codigo} — {item.descricao}")

    print("\nAgrupamento por capítulo (total por capítulo):")
    for grupo in catalogo.agrupar_por_capitulo():
        print(f"  {grupo.rotulo} ({grupo.faixa}): {grupo.total} código(s)")
