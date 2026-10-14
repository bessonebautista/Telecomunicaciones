"""Bucle principal del juego de hockey de aire.

Contiene la maquina de estados (menu, torneo, tienda, partido, resultado) y
la logica de partido: marcador, consumibles, guardado y recompensas.
"""

from __future__ import annotations

import math
import random

import pygame

from . import physics, render, save, tournament
from . import settings as S
from .ai import NIVELES, NIVEL_POR_RONDA, DIFICIL, Rival
from .cosmetics import (
    MESAS_POR_CLAVE, PALAS_POR_CLAVE, PUCKS_POR_CLAVE,
    TODAS_LAS_MESAS, TODAS_LAS_PALAS, TODAS_LAS_PUCKS,
)
from .items import POR_CLAVE, POR_TECLA, TODOS, ItemEnUso
from .physics import Pala, Puck
from .audio import Musica, Sounds

# Estados
MENU = "menu"
TORNEO = "torneo"
TIENDA = "tienda"
PARTIDO = "partido"
PRESENTACION = "presentacion"
RESULTADO = "resultado"
FINAL = "final"
AYUDA = "ayuda"

# Cuanto dura la pantalla "TU vs RIVAL" antes de empezar. En la final dura mas
# y es mas vistosa: es el momento clave del torneo.
PRESENTACION_TIEMPO = {0: 2.6, 1: 2.9, 2: 3.2, 3: 4.6}
PRESENTACION_TIEMPO_RAPIDO = 1.7
CELEBRACION_TIEMPO = 9.0  # celebracion de campeon: monedas y trofeo

# Velocidad maxima de la pala del jugador. El raton no necesita mas: es rapido
# de sobra y, cuanto mas rapida, mas vibracion si se calcula mal.
VMAX_PALA = 1500.0

# Potencia del tiro del jugador. No hay boton para cargarlo: se juega solo con
# el raton, asi que el tiro sale siempre con esta fuerza.
POTENCIA_TIRO = 0.60

# Dispersion del tiro, en GRADOS. 3º se nota poco y evita que el tiro sea un
# laser perfecto.
DISPERSION_TIRO = 3.0

# Suavizado del raton: que parte del movimiento nuevo se acepta en cada
# fotograma. 0.3 deja pasar el 30%: el temblor de la mano se queda muy
# atenuado y el movimiento de verdad llega casi entero.
SUAVIZADO_RATON = 0.22

# Suavizado de la velocidad de la pala, para la direccion del tiro. Con la
# zona muerta la velocidad llega a rajos; sin suavizarla, el tiro saldria
# dando tumbos.
SUAVIZADO_VELOCIDAD = 0.3

# A partir de esta velocidad (px/s) se considera que la pala se esta moviendo
# de verdad y el tiro sale en esa direccion. Por debajo, el tiro va a
# porteria. Es bajo a proposito: el raton va filtrado y la velocidad sale
# suavizada, asi que un movimiento normal queda bastante por debajo de la
# velocidad real del raton.
UMBRAL_MOVIMIENTO = 120.0

BOTON_PAL = pygame.Rect(0, 0, 260, 46)
BOTON_DER = pygame.Rect(0, 0, 190, 46)

# El escudo se coloca justo delante de la porteria, en coordenadas de rink.
ESCUDO_IZQ_X = 26.0
ESCUDO_DER_X = S.TABLE_W - 26.0

# Boton de "volver" de las pantallas de torneo y tienda.
BTN_VOLVER = pygame.Rect(30, 40, 130, 40)
# Pestanas de la tienda.
TAB_CONSUMIBLES = pygame.Rect(150, 120, 170, 36)
TAB_OBJETOS = pygame.Rect(330, 120, 170, 36)


def _btn(pos, w, h):
    r = pygame.Rect(0, 0, w, h)
    r.center = pos
    return r


