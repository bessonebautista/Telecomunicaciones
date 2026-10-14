"""Mide como de fuerte juega la IA en cada nivel.

Juega contra un rival humano simulado (defiende y ataca) y dice quien gana.
Sirve para ver si los niveles estan bien calibrados.

    python tools/hockey_fuerza.py
"""

from __future__ import annotations

import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from hockey import ai as ai_mod  # noqa: E402
from hockey import settings as S  # noqa: E402
from hockey.game import Game  # noqa: E402
from hockey.physics import golpe_dirigido  # noqa: E402


class RivalHumano:
    """Jugador humano simulado: tapa la porteria y remata.

    Intercepts el puck prediciendo su trayectoria, pero NO lo hace perfecto:
    tarda un poco en reaccionar y se equivoca al colocarse, que es lo que
    pasa de verdad con una persona. Asi el medidor dice si un nivel es
    ganable por alguien que juega bien, no si es ganable por un robot.
    """

    def __init__(
        self,
        juego: Game,
        retraso: float = 0.22,
        precision: float = 0.78,
        tapa: float = 0.55,
    ) -> None:
        self.g = juego
        self.retraso = retraso
        self.precision = precision
        self.tapa = tapa
        self.reloj = 0.0
        self.espera = 0.0
        # True cuando ya ha decidido donde tapar y no se mueve mas hasta que
        # la puck pasa o vuelve hacia el campo contrario.
        self.comprometido = False
        self.objetivo = pygame.Vector2(S.TABLE_W * 0.22, S.RINK_CENTER_Y)

    def _predecir(self, linea: float):
        pk = self.g.puck
        x, y, vx, vy = pk.pos.x, pk.pos.y, pk.vel.x, pk.vel.y
        if abs(vx) < 1e-6:
            return None
        dt = 1 / 240
        t = 0.0
        while t < 2.5:
            x += vx * dt
            y += vy * dt
            if y < pk.radio:
                y = pk.radio
                vy = abs(vy)
            elif y > S.TABLE_H - pk.radio:
                y = S.TABLE_H - pk.radio
                vy = -abs(vy)
            t += dt
            if (pk.pos.x - linea) * (x - linea) <= 0:
                return pygame.Vector2(linea, y)
            if (x - linea) * vx < 0 and (pk.pos.x - linea) * vx > 0:
                return None
        return None

    def update(self, dt: float) -> None:
        g = self.g
        pk = g.puck
        self.reloj -= dt
        # Una persona decide donde va a tapar y se compromete: no va
        # recalculando la trayectoria cada 0,2 s y corrigiendo. Si lo hiciera,
        # seria un muro y mediria cualquier cosa. Por eso, cuando ya se ha
        # comprometido con un tiro, no vuelve a mirar hasta que la puck pasa
        # o cambia de lado.
        if not self.comprometido and self.reloj <= 0:
            self.reloj = self.retraso
            p = self._predecir(S.TABLE_W * 0.16)
            if p is not None:
                # La puck viene hacia mi: me coloco cerca de la porteria, con
                # un error de colocacion (una persona no acierta el punto
                # exacto) y me quedo ahi, sin corregir luego.
                fallo = (1.0 - self.tapa) * S.GOAL_W * 0.9
                self.objetivo = pygame.Vector2(
                    S.TABLE_W * 0.16,
                    max(
                        S.PADDLE_R,
                        min(
                            S.TABLE_H - S.PADDLE_R,
                            p.y + random.uniform(-fallo, fallo),
                        ),
                    ),
                )
                self.comprometido = True
            else:
                # Puck en mi campo o yendose: salgo a por ella. Un buen
                # jugador de hockey de aire juega sobre la linea de la red:
                # desde ahi los tiros salen muy rapidos y el rival no llega.
                x = S.TABLE_W * 0.45 if pk.pos.x > S.TABLE_W * 0.5 else S.TABLE_W * 0.30
                self.objetivo = pygame.Vector2(
                    x, max(S.PADDLE_R, min(S.TABLE_H - S.PADDLE_R, pk.pos.y))
                )
        if self.comprometido and (pk.vel.x >= 0.0 or pk.pos.x > S.TABLE_W * 0.5):
            # La puck ha pasado o ha cambiado de lado: vuelvo a decidir.
            self.comprometido = False
        pala = g.pala_jug
        d = self.objetivo - pala.pos
        if d.length() > 2:
            pala.vel = d.normalize() * min(1250.0, d.length() / max(dt, 1e-6))
        pala.mover(dt)

        # Atacar: rematar a la porteria del rival. Un buen jugador busca el
        # lado contrario al que esta el rival y pega fuerte, para que la
        # paddle no llegue a tiempo.
        if self.espera > 0:
            self.espera -= dt
            return
        alcance = pk.radio + pala.radio + 6.0
        if (pk.pos - pala.pos).length() > alcance:
            return
        rival = g.rival.pala
        # Lado de la porteria mas alejado del rival.
        y_rival = rival.pos.y
        if y_rival >= S.RINK_CENTER_Y:
            objetivo_y = S.RINK_CENTER_Y - S.GOAL_W / 2 * 0.72
        else:
            objetivo_y = S.RINK_CENTER_Y + S.GOAL_W / 2 * 0.72
        error = (1.0 - self.precision) * S.GOAL_W * 0.5
        objetivo_y += random.uniform(-error, error)
        objetivo = pygame.Vector2(
            S.TABLE_W - random.uniform(4.0, 24.0), objetivo_y
        )
        # Pega fuerte: una puck rapida llega antes de que el rival se mueva.
        potencia = S.PUCK_MAX_SPEED * (0.72 + 0.25 * self.precision)
        if golpe_dirigido(pk, pala, objetivo, potencia):
            self.espera = 0.08


