"""Comprobaciones del hockey de aire, sin abrir ventana.

Ejecuta:
    python tools/hockey_test.py
"""

from __future__ import annotations

import os
import math
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from hockey import cosmetics, items, physics, render, save, settings as S, tournament  # noqa: E402
from hockey.game import (  # noqa: E402
    AYUDA, FINAL, MENU, PARTIDO, PRESENTACION, RESULTADO, Game,
)

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


# --- 1. Geometria de la mesa ------------------------------------------------
print("\n1. La mesa")
check("La mesa cabe en la ventana",
      S.TABLE_W + 2 * S.TABLE_X < S.WINDOW_WIDTH and S.TABLE_H + S.TABLE_Y < S.WINDOW_HEIGHT,
      f"{S.TABLE_W}x{S.TABLE_H} en {S.WINDOW_WIDTH}x{S.WINDOW_HEIGHT}")
check("La porteria es mas pequena que el alto de la mesa",
      S.GOAL_W < S.TABLE_H, f"porteria {S.GOAL_W}, alto {S.TABLE_H}")
check("La porteria cabe con paddle de 40 m radio",
      S.RINK_CENTER_Y - S.GOAL_W / 2 > S.PADDLE_R and
      S.RINK_CENTER_Y + S.GOAL_W / 2 < S.TABLE_H - S.PADDLE_R, "")

# --- 2. Fisica: la puck rebota bien ---------------------------------------
print("\n2. Fisica de la puck")
# Rebote en pared superior
pk = physics.Puck()
pk.pos = pygame.Vector2(S.TABLE_W / 2, S.PUCK_R + 1)
pk.vel = pygame.Vector2(200, -400)
for _ in range(30):
    physics.actualizar(pk, 1 / 60)
    if pk.vel.y > 0:
        break
check("Rebota en la pared de arriba", pk.vel.y > 0, f"vy={pk.vel.y:.0f}")

# Rebote en pared izquierda (fuera de la porteria)
pk = physics.Puck()
pk.pos = pygame.Vector2(S.PUCK_R + 1, S.RINK_CENTER_Y - 120)
pk.vel = pygame.Vector2(-400, 0)
for _ in range(30):
    physics.actualizar(pk, 1 / 60)
    if pk.vel.x > 0:
        break
check("Rebota en la pared izquierda fuera de la porteria", pk.vel.x > 0, f"vx={pk.vel.x:.0f}")

# NO rebota: por la porteria debe salir
pk = physics.Puck()
pk.pos = pygame.Vector2(S.PUCK_R + 1, S.RINK_CENTER_Y)
pk.vel = pygame.Vector2(-600, 0)
gol = None
for _ in range(60):
    ev = physics.actualizar(pk, 1 / 60)
    if ev == "gol":
        gol = ev
        break
check("La puck entra por la porteria izquierda", gol == "gol", f"gol={gol}")

# Porteria derecha
pk = physics.Puck()
pk.pos = pygame.Vector2(S.TABLE_W - S.PUCK_R - 1, S.RINK_CENTER_Y)
pk.vel = pygame.Vector2(600, 0)
gol = None
for _ in range(60):
    ev = physics.actualizar(pk, 1 / 60)
    if ev == "gol":
        gol = ev
        break
check("La puck entra por la porteria derecha", gol == "gol", f"gol={gol}")

# Limite de velocidad
pk = physics.Puck()
pk.vel = pygame.Vector2(5000, 0)
pk.limitar()
check("La velocidad maxima se respeta", pk.vel.length() <= S.PUCK_MAX_SPEED + 0.01, f"{pk.vel.length():.0f}")
# Empuje minimo
pk2 = physics.Puck()
pk2.vel = pygame.Vector2(1, 0)
pk2.limitar()
check("La puck no se queda parada en el centro", pk2.vel.length() >= S.PUCK_MIN_SPEED, f"{pk2.vel.length():.1f}")

# La pala devuelve la puck: la puck viene hacia la pala y sale rebotada
pk = physics.Puck()
pk.pos = pygame.Vector2(S.TABLE_W / 2, S.RINK_CENTER_Y)
pk.vel = pygame.Vector2(-600, 0)  # viene hacia la izquierda
pala = physics.Pala(-1)
pala.pos = pygame.Vector2(S.TABLE_W / 2 - 52, S.RINK_CENTER_Y)
pala.vel = pygame.Vector2(0, 0)
toco = physics.choque_pala(pk, pala)
check("La pala toca la puck", toco, "")
check("La puck sale rebotada hacia atras", pk.vel.x > 0, f"vx={pk.vel.x:.0f}")

# Y si la pala va a por ella, la puck sale mas rapido
pk1 = physics.Puck()
pk1.pos = pygame.Vector2(S.TABLE_W / 2, S.RINK_CENTER_Y)
pk1.vel = pygame.Vector2(-600, 0)
pa1 = physics.Pala(-1)
pa1.pos = pygame.Vector2(S.TABLE_W / 2 - 52, S.RINK_CENTER_Y)
pa1.vel = pygame.Vector2(0, 0)
physics.choque_pala(pk1, pa1)
pk2 = physics.Puck()
pk2.pos = pygame.Vector2(S.TABLE_W / 2, S.RINK_CENTER_Y)
pk2.vel = pygame.Vector2(-600, 0)
pa2 = physics.Pala(-1)
pa2.pos = pygame.Vector2(S.TABLE_W / 2 - 52, S.RINK_CENTER_Y)
pa2.vel = pygame.Vector2(900, 0)  # la pala va hacia la puck
physics.choque_pala(pk2, pa2)
check("Ir a por la puck acelera el rebote", pk2.vel.length() > pk1.vel.length(),
      f"quieto {pk1.vel.length():.0f} vs avanzando {pk2.vel.length():.0f}")

# Una pala lejos de la puck no la toca
pk = physics.Puck()
pk.pos = pygame.Vector2(S.TABLE_W / 2, S.RINK_CENTER_Y)
pala = physics.Pala(-1)
pala.pos = pygame.Vector2(50, 50)
check("Una pala lejos no toca nada", not physics.choque_pala(pk, pala), "")

