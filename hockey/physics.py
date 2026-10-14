"""Fisica de la mesa vista desde arriba.

Aqui no entra nada de aspecto: la puck rebota en las paredes, en las lineas
centrales, en la pala y en el escudo. Las mesas y palas bonitas se dibujan
encima, pero el juego se juega exactamente igual en todas.
"""

from __future__ import annotations

import math
import random

import pygame

from . import settings as S

# Por debajo de esta distancia la pala no se mueve NI UN PIXEL. Es lo que
# quita el tembleque: el raton de una mano real tiembla uno o dos pixeles
# aunque este quieto, y si la pala los sigue se mueve sola.
PEGADO = 4.0

# Cuanto se le perdona a la pala para que un roce cuente como golpe. Sin esto
# el puck pasa rozando y parece que la pala "no toca", que se juega muy mal.
PERDON = 3.0


class Puck:
    """La puck. Posicion en coordenadas de rink (0..TABLE_W, 0..TABLE_H)."""

    __slots__ = ("pos", "vel", "radio", "giro", "activo")

    def __init__(self) -> None:
        self.pos = pygame.Vector2(S.TABLE_W / 2, S.RINK_CENTER_Y)
        self.vel = pygame.Vector2(0.0, 0.0)
        self.radio = S.PUCK_R
        self.giro = 0.0
        self.activo = True

    def velocidad(self) -> float:
        return self.vel.length()

    def limitar(self) -> None:
        v = self.vel.length()
        if v > S.PUCK_MAX_SPEED:
            self.vel *= S.PUCK_MAX_SPEED / v
        elif 0.0 < v < S.PUCK_MIN_SPEED:
            # La mesa frena la puck: si va muy lenta, la empujamos un poco
            # para que el punto no se eternice.
            self.vel *= S.PUCK_MIN_SPEED / v

    def mover(self, dt: float) -> None:
        self.pos += self.vel * dt
        self.limitar()
        self.giro += self.vel.length() * dt * 0.02

    def sacar(self, hacia: int, fuerza: float | None = None) -> None:
        """Coloca la puck en el centro y la lanza hacia un lado."""
        self.pos = pygame.Vector2(S.TABLE_W / 2, S.RINK_CENTER_Y)
        f = fuerza if fuerza is not None else random.uniform(300.0, 380.0)
        ang = random.uniform(-0.55, 0.55)
        self.vel = pygame.Vector2(f * hacia * math.cos(ang), f * math.sin(ang))
        self.giro = 0.0


class Pala:
    """Una pala (el objeto que mueves).

    ``radio_base`` es su tamano normal. El consumible Gigante la agranda un
    rato (``radio_extra``), asi que el radio real cambia durante el partido.
    """

    __slots__ = ("pos", "vel", "radio", "lado", "color", "radio_base", "radio_extra")

    def __init__(self, lado: int) -> None:
        self.lado = lado  # -1 izquierda, +1 derecha
        self.radio_base = S.PADDLE_R
        self.radio_extra = 0.0
        self.radio = self.radio_base
        if lado < 0:
            self.pos = pygame.Vector2(S.TABLE_W * 0.22, S.RINK_CENTER_Y)
        else:
            self.pos = pygame.Vector2(S.TABLE_W * 0.78, S.RINK_CENTER_Y)
        self.vel = pygame.Vector2(0.0, 0.0)
        self.color = S.C_P1 if lado < 0 else S.C_P2

    def agrandar(self, extra: float) -> None:
        """Aumenta el radio (Gigante). Guarda el valor extra."""
        self.radio_extra = extra
        self.radio = self.radio_base + extra

    def reiniciar(self) -> None:
        """Vuelve a su posicion de inicio y a su tamano normal."""
        if self.lado < 0:
            self.pos = pygame.Vector2(S.TABLE_W * 0.22, S.RINK_CENTER_Y)
        else:
            self.pos = pygame.Vector2(S.TABLE_W * 0.78, S.RINK_CENTER_Y)
        self.vel = pygame.Vector2(0.0, 0.0)
        self.radio_extra = 0.0
        self.radio = self.radio_base

    def mover(self, dt: float) -> None:
        self.pos += self.vel * dt
        self._encajar()

    def _encajar(self) -> None:
        """Mantiene la pala dentro de la mesa.

        Cuando toca el borde, anula la velocidad de ese eje. Si no, la pala
        queda pegada al borde con la velocidad puesta: al apartar el raton
        vuelve disparada y da un tiron. Esto tambien hacia que vibre.
        """
        x = max(self.radio, min(S.TABLE_W - self.radio, self.pos.x))
        if x != self.pos.x:
            self.vel.x = 0.0
        self.pos.x = x
        y = max(self.radio, min(S.TABLE_H - self.radio, self.pos.y))
        if y != self.pos.y:
            self.vel.y = 0.0
        self.pos.y = y

    def mover_hacia(self, objetivo: pygame.Vector2, dt: float, vmax: float) -> None:
        """Lleva la pala a ``objetivo`` con velocidad limitada, sin vibrar.

        Esto es lo que usa el raton del jugador. Lo importante es la ZONA
        MUERTA: si ya estamos a menos de ``PEGADO``, la pala no se mueve NI UN
        PIXEL. Antes aqui se pegaba al objetivo por muy cerca que estuviera, y
        como el raton de una mano real tiembla aunque no se mueva, la pala
        seguia ese temblor: eso era el tembleque.

        Y el paso nunca sobrepasa el objetivo, para que no oscile alrededor de
        la posicion final.
        """
        dif = objetivo - self.pos
        dist = dif.length()
        if dist <= PEGADO:
            self.vel.update(0.0, 0.0)
            return
        paso = min(vmax * dt, dist)
        self.vel = dif / dist * (paso / dt if dt > 0.0 else vmax)
        self.pos += self.vel * dt
        self._encajar()

    def resbalar(self, dt: float) -> None:
        """Movimiento con inercia: para el efecto hielo."""
        self.pos += self.vel * dt
        # El rozamiento es bajisimo: la pala sigue resbalando.
        self.vel *= 0.985
        self._encajar()