def jugar(nivel_ia: str, segundos: float = 240.0, semilla: int | None = None) -> dict:
    if semilla is not None:
        random.seed(semilla)
    g = Game()
    g.preparar_partido("Test", nivel_ia, torneo=False, presentacion=False)
    # Apagamos el raton: si no, el juego arrastra la pala a la esquina (el
    # raton en modo dummy siempre esta en 0,0) y el simulador no manda nada.
    g.control_por_mouse = False
    rival = RivalHumano(g)
    dt = 1 / 60
    for i in range(int(segundos * 60)):
        rival.update(dt)
        g.update(dt)
        if g.marcador[0] >= S.GOALS_TO_WIN or g.marcador[1] >= S.GOALS_TO_WIN:
            return {
                "tu": g.marcador[0],
                "rival": g.marcador[1],
                "segundos": round(i / 60.0, 1),
            }
    return {
        "tu": g.marcador[0],
        "rival": g.marcador[1],
        "segundos": segundos,
    }


if __name__ == "__main__":
    SIEMBRAS = int(os.environ.get("HOCKEY_SIEMBRAS", "3"))
    print(f"Un buen jugador humano contra la IA, {SIEMBRAS} partidas por nivel.")
    print(f"{'nivel':12s} {'tu':>7s} {'rival':>7s} {'victorias':>10s}  veredicto")
    print("-" * 64)
    for nivel in ai_mod.NIVELES_ORDENADOS:
        tu = riv = 0
        ganadas = 0
        for s in range(SIEMBRAS):
            r = jugar(nivel, semilla=1000 + s * 37)
            tu += r["tu"]
            riv += r["rival"]
            if r["tu"] > r["rival"]:
                ganadas += 1
            elif r["tu"] == r["rival"]:
                ganadas += 0.5
        pct = ganadas / SIEMBRAS * 100.0
        if pct >= 60:
            veredicto = f"GANABLE ({pct:.0f}% lo gana)"
        elif pct >= 25:
            veredicto = f"duro ({pct:.0f}% lo gana)"
        else:
            veredicto = f"casi imposible ({pct:.0f}% lo gana)"
        print(f"{nivel:12s} {tu:7d} {riv:7d} {pct:9.0f}%  {veredicto}")
    print()
    print("Lo que buscamos: Novato ganable, Imposible casi imposible de ganar.")