class Game:
    """Juego completo de hockey de aire."""

    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((S.WINDOW_WIDTH, S.WINDOW_HEIGHT))
        pygame.display.set_caption(S.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.datos = save.load()
        self.sonido = Sounds()
        self.sonido.enabled = bool(self.datos.get("sonido", True))
        # La musica solo suena en los menus, nunca con la pelota en juego:
        # hay que poder oir el golpe de la pala y el silbato.
        self.musica = Musica()
        self.musica.habilitada = self.sonido.enabled

        # Equipamiento actual
        self.mesa_sel = "mesa_basica"
        self.pala_sel = "pala_basica"
        self.puck_sel = "puck_clasica"

        self.estado = MENU
        self.menu_idx = 0
        self.tienda_idx = 0
        self.tienda_pestana = 0  # 0=consumibles, 1=objetos
        self.ayuda_vuelta = MENU

        # Partido
        self.puck = Puck()
        self.pala_jug = Pala(-1)
        # En el juego normal la pala sigue al raton. Los tests de balance lo
        # ponen a False y mueven la pala ellos con un jugador simulado.
        self.control_por_mouse = True
        self.rival = Rival(self.datos.get("dificultad", DIFICIL))
        self.marcador = [0, 0]
        self.puntos = [0, 0]
        self.ronda = 0
        self.fase = "sacar"  # sacar, juego, punto, fin
        self.reloj = 0.0
        self.rival_nombre = ""
        self.rival_nivel = DIFICIL
        # Consumibles en uso (jugador)
        self.items_jug: dict[str, ItemEnUso] = {}
        self.items_ia: dict[str, ItemEnUso] = {}
        self.en_torneo = False
        self.ronda = 0
        self.monedas_ronda = 0
        self.gane = False
        self._s_antes = False
        self.presentacion_en = 0.0
        self.presentacion_total = 1.0
        self.rival_lema = ""
        self.rival_color = S.C_P2
        self.rival_emblema = "rayo"
        self.monedas_celebracion = 0
        # Direccion en la que sale el tiro (vector unitario). La calcula el juego a
        # partir de hacia donde mueves la pala.
        self.aim_dir = pygame.Vector2(1.0, 0.0)
        # Raton filtrado por la zona muerta: es la posicion real a la que
        # apunta la pala, sin el temblor de la mano.
        self.raton_filtrado = pygame.Vector2(S.TABLE_W * 0.22, S.RINK_CENTER_Y)
        # Velocidad de la pala suavizada: de aqui sale la direccion del tiro.
        self.vel_pala = pygame.Vector2(0, 0)
        self.gol_destello = 0.0
        self.gol_lado = 0
        self.mensaje = ""
        self.mensaje_timer = 0.0
        self.sacar_para = 1
        self.sacar_en = 0.0
        # Estadisticas del partido
        self.gol_facil = 0
        self.uso_items = 0
        # Para la prevision del mouse
        self.ultimo_toque = 0.0

    # --- Atajos ------------------------------------------------------------
    def tocar(self, sonido: str) -> None:
        self.sonido.play(sonido)

    def mostrar(self, texto: str, segundos: float = 1.4) -> None:
        self.mensaje = texto
        self.mensaje_timer = segundos

    # --- Datos / guardado --------------------------------------------------
    def monedas(self) -> int:
        return int(self.datos.get("monedas", 0))

    def gastar(self, cantidad: int) -> bool:
        if self.monedas() < cantidad:
            return False
        self.datos["monedas"] = self.monedas() - cantidad
        save.save(self.datos)
        return True

    def sumar_monedas(self, cantidad: int) -> None:
        if cantidad <= 0:
            return
        self.datos["monedas"] = self.monedas() + cantidad
        save.save(self.datos)

    def tiene(self, clave: str) -> bool:
        return clave in self.datos.get("objetos", [])

    def obtener(self, clave: str) -> None:
        if not self.tiene(clave):
            self.datos.setdefault("objetos", []).append(clave)
            save.save(self.datos)

    # --- Entrada -----------------------------------------------------------
    def eventos(self) -> None:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                self.tecla(ev.key)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Usamos la posicion del propio clic, no la del raton "actual":
                # asi el boton que se pulsa es siempre el que se ha pulsado.
                self.click(ev.pos)

    def tecla(self, key: int) -> None:
        # El ESPACIO no hace nada en todo el juego: se juega solo con el
        # raton. No esta en ninguna de las listas de teclas de abajo.
        if self.estado == FINAL:
            if key in (
                pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE
            ) and self.presentacion_en < CELEBRACION_TIEMPO - 2.2:
                self.estado = MENU
                self.monedas_celebracion = 0
            return
        if self.estado == PRESENTACION:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                self.saltar_presentacion()
            return
        if self.estado == PARTIDO:
            if key == pygame.K_ESCAPE:
                self.estado = MENU
                self.tocar("clic")
            elif key == pygame.K_r:
                self.reiniciar_partido()
            else:
                self.usar_item(key)
        elif self.estado == AYUDA:
            if key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.estado = self.ayuda_vuelta
        elif self.estado == MENU:
            # Navegacion con teclado, por si se juega sin raton.
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_idx = (self.menu_idx - 1) % len(self.botones_menu())
                self.tocar("clic")
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_idx = (self.menu_idx + 1) % len(self.botones_menu())
                self.tocar("clic")
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.click(self.botones_menu()[self.menu_idx][0].center)

    def click(self, pos) -> None:
        if self.estado == MENU:
            self._click_menu(pos)
        elif self.estado == TORNEO:
            self._click_torneo(pos)
        elif self.estado == TIENDA:
            self._click_tienda(pos)
        elif self.estado == PRESENTACION:
            # Un clic o ENTER salta la presentacion y se empieza ya.
            self.saltar_presentacion()
        elif self.estado == RESULTADO:
            self.estado = TORNEO if self.en_torneo else MENU
            self.tocar("clic")
        elif self.estado == FINAL:
            # La celebracion se puede saltar cuando ya has visto el trofeo.
            if self.presentacion_en < CELEBRACION_TIEMPO - 2.2:
                self.estado = MENU
                self.monedas_celebracion = 0
            self.tocar("clic")
        elif self.estado == AYUDA:
            self.estado = self.ayuda_vuelta

    # --- Menu --------------------------------------------------------------
    def botones_menu(self) -> list[tuple[pygame.Rect, str, object]]:
        cx = S.WINDOW_WIDTH // 2
        return [
            (_btn((cx, 340), 280, 50), "PARTIDO RÁPIDO", "rapido"),
            (_btn((cx, 400), 280, 50), "MODO TORNEO", "torneo"),
            (_btn((cx, 460), 280, 50), "TIENDA", "tienda"),
            (_btn((cx, 520), 280, 44), "AYUDA (cómo jugar)", "ayuda"),
        ]

    def _click_menu(self, pos) -> None:
        for rect, _, accion in self.botones_menu():
            if rect.collidepoint(pos):
                self.tocar("clic")
                if accion == "rapido":
                    self.estado = PARTIDO
                    self.preparar_partido("Rival", DIFICIL, torneo=False)
                elif accion == "torneo":
                    self.estado = TORNEO
                elif accion == "tienda":
                    self.estado = TIENDA
                    self.tienda_idx = 0
                elif accion == "ayuda":
                    self.ayuda_vuelta = MENU
                    self.estado = AYUDA
                return

    # --- Torneo ------------------------------------------------------------
    def rect_jugar(self) -> pygame.Rect:
        return _btn((S.WINDOW_WIDTH // 2, 560), 240, 46)

    def _click_torneo(self, pos) -> None:
        if self.rect_jugar().collidepoint(pos):
            self.tocar("clic")
            self._empezar_ronda()
            return
        if BTN_VOLVER.collidepoint(pos):
            self.estado = MENU
            self.tocar("clic")
            self.tocar("clic")

    # --- Tienda ------------------------------------------------------------
    def rect_item(self, i: int) -> pygame.Rect:
        # Seis tarjetas en columna. El paso (92) y el alto (84) estan elegidos
        # para que la sexta, la de Gigante, termine antes del borde de abajo.
        return pygame.Rect(70, 182 + i * 92, 600, 84)

    def _click_tienda(self, pos) -> None:
        if BTN_VOLVER.collidepoint(pos):
            self.estado = MENU
            self.tocar("clic")
            return
        if TAB_CONSUMIBLES.collidepoint(pos):
            self.tienda_pestana = 0
            self.tocar("clic")
            return
        if TAB_OBJETOS.collidepoint(pos):
            self.tienda_pestana = 1
            self.tocar("clic")
            return
        if self.tienda_pestana == 0:
            for i, item in enumerate(TODOS):
                if self.rect_item(i).collidepoint(pos):
                    self.comprar_item(item)
                    return
        else:
            for i, obj in enumerate(self.objetos_tienda()):
                if self.rect_objeto(i).collidepoint(pos):
                    self.comprar_objeto(obj)
                    return

    def objetos_tienda(self) -> list[tuple[str, str, int, str]]:
        """(tipo, clave, precio, nombre) para la pestana de objetos."""
        lista = []
        for m in TODAS_LAS_MESAS:
            lista.append(("mesa", m.key, 0 if m.solo_ganando else m.precio, m.name))
        for p in TODAS_LAS_PALAS:
            lista.append(("pala", p.key, 0 if p.solo_ganando else p.precio, p.name))
        for p in TODAS_LAS_PUCKS:
            lista.append(("puck", p.key, 0 if p.solo_ganando else p.precio, p.name))
        return lista

    def rect_objeto(self, i: int) -> pygame.Rect:
        # Cinco columnas: 13 objetos salen en 3 filas y caben sin salirse.
        return pygame.Rect(30 + (i % 5) * 205, 200 + (i // 5) * 172, 190, 158)

    def comprar_item(self, item) -> None:
        """Compra una unidad. Cada compra sirve para un solo uso."""
        if self.monedas() < item.precio:
            self.mostrar("No te llegan las monedas", 1.2)
            self.tocar("derrota")
            return
        self.gastar(item.precio)
        self.datos.setdefault("items_comprados", []).append(item.key)
        save.save(self.datos)
        self.mostrar(f"{item.name} comprado (un solo uso)", 1.4)
        self.tocar("moneda")

    def comprar_objeto(self, obj) -> None:
        tipo, clave, precio, _ = obj
        if self.tiene(clave):
            # Equipar
            if tipo == "mesa":
                self.mesa_sel = clave
            elif tipo == "pala":
                self.pala_sel = clave
            elif tipo == "puck":
                self.puck_sel = clave
            self.mostrar("Equipado. Lo usarás en el próximo partido.", 1.2)
            self.tocar("clic")
            return
        if precio <= 0:
            self.mostrar("Solo se consigue ganando el torneo", 1.6)
            self.tocar("derrota")
            return
        if self.monedas() < precio:
            self.mostrar("No te llegan las monedas", 1.2)
            self.tocar("derrota")
            return
        self.gastar(precio)
        self.obtener(clave)
        # equipar lo recien comprado
        if tipo == "mesa":
            self.mesa_sel = clave
        elif tipo == "pala":
            self.pala_sel = clave
        elif tipo == "puck":
            self.puck_sel = clave
        self.mostrar("Comprado y equipado. Listo para el próximo partido.", 1.6)
        self.tocar("moneda")

    def usar_item(self, key: int) -> None:
        """Usa un consumible. Cada compra se gasta UNA vez.

        Al pulsarlo se consume del inventario: cuando se acaba el tiempo, hay
        que volver a comprarlo. Asi un consumible no dura toda la partida ni se
        puede reactivar en bucle.
        """
        item = None
        for cand in TODOS:
            if pygame.key.key_code(cand.hotkey) == key:
                item = cand
                break
        if item is None:
            return
        if self.fase != "juego":
            self.mostrar("Los consumibles solo se usan con la pelota en juego", 1.4)
            return
        if not self.tiene_item(item):
            self.mostrar(f"Te has quedado sin {item.name}. Vuelve a comprarlo "
                         f"({item.precio} monedas)", 1.6)
            self.tocar("derrota")
            return
        estado = self.items_jug.get(item.key)
        if estado is not None and estado.activo:
            self.mostrar(f"{item.name} ya está activo", 1.0)
            return  # ya esta activo
        # En un mismo partido cada consumible se usa UNA vez, aunque tengas
        # mas unidades compradas. Hay que volver a comprar para otro uso.
        if estado is not None and estado.usado:
            self.mostrar(f"Ya has usado {item.name} en este partido. "
                         f"Cómpralo otra vez para volver a usarlo", 1.8)
            self.tocar("derrota")
            return
        # Se consume aqui: una compra, un uso.
        self.consumir_item(item)
        estado = self.items_jug.get(item.key) or ItemEnUso(item)
        estado.activar()
        self.items_jug[item.key] = estado
        self.uso_items += 1
        self.mostrar(f"¡{item.name} activado!", 1.0)
        self.tocar("item")

    def tiene_item(self, item) -> bool:
        """Queda alguna unidad sin usar en el inventario."""
        return item.key in self.datos.setdefault("items_comprados", [])

    def consumir_item(self, item) -> None:
        """Gasta una unidad del consumible. Si era la ultima, desaparece."""
        lista = self.datos.setdefault("items_comprados", [])
        if item.key in lista:
            lista.remove(item.key)
            save.save(self.datos)

    def reiniciar_partido(self) -> None:
        self.marcador = [0, 0]
        self.puntos = [0, 0]
        self.fase = "sacar"
        self.sacar_en = S.SERVE_DELAY
        self.sacar_para = 1
        self.puck = Puck()
        self.pala_jug.reiniciar()
        self.rival.reiniciar()
        for it in self.items_jug.values():
            it.poses = False
            it.tiempo = 0
        self.items_ia = {}
        self.reencajar_raton()
        self.mostrar("Partido reiniciado. Marcador a 0.", 1.4)

    def reencajar_raton(self) -> None:
        """Coloca el filtro del raton donde esta el raton de verdad.

        Sin esto, al empezar un partido la pala sale disparada desde su
        posicion de inicio hasta el raton, y esa velocidad falsea la
        direccion del tiro durante los primeros fotogramas.
        """
        if not self.control_por_mouse:
            return
        try:
            mx, my = pygame.mouse.get_pos()
        except pygame.error:
            return
        x = max(S.PUCK_R, min(S.TABLE_W / 2 - self.pala_jug.radio, mx - S.TABLE_X))
        y = max(self.pala_jug.radio, min(S.TABLE_H - self.pala_jug.radio, my - S.TABLE_Y))
        self.raton_filtrado = pygame.Vector2(x, y)
        self.vel_pala = pygame.Vector2(0, 0)

    # --- Partido -----------------------------------------------------------
    def preparar_partido(
        self, nombre_rival: str, nivel: str, torneo: bool, presentacion: bool = True
    ) -> None:
        self.rival_nombre = nombre_rival
        self.rival_nivel = nivel
        self.rival = Rival(nivel)
        self.marcador = [0, 0]
        self.puntos = [0, 0]
        self.gol_facil = 0
        self.uso_items = 0
        self.puck = Puck()
        self.pala_jug = Pala(-1)
        # En el juego normal la pala sigue al raton. Los tests de balance lo
        # ponen a False y mueven la pala ellos con un jugador simulado.
        self.control_por_mouse = True
        self.items_jug = {}
        self.items_ia = {}
        self.en_torneo = torneo
        self.fase = "sacar"
        self.sacar_en = S.SERVE_DELAY
        self.sacar_para = 1
        if presentacion:
            self.estado = PRESENTACION
            base = PRESENTACION_TIEMPO.get(self.ronda, 2.8)
            if not torneo:
                base = PRESENTACION_TIEMPO_RAPIDO
            self.presentacion_en = base
            self.presentacion_total = base
        else:
            self.estado = PARTIDO
        self.reencajar_raton()

    def _empezar_ronda(self) -> None:
        """Arranca la ronda actual con los datos de su rival."""
        nombre, nivel, lema, color, emblema = tournament.rival_de(self.ronda)
        self.rival_lema = lema
        self.rival_color = color
        self.rival_emblema = emblema
        self.preparar_partido(nombre, nivel, torneo=True)

    def saltar_presentacion(self) -> None:
        """Clic o ENTER empieza el partido antes de tiempo."""
        if self.estado == PRESENTACION:
            self.presentacion_en = 0.0
            self.estado = PARTIDO
            self.tocar("silbato")

    def usar_item_ia(self) -> None:
        """La IA usa consumibles de vez en cuando si los tiene."""
        # La IA no compra: usa un rotulo de vez en cuando.
        if self.marcador[0] >= 3 and self.marcador[1] < 3 and random.random() < 0.006:
            self.mostrar(f"{self.rival_nombre} acaba de usar {it_name}", 1.4)
            self.tocar("item")

    # --- Estado del partido ------------------------------------------------
    def item_activo(self, d: dict, key: str) -> ItemEnUso | None:
        it = d.get(key)
        return it if it and it.activo else None

    def multiplicador_musculos(self, lado: int) -> int:
        it = self.items_jug.get("musculos") if lado == 0 else self.items_ia.get("musculos")
        return 2 if it and it.activo else 1

    def fuerza_monstruo(self) -> float:
        it = self.items_jug.get("monstruo")
        return 1.45 if it and it.activo else 1.0

    def fuerza_rafaga(self) -> float:
        it = self.items_jug.get("rafaga")
        return 1.6 if it and it.activo else 1.0

    def fuerza_gigante(self) -> float:
        """El poder de Gigante: mas tamano y algo mas de potencia al pegar."""
        it = self.items_jug.get("gigante")
        return 1.25 if it and it.activo else 1.0

    def aplicar_tamanos(self) -> None:
        """Aplica (o quita) el tamano de Gigante a las dos palas."""
        extra = S.PADDLE_R * 0.75 if self.items_jug.get("gigante") and self.items_jug["gigante"].activo else 0.0
        self.pala_jug.radio_extra = extra
        self.pala_jug.radio = self.pala_jug.radio_base + extra
        # El rival no tiene Gigante aqui, asi que su pala se queda normal.
        self.rival.pala.radio_extra = 0.0
        self.rival.pala.radio = self.rival.pala.radio_base

    def escudo_poses(self, lado: int) -> ItemEnUso | None:
        it = self.items_jug.get("escudo") if lado == 0 else self.items_ia.get("escudo")
        if it and it.activo and it.gol_protegido < 2:
            return it
        return None

    def hielo_en(self, lado: int) -> float:
        it = self.items_ia.get("hielo") if lado == 0 else self.items_jug.get("hielo")
        return it.fraccion if it and it.activo else 0.0

    def calcular_aim_dir(self, velocidad: pygame.Vector2) -> pygame.Vector2:
        """Hacia donde sale el puck cuando la golpeas, en vector unitario.

        Se juega solo con el raton, asi que el raton solo puede mover la pala.
        Por eso el tiro sale hacia donde MUEVES la pala, como si le dieras con
        el palo: arrastras hacia donde quieres mandar la puck.

        Antes la mira era la posicion del raton, que es justo donde esta la
        pala. El vector de salida daba cero, el codigo caia al punto de
        contacto y la puck salia en la direccion que tocara: para cualquier
        lado.

        Si estas quieto no hay direccion que leer, asi que se va a porteria por
        el lado contrario al que estas, para que un tiro parado no salga
        siempre de frente.
        """
        v = pygame.Vector2(velocidad)
        if v.length() > UMBRAL_MOVIMIENTO:
            return v / v.length()
        lado = 1.0 if self.pala_jug.pos.y <= S.RINK_CENTER_Y else -1.0
        return pygame.Vector2(1.0, lado * 0.45).normalize()


    def actualizar_partido(self, dt: float) -> None:
        self.reloj += dt
        # El tamano de Gigante se actualiza cada fotograma.
        self.aplicar_tamanos()
        # Mouse -> pala del jugador.
        # En los tests esto se apaga y manda el jugador simulado.
        if self.control_por_mouse:
            mx, my = pygame.mouse.get_pos()
            cruda = pygame.Vector2(mx - S.TABLE_X, my - S.TABLE_Y)
            # La pala se queda en su mitad.
            cruda.x = max(S.PUCK_R, min(S.TABLE_W / 2 - self.pala_jug.radio, cruda.x))
            cruda.y = max(self.pala_jug.radio, min(S.TABLE_H - self.pala_jug.radio, cruda.y))
            # Filtro del raton. Cada fotograma el raton nuevo solo pesa una
            # parte, asi que el temblor de la mano queda muy atenuado. El
            # movimiento de verdad llega casi entero: el retardo son unos
            # pocos pixels, que no se notan.
            #
            # Antes la pala se pegaba al raton pixel a pixel y por eso
            # seguia el temblor. Ahora ``mover_hacia`` tiene zona muerta y no
            # se mueve por debajo de ella, que es lo que termina de quitar el
            # tembleque.
            self.raton_filtrado += (cruda - self.raton_filtrado) * SUAVIZADO_RATON
            # Si el filtro se ha quedado muy lejos (al empezar la partida, o
            # si el raton salta de golpe), se pega de una vez. Si no, la pala
            # sale disparada hacia el raton y esa velocidad falsea por
            # completo la direccion del tiro.
            if (self.raton_filtrado - cruda).length() > 250.0:
                self.raton_filtrado = cruda.copy()
            # La velocidad de la pala se guarda suavizada: la zona muerta
            # hace que sea a rajos, y la direccion del tiro sale de ahi.
            self.vel_pala += (self.pala_jug.vel - self.vel_pala) * SUAVIZADO_VELOCIDAD
            # OJO: ``mover_hacia`` ya mueve la pala. No hay que llamar a
            # ``mover`` despues: si se hace, avanza dos pasos por fotograma,
            # se pasa de largo y al siguiente tiene que corregir. Eso tambien
            # era tembleque.
            self.pala_jug.mover_hacia(self.raton_filtrado, dt, VMAX_PALA)
        else:
            self.pala_jug.vel = pygame.Vector2(0, 0)

        # Consumibles: reloj
        for d in (self.items_jug, self.items_ia):
            for it in list(d.values()):
                if it.update(dt):
                    self.mostrar(f"{it.item.name} se acaba", 1.0)

        if self.fase == "sacar":
            self.sacar_en -= dt
            if self.sacar_en <= 0.0:
                self.puck.sacar(self.sacar_para)
                self.fase = "juego"
            return

        if self.fase != "juego":
            return

        # --- IA ---
        # El hielo le resta agarre; la IA ya golpea y remata por su cuenta.
        muleta = 1.0 - 0.45 * self.hielo_en(1)
        if self.rival.actualizar(
            dt, self.puck, muleta, pala_jug_y=self.pala_jug.pos.y
        ):
            self.tocar("pala")
            self.ultimo_toque = 1.0

        # --- Pala del jugador golpea la puck ---
        # Un solo golpe dirigido: comprueba el alcance, aparta la puck y le
        # da la velocidad hacia donde mandamos. La direccion la decide
        # ``calcular_aim_dir``.
        self.aim_dir = self.calcular_aim_dir(self.vel_pala)

        base = (
            S.PUCK_MAX_SPEED
            * POTENCIA_TIRO
            * self.fuerza_rafaga()
            * self.fuerza_monstruo()
            * self.fuerza_gigante()
        )
        # Dispersion pequena sobre la direccion. Se aplica girando un poco el
        # tiro, no moviendo el punto: asi el error siempre es un angulo
        # pequeno, por lejos que pegues.
        #
        # OJO: ``rotate`` ya trabaja en GRADOS. Si aqui se multiplica otra
        # vez por los grados por radian se va a +-170 grados y el tiro sale
        # para cualquier lado: eso fue un bug real.
        desvio = self.aim_dir.rotate(
            random.uniform(-DISPERSION_TIRO, DISPERSION_TIRO)
        )
        objetivo = self.pala_jug.pos + desvio * 400.0
        if physics.golpe_dirigido(self.puck, self.pala_jug, objetivo, base):
            # Nunca hacia tu propia porteria: la puck sale al campo rival.
            if self.puck.vel.x < 60.0:
                self.puck.vel.x = abs(self.puck.vel.x) * 0.5 + 200.0
            self.puck.limitar()
            self.tocar("pala")
            self.ultimo_toque = 0.0

        # --- Escudo del jugador bloquea la entrada ---
        esc = self.escudo_poses(0)
        if esc is not None:
            # Justo delante de su porteria izquierda.
            if physics.choque_escudo(self.puck, ESCUDO_IZQ_X, 16, S.GOAL_W + 20):
                esc.gol_protegido += 1
                self.puck.vel.x = abs(self.puck.vel.x) * 0.9
                self.tocar("pared")
                if esc.gol_protegido >= 2:
                    self.mostrar("¡Se ha roto tu escudo!", 1.2)
                    esc.poses = False

        # --- Escudo rival bloquea la salida ---
        esc2 = self.escudo_poses(1)
        if esc2 is not None:
            if physics.choque_escudo(self.puck, ESCUDO_DER_X, 16, S.GOAL_W + 20):
                esc2.gol_protegido += 1
                self.puck.vel.x = -abs(self.puck.vel.x) * 0.9
                self.tocar("pared")
                if esc2.gol_protegido >= 2:
                    self.mostrar(f"¡Escudo del rival roto: {self.rival_nombre} queda desprotegido!", 1.8)
                    esc2.poses = False

        # --- Mover puck ---
        physics.friccion_mesa(self.puck, dt)
        evento = physics.actualizar(self.puck, dt)
        if evento == "pared":
            self.tocar("pared")

        # --- Gol ---
        if evento == "gol":
            self.registrar_gol()

    def registrar_gol(self) -> None:
        """Suma un gol al marcador de quien lo ha marcado.

        El multiplicador de Musculos se aplica aqui, al marcador de verdad, no
        a un contador aparte que luego no se usaba (por eso antes no contaba).
        """
        if self.puck.pos.x <= 0.0:
            # Ha entrado en tu porteria: gol del rival.
            lados = [0, 1]
        else:
            lados = [1, 0]
        # Solo aplicamos Musculos a los puntos que gana el jugador: es su
        # consumible y multiplica SUS goles.
        self.gol_lado = 1 if self.puck.pos.x <= 0.0 else -1
        quien = 0 if self.gol_lado < 0 else 1
        extra = self.multiplicador_musculos(quien)
        self.marcador[quien] += extra
        self.puntos[quien] += extra
        if quien == 0:
            self.tocar("gol")
            if extra > 1:
                self.mostrar("¡Gol doble por Músculos!", 1.4)
        else:
            self.tocar("gol_enemigo")
        self.gol_destello = 1.0
        self.fase = "punto"
        self.sacar_en = S.POINT_PAUSE
        # Quien acaba de recibir, saca: si te han marcado, sacas tu.
        self.sacar_para = 1 if self.gol_lado < 0 else -1

    # --- Bucle -------------------------------------------------------------
    def _ajustar_musica(self) -> None:
        """Enciende o apaga la musica segun en que pantalla estamos.

        Suena en los menus y en las pantallas de texto (torneo, tienda,
        ayuda, presentacion y celebracion). Se para en cuanto empieza el
        partido, para que se oiga la pala, el silbato y el gol.
        """
        if not self.musica.disponible:
            return
        if self.estado in (PARTIDO, RESULTADO):
            self.musica.parar()
        elif self.sonido.enabled:
            self.musica.tocar()
        else:
            self.musica.parar()

    def update(self, dt: float) -> None:
        self.eventos()
        dt = min(dt, 1.0 / 30.0)

        # La tecla de sonido funciona en cualquier pantalla.
        s_pulsada = pygame.key.get_pressed()[pygame.K_s]
        if s_pulsada and not self._s_antes:
            self.sonido.enabled = not self.sonido.enabled
            self.musica.habilitada = self.sonido.enabled
            self.datos["sonido"] = self.sonido.enabled
            save.save(self.datos)
            self.mostrar(
                "Sonido activado" if self.sonido.enabled else "Sonido silenciado", 1.2
            )
        self._s_antes = s_pulsada

        self._ajustar_musica()

        if self.mensaje_timer > 0:
            self.mensaje_timer = max(0.0, self.mensaje_timer - dt)

        if self.estado == FINAL:
            # La celebracion se acaba sola o si pulsas.
            self.presentacion_en -= dt
            if self.presentacion_en <= 0.0:
                self.estado = MENU
                self.monedas_celebracion = 0

        if self.estado == PRESENTACION:
            self.presentacion_en -= dt
            if self.presentacion_en <= 0.0:
                self.estado = PARTIDO
                self.tocar("silbato")

        if self.estado == PARTIDO:
            self.actualizar_partido(dt)
            self.gol_destello = max(0.0, self.gol_destello - dt * 1.4)
            if self.fase == "punto":
                self.sacar_en -= dt
                if self.marcador[0] >= S.GOALS_TO_WIN or self.marcador[1] >= S.GOALS_TO_WIN:
                    self.fin_partido()
                elif self.sacar_en <= 0.0:
                    self.puck = Puck()
                    self.pala_jug.reiniciar()
                    self.rival.reiniciar()
                    self.fase = "sacar"
                    self.sacar_en = S.SERVE_DELAY

    def fin_partido(self) -> None:
        """Cierra el partido: estadisticas, monedas y avance del torneo."""
        gane = self.marcador[0] > self.marcador[1]
        self.gane = gane
        if gane:
            self.datos["partidos_ganados"] = self.datos.get("partidos_ganados", 0) + 1
            self.datos["mejor_racha"] = self.datos.get("mejor_racha", 0) + 1
        else:
            self.datos["partidos_perdidos"] = self.datos.get("partidos_perdidos", 0) + 1
            self.datos["mejor_racha"] = 0

        self.monedas_ronda = 0
        if self.en_torneo:
            self.monedas_ronda = tournament.total_ganado(self.ronda, gane)
            self.sumar_monedas(self.monedas_ronda)
            if self.ronda > self.datos.get("torneo_ronda", 0):
                self.datos["torneo_ronda"] = self.ronda
            if gane:
                self.ronda += 1
                if self.ronda >= len(tournament.RONDAS):
                    # Campeon: se desbloquea lo mejor.
                    self.datos["torneo_ganado"] = True
                    for clave in ("mesa_suprema", "pala_canela", "puck_canela"):
                        self.obtener(clave)
                    self.mesa_sel = "mesa_suprema"
                    self.pala_sel = "pala_canela"
                    self.puck_sel = "puck_canela"
                    self.tocar("campeon")
                    # La celebracion dura 9 s (o hasta que pulses algo).
                    self.estado = FINAL
                    self.presentacion_en = CELEBRACION_TIEMPO
                    self.presentacion_total = CELEBRACION_TIEMPO
                    self.monedas_celebracion = 40
                    save.save(self.datos)
                    return

        self.estado = RESULTADO
        self.tocar("campeon" if gane else "derrota")
        save.save(self.datos)

    def draw(self) -> None:
        if self.estado == MENU:
            self.draw_menu()
        elif self.estado == AYUDA:
            self.draw_ayuda()
        elif self.estado == TORNEO:
            self.draw_torneo()
        elif self.estado == TIENDA:
            self.draw_tienda()
        elif self.estado == PRESENTACION:
            self.draw_presentacion()
        elif self.estado == PARTIDO:
            self.draw_partido()
        elif self.estado == RESULTADO:
            self.draw_partido()
            self.draw_resultado()
        elif self.estado == FINAL:
            self.draw_partido()
            self.draw_final()

    # --- Dibujos de pantalla ----------------------------------------------
    def draw_presentacion(self) -> None:
        """Pantalla "TU vs RIVAL" antes de cada partido de torneo.

        Cuanto mas advanced la ronda, mas imponente: la final tiene su propio
        tratamiento dorado y dura mas.
        """
        r = render
        ronda = min(self.ronda, len(tournament.RONDAS) - 1)
        nombre_ronda = tournament.RONDAS[ronda]
        es_final = ronda == len(tournament.RONDAS) - 1
        # Progreso de la barra: 0 al empezar, 1 al terminar.
        transcurrido = 1.0 - max(0.0, self.presentacion_en) / max(
            0.001, self.presentacion_total
        )
        t = min(1.0, max(0.0, transcurrido))
        w, h = S.WINDOW_WIDTH, S.WINDOW_HEIGHT
        cx = w // 2

        # --- Fondo ---
        for i in range(h):
            k = i / max(1, h - 1)
            if es_final:
                col = (
                    int(40 + 60 * k),
                    int(20 + 20 * k),
                    int(70 + 40 * k),
                )
            else:
                col = (
                    int(10 + 26 * k),
                    int(14 + 30 * k),
                    int(28 + 40 * k),
                )
            pygame.draw.line(self.screen, col, (0, i), (w, i))

        # --- Rayos de fondo en la final ---
        if es_final:
            for a in range(24):
                ang = a * 0.2618 + self.reloj * 0.25
                largo = 700
                x2 = cx + int(math.cos(ang) * largo)
                y2 = h // 2 + int(math.sin(ang) * largo)
                pygame.draw.line(
                    self.screen, (86, 62, 150), (cx, h // 2), (x2, y2), 2
                )

        # --- Titulo de ronda ---
        color_ronda = S.C_GOLD if es_final else S.C_ACCENT
        r.text(
            self.screen,
            nombre_ronda.upper() + " DE FINAL",
            (cx, 92),
            22,
            color_ronda,
            True,
            center=True,
        )
        if es_final:
            r.text(
                self.screen,
                "EL ÚLTIMO RIVAL",
                (cx, 120),
                14,
                S.C_GOLD,
                True,
                center=True,
            )

        # --- VS con拳 de impacto ---
        aparicion = min(1.0, t * 2.6)
        escala = 0.55 + 0.45 * min(1.0, t * 3.4)
        v_y = 320
        color_rival = self.rival_color
        # Aura roja/dorada detras del VS, como un impacto.
        tam = int(160 * escala * aparicion)
        if tam > 8:
            # Destello radial
            dest = pygame.Surface((tam * 3, tam * 2), pygame.SRCALPHA)
            for k in range(6, 0, -1):
                rad = int(tam * (0.7 + k * 0.16))
                a = int(20 * aparicion)
                pygame.draw.circle(
                    dest, (*color_rival, a),
                    (dest.get_width() // 2, dest.get_height() // 2), rad, 4,
                )
            self.screen.blit(
                dest, (cx - dest.get_width() // 2, v_y - dest.get_height() // 2)
            )
            # Lineas de choque a los lados del VS
            for lado in (-1, 1):
                for i in range(4):
                    off_l = 96 + i * 26
                    largo = 60 - i * 12
                    x0 = cx + lado * off_l
                    pygame.draw.line(
                        self.screen, color_rival,
                        (x0, v_y - largo), (x0, v_y + largo),
                        max(1, 4 - i),
                    )
            r.outline(
                self.screen, "VS", (cx, v_y), tam,
                S.C_DANGER if not es_final else S.C_GOLD,
            )

        # --- Nombres, que entran desde los lados ---
        off = int((1.0 - min(1.0, t * 2.0)) * 340)
        r.outline(self.screen, "TU", (cx - 250 - off, v_y), 48, S.C_P1)
        r.outline(self.screen, self.rival_nombre, (cx + 250 + off, v_y), 48, color_rival)

        # Emblema grande del rival, a la derecha del nombre.
        ex = cx + 250 + off + 130
        if off < 300:
            r.emblema(self.screen, self.rival_emblema, (ex, v_y), 34, color_rival)

        # --- Lema del rival, bajo su nombre ---
        if self.rival_lema and off < 200:
            r.text(
                self.screen, f"«{self.rival_lema}»",
                (cx + 250, v_y + 46), 17, color_rival, True, center=True,
            )

        # --- Nivel del rival ---
        y_niv = v_y + 76
        color_niv = S.C_TEXT_DIM
        if self.rival_nivel in ("Experto", "Imposible"):
            color_niv = S.C_GOLD if es_final else S.C_ACCENT
        if off < 200:
            r.text(
                self.screen, f"NIVEL {self.rival_nivel.upper()}",
                (cx, y_niv), 22, color_niv, True, center=True,
            )
            if self.rival_nivel == "Imposible":
                r.text(
                    self.screen, "CASI NO FALLA",
                    (cx, y_niv + 28), 14, S.C_GOLD, True, center=True,
                )

        # --- Barra de cuenta atrás (cuanto falta para el siguiente rival) ---
        bx, by, bw, bh = cx - 200, h - 120, 400, 12
        pygame.draw.rect(self.screen, (26, 30, 46), (bx, by, bw, bh), border_radius=6)
        relleno = int(bw * t)
        if relleno > 0:
            col = S.C_GOLD if es_final else S.C_ACCENT
            pygame.draw.rect(
                self.screen, col, (bx, by, relleno, bh), border_radius=6
            )
        pygame.draw.rect(
            self.screen, S.C_BORDER, (bx, by, bw, bh), 2, border_radius=6
        )

        # --- Recordatorio del torneo ---
        r.text(
            self.screen,
            f"Ronda {ronda + 1} de {len(tournament.RONDAS)}",
            (cx, h - 150),
            15,
            S.C_TEXT_DIM,
            center=True,
        )
        r.text(
            self.screen,
            f"Haz clic para empezar ya",
            (cx, h - 74),
            14,
            S.C_TEXT_DIM,
            center=True,
        )

    def draw_menu(self) -> None:
        r = render
        r.fondo(self.screen)
        r.outline(self.screen, "HOCKEY DE AIRE", (S.WINDOW_WIDTH // 2, 120), 54, S.C_ACCENT)
        r.text(self.screen, "Vista desde arriba. 5 puntos, consumibles y torneo.",
               (S.WINDOW_WIDTH // 2, 168), 18, S.C_TEXT_DIM, center=True)
        r.text(self.screen, f"{self.monedas()} monedas", (S.WINDOW_WIDTH // 2, 216), 22, S.C_GOLD, True, center=True)
        pos = pygame.mouse.get_pos()
        for rect, label, _ in self.botones_menu():
            r.boton(self.screen, rect, label, rect.collidepoint(pos))
        g = self.datos.get("partidos_ganados", 0)
        p = self.datos.get("partidos_perdidos", 0)
        r.text(self.screen, f"Partidos ganados: {g}   Perdidos: {p}", (S.WINDOW_WIDTH // 2, 600), 15, S.C_TEXT_DIM, center=True)
        r.text(self.screen, "Tecla S: activar o quitar el sonido", (S.WINDOW_WIDTH // 2, 636), 13, S.C_TEXT_DIM, center=True)

    def draw_ayuda(self) -> None:
        r = render
        r.fondo(self.screen)
        r.outline(self.screen, "CÓMO JUGAR", (S.WINDOW_WIDTH // 2, 90), 40, S.C_ACCENT)
        lineas = [
            "Mueve tu pala con el RATÓN. Te quedas siempre en tu mitad.",
            "No hace falta ninguna otra tecla para jugar: solo el ratón.",
            "Gana quien llegue primero a 5 puntos. No hay reloj.",
            "",
            "CÓMO VA EL TIRO: la puck sale hacia donde MUEVES la pala.",
            "Si la arrastras hacia arriba y a la derecha, el tiro va así.",
            "Si estás quieto, sale hacia la portería por el lado opuesto.",
            "Un roce también cuenta como golpe: no se te pasa de largo.",
            "",
            "teclas 1 a 6. Se compran en la TIENDA, antes del partido:",
            "  1  Monstruo - al golpear, el puck sale disparado",
            "  2  Escudo   - muro invisible en tu portería; aguanta 2 goles",
            "  3  Músculos - cada punto que marcas vale por dos",
            "  4  Ráfaga   - tu pala pega mucho más fuerte",
            "  5  Hielo    - al rival le resbala la pala y juega peor",
            "  6  Gigante  - tu pala se vuelve enorme durante un rato",
            "",
            "Cada compra sirve para UN SOLO uso. Cuando se acaba el tiempo,",
            "tienes que volver a la tienda y comprarlo otra vez.",
            "",
            "La música suena en los menús y se para al empezar el partido,",
            "para que se oiga bien la pala, el silbato y los goles.",
            "",
            "MONEDAS: en el torneo ganas más según lo lejos que llegues.",
            "Si ganas el torneo entero, te llevas el bote y desbloqueas los",
            "mejores objetos. Los demás se compran con monedas.",
            "",
            "Haz clic para volver al menú",
        ]
        y = 120
        paso = 20
        for ln in lineas:
            sangria = ln.startswith("  ")
            r.text(self.screen, ln.strip(), (S.WINDOW_WIDTH // 2, y), 14,
                   S.C_TEXT_DIM if sangria else S.C_TEXT, center=True)
            y += paso
        # Ojo: la ayuda es la pantalla con mas texto. Si anades lineas, baja
        # el paso para que no se salga por abajo de la ventana.

    def draw_torneo(self) -> None:
        r = render
        r.fondo(self.screen)
        r.boton(self.screen, BTN_VOLVER, "< MENÚ", BTN_VOLVER.collidepoint(pygame.mouse.get_pos()))
        r.text(self.screen, "MODO TORNEO", (S.WINDOW_WIDTH // 2, 66), 32, S.C_ACCENT, True, center=True)
        r.text(self.screen, f"{self.monedas()} monedas", (S.WINDOW_WIDTH - 40, 52), 20, S.C_GOLD, True, right=True)

        # bracket
        x0 = 120
        y_top = 180
        alto = 70
        for i, ronda in enumerate(tournament.RONDAS):
            y = y_top + i * 96
            won = i < self.ronda
            actual = i == self.ronda
            col = S.C_PANEL_ALT if actual else S.C_PANEL
            rect = pygame.Rect(x0 - 20, y, 470, alto)
            r.panel(self.screen, rect, color=col,
                    border=S.C_ACCENT if actual else (S.C_GOOD if won else S.C_BORDER), width=2)
            nombre, nivel, lema, color, emblema = tournament.rival_de(i)
            r.text(self.screen, ronda, (rect.x + 14, rect.y + 8), 17,
                   S.C_ACCENT if actual else S.C_TEXT, True)
            r.text(self.screen, f"contra {nombre} · {nivel}",
                   (rect.x + 14, rect.y + 34), 14, color)
            # Emblema del rival, al final de la tarjeta.
            r.emblema(self.screen, emblema, (rect.right - 30, rect.centery), 20, color)
            if won:
                r.text(self.screen, "GANADA", (rect.right - 60, rect.y + 14), 15,
                       S.C_GOOD, True, right=True)
                r.text(self.screen, f"+{tournament.total_ganado(i, True)} monedas",
                       (rect.right - 60, rect.y + 36), 12, S.C_TEXT_DIM, right=True)
            elif actual:
                r.text(self.screen, "ESTÁS AQUÍ", (rect.right - 60, rect.y + 14), 14,
                       S.C_ACCENT, True, right=True)
                r.text(self.screen, "JUGAR PARA SEGUIR",
                       (rect.right - 60, rect.y + 36), 12, S.C_TEXT_DIM, right=True)

        # recompensas
        r.text(self.screen,
               f"Si ganas el torneo: +{tournament.BOTE_CAMPEON} monedas y los mejores objetos",
               (S.WINDOW_WIDTH // 2, 620), 14, S.C_GOLD, center=True)

        pos = pygame.mouse.get_pos()
        rect = self.rect_jugar()
        r.boton(
            self.screen,
            rect,
            f"JUGAR {tournament.RONDAS[self.ronda].upper()}",
            rect.collidepoint(pos),
        )

    def draw_tienda(self) -> None:
        r = render
        r.fondo(self.screen)
        r.boton(self.screen, BTN_VOLVER, "< MENÚ", BTN_VOLVER.collidepoint(pygame.mouse.get_pos()))
        r.text(self.screen, "TIENDA", (S.WINDOW_WIDTH // 2, 66), 32, S.C_ACCENT, True, center=True)
        r.text(self.screen, f"{self.monedas()} monedas", (S.WINDOW_WIDTH - 40, 52), 20, S.C_GOLD, True, right=True)
        pos = pygame.mouse.get_pos()
        r.boton(self.screen, TAB_CONSUMIBLES, "CONSUMIBLES", TAB_CONSUMIBLES.collidepoint(pos), self.tienda_pestana == 0)
        r.boton(self.screen, TAB_OBJETOS, "OBJETOS", TAB_OBJETOS.collidepoint(pos), self.tienda_pestana == 1)
        num = f"1-{len(TODOS)}" if len(TODOS) > 1 else "1"
        r.text(self.screen,
               f"Se compran antes del partido y duran un rato. "
               f"Para usarlos, teclas {num} con la pelota en juego.",
               (S.WINDOW_WIDTH // 2, 165), 13, S.C_TEXT_DIM, center=True)

        if self.tienda_pestana == 0:
            for i, item in enumerate(TODOS):
                rect = self.rect_item(i)
                r.tarjeta_item(
                    self.screen, rect, item, self.tiene_item(item),
                    rect.collidepoint(pos), self.monedas(),
                )
        else:
            for i, obj in enumerate(self.objetos_tienda()):
                rect = self.rect_objeto(i)
                tipo, clave, precio, nombre = obj
                color = {
                    "mesa": (120, 190, 255), "pala": (255, 170, 120), "puck": (200, 200, 220)
                }[tipo]
                r.tarjeta_cosmetica(
                    self.screen, rect, nombre, color, precio,
                    self.tiene(clave), self.esta_equipado(tipo, clave),
                    rect.collidepoint(pos), tipo, clave,
                )

    def esta_equipado(self, tipo: str, clave: str) -> bool:
        if tipo == "mesa":
            return self.mesa_sel == clave
        if tipo == "pala":
            return self.pala_sel == clave
        return self.puck_sel == clave

    def draw_partido(self) -> None:
        r = render
        r.fondo(self.screen)
        mesa = MESAS_POR_CLAVE[self.mesa_sel]
        r.mesa(self.screen, mesa)

        # auras: cada consumible activo se ve sobre la pala que afecta
        px = r._px(self.pala_jug.pos.x)
        py = r._py(self.pala_jug.pos.y)
        rx = r._px(self.rival.pala.pos.x)
        ry = r._py(self.rival.pala.pos.y)
        mon = self.items_jug.get("monstruo")
        if mon and mon.activo:
            r.aura_monstruo(self.screen, px, py, mon.fraccion)
        mus = self.items_jug.get("musculos")
        if mus and mus.activo:
            r.aura_musculos(self.screen, px, py, mus.fraccion, self.reloj)
        hi = self.items_jug.get("hielo")
        if hi and hi.activo:
            r.aura_hielo_en_rival(self.screen, rx, ry, hi.fraccion)
        esc = self.escudo_poses(0)
        if esc:
            r.escudo(self.screen, esc.fraccion)

        # destello de gol
        r.porteria_destello(self.screen, mesa, self.gol_lado, self.gol_destello)

        # objetos
        r.puck(self.screen, self.puck, PUCKS_POR_CLAVE[self.puck_sel])
        r.pala(self.screen, self.pala_jug, PALAS_POR_CLAVE[self.pala_sel], self.reloj)
        r.pala(self.screen, self.rival.pala, PALAS_POR_CLAVE["pala_basica"], self.reloj)

        # marcador
        r.marcador(self.screen, self.marcador[0], self.marcador[1], S.GOALS_TO_WIN)
        # nombre rival
        r.text(self.screen, f"Rival: {self.rival_nombre}", (S.WINDOW_WIDTH - 40, 92), 15, S.C_P2, True, right=True)
        # consumibles del rival (visibles)
        barra_ia = [it for it in self.items_ia.values() if it.activo]
        r.barra_items(self.screen, barra_ia, S.WINDOW_WIDTH - 190, 120)
        # barra de items del jugador
        barra_j = [it for it in self.items_jug.values() if it.activo]
        r.barra_items(self.screen, barra_j, 20, S.WINDOW_HEIGHT - 66, hacia_arriba=True)

        # Barra de consumibles comprados, con su tecla
        for i, item in enumerate(TODOS):
            x = 16 + i * 112
            y = S.WINDOW_HEIGHT - 30
            estado = self.items_jug.get(item.key)
            activo = estado is not None and estado.activo
            en_bolsa = self.tiene_item(item)
            if activo:
                r.panel(
                    self.screen, pygame.Rect(x, y, 104, 24),
                    color=S.C_PANEL_ALT, border=item.color, radius=6, width=2,
                )
            elif en_bolsa:
                r.panel(
                    self.screen, pygame.Rect(x, y, 104, 24),
                    color=S.C_PANEL, border=item.color, radius=6, width=1,
                )
            # Tecla
            col = item.color if en_bolsa else (58, 68, 88)
            r.text(self.screen, item.hotkey, (x + 12, y + 4), 15, col, True)
            r.text(
                self.screen, item.name[:8], (x + 30, y + 5), 13,
                col if en_bolsa else S.C_TEXT_DIM,
            )

        # fase
        if self.fase == "sacar":
            quien = "TÚ" if self.sacar_para < 0 else self.rival_nombre
            r.outline(self.screen, f"SACA {quien}", (S.WINDOW_WIDTH // 2, S.TABLE_Y + 60), 30, S.C_ACCENT)
        if self.mensaje_timer > 0:
            r.outline(self.screen, self.mensaje,
                      (S.WINDOW_WIDTH // 2, S.TABLE_Y + S.TABLE_H - 30), 20, S.C_TEXT)
        # pausa
        if self.fase == "punto":
            r.text(self.screen, "Punto", (S.WINDOW_WIDTH // 2, S.TABLE_Y + 40), 30, S.C_TEXT, True, center=True)

    def draw_resultado(self) -> None:
        r = render
        gane = self.marcador[0] > self.marcador[1]
        capa = pygame.Surface((S.WINDOW_WIDTH, S.WINDOW_HEIGHT), pygame.SRCALPHA)
        capa.fill((6, 10, 18, 160))
        self.screen.blit(capa, (0, 0))
        r.outline(self.screen, "¡GANASTE!" if gane else "HAS PERDIDO",
                  (S.WINDOW_WIDTH // 2, 260), 44, S.C_GOOD if gane else S.C_DANGER)
        r.text(self.screen, f"{self.marcador[0]} - {self.marcador[1]}  contra {self.rival_nombre}",
               (S.WINDOW_WIDTH // 2, 320), 20, S.C_TEXT, center=True)
        if self.en_torneo:
            r.text(
                self.screen,
                f"Has ganado {self.monedas_ronda} monedas",
                (S.WINDOW_WIDTH // 2, 360),
                22,
                S.C_GOLD,
                True,
                center=True,
            )
            nombre = tournament.rival_de(
                min(self.ronda, len(tournament.RONDAS) - 1)
            )[0]
            r.text(
                self.screen,
                f"Siguiente rival: {nombre}" if gane else "Torneo terminado: se acabó por esta vez",
                (S.WINDOW_WIDTH // 2, 395),
                15,
                S.C_TEXT_DIM,
                center=True,
            )
        r.text(self.screen, "Haz clic para continuar",
               (S.WINDOW_WIDTH // 2, 430), 16, S.C_TEXT_DIM, center=True)

    def draw_final(self) -> None:
        """Celebracion de campeon: trofeo, felicitaciones y monedas del cielo."""
        r = render
        w, h = S.WINDOW_WIDTH, S.WINDOW_HEIGHT
        cx = w // 2
        t = min(1.0, max(0.0, 1.0 - self.presentacion_en / max(0.001, self.presentacion_total)))
        ahora = pygame.time.get_ticks() / 1000.0

        # --- Fondo oscuro con focos dorados ---
        for i in range(h):
            k = i / max(1, h - 1)
            pygame.draw.line(
                self.screen,
                (int(22 + 52 * k), int(16 + 36 * k), int(8 + 18 * k)),
                (0, i), (w, i),
            )
        focos = pygame.Surface((w, h), pygame.SRCALPHA)
        for k in range(7):
            x = cx - 360 + k * 120
            pygame.draw.polygon(
                focos, (255, 214, 120, 22),
                [(x, 0), (x + 46, 0), (x + 150, h), (x - 104, h)],
            )
        self.screen.blit(focos, (0, 0))
        # Polvo de luz alrededor del trofeo
        polvo = pygame.Surface((w, h), pygame.SRCALPHA)
        for k in range(3):
            rad = 150 + k * 70 + int(math.sin(ahora * 1.5 + k) * 8)
            pygame.draw.circle(
                polvo, (255, 206, 110, 16),
                (cx, int(h * 0.42)), rad, 3,
            )
        self.screen.blit(polvo, (0, 0))

        # --- Monedas cayendo del cielo ---
        for i in range(self.monedas_celebracion):
            fase = ahora * 0.55 + i * 0.83
            y = -40 + (fase * 90) % (h + 120)
            x = cx + math.sin(fase * 0.9 + i * 2.1) * (w * 0.44)
            self._dibujar_moneda(int(x), int(y), i)

        # --- Titulo ---
        r.outline(self.screen, "¡CAMPEÓN!", (cx, 110), 58, S.C_GOLD)
        r.text(self.screen, "Has ganado el torneo entero", (cx, 158), 20, S.C_TEXT, True, center=True)

        # --- Trofeo entrando con rebote ---
        if t > 0.1:
            p = min(1.0, (t - 0.1) / 0.34)
            rebote = abs(math.sin(p * math.pi * 1.9)) * (1.0 - p)
            r.trofeo(self.screen, (cx, int(308 - rebote * 110)), int(115 * p))

        # --- Felicitaciones y premio ---
        if t > 0.55:
            # Con contorno: si no, las monedas que caen tapan el texto.
            r.outline(
                self.screen, "Enhorabuena: has vencido al Rey Neon",
                (cx, 430), 21, S.C_GOLD, edge=(30, 20, 8),
            )
            r.outline(
                self.screen, f"Premio del campeón: {tournament.BOTE_CAMPEON} monedas",
                (cx, 464), 18, S.C_TEXT, edge=(30, 20, 8),
            )
            r.outline(
                self.screen, "Ahora puedes usar: mesa Suprema, pala Canela y puck Canela",
                (cx, 492), 14, S.C_GOLD, edge=(30, 20, 8),
            )
        if t > 0.8:
            r.text(
                self.screen, "Haz clic para volver al menú",
                (cx, h - 36), 16, S.C_TEXT, True, center=True,
            )

    def _dibujar_moneda(self, x: int, y: int, semilla: int) -> None:
        """Moneda dorada cayendo, girando sobre si misma."""
        giro = math.sin(pygame.time.get_ticks() / 90.0 + semilla)
        rx = max(2, int(11 * abs(giro)))
        r2 = 11
        pygame.draw.ellipse(
            self.screen, (168, 126, 22), (x - rx, y - r2, rx * 2, r2 * 2)
        )
        pygame.draw.ellipse(
            self.screen, S.C_GOLD, (x - rx, y - r2, rx * 2, r2 * 2), 2
        )

    # --- Principal ---------------------------------------------------------
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(S.FPS) / 1000.0
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
