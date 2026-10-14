"""El rival: coloca su pala, intercepta la puck y remata a porteria.

La IA hace tres cosas, en este orden de prioridad:

1. **Defender**: si la puck viene hacia su porteria, se coloca en la linea
   para taparla.
2. **Recuperar**: si la puck se ha pasado y va hacia su campo, la persigue.
3. **Atacar**: cuando la tiene cerca, apunta a la porteria del jugador.

La prediccion simula la puck con los rebotes en las paredes, asi que la IA
sabe donde va a estar de verdad y no a donde parece que va. Ademas, nunca se
mete la puck en su propia porteria al golpear.
"""

from __future__ import annotations

import math
import random

import pygame

from . import physics, settings as S
from .physics import Pala, Puck

# Los niveles suben fuerte. "Imposible" esta pensado para que el torneo sea
# de verdad muy dificil: la IA casi no falla y ataca sin descanso.
# Los valores mas bajos son para que los niveles bajos se ganen jugando bien.
NIVELES = {
    "Novato": {
        "reaccion": 0.70,
        "velocidad": 280.0,
        "error": 420.0,
        "agresividad": 0.12,
        "espera": 0.60,
        "precision": 0.0,
        "defensa": 0.08,
        "potencia": 0.34,
        "fallo": 0.80,
    },
    "Normal": {
        "reaccion": 0.55,
        "velocidad": 340.0,
        "error": 380.0,
        "agresividad": 0.18,
        "espera": 0.50,
        "precision": 0.0,
        "defensa": 0.12,
        "potencia": 0.38,
        "fallo": 0.70,
    },
    "Dificil": {
        "reaccion": 0.34,
        "velocidad": 540.0,
        "error": 200.0,
        "agresividad": 0.52,
        "espera": 0.20,
        "precision": 0.26,
        "defensa": 0.40,
        "potencia": 0.72,
        "fallo": 0.36,
    },
    "Experto": {
        "reaccion": 0.10,
        "velocidad": 880.0,
        "error": 44.0,
        "agresividad": 0.92,
        "espera": 0.03,
        "precision": 0.68,
        "defensa": 0.90,
        "potencia": 1.08,
        "fallo": 0.055,
    },
    "Imposible": {
        "reaccion": 0.04,
        "velocidad": 1200.0,
        "error": 12.0,
        "agresividad": 1.0,
        "espera": 0.0,
        "precision": 0.92,
        "defensa": 1.0,
        "potencia": 1.22,
        "fallo": 0.01,
    },
}

NIVEL_POR_RONDA = ("Novato", "Normal", "Dificil", "Experto", "Imposible")
DIFICIL = "Normal"

# Orden de preferencia de niveles para no repetir.
RANGOS = {
    "Novato": ("Novato",),
    "Normal": ("Normal", "Novato"),
    "Dificil": ("Dificil", "Normal"),
    "Experto": ("Experto", "Dificil"),
    "Imposible": ("Imposible", "Experto"),
}


