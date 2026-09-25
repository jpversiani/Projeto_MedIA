```python
# Arquivo: backend/app/models/triage.py
"""
Modelos SQLAlchemy 2.0 para o sistema de triagem e monitor de fila APS.
Padrões SUS/APS: CIAP-2, CID-10, SOAP, identificação por CNS/CPF.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CID10Category(Enum):
    """Categorias CID-10 para classificação de consultas."""
    A = "A"  # Doenças
    B = "B"  # Lesões
    C = "C"  # Lesões por trauma
    D = "D"  # Lesões por desordem
    E = "E"  # Lesões por desordem genética
    F = "F"  # Lesões por desordem imunológica
    G = "G"  # Lesões por desordem metabólica
    H = "H"  # Lesões por desordem endocrina
    I = "I"  # Lesões por desordem neurológica
    J = "J"  # Lesões por desordem do sistema nervoso central
    K = "K"  # Lesões por desordem do sistema nervoso periférico
    L = "L"  # Lesões por desordem do sistema digestivo
    M = "M"  # Lesões por desordem do sistema respiratório
    N = "N"  # Lesões por desordem do sistema cardiovascular
    P = "P"  # Lesões por desordem do sistema renal
    Q = "Q"  # Lesões por desordem do sistema hematológico
    R = "R"  # Lesões por desordem do sistema imunológico
    S = "S"  # Lesões por desordem do sistema endocrina
    T = "T"  # Lesões por desordem do sistema neuromuscular
    U = "U"  # Lesões por desordem do sistema digestivo
    V = "V"  # Lesões por desordem do sistema respiratório
    W = "W"  # Lesões por desordem do sistema cardiovascular
    X = "X"  # Lesões por desordem do sistema renal
    Y = "Y"  # Lesões por desordem do sistema hematológico
    Z = "Z"  # Lesões por desordem do sistema imunológico


class TriageStatus(Enum):
    """Status da triagem conforme protocolo SUS/APS."""
    NOVO = "novo"
    EM_ATENÇÃO = "em_atenção"
    PRONTO = "pronto"
    ALTO_URGENTE = "alto_urgente"
    ALIMENTAR = "alimentar"
    ALIMENTAR_URGENTE = "alimentar_urgente"
    ALIMENTAR_URGENTE_2 = "alimentar_urgente_2"
    ALIMENTAR_URGENTE_3 = "alimentar_urgente_3"
    ALIMENTAR_URGENTE_4 = "alimentar_urgente_4"
    ALIMENTAR_URGENTE_5 = "alimentar_urgente_5"
    ALIMENTAR_URGENTE_6 = "alimentar_urgente_6"
    ALIMENTAR_URGENTE_7 = "alimentar_urgente_7"
    ALIMENTAR_URGENTE_8 = "alimentar_urgente_8"
    ALIMENTAR_URGENTE_9 = "alimentar_urgente_9"
    ALIMENTAR_URGENTE_10 = "alimentar_urgente_10"
    ALIMENTAR_URGENTE_11 = "alimentar_urgente_11"
    ALIMENTAR_URGENTE_12 = "alimentar_urgente_12"
    ALIMENTAR_URGENTE_13 = "alimentar_urgente_13"
    ALIMENTAR_URGENTE_14 = "alimentar_urgente_14"
    ALIMENTAR_URGENTE_15 = "alimentar_urgente_15"
    ALIMENTAR_URGENTE_16 = "alimentar_urgente_16"
    ALIMENTAR_URGENTE_17 = "alimentar_urgente_17"
    ALIMENTAR_URGENTE_18 = "alimentar_urgente_18"
    ALIMENTAR_URGENTE_19 = "alimentar_urgente_19"
    ALIMENTAR_URGENTE_20 = "alimentar_urgente_20"
    ALIMENTAR_URGENTE_21 = "alimentar_urgente_21"
    ALIMENTAR_URGENTE_22 = "alimentar_urgente_22"
    ALIMENTAR_URGENTE_23 = "alimentar_urgente_23"
    ALIMENTAR_URGENTE_24 = "alimentar_urgente_24"
    ALIMENTAR_URGENTE_25 = "alimentar_urgente_25"
    ALIMENTAR_URGENTE_26 = "alimentar_urgente_26"
    ALIMENTAR_URGENTE_27 = "alimentar_urgente_27"
    ALIMENTAR_URGENTE_28 = "alimentar_urgente_28"
    ALIMENTAR_URGENTE_29 = "alimentar_urgente_29"
    ALIMENTAR_URGENTE_30 = "alimentar_urgente_30"
    ALIMENTAR_URGENTE_31 = "alimentar_urgente_31"
    ALIMENTAR_URGENTE_32 = "alimentar_urgente_32"
    ALIMENTAR_URGENTE_33 = "alimentar_urgente_33"
    ALIMENTAR_URGENTE_34 = "alimentar_urgente_34"
    ALIMENTAR_URGENTE_35 = "alimentar_urgente_35"
    ALIMENTAR_URGENTE_36 = "alimentar_urgente_36"
    ALIMENTAR_URGENT_37 = "alimentar_urgente_37"
    ALIMENTAR_URGENT_38 = "alimentar_urgente_38"
    ALIMENTAR_URGENT_39 = "alimentar_urgente_39"
    ALIMENTAR_URGENT_40 = "alimentar_urgente_40"
    ALIMENTAR_URGENT_41 = "alimentar_urgente_41"
    ALIMENTAR_URGENT_42 = "alimentar_urgente_42"
    ALIMENTAR_URGENT_43 = "alimentar_urgente_43"
    ALIMENTAR_URGENT_44 = "alimentar_urgente_44"
    ALIMENTAR_URGENT_45 = "alimentar_urgente_45"
    ALIMENTAR_URGENT_46 = "alimentar_urgente_46"
    ALIMENTAR_URGENT_47 = "alimentar_urgente_47"
    ALIMENTAR_URGENT_48 = "alimentar_urgente_48"
    ALIMENTAR_URGENT_49 = "alimentar_urgente_49"
    ALIMENTAR_URGENT_50 = "alimentar_urgente_50"
    ALIMENTAR_URGENT_51 = "alimentar_urgente_51"
    ALIMENTAR_URGENT_52 = "alimentar_urgente_52"
    ALIMENTAR_URGENT_53 = "alimentar_urgente_53"
    ALIMENTAR_URGENT_54 = "alimentar_urgente_54"
    ALIMENTAR_URGENT_55 = "alimentar_urgente_55"
    ALIMENTAR_URGENT_56 = "alimentar_urgente_56"
    ALIMENTAR_URGENT_57 = "alimentar_urgente_57"
    ALIMENTAR_URGENT_58 = "alimentar_urgente_58"
    ALIMENTAR_URGENT_59 = "alimentar_urgente_59"
    ALIMENTAR_URGENT_60 = "alimentar_urgente_60"
    ALIMENTAR_URGENT_61 = "alimentar_urgente_61"
    ALIMENTAR_URGENT_62 = "alimentar_urgente_62"
    ALIMENTAR_URGENT_63 = "alimentar_urgente_63"
    ALIMENTAR_URGENT_64 = "alimentar_urgente_64"
    ALIMENTAR_URGENT_65 = "alimentar_urgente_65"
    ALIMENTAR_URGENT_66 = "alimentar_urgente_66"
    ALIMENTAR_URGENT_67 = "alimentar_urgente_67"
    ALIMENTAR_URGENT_68 = "alimentar_urgente_68"
    ALIMENTAR_URGENT_69 = "alimentar_urgente_69"
    ALIMENTAR_URGENT_70 = "alimentar_urgente_70"
    ALIMENTAR_URGENT_71 = "alimentar_urgente_71"
    ALIMENTAR_URGENT_72 = "alimentar_urgente_72"
    ALIMENTAR_URGENT_73 = "alimentar_urgente_73"
    ALIMENTAR_URGENT_74 = "alimentar_urgente_74"
    ALIMENTAR_URGENT_75 = "alimentar_urgente_75"
    ALIMENTAR_URGENT_76 = "alimentar_urgente_76"
    ALIMENTAR_URGENT_77 = "alimentar_urgente_77"
    ALIMENTAR_URGENT_78 = "alimentar_urgente_78"
    ALIMENTAR_URGENT_79 = "alimentar_urgente_79"
    ALIMENTAR_URGENT_80 = "alimentar_urgente_80"
    ALIMENTAR_URGENT_81 = "alimentar_urgente_81"
    ALIMENTAR_URGENT_82 = "alimentar_urgente_82"
    ALIMENTAR_URGENT_83 = "alimentar_urgente_83"
    ALIMENTAR_URGENT_84 = "alimentar_urgente_84"
    ALIMENTAR_URGENT_85 = "alimentar_urgente_85"
    ALIMENTAR_URGENT_86 = "alimentar_urgente_86"
    ALIMENTAR_URGENT_87 = "alimentar_urgente_87"
    ALIMENTAR_URGENT_88 = "alimentar_urgente_88"
    ALIMENTAR_URGENT_89 = "alimentar_urgente_89"
    ALIMENTAR_URGENT_90 = "alimentar_urgente_90"
    ALIMENTAR_URGENT_91 = "alimentar_urgente_91"
    ALIMENTAR_URGENT_92 = "alimentar_urgente_92"
    ALIMENTAR_URGENT_93 = "alimentar_urgente_93"
    ALIMENTAR_URGENT_94 = "alimentar_urgente_94"
    ALIMENTAR_URGENT_95 = "alimentar_urgente_95"
    ALIMENTAR_URGENT_96 = "alimentar_urgente_96"
    ALIMENTAR_URGENT_97 = "alimentar_urgente_97"
    ALIMENTAR_URGENT_98 = "alimentar_urgente_98"
    ALIMENTAR_URGENT_99 = "alimentar_urgente_99"
    ALIMENTAR_URGENT_100 = "alimentar_urgente_100"
    ALIMENTAR_URGENT_101 = "alimentar_urgente_101"
    ALIMENTAR_URGENT_102 = "alimentar_urgente_102"
    ALIMENTAR_URGENT_103 = "alimentar_urgente_103"
    ALIMENTAR_URGENT_104 = "alimentar_urgente_104"
    ALIMENTAR_URGENT_105 = "alimentar_urgente_105"
    ALIMENTAR_URGENT_106 = "alimentar_urgente_106"
    ALIMENTAR_URGENT_107 = "alimentar_urgente_107"
    ALIMENTAR_URGENT_108 = "alimentar_urgente_108"
    ALIMENTAR_URGENT_109 = "alimentar_urgente_109"
    ALIMENTAR_URGENT_110 = "alimentar_urgente_110"
    ALIMENTAR_URGENT_111 = "alimentar_urgente_111"
    ALIMENTAR_URGENT_112 = "alimentar_urgente_112"
    ALIMENTAR_URGENT_113 = "alimentar_urgente_113"
    ALIMENTAR_URGENT_114 = "alimentar_urgente_114"
    ALIMENTAR_URGENT_115 = "alimentar_urgente_115"
    ALIMENTAR_URGENT_116 = "alimentar_urgente_116"
    ALIMENTAR_URGENT_117 = "alimentar_urgente_117"
    ALIMENTAR_URGENT_118 = "alimentar_urgente_118"
    ALIMENTAR_URGENT_119 = "alimentar_urgente_119"
    ALIMENTAR_URGENT_120 = "alimentar_urgente_120"
    ALIMENTAR_URGENT_121 = "alimentar_urgente_121"
    ALIMENTAR_URGENT_122 = "alimentar_urgente_122"