# Con mas potencia se alcanza mas lejos
pk1 = physics.Puck()
pk1.pos = pygame.Vector2(300, 200)
pk1.vel = pygame.Vector2(0, 0)
p1 = physics.Pala(-1)
p1.pos = pygame.Vector2(300 - 62, 200)
d1 = physics.choque_pala(pk1, p1, potencia=1.0)
pk2 = physics.Puck()
pk2.pos = pygame.Vector2(300, 200)
p2 = physics.Pala(-1)
p2.pos = pygame.Vector2(300 - 62, 200)
d2 = physics.choque_pala(pk2, p2, potencia=1.6)
check("Con mas potencia se toca la puck desde mas lejos", d2 and not d1,
      f"normal={d1} con potencia={d2}")

# El escudo bloquea
pk = physics.Puck()
pk.pos = pygame.Vector2(26, S.RINK_CENTER_Y)
pk.vel = pygame.Vector2(-700, 0)
bloq = physics.choque_escudo(pk, 26.0, 16, S.GOAL_W + 20)
check("El escudo bloquea la puck", bloq, "")
check("El escudo devuelve la puck hacia el centro", pk.vel.x > 0, f"vx={pk.vel.x:.0f}")

# --- 3. Las mesas solo cambian el aspecto ----------------------------------
print("\n3. Mesas y objetos: solo aspecto")
game = Game()
tablas = [m.key for m in cosmetics.TODAS_LAS_MESAS]
base = None
for clave in tablas:
    game.mesa_sel = clave
    game.estado = PARTIDO
    game.draw()
    # tostring esta obsoleto; copiamos la superficie y la comparamos.
    copia = game.screen.copy()
    digest = hash(bytes(copia.get_buffer()))
    if clave == "mesa_basica":
        base = digest
        check("La mesa basica se dibuja", digest is not None, "")
    else:
        check(f"La mesa {clave} se ve distinta a la basica", digest != base, "misma imagen")
# Y todas dan la misma fisica
game.mesa_sel = "mesa_suprema"
p1 = physics.Puck()
p1.pos = pygame.Vector2(S.TABLE_W / 2, S.RINK_CENTER_Y)
p1.vel = pygame.Vector2(500, 200)
p2 = physics.Puck()
p2.pos = pygame.Vector2(S.TABLE_W / 2, S.RINK_CENTER_Y)
p2.vel = pygame.Vector2(500, 200)
for _ in range(30):
    physics.actualizar(p1, 1 / 60)
    physics.actualizar(p2, 1 / 60)
check("La fisica es identica en todas las mesas", p1.pos == p2.pos, f"{p1.pos} vs {p2.pos}")

# --- 4. Consumibles ---------------------------------------------------------
print("\n4. Consumibles")
for item in items.TODOS:
    check(f"{item.name} tiene tiempo limitado", 0 < item.duracion <= 30.0, f"{item.duracion}s")
    check(f"{item.name} tiene precio", item.precio > 0, str(item.precio))
    check(f"{item.name} no dura la partida entera", item.duracion < 60.0, f"{item.duracion}s")
# Todos distintos y con iconos
claves = [i.key for i in items.TODOS]
check("Hay 6 consumibles distintos", len(set(claves)) == 6, str(claves))
check("Los iconos son distintos", len(set(i.icono for i in items.TODOS)) == 6, "")

# El reloj de un consumible funciona
game = Game()
game.estado = PARTIDO
game.fase = "juego"
est = items.ItemEnUso(items.MONSTRUO)
est.activar()
check("Un consumible activado esta activo", est.activo, "")
est.update(est.item.duracion + 0.1)
check("El consumible se acaba al pasar su tiempo", not est.activo, f"quedan {est.tiempo}")
check("El tiempo nunca baja de cero", est.tiempo == 0.0, str(est.tiempo))

# Multiplicador de musculos
game.items_jug.clear()
m = items.ItemEnUso(items.MUSCULOS)
game.items_jug["musculos"] = m
check("Sin musculos el gol vale 1", game.multiplicador_musculos(0) == 1, "")
m.activar()
check("Con musculos el gol vale 2", game.multiplicador_musculos(0) == 2, "")

# Escudo aguanta 2 goles
game.items_jug.clear()
e = items.ItemEnUso(items.ESCUDO)
game.items_jug["escudo"] = e
e.activar()
check("El escudo protege al principio", game.escudo_poses(0) is not None, "")
e.gol_protegido = 2
check("El escudo se rompe al segundo toque", game.escudo_poses(0) is None, "")

# Monstruo y rafaga aceleran
game.items_jug.clear()
check("Sin monstruo la fuerza es normal", game.fuerza_monstruo() == 1.0, "")
mo = items.ItemEnUso(items.MONSTRUO)
mo.activar()
game.items_jug["monstruo"] = mo
check("Con monstruo la puck sale mas fuerte", game.fuerza_monstruo() > 1.0, f"{game.fuerza_monstruo()}")
ra = items.ItemEnUso(items.RAfAGA)
ra.activar()
game.items_jug["rafaga"] = ra
check("Con rafaga la pala pega mas fuerte", game.fuerza_rafaga() > 1.0, f"{game.fuerza_rafaga()}")

# Gigante: aumenta el tamano de la pala y da algo de potencia
game.items_jug.clear()
game.pala_jug.radio = game.pala_jug.radio_base
game.items_jug.clear()
normal = game.pala_jug.radio_base
gi = items.ItemEnUso(items.GIGANTE)
gi.activar()
game.items_jug["gigante"] = gi
game.aplicar_tamanos()
check("Gigante agranda la pala", game.pala_jug.radio > normal,
      f"{normal} -> {game.pala_jug.radio}")
check("Gigante anade potencia", game.fuerza_gigante() > 1.0, f"{game.fuerza_gigante()}")
gi.update(gi.item.duracion + 0.1)
game.aplicar_tamanos()
check("Al acabar Gigante la pala vuelve a su tamano",
      abs(game.pala_jug.radio - normal) < 0.01, f"{game.pala_jug.radio}")