def _rebote_pared(puck: Puck) -> bool:
    """Rebotes en las paredes superior, inferior y lineas de porteria."""
    golpe = False
    if puck.pos.y - puck.radio < 0.0:
        puck.pos.y = puck.radio
        puck.vel.y = abs(puck.vel.y) * S.PUCK_RESTITUTION
        golpe = True
    elif puck.pos.y + puck.radio > S.TABLE_H:
        puck.pos.y = S.TABLE_H - puck.radio
        puck.vel.y = -abs(puck.vel.y) * S.PUCK_RESTITUTION
        golpe = True

    dentro_porteria = abs(puck.pos.y - S.RINK_CENTER_Y) < S.GOAL_W / 2 - 6.0

    if not dentro_porteria:
        if puck.pos.x - puck.radio < 0.0:
            puck.pos.x = puck.radio
            puck.vel.x = abs(puck.vel.x) * S.PUCK_RESTITUTION
            golpe = True
        elif puck.pos.x + puck.radio > S.TABLE_W:
            puck.pos.x = S.TABLE_W - puck.radio
            puck.vel.x = -abs(puck.vel.x) * S.PUCK_RESTITUTION
            golpe = True
    return golpe


def _gol(puck: Puck) -> int | None:
    """Devuelve el lado que ha marcado, o None si aun no hay gol."""
    if puck.pos.x + puck.radio <= 0.0:
        return 1
    if puck.pos.x - puck.radio >= S.TABLE_W:
        return -1
    return None


def choque_pala(puck: Puck, pala: Pala, potencia: float = 1.0) -> bool:
    """Rebote de la puck contra una pala. Devuelve True si ha tocado.

    El radio minimo se agranda con la potencia, para que pegar con ganas
    alcance mas lejos: es la sensacion de "voy a por esa".
    """
    offset = puck.pos - pala.pos
    dist = offset.length()
    alcance = pala.radio * potencia
    minimo = puck.radio + alcance
    if dist >= minimo or dist == 0.0:
        return False

    normal = offset / dist
    # Empujamos la puck fuera del solape.
    puck.pos = pala.pos + normal * minimo
    # Rebote: quitamos la componente que entra hacia dentro de la pala.
    hacia_dentro = puck.vel.dot(normal)
    if hacia_dentro < 0.0:
        puck.vel -= normal * hacia_dentro * (1.0 + S.PADDLE_BOUNCE)
    # El movimiento de la pala se transmite, pero solo cuenta la parte que va
    # hacia la puck: si la pala se aleja, no tiene por que empujarla. Es lo
    # que hace que ir a por la pelota con ganas la mande mas lejos.
    avance = pala.vel.dot(normal)
    if avance > 0.0:
        puck.vel += normal * (avance * 0.55 * potencia)
    puck.limitar()
    return True


