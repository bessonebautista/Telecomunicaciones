"""Hockey de Aire: juego de hockey de aire en 2D visto desde arriba.

La fisica es siempre la misma; las mesas, palas y pucks solo cambian el
aspecto. Lo que cambia las reglas son los consumibles, que se compran con
monedas antes de cada partido.
"""

__all__ = ["Game"]


def __getattr__(name: str):
    # Import perezoso: no abrir la ventana al importar el paquete.
    if name == "Game":
        from .game import Game

        return Game
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