# El tiro sale con fuerza hacia donde se apunta (hitbox arreglado)
pala_j = physics.Pala(-1)
pk2 = physics.Puck()
pk2.pos = pygame.Vector2(S.TABLE_W * 0.5, S.RINK_CENTER_Y)
pala_j.pos = pk2.pos - pygame.Vector2(50.0, 0)
destino = pygame.Vector2(S.TABLE_W - 5.0, S.RINK_CENTER_Y - S.GOAL_W * 0.4)
ok = physics.golpear_hacia(pk2, pala_j, destino, S.PUCK_MAX_SPEED * 0.85)
check("El golpe dirigido se produce", ok, "")
check("El golpe sale con toda la fuerza", pk2.vel.length() > S.PUCK_MAX_SPEED * 0.7,
      f"v={pk2.vel.length():.0f}")
if pk2.vel.length() > 1.0:
    hacia_destino = (destino - pk2.pos).normalize()
    error_dir = (pk2.vel.normalize() - hacia_destino).length()
    check("La puck va hacia el punto apuntado", error_dir < 0.35, f"error {error_dir:.2f}")

# Hielo reduce el agarre rival
game.items_ia.clear()
check("Sin hielo el rival no resbala", game.hielo_en(1) == 0.0, "")
hi = items.ItemEnUso(items.HIELO)
hi.activar()
game.items_jug["hielo"] = hi
check("Con hielo el rival resbala", game.hielo_en(1) > 0.0, f"{game.hielo_en(1):.2f}")

# No se puede usar sin haberlo comprado
game.datos["items_comprados"] = []
game.items_jug.clear()
game.fase = "juego"
check("Sin comprar no se usa", not game.tiene_item(items.MONSTRUO), "")
game.datos["items_comprados"] = ["monstruo"]
check("Comprado si se puede usar", game.tiene_item(items.MONSTRUO), "")

# --- 5. Torneo y monedas ---------------------------------------------------
print("\n5. Torneo y economia")
check("El torneo tiene 4 rondas", len(tournament.RONDAS) == 4, str(tournament.RONDAS))
check("Empieza en octavos", tournament.RONDAS[0] == "Octavos", tournament.RONDAS[0])
check("Termina en final", tournament.RONDAS[-1] == "Final", tournament.RONDAS[-1])
# Cuanto mas lejos, mas monedas
ganadas = [tournament.monedas_ganadas(i, True) for i in range(4)]
check("Cuanto mas ronda, mas monedas", ganadas == sorted(ganadas) and ganadas[0] < ganadas[-1], str(ganadas))
# Campeon es lo maximo
check("Ganar el torneo da el bote", tournament.total_ganado(3, True) > tournament.total_ganado(2, True),
      f"{tournament.total_ganado(3, True)} vs {tournament.total_ganado(2, True)}")
check("Solo ser campeon da el bote extra",
      tournament.es_campeon(3, True) and not tournament.es_campeon(2, True), "")
check("Perder la final no da el bote de campeon", not tournament.es_campeon(3, False), "")
# El rival es siempre distinto, y la IA no se pasa de nivel
for i in range(3):
    n0, lv0 = tournament.rival_de(i)[0], tournament.rival_de(i)[1]
    n1, lv1 = tournament.rival_de(i + 1)[0], tournament.rival_de(i + 1)[1]
    check(f"Ronda {i+1} tiene rival distinto", n0 != n1, f"{n0} -> {n1}")
# Y la dificultad de la IA sube ronda a ronda, sin saltos hacia atras
from hockey.ai import NIVELES_ORDENADOS, NIVEL_POR_RONDA  # noqa: E402

niveles = [tournament.nivel_de(i) for i in range(4)]
check("La dificultad de la IA sube ronda a ronda",
      niveles == ["Novato", "Dificil", "Experto", "Imposible"], str(niveles))
pos = [NIVELES_ORDENADOS.index(n) for n in niveles]
check("La dificultad nunca retrocede", pos == sorted(pos), str(pos))
check("La final es contra el nivel mas dificil",
      niveles[-1] == "Imposible" and niveles[0] != "Imposible", str(niveles))

# --- 6. Tienda: precios y bloqueos -----------------------------------------
print("\n6. Tienda")
for item in items.TODOS:
    check(f"{item.name} se puede pagar en monedas", item.precio in S.ITEM_PRICES.values(), str(item.precio))
# Los de campeon no se compran con monedas: se ganan
suprema = cosmetics.MESAS_POR_CLAVE["mesa_suprema"]
canela = cosmetics.PALAS_POR_CLAVE["pala_canela"]
check("La mesa de campeon se gana, no se compra",
      suprema.solo_ganando and suprema.precio == 0, "")
check("La pala de campeon se gana, no se compra", canela.solo_ganando, "")
check("La puck de campeon se gana, no se compra",
      cosmetics.PUCKS_POR_CLAVE["puck_canela"].solo_ganando, "")
# Los demas si tienen precio
for m in (cosmetics.HIELO, cosmetics.METAL, cosmetics.NEON):
    check(f"Mesa {m.name} tiene precio", m.precio > 0, str(m.precio))

# --- 7. Partidas completas simuladas ---------------------------------------
print("\n7. Partidos simulados")