def choque_escudo(puck: Puck, centro_x: float, ancho: float, alto: float) -> bool:
    """El escudo es un rectangulo vertical delante de la porteria."""
    x0 = centro_x - ancho / 2
    x1 = centro_x + ancho / 2
    y0 = S.RINK_CENTER_Y - alto / 2
    y1 = S.RINK_CENTER_Y + alto / 2
    if not (x0 <= puck.pos.x <= x1 and y0 <= puck.pos.y <= y1):
        return False
    # Lo empujamos hacia el centro de la mesa.
    puck.pos.x = centro_x + ancho / 2 + puck.radio
    puck.vel.x = abs(puck.vel.x) * S.PUCK_RESTITUTION
    puck.vel.y *= 0.92
    return True


def golpear_hacia(
    puck: Puck, pala: Pala, objetivo: pygame.Vector2, potencia: float
) -> bool:
    """Golpe dirigido: manda la puck hacia ``objetivo``.

    A diferencia de ``choque_pala``, que solo resuelve un rebote, esto elige
    la direccion de salida. Lo usa la IA para apuntar a la porteria del
    contrario en vez de devolver la puck donde toca.

    Devuelve True si la pala estaba al alcance y se ha golpeado.
    """
    offset = puck.pos - pala.pos
    dist = offset.length()
    alcance = puck.radio + pala.radio
    if dist >= alcance or dist == 0.0:
        return False
    # Separamos la puck para que no se quede enganchada dentro de la pala.
    normal = offset / dist
    puck.pos = pala.pos + normal * alcance
    # La direccion de salida se calcula DESDE LA PALA, no desde la puck. Si se
    # calcula desde la puck y el golpe es de lado, la direccion queda casi
    # nula y el tiro sale sin fuerza ninguna (parece que no golpeas).
    direccion = objetivo - pala.pos
    if direccion.length_squared() < 1.0:
        # Apunta a un sitio valido: al menos 1 m por delante de la pala.
        direccion = normal * -1.0 if normal.x > 0 else normal * 1.0
    puck.vel = direccion.normalize() * potencia
    puck.limitar()
    return True


def golpe_dirigido(
    puck: Puck,
    pala: Pala,
    objetivo: pygame.Vector2,
    potencia: float,
    perdon: float = PERDON,
) -> bool:
    """Golpe del jugador: la puck sale hacia donde se apunta.

    Hace las tres cosas de una vez (comprobar el alcance, apartar la puck para
    que no se enganche y darle la velocidad de salida). Antes se llamaba a
    ``choque_pala`` y luego a ``golpear_hacia``, y eso nunca funcionaba bien:
    ``choque_pala`` deja la puck a la distancia EXACTA de contacto, y
    ``golpear_hacia`` rechaza justo esa distancia, asi que el tiro dirigido
    casi no se aplicaba nunca y la puck salia rebotando en depende de en que
    punto de la pala la habias tocado.

    ``perdon`` agranda un poco el alcance para que un roce cuente como golpe:
    sin eso el puck te pasa por al lado y parece que la pala no toca.
    """
    offset = puck.pos - pala.pos
    dist = offset.length()
    alcance = puck.radio + pala.radio + perdon
    if dist >= alcance or dist == 0.0:
        return False

    normal = offset / dist
    # Apartamos la puck justo fuera del contacto, con un pelo de margen para
    # que no vuelva a solaparse en el siguiente fotograma.
    fuera = puck.radio + pala.radio + 0.5
    puck.pos = pala.pos + normal * fuera

    direccion = objetivo - pala.pos
    if direccion.length_squared() < 1.0:
        # Apunta a un sitio valido: al menos un metro por delante de la pala.
        direccion = normal if normal.x < 0.0 else normal * -1.0
    puck.vel = direccion.normalize() * potencia
    puck.limitar()
    return True


def actualizar(puck: Puck, dt: float) -> str:
    """Un paso de la puck. Devuelve "pared", "gol" o ""."""
    puck.mover(dt)
    evento = ""
    if _rebote_pared(puck):
        evento = "pared"
    gol = _gol(puck)
    if gol is not None:
        return "gol"
    return evento


def friccion_mesa(puck: Puck, dt: float) -> None:
    """La mesa frena la puck poco a poco."""
    puck.vel *= max(0.0, 1.0 - S.PUCK_FRICTION * dt)
