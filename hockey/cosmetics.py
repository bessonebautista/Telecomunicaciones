"""Las mesas y las palas: SOLO cambian como se ven.

La fisica es identica en todas. Aqui no hay ni una constante de movimiento,
solo colores, brillos y detalles de dibujo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import settings as S


@dataclass(frozen=True)
class Mesa:
    key: str
    name: str
    # Colores del hielo y de las lineas
    hielo: tuple
    hielo_oscuro: tuple
    linea: tuple
    marco: tuple
    brillo: float = 0.0  # intensidad del efecto de brillo
    precio: int = 0
    solo_ganando: bool = False
    desc: str = ""
    # Estetica extra: patron de fondo y color de los adornos
    patron: str = "liso"  # "liso", "rayas", "rejilla", "ondas", "circuito", "veta"
    acento: tuple = (0, 0, 0)  # color de los adornos decorativos
    estrellas: bool = False  # motas doradas de fondo


BASICA = Mesa(
    key="mesa_basica",
    name="Basica",
    hielo=(38, 62, 104),
    hielo_oscuro=(30, 48, 82),
    linea=(228, 236, 250),
    marco=(58, 78, 112),
    patron="rejilla",
    acento=(74, 112, 168),
    desc="La de siempre. Azul con rejilla fina y marco gris.",
)

HIELO = Mesa(
    key="mesa_hielo",
    name="Hielo",
    hielo=(150, 214, 240),
    hielo_oscuro=(58, 128, 166),
    linea=(18, 74, 110),
    marco=(214, 244, 255),
    brillo=0.20,
    precio=S.COSMETIC_PRICES["mesa_hielo"],
    patron="ondas",
    acento=(238, 252, 255),
    estrellas=True,
    desc="Blanca y gelida, con ondas y destellos.",
)

METAL = Mesa(
    key="mesa_metal",
    name="Metal",
    hielo=(84, 88, 104),
    hielo_oscuro=(54, 58, 72),
    linea=(232, 238, 248),
    marco=(176, 184, 204),
    brillo=0.30,
    precio=S.COSMETIC_PRICES["mesa_metal"],
    patron="rayas",
    acento=(150, 158, 178),
    desc="Cepillado metálico con brillo marcado.",
)

NEON = Mesa(
    key="mesa_neon",
    name="Neon",
    hielo=(26, 22, 58),
    hielo_oscuro=(16, 14, 38),
    linea=(255, 92, 220),
    marco=(84, 236, 255),
    brillo=0.45,
    precio=260,
    patron="circuito",
    acento=(96, 232, 255),
    desc="Circuito neon rosa y cian sobre fondo oscuro.",
)

SUPREMA = Mesa(
    key="mesa_suprema",
    name="Suprema",
    hielo=(64, 30, 92),
    hielo_oscuro=(40, 18, 62),
    linea=(255, 216, 112),
    marco=(255, 178, 60),
    brillo=0.55,
    solo_ganando=True,
    patron="veta",
    acento=(255, 198, 74),
    estrellas=True,
    desc="La de campeón. Morada con vetas de oro.",
)

TODAS_LAS_MESAS = (BASICA, HIELO, METAL, NEON, SUPREMA)
MESAS_POR_CLAVE = {m.key: m for m in TODAS_LAS_MESAS}


@dataclass(frozen=True)
class Pala:
    key: str
    name: str
    cuerpo: tuple
    borde: tuple
    detalle: str  # "liso", "rayas", "flama", "estrella"
    precio: int = 0
    solo_ganando: bool = False
    desc: str = ""


PALA_BASICA = Pala(
    key="pala_basica",
    name="Basica",
    cuerpo=(70, 120, 190),
    borde=(196, 222, 255),
    detalle="liso",
    desc="Pala estándar de la casa.",
)

PALA_PRO = Pala(
    key="pala_pro",
    name="Pro",
    cuerpo=(58, 92, 74),
    borde=(178, 240, 200),
    detalle="rayas",
    precio=S.COSMETIC_PRICES["pala_pro"],
    desc="Verde con dos rayas laterales.",
)

PALA_FUEGO = Pala(
    key="pala_fuego",
    name="Fuego",
    cuerpo=(168, 62, 40),
    borde=(255, 190, 120),
    detalle="flama",
    precio=S.COSMETIC_PRICES["pala_fuego"],
    desc="Naranja con llamas en el borde.",
)

PALA_CANELA = Pala(
    key="pala_canela",
    name="Canela",
    cuerpo=(58, 48, 92),
    borde=(214, 176, 255),
    detalle="estrella",
    solo_ganando=True,
    desc="La de campeón, con estrella en el centro.",
)

TODAS_LAS_PALAS = (PALA_BASICA, PALA_PRO, PALA_FUEGO, PALA_CANELA)
PALAS_POR_CLAVE = {p.key: p for p in TODAS_LAS_PALAS}


@dataclass(frozen=True)
class Puck:
    key: str
    name: str
    cuerpo: tuple
    borde: tuple
    estilo: str  # "liso", "grieta", "oro", "llama"
    precio: int = 0
    solo_ganando: bool = False
    desc: str = ""


PUCK_CLASICA = Puck(
    key="puck_clasica",
    name="Clasica",
    cuerpo=(24, 28, 38),
    borde=(226, 232, 244),
    estilo="liso",
    desc="Puck negra de siempre.",
)

PUCK_oro = Puck(
    key="puck_oro",
    name="Oro",
    cuerpo=(176, 134, 24),
    borde=(255, 224, 120),
    estilo="oro",
    precio=S.COSMETIC_PRICES["puck_oro"],
    desc="Dorado, como el premio de campeón.",
)

PUCK_FUEGO = Puck(
    key="puck_fuego",
    name="Fuego",
    cuerpo=(150, 40, 30),
    borde=(255, 150, 90),
    estilo="llama",
    precio=S.COSMETIC_PRICES["puck_fuego"],
    desc="Roja con llamas al girar.",
)

PUCK_CANELA = Puck(
    key="puck_canela",
    name="Canela",
    cuerpo=(96, 24, 118),
    borde=(238, 200, 255),
    estilo="grieta",
    solo_ganando=True,
    desc="Violeta de campeón, con grietas de luz.",
)

TODAS_LAS_PUCKS = (PUCK_CLASICA, PUCK_oro, PUCK_FUEGO, PUCK_CANELA)
PUCKS_POR_CLAVE = {p.key: p for p in TODAS_LAS_PUCKS}