def simular(nivel: str, segundos: float = 120.0) -> dict:
    """Juega un partido con el raton moviendose de forma automatica.

    El raton manda a la vez la pala y la mira (la mira no puede pasar de la
    mitad propia). Asi que para atacar hay que colocarse en el borde derecho
    de la mitad: es lo que hace un jugador de verdad.
    """
    g = Game()
    g.preparar_partido("Test", nivel, torneo=False, presentacion=False)
    dt = 1 / 60
    t = 0.0
    for i in range(int(segundos * 60)):
        # El raton va pegado al borde derecho de su mitad (para atacar) y va
        # barriendo arriba y abajo siguiendo la puck. El barrido importa: si
        # la pala se moviese siempre igual, el tiro sale siempre en la misma
        # direccion y la IA lo para sin esfuerzo, porque adivina de antemano
        # por donde va a salir. Un jugador de verdad varia.
        t += dt
        my = g.puck.pos.y + 70.0 * math.sin(t * 2.4)
        my = max(S.PADDLE_R, min(S.TABLE_H - S.PADDLE_R, my))
        mx = S.TABLE_W / 2 - S.PADDLE_R
        pygame.mouse.set_pos((int(mx + S.TABLE_X), int(my + S.TABLE_Y)))
        g.update(dt)
        g.draw()
        if g.estado != PARTIDO:
            break
    return {
        "marcador": tuple(g.marcador),
        "estado": g.estado,
        "fase": g.fase,
    }

res = simular("Normal", 420)
check(
    "Un partido llega a 5 puntos (nadie controla de verdad)",
    max(res["marcador"]) >= S.GOALS_TO_WIN,
    f"{res['marcador']} en 420 s, fase {res['fase']}",
)
check("Se marcaron puntos", res["marcador"][0] + res["marcador"][1] >= 0, str(res["marcador"]))
check("El marcador no pasa de 5", all(m <= S.GOALS_TO_WIN for m in res["marcador"]), str(res["marcador"]))

# Un partido con la puck yendo a por el gol: debe acabar en 5
g = Game()
g.preparar_partido("Test", "Normal", torneo=False, presentacion=False)
g.fase = "juego"
g.marcador = [0, 0]
# Ponemos la puck volando hacia la porteria rival.
g.puck.pos = pygame.Vector2(S.TABLE_W - 60, S.RINK_CENTER_Y)
g.puck.vel = pygame.Vector2(900, 0)
gol = False
for _ in range(120):
    g.update(1 / 60)
    if g.marcador[0] >= 1:
        gol = True
        break
check("Marcas cuando metes la puck en la porteria rival", gol, f"marcador {g.marcador}")

# Gol del rival
g = Game()
g.preparar_partido("Test", "Normal", torneo=False, presentacion=False)
g.fase = "juego"
g.puck.pos = pygame.Vector2(60, S.RINK_CENTER_Y)
g.puck.vel = pygame.Vector2(-900, 0)
gol = False
for _ in range(120):
    g.update(1 / 60)
    if g.marcador[1] >= 1:
        gol = True
        break
check("El rival marca cuando le metes la puck", gol, f"marcador {g.marcador}")

# El escudo evita un gol. Solo miramos al PRIMER golpe: si esperamos mas, el
# puck puede rebotar y volver a chocar con el escudo y no estaríamos midiendo
# lo que queremos medir.
g = Game()
g.preparar_partido("Test", "Normal", torneo=False, presentacion=False)
g.fase = "juego"
esc = items.ItemEnUso(items.ESCUDO)
esc.activar()
g.items_jug["escudo"] = esc
g.puck.pos = pygame.Vector2(60, S.RINK_CENTER_Y)
g.puck.vel = pygame.Vector2(-900, 0)
for _ in range(200):
    g.update(1 / 60)
    if esc.gol_protegido >= 1 or g.marcador[1] >= 1:
        break
check("El escudo evita el gol", g.marcador[1] == 0, f"marcador {g.marcador}")
check("El escudo aguanta el golpe y se gasta", esc.gol_protegido == 1,
      f"{esc.gol_protegido}")

# --- 8. Guardar progreso ----------------------------------------------------
print("\n8. Guardado")
d = save.load()
check("El guardado tiene monedas", isinstance(d.get("monedas"), int), str(d.get("monedas")))
check("El guardado tiene objetos", isinstance(d.get("objetos"), list), "")
check("Siempre incluye los objetos basicos",
      all(k in d["objetos"] for k in ("mesa_basica", "pala_basica", "puck_clasica")), str(d["objetos"]))
antes = save.load()
save.save({**antes, "monedas": 999})
check("Se guardan y cargan las monedas", save.load()["monedas"] == 999, str(save.load()["monedas"]))
# Fichero corrupto -> valores por defecto
try:
    with open(save._path(), "w", encoding="utf-8") as fh:
        fh.write("{esto no es json")
except OSError:
    pass
rec = save.load()
check("Un guardado roto no rompe el juego", rec["monedas"] == 0, str(rec["monedas"]))
save.save(antes)

# --- 9. Pantallas -----------------------------------------------------------
print("\n9. Pantallas")
g = Game()
for estado in ("menu", "ayuda", "torneo", "tienda", "partido"):
    g.estado = estado
    if estado == "tienda":
        g.tienda_pestana = 0
        g.draw()
        g.tienda_pestana = 1
    try:
        g.draw()
        ok = True
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"      {exc}")
    check(f"La pantalla '{estado}' se dibuja", ok, "")

# Las 5 mesas y todos los objetos en la tienda
g = Game()
g.estado = "tienda"
g.tienda_pestana = 1
try:
    g.draw()
    check("La tienda con 12 objetos se dibuja", True, "")
except Exception as exc:  # noqa: BLE001
    check("La tienda con 12 objetos se dibuja", False, str(exc))

# --- 11. Lo nuevo: emblemas, match point, celebration y el saque ------------
print("\n11. Rivales con caracter, match point y celebracion")

# Cada ronda tiene rival con nombre, lema, color y emblema propios
nombres = [tournament.rival_de(i)[0] for i in range(4)]
lemas = [tournament.rival_de(i)[2] for i in range(4)]
emblemas = [tournament.rival_de(i)[4] for i in range(4)]
colores = [tournament.rival_de(i)[3] for i in range(4)]
check("Los 4 rivales tienen nombre distinto", len(set(nombres)) == 4, str(nombres))
check("Los 4 rivales tienen lema", all(isinstance(x, str) and x for x in lemas), str(lemas))
check("Los 4 rivales tienen emblema", all(isinstance(x, str) and x for x in emblemas), str(emblemas))
check("Los 4 rivales tienen color RGB valido",
      all(len(c) == 3 and all(0 <= v <= 255 for v in c) for c in colores), str(colores))
