"""Juega el torneo entero de punta a punta, con bots, y comprueba
que la economia y el avance de rondas funcionan.

Ejecuta:
    python tools/hockey_torneo.py
"""

from __future__ import annotations

import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from hockey import save, settings as S, tournament  # noqa: E402
from hockey.game import FINAL, PARTIDO, Game  # noqa: E402

PASS = 0
FAIL = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  OK    {name}")
    else:
        FAIL += 1
        print(f"  FALLO {name}  {detail}")


MAX_SEGUNDOS = 900.0  # contra Imposible los partidos se alargan mucho


def jugar_ronda(g: Game, segundos: float = 150.0) -> tuple[int, int]:
    """Juega un partido entero con un bot, hasta que alguien llegue a 5.

    Usa el mismo rival humano simulado que hockey_fuerza.py: juega en la linea
    de la red, tapa y contraataca. Un bot que solo persiga la puck nunca
    marcaria y el torneo no diria nada.
    """
    from hockey_fuerza import RivalHumano

    # Simula a un jugador decente (no experto): es la referencia para saber si
    # el torneo es ganable o imposible.
    bot = RivalHumano(g, precision=0.82)
    dt = 1 / 60
    for _ in range(int(min(segundos, MAX_SEGUNDOS) * 60)):
        bot.update(dt)
        g.update(dt)
        g.draw()
        if g.marcador[0] >= S.GOALS_TO_WIN or g.marcador[1] >= S.GOALS_TO_WIN:
            break
        if g.estado != PARTIDO:
            break
    return g.marcador[0], g.marcador[1]


print("\nTorneo completo (bot vs IA, 4 rondas)")
# Empezamos limpio.
save.reset()
# Con semilla fija la simulacion es reproducible: si falla, siempre falla igual.
random.seed(7)
g = Game()
ronda = 0
total = 0
monedas_inicio = 0
for i in range(4):
    nombre, nivel = tournament.rival_de(ronda)[0], tournament.rival_de(ronda)[1]
    g.preparar_partido(nombre, nivel, torneo=True, presentacion=False)
    g.ronda = ronda
    mj, mi = jugar_ronda(g, MAX_SEGUNDOS)
    gane = mj > mi
    monedas_ya_dadas = g.monedas() - monedas_inicio
    print(
        f"  {tournament.RONDAS[ronda]:10s} vs {nombre:10s} ({nivel:7s}) "
        f"{mj}-{mi}  {'GANA' if gane else 'pierde'}  +{monedas_ya_dadas}"
    )
    # Si nadie llego a 5 por tiempo, se cierra el partido a mano (como si el
    # jugador pulsara ENTER). Si ya se cerro solo, no se toca nada.
    if g.estado == PARTIDO:
        g.marcador[0], g.marcador[1] = mj, mi
        g.fase = "punto"
        g.fin_partido()
    total += g.monedas() - monedas_inicio
    monedas_inicio = g.monedas()
    # Este bot es solo un proxy para que la simulacion corra; que gane o pierda
    # no dice nada del equilibrio real del juego (eso lo mide hockey_fuerza.py).
    # Lo que si tiene que ser verdad es que la ronda se cierra y da monedas.
    check(
        f"Ronda {tournament.RONDAS[ronda]}: la ronda se cierra y paga",
        monedas_ya_dadas > 0 or g.estado == FINAL,
        f"{mj}-{mi}, +{monedas_ya_dadas}",
    )
    if not gane:
        print("    (el bot se queda aqui; el equilibrio real lo mide hockey_fuerza.py)")
        # Para seguir comprobando el resto del torneo, fingimos que gana, con
        # su economia real. Asi todas las rondas se pagan y se pueden verificar.
        g.marcador[0], g.marcador[1] = S.GOALS_TO_WIN, mj
        g.estado = PARTIDO
        monedas_por_ganar = tournament.total_ganado(ronda, True)
        g.ronda = ronda
        g.fase = "punto"
        monedas_inicio = g.monedas()
        g.fin_partido()
        extra = g.monedas() - monedas_inicio
        total += extra
        monedas_inicio = g.monedas()
        print(
            f"  {tournament.RONDAS[ronda]:10s} (forzado)          "
            f"5-{mj}  GANA  +{extra}"
        )
    if g.estado == FINAL:
        print("    ¡CAMPEON!")
        break
    ronda += 1

