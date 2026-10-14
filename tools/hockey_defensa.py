"""Prueba aislada: puede un tiro bien colocado superar la defensa de la IA?

Dispara la puck desde el centro hacia la porteria del rival a distintas alturas
y mide cuantas pasan. Es la medida directa de si la defensa es batible.

    python tools/hockey_defensa.py
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from hockey import ai as ai_mod  # noqa: E402
from hockey import physics, settings as S  # noqa: E402
from hockey.physics import Pala, Puck  # noqa: E402


def probar_tiro(nivel: str, y_destino: float, potencia: float, segundos: float = 2.5) -> bool:
    """Lanza un tiro con la pala pegada a la puck y dice si entra.

    Ojo con como se mide: en cuanto el rival TOCA la puck, el tiro esta
    parado. Antes se dejaba seguir la simulacion y, como la puck rebotaba por
    la mitad del jugador durante el resto del tiempo, acababa entrando por
    azar y el medidor contaba como "bueno" un tiro que en realidad habia
    parado el rival. Ahora se para en el primer contacto.
    """
    rival = ai_mod.Rival(nivel)
    pk = Puck()
    pk.pos = pygame.Vector2(S.TABLE_W * 0.5, S.RINK_CENTER_Y)
    tirador = Pala(-1)
    tirador.pos = pygame.Vector2(S.TABLE_W * 0.5 - 50.0, S.RINK_CENTER_Y)
    objetivo = pygame.Vector2(S.TABLE_W - 5.0, y_destino)
    if not physics.golpe_dirigido(pk, tirador, objetivo, potencia):
        return False
    dt = 1 / 240
    for _ in range(int(segundos * 240)):
        # Si el rival toca la puck, el tiro se para aqui.
        if rival.actualizar(dt, pk):
            return False
        ev = physics.actualizar(pk, dt)
        if ev == "gol":
            return True
    return False


if __name__ == "__main__":
    print("Tiros desde el centro a distintas alturas. 'PASA' = la IA no tapa.")
    alturas = {
        "esquina alta": S.RINK_CENTER_Y - S.GOAL_W * 0.45,
        "arriba-centro": S.RINK_CENTER_Y - S.GOAL_W * 0.20,
        "centro": S.RINK_CENTER_Y,
        "abajo-centro": S.RINK_CENTER_Y + S.GOAL_W * 0.20,
        "esquina baja": S.RINK_CENTER_Y + S.GOAL_W * 0.45,
    }
    for nivel in ai_mod.NIVELES_ORDENADOS:
        pasan = 0
        total = 0
        detalle = []
        for etiqueta, y in alturas.items():
            for potencia in (0.6, 0.85, 1.0):
                total += 1
                if probar_tiro(nivel, y, S.PUCK_MAX_SPEED * potencia):
                    pasan += 1
                    detalle.append(etiqueta)
        pct = 100.0 * pasan / total if total else 0
        print(f"\n{nivel}: {pasan}/{total} tiros pasan ({pct:.0f}%)")
        if detalle:
            # Cuenta por cuanto pasa de cada sitio.
            from collections import Counter
            c = Counter(detalle)
            print("   por donde:", ", ".join(f"{k} x{v}" for k, v in c.items()))
    print()
    print("Referencia: 0% = defensa impenetrable, 100% = no tapa nada.")
    print("Lo sano para un juego: 20-50% en Novato, bajando a <10% en Imposible.")