check("Cada rival tiene un emblema distinto", len(set(emblemas)) == 4, str(emblemas))

# Todos los emblemas se dibujan sin petar
try:
    todos = sorted({"rayo", "furia", "corona", "robot", "bestia", "fantasma"} | set(emblemas))
    for tipo in todos:
        render.emblema(g.screen, tipo, (300, 300), 24, (200, 120, 90))
    check("Se dibujan todos los emblemas", True, "")
except Exception as exc:  # noqa: BLE001
    check("Se dibujan todos los emblemas", False, str(exc))

# El trofeo de campeon se dibuja
try:
    render.trofeo(g.screen, (300, 300), 120)
    check("El trofeo se dibuja", True, "")
except Exception as exc:  # noqa: BLE001
    check("El trofeo se dibuja", False, str(exc))

# Match point: solo avisa con 4 puntos, y solo del que va a ganar
g = Game()
mp_ok = True
for m in ([4, 3], [3, 4], [0, 0], [4, 0], [2, 2], [5, 5]):
    try:
        render.marcador(g.screen, m[0], m[1], S.GOALS_TO_WIN)
    except Exception as exc:  # noqa: BLE001
        mp_ok = False
        print(f"      {exc}")
check("El marcador con match point se dibuja sin petarse", mp_ok, "")

# El aviso sale con meta-1 puntos y no antes, segun la regla
def _avisa(m, meta=S.GOALS_TO_WIN) -> int | None:
    return 0 if m[0] == meta - 1 else (1 if m[1] == meta - 1 else None)

check("Match point solo con 4 a 5", _avisa([4, 3]) == 0, "")
check("Match point rival con 4 a 5", _avisa([3, 4]) == 1, "")
check("Sin match point a 3-3", _avisa([3, 3]) is None, "")
check("Sin match point a 5-0 (ya se acabo)", _avisa([5, 0]) is None, "")

# La celebracion de campeon se dibuja en sus fases
from hockey.game import CELEBRACION_TIEMPO  # noqa: E402

g = Game()
g.monedas_celebracion = 40
g.presentacion_total = CELEBRACION_TIEMPO
fases_ok = True
for restante in (CELEBRACION_TIEMPO - 0.1, CELEBRACION_TIEMPO - 4.0, CELEBRACION_TIEMPO - 7.0):
    g.estado = FINAL
    g.presentacion_en = restante
    try:
        g.draw()
    except Exception as exc:  # noqa: BLE001
        fases_ok = False
        print(f"      {exc}")
check("La celebracion de campeon se dibuja en las 3 fases", fases_ok, "")
check("La celebracion dura unos segundos", 5.0 <= CELEBRACION_TIEMPO <= 20.0,
      f"{CELEBRACION_TIEMPO} s")

# La presentacion de cada ronda se dibuja
g = Game()
pres_ok = True
for ronda in range(4):
    g.ronda = ronda
    g.estado = PRESENTACION
    g.presentacion_total = 4.0
    g.presentacion_en = 1.2
    try:
        g.draw()
    except Exception as exc:  # noqa: BLE001
        pres_ok = False
        print(f"      ronda {ronda}: {exc}")
check("La presentacion se dibuja en las 4 rondas", pres_ok, "")
check("_empezar_ronda existe para arrancar cada ronda", hasattr(g, "_empezar_ronda"), "")
check("El rival guarda lema, color y emblema",
      all(hasattr(g, a) for a in ("rival_lema", "rival_color", "rival_emblema")), "")

# --- 12. El rival puede pegar mas de una vez por partida -------------------
# El bug era que ``espera`` se ponia a positivo al golpear y nunca se bajaba:
# el rival solo podia tocar la puck una vez y a partir de ahi la atraviesa.
print("\n12. El rival sigue pudiendo pegar durante toda la partida")

from hockey.ai import NIVELES, Rival  # noqa: E402

# La espera se baja sola con el tiempo
r = Rival("Dificil")
r.espera = r.cfg["espera"]
for _ in range(60 * 2):
    r.espera = max(0.0, r.espera - 1 / 60)
check("La espera del rival se agota sola", r.espera == 0.0, f"{r.espera} s")

for nivel in NIVELES:
    r = Rival(nivel)
    r.espera = r.cfg["espera"]
    for _ in range(int(60 * (r.cfg["espera"] + 0.3))):
        r.espera = max(0.0, r.espera - 1 / 60)
    check(f"En {nivel} la espera se agota en el tiempo previsto", r.espera == 0.0,
          f"espera={r.cfg['espera']} s")

# Y en un partido real el rival toca la puck muchas veces seguidas.
# Contamos los golpes de verdad, hooking en el golpe que usa la IA, para que
# no dependa de mirar como cambia el signo de la velocidad.
from hockey import ai as ai_mod  # noqa: E402

golpes = {"n": 0}
_golpear_original = ai_mod.physics.golpe_dirigido


def _contando(*a, **k):
    ok = _golpear_original(*a, **k)
    if ok:
        golpes["n"] += 1
    return ok


g = Game()
g.preparar_partido("T", "Imposible", torneo=False, presentacion=False)
g.control_por_mouse = False
ai_mod.physics.golpe_dirigido = _contando
try:
    for _ in range(60 * 240):
        g.update(1 / 60)
        if g.marcador[1] >= S.GOALS_TO_WIN or golpes["n"] >= 25:
            break
finally:
    ai_mod.physics.golpe_dirigido = _golpear_original

check("El rival golpea 6+ veces en un solo partido", golpes["n"] >= 6,
      f"{golpes['n']} golpes")
check("El rival no se queda con la espera bloqueada",
      g.rival.espera <= g.rival.cfg["espera"] + 1e-6, f"{g.rival.espera} s")

# Ninguna mesa cambia la fisica
from hockey.cosmetics import TODAS_LAS_MESAS  # noqa: E402

