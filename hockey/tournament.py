"""El torneo: octavos, cuartos, semifinal y final.

Cada ronda es un partido. Las monedas se ganan segun hasta donde llegas, y
solo el campeon se lleva el bote grande. El bracket esta fijado, asi que
siempre juegas las mismas rondas.
"""

from __future__ import annotations

# Cada rival tiene su propio caracter: nombre, lema, color y emblema. El emblema
# se dibuja en la pantalla de presentacion, para que se te quede quien tienes
# enfrente antes de empezar el partido.
#
#   (nombre, nivel, lema, color RGB, emblema)
#   emblema: "rayo", "furia", "corona", "robot", "bestia", "fantasma"
BRACKET = (
    (
        "Rayo",
        "Novato",
        "Rápido y nervioso",
        (255, 226, 96),
        "rayo",
    ),
    (
        "Tormenta",
        "Dificil",
        "No perdona un fallo",
        (120, 200, 255),
        "furia",
    ),
    (
        "Titan",
        "Experto",
        "Muro de acero",
        (196, 132, 255),
        "corona",
    ),
    (
        "Rey Neon",
        "Imposible",
        "La máquina perfecta",
        (255, 92, 122),
        "robot",
    ),
)

RONDAS = ("Octavos", "Cuartos", "Semifinal", "Final")

# Monedas por ronda alcanzada y por ronda ganada.
MONEDAS_POR_RONDA = (40, 70, 110, 160)
MONEDAS_POR_GANAR = (60, 100, 150, 220)
BOTE_CAMPEON = 350


def ronda_actual(alcanzada: int) -> str | None:
    if alcanzada < 0 or alcanzada >= len(RONDAS):
        return None
    return RONDAS[alcanzada]


def rival_de(alcanzada: int) -> tuple:
    """Datos completos del rival: (nombre, nivel, lema, color, emblema)."""
    return BRACKET[max(0, min(alcanzada, len(BRACKET) - 1))]


def nivel_de(alcanzada: int) -> str:
    """Nivel de la IA de una ronda, ya recortado al rango valido."""
    from .ai import NIVELES

    nombre = rival_de(alcanzada)[1]
    return nombre if nombre in NIVELES else "Normal"


def monedas_ganadas(alcanzada: int, gano_ronda: bool) -> int:
    """Monedas por avanzar en el torneo.

    ``alcanzada`` es la ronda MAXIMA a la que llegaste (0 = octavos).
    Cuanto mas lejos, mas monedas. Si llegaste a la final pero perdiste, te
    llevas lo de haber llegado, pero no el bote de campeon.
    """
    if alcanzada < 0:
        return 0
    alcance = MONEDAS_POR_RONDA[min(alcanzada, len(MONEDAS_POR_RONDA) - 1)]
    if not gano_ronda:
        # Perdiste en esta ronda: te llevas lo de haber llegado hasta ella.
        return alcance
    gano = MONEDAS_POR_GANAR[min(alcanzada, len(MONEDAS_POR_GANAR) - 1)]
    return alcance + gano


def es_campeon(alcanzada: int, gano_ronda: bool) -> bool:
    return gano_ronda and alcanzada == len(BRACKET) - 1


def total_ganado(alcanzada: int, gano_ronda: bool) -> int:
    """Monedas totales de una unidad del torneo."""
    base = monedas_ganadas(alcanzada, gano_ronda)
    if es_campeon(alcanzada, gano_ronda):
        base += BOTE_CAMPEON
    return base