class Rival:
    """Controla la pala de la derecha (el bando del jugador es el izquierdo)."""

    def __init__(self, nivel: str = DIFICIL) -> None:
        self.nivel = nivel if nivel in NIVELES else DIFICIL
        self.cfg = NIVELES[self.nivel]
        self.pala = Pala(+1)
        self.objetivo = self.pala.pos.copy()
        self.reloj = 0.0
        self.espera = 0.0
        self.modo = "defensa"
        self.ultimo_gol_recibido = 0.0
        # Donde esta la pala del jugador. La IA lo usa para disparar al lado
        # contrario, que es la unica esquina que el defensor no puede tapar.
        self.pala_jug_y = S.RINK_CENTER_Y

    def reiniciar(self) -> None:
        self.pala.reiniciar()
        self.objetivo = self.pala.pos.copy()
        self.reloj = 0.0
        self.espera = 0.0
        self.modo = "defensa"

    # --- Prediccion ---------------------------------------------------------
    def _simular(self, puck: Puck, objetivo_x: float, horizonte: float = 2.5):
        """Simula la puck con rebotes hasta ``objetivo_x``.

        Devuelve (punto, t) del primer cruce, o None si no llega. Los rebotes
        en las paredes se respetan, que es lo que hacia que la IA no se
        quedara ShortTracing cuando la puck bota.
        """
        x = puck.pos.x
        y = puck.pos.y
        vx = puck.vel.x
        vy = puck.vel.y
        if abs(vx) < 1e-6:
            return None
        dt = 1.0 / 240.0
        t = 0.0
        while t < horizonte:
            x += vx * dt
            y += vy * dt
            if y < puck.radio:
                y = puck.radio
                vy = abs(vy) * S.PUCK_RESTITUTION
            elif y > S.TABLE_H - puck.radio:
                y = S.TABLE_H - puck.radio
                vy = -abs(vy) * S.PUCK_RESTITUTION
            t += dt
            # Cruce de la linea objetivo en el sentido de avance.
            if (puck.pos.x - objetivo_x) * (x - objetivo_x) <= 0.0:
                return pygame.Vector2(x, y), t
            # Si la puck se ha ido del otro lado y no vuelve, no hay intercepcion.
            if abs(vx) > 0.0:
                if (x - objetivo_x) * vx < 0.0 and (puck.pos.x - objetivo_x) * vx > 0.0:
                    return None
        return None

    def _punto_de_intercepcion(self, puck: Puck) -> pygame.Vector2 | None:
        """Donde deberia estar la pala para tocar la puck de camino.

        La simulacion es exacta, asi que si se usara tal cual la IA se
        colocaria siempre en el punto correcto y no fallaria nunca. Por eso se
        le mete ruido: un error base que escala con el nivel y, ademas, de vez
        en cuando se equivoca del todo (no ve el rebote).
        """
        linea = S.TABLE_W - S.PADDLE_R - S.PUCK_R - 10.0
        r = self._simular(puck, linea)
        if r is None:
            return None
        punto, _ = r
        # Error de lectura permanente, proporcional a lo malo que juegue.
        e = self.cfg["error"]
        punto = punto + pygame.Vector2(
            random.uniform(-1.0, 1.0) * e * 0.45,
            random.uniform(-1.0, 1.0) * e * 0.75,
        )
        # Y de vez en cuando se queda totalmente descolocada.
        if random.random() < self.cfg.get("fallo", 0.2):
            punto = punto + pygame.Vector2(
                random.uniform(-1.0, 1.0) * e * 1.8,
                random.uniform(-1.0, 1.0) * e * 1.8,
            )
        return punto

    # --- Objetivo de la pala ------------------------------------------------
    def _elegir_objetivo(self, puck: Puck) -> None:
        cfg = self.cfg
        viene = puck.vel.x > 0.0  # la puck viene hacia el rival
        en_mitad = puck.pos.x > S.TABLE_W * 0.5

        if viene:
            # Defender: tapar la linea de la puck, pero saliendo a Challenges.
            # Si se queda pegada a su porteria, no hay partido: nunca se
            # pueden meter goles. Al salir, deja un hueco detras y asi el
            # buen jugador puede GoneAround.
            self.modo = "defensa"
            punto = self._punto_de_intercepcion(puck)
            y_obj = punto.y if punto is not None else puck.pos.y
            # Base: una linea por delante de su porteria.
            # Cuanta MAS defensa, mas pegada se queda a la red: tapa mejor los
            # angulos, pero tarda mas en llegar al centro. Cuanta menos, mas
            # sale a tapar antes y deja un hueco detras por el que colarse.
            x_def = S.TABLE_W - S.PADDLE_R - (40.0 + (1.0 - cfg["defensa"]) * 220.0)
            rapidez = puck.vel.length()
            if rapidez > 500.0:
                # Puck rapida: sale a cortarla antes de que llegue a la linea.
                x_def -= min(240.0, rapidez * 0.18) * cfg["defensa"]
            x_obj = max(S.TABLE_W * 0.5 + S.PADDLE_R, x_def)
            y_obj = y_obj + random.uniform(-cfg["error"], cfg["error"]) * (1.0 - cfg["defensa"])
        elif en_mitad:
            # Recuperar: la puck va para su campo.
            self.modo = "recuperar"
            x_obj = min(S.TABLE_W - S.PADDLE_R, puck.pos.x + 26.0)
            y_obj = puck.pos.y + random.uniform(-cfg["error"], cfg["error"]) * 0.5
        else:
            # La puck esta en campo del jugador. posicionamento en el centro,
            # un poco adelantado para poder contraatacar. Cuanto mejor juega,
            # mas adelante se pone y mas espacio deja detras.
            self.modo = "espera"
            # Puck en campo del jugador: se coloca en una linea de ataque,
            # ni tan cerca de su porteria (no taparia los angulos) ni tan
            # lejos (no tendria tiempo a volver si pierde la puck).
            x_obj = S.TABLE_W - S.PADDLE_R - (150.0 - cfg["defensa"] * 90.0)
            y_obj = S.RINK_CENTER_Y + (puck.pos.y - S.RINK_CENTER_Y) * 0.35
            y_obj += random.uniform(-cfg["error"], cfg["error"]) * 0.3

        self.objetivo = pygame.Vector2(
            max(S.TABLE_W * 0.5 + S.PADDLE_R, min(S.TABLE_W - S.PADDLE_R, x_obj)),
            max(S.PADDLE_R + 2.0, min(S.TABLE_H - S.PADDLE_R - 2.0, y_obj)),
        )

    # --- Ataque -------------------------------------------------------------
    def _porteria_objetivo(self, puck: Puck) -> pygame.Vector2:
        """Apunta a la porteria del jugador (la izquierda), a una esquina.

        Elige el lado CONTRARIO al que esta la pala del jugador: es la
        esquina que este no puede tapar. Un rival que dispara al centro o a
        ciegas se choca contra la pala y no marca nunca.
        """
        # Cuanto mas preciso es, mas se acerca al centro de la porteria, que
        # es mas dificil de tapar.
        centrado = self.cfg["precision"]
        medio = S.RINK_CENTER_Y
        margen = S.GOAL_W / 2.0
        # Lado del jugador: si esta arriba, buscamos abajo, y al reves.
        lado = -1.0 if self.pala_jug_y >= medio else 1.0
        if random.random() < (1.0 - centrado) * 0.5:
            # Cuando no es muy preciso, a veces se equivoca de lado.
            lado = -lado
        y = medio + lado * margen * (0.15 + (1.0 - centrado) * 0.7)
        # Un poco dentro de la porteria para que cuente como gol.
        x = 8.0 + random.uniform(0.0, 26.0)
        return pygame.Vector2(x, y)

    def _golpear(self, puck: Puck, dt: float) -> bool:
        """Remata a porteria si la tiene al alcance. Nada de gol en contra."""
        if self.espera > 0.0:
            return False
        alcance = puck.radio + self.pala.radio + physics.PERDON
        # Un poco de margen para que no se le escapen por poco.
        alcance += 6.0 + (1.0 - self.cfg["precision"]) * 14.0
        if (puck.pos - self.pala.pos).length() > alcance:
            return False

        objetivo = self._porteria_objetivo(puck)
        potencia = (
            S.PUCK_MAX_SPEED
            * 0.42
            * self.cfg["potencia"]
            * (0.82 + self.cfg["agresividad"] * 0.3)
        )
        # Cuanto mas lejos este la porteria, mas tiene que pegar.
        distancia = (puck.pos - objetivo).length()
        potencia = min(potencia * (0.75 + distancia / 90.0), S.PUCK_MAX_SPEED * 0.82)

        # Mismo golpe dirigido que el jugador: comprueba el alcance y manda la
        # puck a la porteria en una sola llamada, sin depender de un rebote.
        if physics.golpe_dirigido(puck, self.pala, objetivo, potencia):
            self.espera = self.cfg["espera"]
            self.modo = "ataca"
            return True
        return False

    # --- Bucle --------------------------------------------------------------
    def actualizar(
        self, dt: float, puck: Puck, muleta: float = 1.0, pala_jug_y: float | None = None
    ) -> bool:
        """Un paso de la IA. Devuelve True si ha golpeado la puck."""
        if pala_jug_y is not None:
            self.pala_jug_y = pala_jug_y
        # La espera tras golpear hay que BAJARLA aqui. Si no, ``self.espera``
        # se queda en positivo para siempre y el rival solo puede tocar la
        # puck una vez en toda la partida: a partir de ahi la pelota atraviesa
        # su pala sin que la toque. Ese fue un bug real.
        if self.espera > 0.0:
            self.espera = max(0.0, self.espera - dt)

        # Primero intenta pegar: si puede, no pierde un fotograma.
        if self._golpear(puck, dt):
            return True

        self.reloj -= dt
        if self.reloj <= 0.0:
            self.reloj = self.cfg["reaccion"] * random.uniform(0.75, 1.25)
            self._elegir_objetivo(puck)

        dif = self.objetivo - self.pala.pos
        dist = dif.length()
        vel_max = self.cfg["velocidad"] * muleta
        if dist > 2.0:
            vel_deseada = dif.normalize() * min(vel_max, dist / max(dt, 1e-6))
            cambio = vel_deseada - self.pala.vel
            # Aceleracion limitada, para que la pala tenga peso y no teletransporte.
            acc = 5200.0
            cambio.x = max(-acc * dt, min(acc * dt, cambio.x))
            cambio.y = max(-acc * dt, min(acc * dt, cambio.y))
            self.pala.vel += cambio
        else:
            self.pala.vel *= 0.80
        v = self.pala.vel.length()
        if v > vel_max:
            self.pala.vel *= vel_max / v
        self.pala.mover(dt)
        return False

    # --- Utilidad -----------------------------------------------------------
    @staticmethod
    def nivel_para(ronda: int) -> str:
        """Nivel del rival segun la ronda del torneo (0 = octavos)."""
        return NIVEL_POR_RONDA[min(ronda, len(NIVEL_POR_RONDA) - 1)]


# Los cinco niveles, del mas facil al mas imposible. El torneo los usa en este
# orden: octavos Novato y la final contra "Imposible".
NIVELES_ORDENADOS = ("Novato", "Normal", "Dificil", "Experto", "Imposible")