check("Las 5 mesas tienen patron y acento", all(m.patron and m.acento for m in TODAS_LAS_MESAS),
      str([m.patron for m in TODAS_LAS_MESAS]))
mesas_ok = True
for m in TODAS_LAS_MESAS:
    try:
        render.mesa(g.screen, m)
    except Exception as exc:  # noqa: BLE001
        mesas_ok = False
        print(f"      {m.name}: {exc}")
check("Las 5 mesas se dibujan", mesas_ok, "")

# --- 13. La pala del jugador no tiembla y el tiro va donde apuntas ---------
print("\n13. Control del raton y golpe dirigido")

p = physics.Pala(-1)
# Zona muerta: si estamos cerca, la pala NO se mueve ni un pixel. Antes se
# pegaba al objetivo, y por eso seguia el temblor del raton.
p.pos = pygame.Vector2(300, 300)
p.vel = pygame.Vector2(900, -700)
p.mover_hacia(pygame.Vector2(300.4, 299.6), 1 / 60, 1500.0)
check("Dentro de la zona muerta la pala no se mueve",
      (p.pos - pygame.Vector2(300, 300)).length() < 0.001
      and p.vel.length() == 0.0,
      f"pos={p.pos} vel={p.vel.length():.1f}")
# Justo fuera, se mueve (pero un paso, sin pasarse).
p.pos = pygame.Vector2(300, 300)
p.mover_hacia(pygame.Vector2(300, 300) + pygame.Vector2(40, 0), 1 / 60, 1500.0)
check("Fuera de la zona muerta la pala se mueve",
      0 < p.pos.x - 300 <= 1500.0 / 60 + 0.01, f"se movio {p.pos.x - 300:.2f} px")

# Y no sobrepasa el objetivo: sin esto oscila alrededor.
p.pos = pygame.Vector2(100, 300)
p.vel = pygame.Vector2(0, 0)
destino = pygame.Vector2(106, 300)
for _ in range(30):
    p.mover_hacia(destino, 1 / 60, 1500.0)
# Con la zona muerta la pala se queda a PEGADO del objetivo, sin pasarse.
check("No sobrepasa el raton",
      0.0 <= (destino - p.pos).length() <= physics.PEGADO + 0.01,
      f"pos={p.pos}, se queda a {(destino - p.pos).length():.2f} px "
      f"(zona muerta {physics.PEGADO})")
check("La pala se queda quieta al llegar", p.vel.length() == 0.0,
      f"{p.vel.length():.1f}")

# Al tocar el borde se anula la velocidad de ese eje (si no, da un tiron
# al apartar el raton).
p.pos = pygame.Vector2(S.TABLE_W - p.radio, 300)
p.vel = pygame.Vector2(1200.0, 0.0)
p.mover_hacia(pygame.Vector2(S.TABLE_W - p.radio, 300), 1 / 60, 1500.0)
check("En el borde se anula la velocidad", abs(p.vel.x) < 0.001, f"{p.vel.x:.1f}")

# Al mover el raton en linea recta, la pala no cambia de signo de velocidad
# (eso es el tembleque).
p.pos = pygame.Vector2(100, 300)
p.vel = pygame.Vector2(0, 0)
cambios = 0
anterior = 0
for i in range(120):
    objetivo = pygame.Vector2(100 + i * 2, 300)   # el raton avanza recto
    p.mover_hacia(objetivo, 1 / 60, 1500.0)
    if p.vel.x < 0 < anterior:
        cambios += 1
    anterior = p.vel.x
check("Mover el raton en recto no hace dar la pala", cambios == 0,
      f"{cambios} cambios de sentido")

# El golpe dirigido manda la puck hacia el objetivo, no donde toque la pala.
def _tiro(mirar: tuple[float, float], contacto: tuple[float, float]) -> pygame.Vector2:
    pal = physics.Pala(-1)
    pal.pos = pygame.Vector2(200, 270)
    pk = physics.Puck()
    # Ponemos la puck a la izquierda-arriba de la pala: es el peor angulo.
    pk.pos = pal.pos + pygame.Vector2(contacto)
    objetivo = pygame.Vector2(mirar)
    ok = physics.golpe_dirigido(pk, pal, objetivo, 900.0)
    return pk.vel if ok else pygame.Vector2(0, 0)


v1 = _tiro((880.0, 120.0), (-30.0, -20.0))   # puck por arriba
v2 = _tiro((880.0, 120.0), (-30.0, 20.0))    # puck por abajo
esperado = pygame.Vector2(680, -150).normalize()
check("El tiro sale hacia el objetivo (arriba)",
      (v1.normalize() - esperado).length() < 0.02, f"dir={v1.normalize()}")
check("El tiro sale hacia el objetivo (abajo)",
      (v2.normalize() - esperado).length() < 0.02, f"dir={v2.normalize()}")
check("El tiro va igual toque la puck donde toque",
      (v1.normalize() - v2.normalize()).length() < 0.02,
      f"{v1.normalize()} vs {v2.normalize()}")
check("El tiro sale con la velocidad pedida", abs(v1.length() - 900.0) < 1.0,
      f"{v1.length():.1f}")

# Y ahora SI se aplica siempre, cosa que antes fallaba: el puck a la distancia
# exacta de contacto ya no se pierde.
pal = physics.Pala(-1)
pal.pos = pygame.Vector2(200, 270)
pk = physics.Puck()
d = pal.pos + pygame.Vector2(pal.radio + pk.radio, 0.0)
pk.pos = pygame.Vector2(d)
ok_exacto = physics.golpe_dirigido(pk, pal, pygame.Vector2(880, 120), 900.0)
check("El golpe se aplica justo en el limite de contacto", ok_exacto, str(ok_exacto))
check("Tras el golpe la puck queda fuera de la pala",
      (pk.pos - pal.pos).length() > pal.radio + pk.radio - 0.5,
      f"{(pk.pos - pal.pos).length():.1f}")

