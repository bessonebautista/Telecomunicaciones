"""Los consumibles: objetos que se compran ANTES del partido.

Ninguno dura toda la partida. Todos tienen un tiempo, y se ven en los dos
bandos, para que se note cuando los lleva puesta el rival.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    key: str
    name: str
    hotkey: str
    duracion: float  # segundos
    color: tuple
    icono: str
    desc: str  # que hace
    precio: int

    @property
    def etiqueta(self) -> str:
        return f"{int(self.duracion)}s"


MONSTRUO = Item(
    key="monstruo",
    name="Monstruo",
    hotkey="1",
    duracion=14.0,
    color=(120, 240, 160),
    icono="furia",
    desc="Al golpear, el puck sale disparado.",
    precio=60,
)

ESCUDO = Item(
    key="escudo",
    name="Escudo",
    hotkey="2",
    duracion=18.0,
    color=(110, 200, 255),
    icono="escudo",
    desc="Muro invisible en tu portería: detiene los dos primeros goles.",
    precio=80,
)

MUSCULOS = Item(
    key="musculos",
    name="Músculos",
    hotkey="3",
    duracion=15.0,
    color=(255, 150, 90),
    icono="fuerza",
    desc="Cada punto que marcas vale por dos.",
    precio=70,
)

RAfAGA = Item(
    key="rafaga",
    name="Ráfaga",
    hotkey="4",
    duracion=10.0,
    color=(255, 230, 120),
    icono="rayo",
    desc="Tu pala pega con un 60% más de fuerza.",
    precio=55,
)

HIELO = Item(
    key="hielo",
    name="Hielo",
    hotkey="5",
    duracion=12.0,
    color=(150, 220, 255),
    icono="hielo",
    desc="Al rival le resbala la pala: tarda más en frenarse y juega peor.",
    precio=65,
)

GIGANTE = Item(
    key="gigante",
    name="Gigante",
    hotkey="6",
    duracion=14.0,
    color=(190, 130, 255),
    icono="gigante",
    desc="Tu pala se hace enorme: tapa mucho más y pega con más potencia.",
    precio=90,
)

TODOS = (MONSTRUO, ESCUDO, MUSCULOS, RAfAGA, HIELO, GIGANTE)
POR_CLAVE = {i.key: i for i in TODOS}
POR_TECLA = {i.hotkey: i for i in TODOS}


class ItemEnUso:
    """Estado de un consumible dentro de un partido."""

    __slots__ = ("item", "tiempo", "poses", "gol_protegido", "usado")

    def __init__(self, item: Item) -> None:
        self.item = item
        self.tiempo = item.duracion
        self.poses = False
        self.gol_protegido = 0
        self.usado = False

    @property
    def activo(self) -> bool:
        return self.poses and self.tiempo > 0.0

    @property
    def fraccion(self) -> float:
        return max(0.0, min(1.0, self.tiempo / self.item.duracion))

    def activar(self) -> None:
        self.poses = True
        self.usado = True
        self.tiempo = self.item.duracion

    def update(self, dt: float) -> bool:
        """Avanza el reloj. Devuelve True si se acaba en este fotograma."""
        if not self.poses:
            return False
        self.tiempo -= dt
        if self.tiempo <= 0.0:
            self.tiempo = 0.0
            self.poses = False
            return True
        return False