print(f"\n  Monedas totales del recorrido: {total}")
check("Se ganan monedas al avanzar", total > 0, str(total))
check(
    "Las monedas del guardado coinciden con lo ganado",
    g.monedas() == total,
    f"guardado {g.monedas()} vs calculado {total}",
)

# --- Comprobaciones de la economia ----------------------------------------
print("\nEconomia del torneo")
# Cuanto mas lejos, mas monedas: comprobarlo con los 4 posibles finales.
ganadas = [tournament.total_ganado(i, True) for i in range(4)]
print(f"  {'ronda':10s} {'ganando':>8s} {'perdiendo':>10s}")
for i, ronda_nombre in enumerate(tournament.RONDAS):
    print(
        f"  {ronda_nombre:10s} {tournament.total_ganado(i, True):8d} "
        f"{tournament.total_ganado(i, False):10d}"
    )
check("Ganando siempre da mas que perdiendo", all(
    tournament.total_ganado(i, True) > tournament.total_ganado(i, False) for i in range(4)
), "")
check("Cada ronda ganada da mas que la anterior",
      ganadas == sorted(ganadas) and len(set(ganadas)) == 4, str(ganadas))

# Cuantas monedas hacen falta para elroke consumible mas caro
caro = max(S.ITEM_PRICES.values())
check("Una ronda de octavos alcanza para comprar algo",
      tournament.total_ganado(0, True) >= caro,
      f"ganas {tournament.total_ganado(0, True)}, el mas caro cuesta {caro}")
check("El bote de campeon permite comprar varios objetos",
      tournament.BOTE_CAMPEON >= caro * 3,
      f"bote {tournament.BOTE_CAMPEON}")

# --- Campeon desbloquea lo mejor -------------------------------------------
print("\nDesbloqueos de campeon")
g2 = Game()
g2.ronda = 3
g2.en_torneo = True
g2.marcador = [5, 3]
g2.fase = "punto"
g2.fin_partido()
check("Ganar la final lleva a la pantalla de campeon", g2.estado == FINAL, g2.estado)
check("Se desbloquea la mesa suprema", g2.tiene("mesa_suprema"), str(g2.datos["objetos"]))
check("Se desbloquea la pala de campeon", g2.tiene("pala_canela"), "")
check("Se desbloquea la puck de campeon", g2.tiene("puck_canela"), "")
check("Se marca que se gano el torneo", g2.datos.get("torneo_ganado") is True, "")
check("Se equipa la mesa de campeon", g2.mesa_sel == "mesa_suprema", g2.mesa_sel)

# --- Perder en octavos no da nada raro ------------------------------------
# Se parte de una partida limpia para comprobar que perder no da el bote.
save.reset()
g3 = Game()
g3.ronda = 0
g3.en_torneo = True
g3.marcador = [2, 5]
g3.fase = "punto"
monedas_antes = g3.monedas()
g3.fin_partido()
print(f"  Perdiendo en octavos: +{g3.monedas() - monedas_antes} monedas")
check("Perder da alguna moneda por el intento", g3.monedas() > monedas_antes,
      f"{monedas_antes} -> {g3.monedas()}")
check("Perder en octavos no desbloquea lo de campeon", not g3.tiene("mesa_suprema"),
      str(g3.datos["objetos"]))
check("Perder en octavos no da el bote grande",
      g3.monedas() - monedas_antes < tournament.BOTE_CAMPEON, "")
check("Perder en octavos no marca el torneo como ganado",
      g3.datos.get("torneo_ganado") is not True, "")
check("Perder en octavos lleva a la pantalla de resultado", g3.estado == "resultado",
      g3.estado)

# --- Un partido rapido no da monedas --------------------------------------
g4 = Game()
g4.ronda = 2
g4.en_torneo = False
g4.marcador = [5, 2]
m4 = g4.monedas()
g4.fin_partido()
check("El partido rapido no da monedas (solo el torneo)", g4.monedas() == m4,
      f"{m4} -> {g4.monedas()}")

save.reset()
print(f"\n{'=' * 52}")
print(f"  {PASS} correctas, {FAIL} fallidas")
print(f"{'=' * 52}")
pygame.quit()
sys.exit(1 if FAIL else 0)