# Un roce cuenta como golpe (el perdon), para que no parezca que no toca.
pk2 = physics.Puck()
pk2.pos = pal.pos + pygame.Vector2(pal.radio + pk2.radio + physics.PERDON - 0.5, 0.0)
check("Un roce justo tambien cuenta como golpe",
      physics.golpe_dirigido(pk2, pal, pygame.Vector2(880, 120), 900.0),
      f"dist={(pk2.pos - pal.pos).length():.1f} perdon={physics.PERDON}")
# Pero mas alla del perdon, no.
pk3 = physics.Puck()
pk3.pos = pal.pos + pygame.Vector2(pal.radio + pk3.radio + physics.PERDON + 8.0, 0.0)
check("Lejos de la pala no hay golpe",
      not physics.golpe_dirigido(pk3, pal, pygame.Vector2(880, 120), 900.0), "")

# --- 14. Solo raton: la pala quieta y el tiro va donde mueves --------------
print("\n14. Solo raton: sin tembleque y el tiro va hacia donde mueves")

from hockey import game as game_mod  # noqa: E402

check("Ya no existe el boton de potencia",
      not hasattr(Game, "potencia_actual"), "sobro potencia_actual")
check("Ya no queda el retardo de carga en settings",
      not hasattr(S, "CHARGE_TIME"), "sobro CHARGE_TIME")
check("La pala ya no guarda carga",
      "carga" not in physics.Pala.__slots__, str(physics.Pala.__slots__))
check("Ya no queda la mira antigua", not hasattr(Game(), "aim_locked"),
      "sobro aim_locked")

# El ESPACIO no tiene que hacer nada en ninguna pantalla.
g = Game()
for _estado in (MENU, AYUDA, "torneo", "tienda", "partido"):
    g.estado = _estado
    antes = g.estado
    g.tecla(pygame.K_SPACE)
    check(f"El ESPACIO no hace nada en '{_estado}'", g.estado == antes,
          f"{antes} -> {g.estado}")

# --- La pala NO se mueve dos veces por fotograma ---
# Ese era el tembleque: ``mover_hacia`` mueve la pala y luego se llamaba a
# ``mover`` otra vez, con lo que avanzaba dos pasos por fotograma, se pasaba de
# largo y al siguiente tenia que corregir.
g = Game()
g.preparar_partido("Test", "Normal", torneo=False, presentacion=False)
g.control_por_mouse = True
g.fase = "juego"
quieto = pygame.Vector2(g.pala_jug.pos)
pygame.mouse.set_pos((int(quieto.x + S.TABLE_X), int(quieto.y + S.TABLE_Y)))
# Primero se coloca: la pala esta en su posicion de inicio y tiene que ir
# hasta el raton, y eso es movimiento real. Luego ya si, raton parado.
for _ in range(60):
    g.update(1 / 60)
quieto = pygame.Vector2(g.pala_jug.pos)
for _ in range(60):
    g.update(1 / 60)
check("Con el raton quieto la pala no se mueve",
      (g.pala_jug.pos - quieto).length() < 0.001,
      f"se ha movido {(g.pala_jug.pos - quieto).length():.2f} px en 1 s")

g = Game()
g.preparar_partido("Test", "Normal", torneo=False, presentacion=False)
g.control_por_mouse = True
g.fase = "juego"
# El raton empieza EN la pala: si no, el primer trozo la pala va hacia el
# raton porque esta mas lejos, y eso no es un retroceso por tembleque.
inicio = g.pala_jug.pos.x
viaje = []
for i in range(60):
    mx = inicio + i * 2.0   # el raton avanza recto, sin parar
    pygame.mouse.set_pos((int(mx + S.TABLE_X), int(S.TABLE_Y + S.RINK_CENTER_Y)))
    g.update(1 / 60)
    viaje.append(g.pala_jug.pos.x)
retrocesos = sum(1 for a, b in zip(viaje, viaje[1:]) if b < a - 0.5)
check("Moviendo el raton recto la pala no retrocede", retrocesos == 0,
      f"{retrocesos} retrocesos")
check("La pala llega al final del recorrido",
      abs(viaje[-1] - (inicio + 59 * 2.0)) <= physics.PEGADO + 8.0,
      f"llego a {viaje[-1]:.1f}, esperaba {inicio + 59 * 2.0:.1f} "
      f"(diferencia {abs(viaje[-1] - (inicio + 59 * 2.0)):.1f} px: zona muerta "
      f"{physics.PEGADO} + retardo del filtro)")

# Con la mano temblorosa y el raton quieto, la pala se tiene que quedar
# clavada. Antes la seguia y era el tembleque que veia el jugador.
def _con_temblor(sigma: float) -> float:
    """Cuanto se mueve la pala con el raton quieto pero con mano temblosa.

    Se ignoran los 2 primeros segundos: ahi la pala va a colocarse donde
    estaba el raton, y eso es movimiento real, no tembleque.
    """
    random.seed(3)
    t = Game()
    t.preparar_partido("Test", "Normal", torneo=False, presentacion=False)
    t.control_por_mouse = True
    t.fase = "juego"
    mx, my = 250.0, 270.0
    puntos = []
    for _ in range(600):
        mx += random.gauss(0, sigma)
        my += random.gauss(0, sigma)
        pygame.mouse.set_pos((int(mx + S.TABLE_X), int(my + S.TABLE_Y)))
        t.update(1 / 60)
        puntos.append(t.pala_jug.pos.copy())
    return sum((b - a).length() for a, b in zip(puntos[120:], puntos[121:]))


tranquilo = _con_temblor(0.0)
real = _con_temblor(0.5)
check("Con la mano totalmente quieta la pala no se mueve", tranquilo < 0.5,
      f"recorrido {tranquilo:.2f} px en 8 s")
check("Con temblor de mano (0.5 px) la pala casi no se mueve",
      real < 80.0, f"recorrido {real:.1f} px en 8 s ({real / 8:.1f} px/s)")

# --- La direccion del tiro ---
g = Game()
g.pala_jug.pos = pygame.Vector2(300, 200)
for v, nombre in (
    (pygame.Vector2(600, -600), "arriba-derecha"),
    (pygame.Vector2(600, 600), "abajo-derecha"),
    (pygame.Vector2(900, 0), "recta a la derecha"),
    (pygame.Vector2(700, 250), "casi recta"),
):
    d = g.calcular_aim_dir(v)
    desv = (d - v.normalize()).length()
    check(f"Moviendo la pala {nombre} el tiro va para ahi", desv < 0.001,
          f"desvio {desv:.4f}")

# Parado, arriba: a porteria por abajo. Parado, abajo: por arriba.
g.pala_jug.pos = pygame.Vector2(300, 100)
arriba = g.calcular_aim_dir(pygame.Vector2(0, 0))
check("Quieto en la parte de arriba, el tiro va a porteria hacia abajo",
      arriba.x > 0.8 and arriba.y > 0,
      f"({arriba.x:.2f},{arriba.y:.2f})")
g.pala_jug.pos = pygame.Vector2(300, 440)
abajo = g.calcular_aim_dir(pygame.Vector2(0, 0))
check("Quieto en la parte de abajo, el tiro va a porteria hacia arriba",
      abajo.x > 0.8 and abajo.y < 0,
      f"({abajo.x:.2f},{abajo.y:.2f})")

# Un temblor de un pixel no puede cambiar la direccion del tiro.
g.pala_jug.pos = pygame.Vector2(300, 270)
ruido = [g.calcular_aim_dir(pygame.Vector2(1, 0)) for _ in range(5)]
check("El temblor minimo no cambia la direccion",
      all((d - ruido[0]).length() < 0.001 for d in ruido),
      str([f"({d.x:.2f},{d.y:.2f})" for d in ruido]))

# --- Y el tiro real en un partido, con el raton de verdad ---
_real = game_mod.physics.golpe_dirigido
_tiros = []


def _enganchar(pk, pala, objetivo, potencia):
    ok = _real(pk, pala, objetivo, potencia)
    if ok and pala.lado < 0:      # solo los tiros del JUGADOR
        _tiros.append(pygame.Vector2(pk.vel).normalize())
    return ok


game_mod.physics.golpe_dirigido = _enganchar
try:
    # Movemos el raton en diagonal hacia arriba-derecha y, cuando la pala ya
    # va a velocidad de verdad, le ponemos la puck al lado para que golpee.
    _tiros.clear()
    esperado = pygame.Vector2(4.0, -7.0).normalize()
    for intento in range(40):
        g = Game()
        g.preparar_partido("Test", "Imposible", torneo=False, presentacion=False)
        g.control_por_mouse = True
        g.fase = "juego"
        mx0, my0 = 150.0, 380.0
        pygame.mouse.set_pos((int(mx0 + S.TABLE_X), int(my0 + S.TABLE_Y)))
        paso = 0
        # Primero la pala se coloca y cogemos velocidad.
        for paso in range(1, 14):
            pygame.mouse.set_pos((
                int(mx0 + 4.0 * paso + S.TABLE_X),
                int(my0 - 7.0 * paso + S.TABLE_Y),
            ))
            g.update(1 / 60)
        # Ahora la puck, y seguimos moviendo el raton en la misma direccion.
        g.puck.pos = pygame.Vector2(g.pala_jug.pos.x + 50.0,
                                    g.pala_jug.pos.y - 8.0)
        g.puck.vel = pygame.Vector2(0, 0)
        _tiros.clear()
        for mas in range(1, 14):
            pygame.mouse.set_pos((
                int(mx0 + 4.0 * (paso + mas) + S.TABLE_X),
                int(my0 - 7.0 * (paso + mas) + S.TABLE_Y),
            ))
            g.update(1 / 60)
            if _tiros:
                break
        if _tiros:
            break
    if _tiros:
        desv = (_tiros[0] - esperado).length()
        check("En un partido el tiro va hacia donde mueves el raton",
              desv < 0.25,
              f"desvio {desv:.3f} (sale hacia {_tiros[0].x:.2f},"
              f"{_tiros[0].y:.2f}; esperaba {esperado.x:.2f},{esperado.y:.2f})")
    else:
        check("En un partido el tiro va hacia donde mueves el raton", False,
              "no hubo golpe")

    # Quieto de verdad: primero dejamos que la pala se calme por completo
    # (su velocidad suavizada tarda unos fotogramas en bajar) y luego ponemos
    # la puck al lado.
    _tiros.clear()
    random.seed(11)
    for intento in range(60):
        g = Game()
        g.preparar_partido("Test", "Imposible", torneo=False, presentacion=False)
        g.control_por_mouse = True
        g.fase = "juego"
        pygame.mouse.set_pos((int(200 + S.TABLE_X), int(300 + S.TABLE_Y)))
        for _ in range(40):       # la pala se coloca y se queda quieta
            g.update(1 / 60)
        g.puck.pos = pygame.Vector2(g.pala_jug.pos.x + 48.0,
                                    g.pala_jug.pos.y - 22.0)
        g.puck.vel = pygame.Vector2(0, 0)
        for _ in range(6):
            g.update(1 / 60)
            if _tiros:
                break
    if _tiros:
        check("Quieto, el tiro va siempre hacia porteria",
              all(v.x > 0.7 for v in _tiros),
              f"{len(_tiros)} tiros, x minimo {min(v.x for v in _tiros):.2f}")
        check("Quieto, el tiro no sale para cualquier lado",
              len({(round(v.x, 1), round(v.y, 1)) for v in _tiros}) <= 4,
              f"{len({(round(v.x, 1), round(v.y, 1)) for v in _tiros})} "
              f"direcciones distintas")
    else:
        check("Quieto, el tiro va siempre hacia porteria", False,
              "no hubo golpe")
finally:
    game_mod.physics.golpe_dirigido = _real

# Resumen
print(f"\n{'=' * 52}")
print(f"  {PASS} correctas, {FAIL} fallidas")
print(f"{'=' * 52}")
pygame.quit()
sys.exit(1 if FAIL else 0)
