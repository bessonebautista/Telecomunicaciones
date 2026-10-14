"""Dibujado del hockey de aire: mesa, palas, puck, marcador e interfaz.

La mesa se dibuja con la altura de la pista como fondo. Los esteticos solo
cambian como se ven (colores, brillos, marcas). La fisica no se toca aqui.
"""

from __future__ import annotations

import math
import random

import pygame

from . import settings as S
from .cosmetics import Mesa, Pala as SkinPala, Puck as SkinPuck
from .items import ItemEnUso
from .physics import Pala, Puck

# --- Tipografias -----------------------------------------------------------
_FCACHE: dict[tuple[int, bool], pygame.font.Font] = {}
# Fuentes por orden de preferencia. Se piden por nombre de familia y con el
# flag de negrita, que es como pygame encuentra la variante correcta (pedir
# "segoeuib" a pelo no encuentra nada y se acaba usando la fuente de pygame,
# que tiene otro aspecto).
_FAMILIAS = ("segoeui", "verdana", "tahoma", "arial", "calibri", "dejavusans")


def _font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _FCACHE:
        path = None
        for nombre in _FAMILIAS:
            path = pygame.font.match_font(nombre, bold=bold)
            if path:
                break
        _FCACHE[key] = pygame.font.Font(path, size) if path else pygame.font.Font(None, size)
    return _FCACHE[key]


def text(
    surf: pygame.Surface,
    msg: str,
    pos: tuple[int, int],
    size: int = 18,
    color: tuple = S.C_TEXT,
    bold: bool = False,
    center: bool = False,
    right: bool = False,
    alpha: int = 255,
) -> pygame.Rect:
    s = _font(size, bold).render(str(msg), True, color)
    if alpha < 255:
        s = s.copy()
        s.set_alpha(alpha)
    r = s.get_rect()
    if center:
        r.center = pos
    elif right:
        r.topright = pos
    else:
        r.topleft = pos
    surf.blit(s, r)
    return r


def outline(
    surf: pygame.Surface,
    msg: str,
    pos: tuple[int, int],
    size: int = 40,
    color: tuple = S.C_TEXT,
    edge=(0, 0, 0),
    center: bool = True,
) -> None:
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        text(surf, msg, (pos[0] + dx, pos[1] + dy), size, edge, True, center, center)
    text(surf, msg, pos, size, color, True, center, center)


def panel(
    surf: pygame.Surface,
    rect: pygame.Rect,
    color: tuple = S.C_PANEL,
    border: tuple = S.C_BORDER,
    radius: int = 10,
    alpha: int = 235,
    width: int = 2,
) -> None:
    body = pygame.Surface(rect.size, pygame.SRCALPHA)
    body.fill((*color, alpha))
    surf.blit(body, rect.topleft)
    if border:
        pygame.draw.rect(surf, border, rect, width, border_radius=radius)


# --- Fondo -----------------------------------------------------------------
def fondo(surf: pygame.Surface) -> None:
    for i in range(S.WINDOW_HEIGHT):
        t = i / max(1, S.WINDOW_HEIGHT - 1)
        col = tuple(
            int(S.C_BG_TOP[c] + (S.C_BG_BOTTOM[c] - S.C_BG_TOP[c]) * t) for c in range(3)
        )
        pygame.draw.line(surf, col, (0, i), (S.WINDOW_WIDTH, i))


# --- La mesa (arriba) ------------------------------------------------------
def _px(p: float) -> int:
    return int(p + S.TABLE_X)


def _py(p: float) -> int:
    return int(p + S.TABLE_Y)


def _patron(surf: pygame.Surface, m: Mesa, w: int, h: int) -> None:
    """El fondo decorativo de cada mesa. Solo estetica: no toca la fisica."""
    patron = m.patron
    if patron == "liso":
        return
    capa = pygame.Surface((w, h), pygame.SRCALPHA)
    ac = m.acento
    if patron == "rejilla":
        # Rejilla fina, como los divisiones de un rink de verdad.
        for gx in range(0, w + 1, 40):
            pygame.draw.line(capa, (*ac, 26), (gx, 0), (gx, h))
        for gy in range(0, h + 1, 40):
            pygame.draw.line(capa, (*ac, 26), (0, gy), (w, gy))
    elif patron == "rayas":
        # Cepillado metalico: bandas verticales alternas.
        for gx in range(0, w + 1, 14):
            a = 30 if (gx // 14) % 2 == 0 else 10
            pygame.draw.line(capa, (*ac, a), (gx, 0), (gx, h))
    elif patron == "ondas":
        # Ondas de hielo, muy suaves.
        for i, base in enumerate(range(-60, h + 60, 60)):
            pts = [(gx, base + math.sin(gx / 55.0 + i) * 11) for gx in range(0, w + 7, 7)]
            pygame.draw.lines(capa, (*ac, 40), False, pts, 3)
    elif patron == "circuito":
        # Pistas de un circuito neon: placas con pistas que van de una a otra.
        rng = random.Random(7)
        nodos: list[tuple[int, int]] = []
        for _ in range(16):
            nodos.append((rng.randrange(30, w - 110), rng.randrange(24, h - 40)))
        # Pistas
        for i, (ax, ay) in enumerate(nodos):
            bx, by = nodos[(i + 1) % len(nodos)]
            jugos = rng.randrange(3)
            puntos = [(ax, ay)]
            if jugos == 0:
                puntos.append((bx, ay))
            elif jugos == 1:
                puntos.append((ax, by))
            else:
                puntos.append(((ax + bx) // 2, ay))
                puntos.append(((ax + bx) // 2, by))
            puntos.append((bx, by))
            pygame.draw.lines(capa, (*ac, 52), False, puntos, 3)
            pygame.draw.circle(capa, (*ac, 130), (ax, ay), 4)
        # Placas
        for gx, gy in nodos[::2]:
            gw = rng.choice((40, 56, 72))
            pygame.draw.rect(capa, (*ac, 46), (gx - 8, gy - 8, gw, 20), border_radius=4)
            pygame.draw.rect(capa, (*ac, 110), (gx - 8, gy - 8, gw, 20), 2, border_radius=4)
    elif patron == "veta":
        # Vetas de oro: ondas largas y suaves, como una piedra framada.
        for i, base in enumerate(range(-40, h + 80, 70)):
            pts = []
            for gx in range(0, w + 12, 12):
                fy = base + math.sin(gx / 130.0 + i * 0.9) * 26 + math.sin(gx / 47.0 + i) * 6
                pts.append((gx, fy))
            pygame.draw.lines(capa, (*ac, 40), False, pts, 4)
    surf.blit(capa, (0, 0))


def _motas(surf: pygame.Surface, m: Mesa, w: int, h: int) -> None:
    """Motas doradas flotando, para las mesas de campeon."""
    if not m.estrellas:
        return
    capa = pygame.Surface((w, h), pygame.SRCALPHA)
    t = pygame.time.get_ticks() / 1000.0
    rng = random.Random(3)
    for _ in range(28):
        bx = rng.randrange(0, w)
        by = rng.randrange(0, h)
        fase = t * (0.25 + (bx % 7) * 0.03) + by * 0.01
        fy = int((by + math.sin(fase) * 24) % h)
        a = max(0, min(190, 70 + int(70 * math.sin(fase))))
        pygame.draw.circle(capa, (*m.acento, a), (bx, fy), 2)
    surf.blit(capa, (0, 0))


def mesa(surf: pygame.Surface, m: Mesa) -> None:
    """Dibuja la mesa vista desde arriba con el estilo indicado.

    Todo esto es puro adorno: las medidas y la fisica no cambian de una mesa
    a otra, solo el aspecto.
    """
    x0, y0 = _px(0), _py(0)
    w, h = int(S.TABLE_W), int(S.TABLE_H)

    # --- Marco exterior, con canto claro para dar volumen ---
    pygame.draw.rect(
        surf, m.marco,
        (x0 - S.WALL, y0 - S.WALL, w + 2 * S.WALL, h + 2 * S.WALL),
        border_radius=12,
    )
    pygame.draw.rect(
        surf, tuple(min(255, c + 28) for c in m.marco),
        (x0 - S.WALL, y0 - S.WALL, w + 2 * S.WALL, h + 2 * S.WALL),
        3, border_radius=12,
    )

    # --- Hielo, con las lineas de un rink de hockey de verdad ---
    pista = pygame.Surface((w, h))
    pista.fill(m.hielo)
    mid = h // 2
    for k in (1, 3):
        bx = k * w // 4
        pygame.draw.line(pista, m.acento, (bx, 0), (bx, h), 3)
        # Hash marks de la linea azul, fuera del circulo de salida
        for dx in (-92, 92):
            pygame.draw.line(
                pista, m.linea,
                (bx + dx, mid - 22), (bx + dx, mid + 22), 2,
            )
    # Linea roja del centro
    pygame.draw.line(pista, m.hielo_oscuro, (w // 2, 0), (w // 2, h), 3)

    _patron(pista, m, w, h)

    if m.brillo > 0.0:
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(0, h, 3):
            a = int(255 * m.brillo * (1.0 - i / h))
            if a <= 0:
                break
            pygame.draw.line(glow, (255, 255, 255, a), (0, i), (w, i))
        pista.blit(glow, (0, 0))

    _motas(pista, m, w, h)
    surf.blit(pista, (x0, y0))

    # --- Circulos de salida, como en un rink de hockey ---
    mid_p = y0 + mid
    # Circulo central
    pygame.draw.ellipse(
        surf, m.linea, (x0 + w // 2 - 92, mid_p - 92, 184, 184), 3
    )
    pygame.draw.circle(surf, m.linea, (x0 + w // 2, mid_p), 5)
    # Circulos de puesta en juego, en el centro de cada zona
    for zx in (w // 4, w * 3 // 4):
        pygame.draw.ellipse(surf, m.linea, (x0 + zx - 76, mid_p - 76, 152, 152), 2)
        pygame.draw.circle(surf, m.linea, (x0 + zx, mid_p), 4)
        # Colas de la marca de salida
        for sy in (-1, 1):
            pygame.draw.line(
                surf, m.linea,
                (x0 + zx - 76, mid_p + sy * 92), (x0 + zx + 76, mid_p + sy * 92), 2,
            )
    # Puntos de la zona neutral
    for dx in (-2, -1, 1, 2):
        pygame.draw.circle(surf, m.linea, (x0 + w // 2 + dx * 60, mid_p), 3)

    # --- Creces (area delante de cada meta) ---
    for gx, hacia_dcha in ((x0, True), (x0 + w, False)):
        aw = 92
        ah = int(S.GOAL_W) + 84
        area = pygame.Surface((aw, ah), pygame.SRCALPHA)
        pygame.draw.rect(area, (*m.acento, 46), (0, 0, aw, ah), border_radius=16)
        pygame.draw.rect(area, (*m.linea, 120), (0, 0, aw, ah), 2, border_radius=16)
        surf.blit(area, (gx if hacia_dcha else gx - aw, mid_p - ah // 2))

    # --- Lineas de porteria y travesanos ---
    for gx in (x0, x0 + w):
        y_a = mid_p - int(S.GOAL_W) // 2
        y_b = mid_p + int(S.GOAL_W) // 2
        pygame.draw.line(surf, m.linea, (gx, y_a), (gx, y_b), 4)
        gx_in = gx + (18 if gx == x0 else -18)
        pygame.draw.line(surf, m.hielo_oscuro, (gx_in, y_a), (gx_in, y_b), 3)
        travesano = gx - 10 if gx == x0 else gx + 10
        pygame.draw.line(surf, m.marco, (travesano, y_a), (travesano, y_b), 6)

    # --- Borde del rink ---
    pygame.draw.rect(surf, m.linea, (x0, y0, w, h), 3, border_radius=6)


def porteria_destello(surf: pygame.Surface, m: Mesa, lado: int, intensidad: float) -> None:
    """Un brillo en la porteria cuando acaba demarked gol."""
    if intensidad <= 0.0:
        return
    x = _px(0) if lado < 0 else _px(S.TABLE_W)
    mid = _py(S.RINK_CENTER_Y)
    alto = int(S.GOAL_W)
    g = pygame.Surface((70, alto), pygame.SRCALPHA)
    for i in range(alto):
        a = int(255 * intensidad * 0.7)
        pygame.draw.line(g, (255, 255, 255, a), (0, i), (70, i))
    surf.blit(g, (x - 70 if lado < 0 else x, mid - alto // 2))


# --- Pala ------------------------------------------------------------------
def pala(surf: pygame.Surface, p: Pala, skin: SkinPala, t: float) -> None:
    cx, cy = _px(p.pos.x), _py(p.pos.y)
    r = int(p.radio)
    # Sombra
    sh = pygame.Surface((r * 2 + 12, r * 2 + 12), pygame.SRCALPHA)
    pygame.draw.circle(sh, (0, 0, 0, 90), (sh.get_width() // 2, sh.get_height() // 2), r)
    surf.blit(sh, (cx - r - 6, cy - r - 6))

    # Aura violeta de Gigante
    if p.radio_extra > 0.5:
        aura = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
        pygame.draw.circle(
            aura, (190, 130, 255, 70), (aura.get_width() // 2, aura.get_height() // 2), r + 13
        )
        surf.blit(aura, (cx - r - 15, cy - r - 15))

    # Cuerpo
    pygame.draw.circle(surf, (12, 16, 24), (cx, cy), r + 2)
    pygame.draw.circle(surf, skin.cuerpo, (cx, cy), r)
    pygame.draw.circle(surf, skin.borde, (cx, cy), r, 3)

    # Detalle segun skin
    if skin.detalle == "rayas":
        for k in (-8, 8):
            pygame.draw.line(surf, skin.borde, (cx - r + 6, cy + k), (cx + r - 6, cy + k), 2)
    elif skin.detalle == "flama":
        for a in range(6):
            ang = t * 3 + a * 1.05
            rr = r * 0.72
            fx = cx + math.cos(ang) * rr
            fy = cy + math.sin(ang) * rr
            pygame.draw.circle(surf, (255, 190, 80), (fx, fy), 3)
    elif skin.detalle == "estrella":
        pts = []
        for a in range(10):
            ang = -math.pi / 2 + a * math.pi / 5
            rad = r * 0.42 if a % 2 == 0 else r * 0.2
            pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
        pygame.draw.polygon(surf, S.C_GOLD, pts)


# --- Puck ------------------------------------------------------------------
def puck(surf: pygame.Surface, pk: Puck, skin: SkinPuck) -> None:
    cx, cy = _px(pk.pos.x), _py(pk.pos.y)
    r = int(pk.radio)
    sh = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 80), sh.get_rect())
    surf.blit(sh, (cx - r - 5, cy - r))

    pygame.draw.circle(surf, (10, 12, 18), (cx, cy), r + 2)
    pygame.draw.circle(surf, skin.cuerpo, (cx, cy), r)
    pygame.draw.circle(surf, skin.borde, (cx, cy), r, 2)

    if skin.estilo == "grieta":
        for a in range(3):
            ang = pk.giro + a * 2.09
            pygame.draw.line(
                surf,
                (200, 120, 255),
                (cx + math.cos(ang) * r * 0.4, cy + math.sin(ang) * r * 0.4),
                (cx + math.cos(ang) * r * 0.8, cy + math.sin(ang) * r * 0.8),
                2,
            )
    elif skin.estilo == "oro":
        pygame.draw.circle(surf, (255, 235, 150), (cx - r // 3, cy - r // 3), max(2, r // 4))
    elif skin.estilo == "llama":
        for a in range(5):
            ang = -pk.giro * 2 + a * 1.26
            rr = r * 1.35
            fx = cx + math.cos(ang) * rr
            fy = cy + math.sin(ang) * rr
            pygame.draw.circle(surf, (255, 140, 60), (fx, fy), 3)


# --- Escudo ----------------------------------------------------------------
def escudo(surf: pygame.Surface, intensidad: float) -> None:
    """El muro invisible en la porteria del jugador (izquierda)."""
    if intensidad <= 0.0:
        return
    x = _px(8)
    mid = _py(S.RINK_CENTER_Y)
    alto = int(S.GOAL_W + 20)
    ancho = 14
    layer = pygame.Surface((ancho + 20, alto), pygame.SRCALPHA)
    a = int(150 * intensidad)
    for i in range(alto):
        pygame.draw.line(layer, (120, 210, 255, a), (10, i), (10 + ancho, i), 1)
    surf.blit(layer, (x - 10, mid - alto // 2))
    pygame.draw.rect(surf, (140, 220, 255), (x, mid - alto // 2, ancho, alto), 2, border_radius=6)


def _aura(surf: pygame.Surface, x: float, y: float, radio: int, color: tuple, intensidad: float) -> None:
    """Halo circular translucido alrededor de un punto de la mesa."""
    if intensidad <= 0.0 or radio <= 0:
        return
    capa = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
    pygame.draw.circle(
        capa, (*color, int(150 * intensidad)), (radio, radio), radio, width=4
    )
    surf.blit(capa, (int(x) - radio, int(y) - radio))


def y_centre() -> int:
    return _py(S.RINK_CENTER_Y)


def aura_musculos(surf: pygame.Surface, x: float, y: float, intensidad: float, t: float) -> None:
    """Aura naranja de Musculos, sobre la pala del jugador."""
    radio = 58 + int(6 * math.sin(t * 8))
    _aura(surf, x, y, radio, (255, 150, 60), intensidad)


def aura_monstruo(surf: pygame.Surface, x: float, y: float, intensidad: float) -> None:
    """Aura verde de Monstruo."""
    _aura(surf, x, y, 48, (120, 240, 160), intensidad)


def aura_hielo_en_rival(surf: pygame.Surface, x: float, y: float, intensidad: float) -> None:
    """Aura azul de Hielo, sobre la pala del rival."""
    _aura(surf, x, y, 50, (150, 220, 255), intensidad)


# --- Marcador --------------------------------------------------------------
def marcador(surf: pygame.Surface, g1: int, g2: int, meta: int) -> None:
    """Marcador. Con 4 puntos de alguien, avisa de MATCH POINT bien grande."""
    cx = S.WINDOW_WIDTH // 2
    # Quien va a 4 puntos va a ganar el punto siguiente: aviso.
    match_point = 0 if g1 == meta - 1 else (1 if g2 == meta - 1 else None)
    panel(surf, pygame.Rect(cx - 170, 16, 340, 62))
    text(surf, "TU", (cx - 150, 32), 20, S.C_P1, True)
    text(surf, "RIVAL", (cx + 150, 32), 20, S.C_P2, True, right=True)
    text(surf, str(g1), (cx - 78, 24), 44, S.C_P1, True, center=True)
    text(surf, ":", (cx, 30), 40, S.C_TEXT_DIM, True, center=True)
    text(surf, str(g2), (cx + 78, 24), 44, S.C_P2, True, center=True)
    text(surf, f"primero en {meta}", (cx, 62), 12, S.C_TEXT_DIM, center=True)

    if match_point is not None:
        # Match point: banda roja/dorada pulsante detras del marcador.
        pulso = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 130.0)
        col = S.C_GOLD if match_point == 0 else S.C_DANGER
        banda = pygame.Surface((360, 84), pygame.SRCALPHA)
        for i in range(84):
            a = int((70 + 60 * pulso) * (1.0 - abs(i - 42) / 84.0))
            pygame.draw.line(banda, (*col, a), (0, i), (360, i))
        surf.blit(banda, (cx - 180, 8))
        outline(
            surf,
            "MATCH POINT",
            (cx, 100),
            int(34 + 4 * pulso),
            col,
            edge=(10, 12, 20),
        )
        text(
            surf,
            "te falta un solo punto para ganar" if match_point == 0
            else "al rival le falta un solo punto para ganar",
            (cx, 122),
            13,
            col,
            True,
            center=True,
        )


# --- Barra de consumibles activos -------------------------------------------
def barra_items(surf: pygame.Surface, activos: list[ItemEnUso], x: int, y: int,
                hacia_arriba: bool = False) -> None:
    """Lista los consumibles activos con su cuenta atras.

    Con ``hacia_arriba`` la lista crece hacia arriba desde ``y``. Lo usa el
    jugador, para que sus tarjetas queden por encima de la barra de teclas y no
    se solapen con ella.
    """
    vivos = [it for it in activos if it.activo]
    paso = 32
    if hacia_arriba:
        y -= paso * len(vivos)
    for it in vivos:
        w = 150
        rect = pygame.Rect(x, y, w, 26)
        panel(surf, rect, alpha=220, border=it.item.color, radius=8, width=2)
        # relleno de tiempo restante
        fill = int((w - 6) * it.fraccion)
        if fill > 0:
            bar = pygame.Surface((fill, rect.height - 4), pygame.SRCALPHA)
            bar.fill((*it.item.color, 70))
            surf.blit(bar, (rect.x + 3, rect.y + 2))
        text(surf, it.item.name, (rect.x + 8, rect.y + 5), 13, it.item.color, True)
        text(surf, f"{it.tiempo:.0f}s", (rect.x + w - 6, rect.y + 5), 13, S.C_TEXT, True, right=True)
        y += paso


# --- Botones y tarjetas ----------------------------------------------------
def boton(surf: pygame.Surface, rect: pygame.Rect, label: str, hover: bool, activo: bool = False) -> None:
    if activo:
        col, bord, txt = (58, 120, 82), S.C_GOOD, S.C_TEXT
    elif hover:
        col, bord, txt = S.C_PANEL_ALT, S.C_ACCENT, S.C_TEXT
    else:
        col, bord, txt = S.C_PANEL, S.C_BORDER, S.C_TEXT_DIM
    panel(surf, rect, color=col, border=bord, radius=10, width=2)
    text(surf, label, rect.center, 17, txt, True, center=True)


def tarjeta_item(
    surf: pygame.Surface,
    rect: pygame.Rect,
    item,
    en_inventario: bool,
    hover: bool,
    puntos: int,
) -> None:
    """Tarjeta de un consumible en la tienda.

    ``en_inventario`` dice si queda alguna unidad sin usar: si es asi sale
    "YA ADQUIRIDO" para que se vea que ya lo tienes.
    """
    col = S.C_PANEL_ALT if hover else S.C_PANEL
    bord = item.color if (hover or en_inventario) else S.C_BORDER
    panel(surf, rect, color=col, border=bord, radius=10, width=2 if (hover or en_inventario) else 1)
    # Tecla
    badge = pygame.Rect(rect.x + 10, rect.y + 10, 28, 26)
    pygame.draw.rect(surf, item.color, badge, border_radius=7)
    text(surf, item.hotkey, badge.center, 15, (16, 20, 28), True, center=True)
    # Nombre y duracion
    text(surf, item.name, (rect.x + 46, rect.y + 10), 18, item.color, True)
    dur = pygame.Rect(rect.x + 46, rect.y + 34, 62, 20)
    pygame.draw.rect(surf, S.C_PANEL, dur, border_radius=10)
    text(surf, f"{item.duracion:.0f} s", dur.center, 12, S.C_TEXT_DIM, True, center=True)
    # Descripcion
    text(surf, item.desc, (rect.x + 10, rect.y + 44), 12, S.C_TEXT_DIM)
    # Logo grande a la derecha
    icono_item(surf, item, (rect.right - 44, rect.centery - 2), 24)
    # Estado
    if en_inventario:
        pygame.draw.circle(surf, S.C_GOOD, (rect.x + 16, rect.bottom - 18), 5)
        text(surf, "YA ADQUIRIDO", (rect.x + 28, rect.bottom - 26), 14, S.C_GOOD, True)
    elif puntos >= item.precio:
        text(surf, f"{item.precio} monedas", (rect.x + 10, rect.bottom - 26), 14, S.C_ACCENT, True)
    else:
        faltan = item.precio - puntos
        text(surf, f"{item.precio}  (te faltan {faltan})", (rect.x + 10, rect.bottom - 26), 13, S.C_TEXT_DIM, True)


def _degradar(surf: pygame.Surface, poly: list, color: tuple, claro: bool = True) -> None:
    """Rellena un poligono con un degradado vertical suave."""
    ys = [p[1] for p in poly]
    if not ys:
        return
    y0, y1 = min(ys), max(ys)
    alto = max(1, int(y1 - y0))
    for i in range(alto):
        k = i / alto
        if claro:
            c = tuple(int(color[j] + (255 - color[j]) * k * 0.45) for j in range(3))
        else:
            c = tuple(int(color[j] * (1.0 - k * 0.45)) for j in range(3))
        pygame.draw.line(surf, c, (poly[0][0] - 40, y0 + i), (poly[0][0] + 260, y0 + i), 1)


def icono_item(surf: pygame.Surface, item, pos: tuple[int, int], r: int) -> None:
    """Logo del consumible, con detalle: mas bonito que un poligono simple."""
    cx, cy = pos
    col = item.color
    claro = tuple(min(255, int(c * 1.35)) for c in col)
    oscuro = tuple(int(c * 0.55) for c in col)

    # Aro de fondo comun a todos los iconos.
    halo = pygame.Surface((r * 2 + 26, r * 2 + 26), pygame.SRCALPHA)
    pygame.draw.circle(halo, (*col, 46), (r + 13, r + 13), r + 11)
    pygame.draw.circle(halo, (*col, 130), (r + 13, r + 13), r + 11, 2)
    surf.blit(halo, (cx - r - 13, cy - r - 13))

    if item.icono == "escudo":
        pts = [
            (cx, cy - r), (cx + r * 0.86, cy - r * 0.5), (cx + r * 0.7, cy + r * 0.5),
            (cx, cy + r), (cx - r * 0.7, cy + r * 0.5), (cx - r * 0.86, cy - r * 0.5),
        ]
        pygame.draw.polygon(surf, claro, pts)
        pygame.draw.polygon(surf, col, pts, 3)
        pygame.draw.line(surf, oscuro, (cx, cy - r * 0.5), (cx, cy + r * 0.6), 4)
        pygame.draw.line(surf, oscuro, (cx - r * 0.42, cy - r * 0.05), (cx + r * 0.42, cy - r * 0.05), 4)
    elif item.icono == "fuerza":
        pygame.draw.ellipse(surf, claro, (cx - r * 0.62, cy - r * 0.72, r * 1.24, r * 1.5))
        pygame.draw.ellipse(surf, col, (cx - r * 0.62, cy - r * 0.72, r * 1.24, r * 1.5), 3)
        pygame.draw.line(surf, col, (cx - r * 0.2, cy - r * 0.4), (cx + r * 0.2, cy - r * 0.4), 3)
        pygame.draw.line(surf, col, (cx - r * 0.2, cy + r * 0.2), (cx + r * 0.2, cy + r * 0.2), 3)
        pygame.draw.arc(surf, (16, 20, 28), (cx - r * 0.72, cy - r * 0.82, r * 1.44, r * 1.7),
                        math.pi, 2 * math.pi, 5)
    elif item.icono == "furia":
        pygame.draw.arc(surf, col, (cx - r * 0.9, cy - r * 0.9, r * 1.8, r * 1.8),
                        0, 2 * math.pi, 5)
        for i in range(7):
            a = math.pi * 0.15 + i * (math.pi * 0.7 / 6)
            x0 = cx + math.cos(a) * r * 0.78
            y0 = cy + math.sin(a) * r * 0.78
            x1 = cx + math.cos(a) * r * 0.34
            y1 = cy + math.sin(a) * r * 0.34
            pygame.draw.line(surf, claro, (x0, y0), (x1, y1), 4)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy - r * 0.15), max(2, r // 6))
    elif item.icono == "rayo":
        for i in range(3, 0, -1):
            pygame.draw.polygon(
                surf, col,
                [
                    (cx + r * (0.34 + 0.12 * (3 - i)), cy - r * (0.6 + 0.14 * (3 - i))),
                    (cx - r * 0.16, cy + r * 0.08),
                    (cx - r * 0.02, cy + r * 0.12),
                ],
            )
        pygame.draw.polygon(
            surf, col,
            [(cx + r * 0.42, cy - r), (cx - r * 0.52, cy + r * 0.12),
             (cx - r * 0.04, cy + r * 0.1), (cx - r * 0.34, cy + r),
             (cx + r * 0.56, cy - r * 0.12), (cx + r * 0.06, cy - r * 0.1)],
        )
        pygame.draw.polygon(surf, claro, [(cx + r * 0.3, cy - r * 0.6), (cx - r * 0.2, cy + r * 0.02),
                                          (cx + r * 0.05, cy), (cx - r * 0.1, cy + r * 0.3)])
    elif item.icono == "hielo":
        for i in range(6):
            a = i * math.pi / 3
            x0, y0 = cx + math.cos(a) * r, cy + math.sin(a) * r
            x1, y1 = cx - math.cos(a) * r, cy - math.sin(a) * r
            pygame.draw.line(surf, col, (x0, y0), (x1, y1), 4)
            for k in (0.42, 0.68):
                bx, by = cx + (x1 - cx) * k, cy + (y1 - cy) * k
                for g in (-0.7, 0.7):
                    aa = a + g
                    pygame.draw.line(
                        surf, claro,
                        (bx, by),
                        (bx + math.cos(aa) * r * 0.3, by + math.sin(aa) * r * 0.3), 2,
                    )
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), max(2, r // 7))
    elif item.icono == "gigante":
        # Una pala grande con flechas de crecimiento.
        pygame.draw.circle(surf, claro, (cx, cy), r, 4)
        pygame.draw.circle(surf, col, (cx, cy), int(r * 0.55))
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), int(r * 0.55), 2)
        for sx_, sy_ in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            x0 = cx + sx_ * r * 0.72
            y0 = cy + sy_ * r * 0.72
            x1 = cx + sx_ * r * 1.12
            y1 = cy + sy_ * r * 1.12
            pygame.draw.line(surf, claro, (x0, y0), (x1, y1), 4)
            px, py = -sy_ * 5, sx_ * 5
            pygame.draw.polygon(
                surf, claro,
                [(x1, y1), (x1 - sx_ * 7 + px, y1 - sy_ * 7 + py),
                 (x1 - sx_ * 7 - px, y1 - sy_ * 7 - py)],
            )


def _icono(surf: pygame.Surface, item, pos: tuple[int, int], r: int) -> None:
    """Alias antiguo, por si se usa en otro sitio."""
    icono_item(surf, item, pos, r)


def emblema(surf: pygame.Surface, tipo: str, pos: tuple[int, int], r: int, color: tuple) -> None:
    """Emblema del rival, para que cada uno tenga su caracter."""
    cx, cy = pos
    claro = tuple(min(255, int(c * 1.4)) for c in color)
    # Halo
    halo = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
    pygame.draw.circle(halo, (*color, 52), (r + 10, r + 10), r + 9)
    pygame.draw.circle(halo, (*color, 140), (r + 10, r + 10), r + 9, 2)
    surf.blit(halo, (cx - r - 10, cy - r - 10))

    if tipo == "rayo":
        pygame.draw.polygon(
            surf, color,
            [(cx + r * 0.4, cy - r), (cx - r * 0.5, cy + r * 0.12),
             (cx - r * 0.05, cy + r * 0.1), (cx - r * 0.35, cy + r),
             (cx + r * 0.55, cy - r * 0.12), (cx + r * 0.05, cy - r * 0.1)],
        )
    elif tipo == "furia":
        # Mandibula con dientes.
        pygame.draw.arc(surf, color, (cx - r, cy - r, r * 2, r * 2), 0, 2 * math.pi, 4)
        for i in range(6):
            a = math.pi * 0.18 + i * (math.pi * 0.64 / 5)
            pygame.draw.line(
                surf, claro,
                (cx + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8),
                (cx + math.cos(a) * r * 0.34, cy + math.sin(a) * r * 0.34), 4,
            )
    elif tipo == "corona":
        # Corona: rey del torneo.
        pts = [
            (cx - r * 0.8, cy + r * 0.5), (cx - r * 0.8, cy - r * 0.3),
            (cx - r * 0.4, cy + r * 0.05), (cx, cy - r * 0.7),
            (cx + r * 0.4, cy + r * 0.05), (cx + r * 0.8, cy - r * 0.3),
            (cx + r * 0.8, cy + r * 0.5),
        ]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.line(surf, claro, (cx - r * 0.7, cy + r * 0.5), (cx + r * 0.7, cy + r * 0.5), 3)
    elif tipo == "robot":
        # Cabeza robot con ojo.
        pygame.draw.rect(surf, color, (cx - int(r * 0.7), cy - int(r * 0.6), int(r * 1.4), int(r * 1.2)), border_radius=5)
        pygame.draw.rect(surf, claro, (cx - int(r * 0.45), cy - int(r * 0.3), int(r * 0.9), int(r * 0.4)), border_radius=3)
        pygame.draw.line(surf, color, (cx, cy - int(r * 0.6)), (cx, cy - int(r * 1.0)), 3)
        pygame.draw.circle(surf, claro, (cx, cy - int(r * 1.05)), 4)
    elif tipo == "bestia":
        # Garras.
        for i in (-1, 0, 1):
            x0 = cx + i * r * 0.5
            pygame.draw.line(surf, color, (x0, cy + r * 0.6), (x0 - r * 0.2, cy - r * 0.7), 4)
            pygame.draw.line(surf, claro, (x0 - r * 0.2, cy - r * 0.7), (x0 + r * 0.05, cy - r * 0.4), 3)
    else:  # fantasma
        pts = [(cx + math.cos(a) * r, cy + math.sin(a) * r)
               for a in [i * math.pi / 4 for i in range(8)]]
        pts += [(cx + r * 0.6, cy + r), (cx, cy + r * 0.6), (cx - r * 0.6, cy + r)]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.circle(surf, (16, 20, 28), (cx - r * 0.32, cy - r * 0.15), max(2, r // 5))
        pygame.draw.circle(surf, (16, 20, 28), (cx + r * 0.32, cy - r * 0.15), max(2, r // 5))


def trofeo(surf: pygame.Surface, pos: tuple[int, int], r: int) -> None:
    """Trofeo dorado de campeon: copa con asas, peana y estrella."""
    cx, cy = pos
    if r < 6:
        return
    dorado = (232, 184, 44)
    claro = (255, 238, 158)
    oscuro = (158, 116, 18)
    sombra = (196, 150, 30)
    lw = max(1, r // 26)

    # --- Asas, detras de la copa ---
    for lado in (-1, 1):
        ax = cx + lado * r * 0.46
        pygame.draw.arc(
            surf, oscuro,
            (ax - r * 0.24, cy - r * 0.72, r * 0.48, r * 0.56),
            0 if lado > 0 else math.pi / 2,
            math.pi / 2 if lado > 0 else math.pi,
            lw * 2,
        )

    # --- Copa: trapecio ancho arriba ---
    arriba_y, abajo_y = cy - r * 0.78, cy - r * 0.02
    pygame.draw.polygon(
        surf, dorado,
        [(cx - r * 0.5, arriba_y), (cx + r * 0.5, arriba_y),
         (cx + r * 0.22, abajo_y), (cx - r * 0.22, abajo_y)],
    )
    # Brillo interior de la copa
    pygame.draw.polygon(
        surf, claro,
        [(cx - r * 0.42, arriba_y + r * 0.05), (cx - r * 0.05, arriba_y + r * 0.05),
         (cx - r * 0.06, abajo_y - r * 0.05), (cx - r * 0.18, abajo_y - r * 0.05)],
    )
    pygame.draw.line(surf, claro, (cx - r * 0.5, arriba_y), (cx + r * 0.5, arriba_y), lw * 2)

    # --- Estrella en el centro de la copa ---
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r * 0.2 if i % 2 == 0 else r * 0.085
        pts.append((cx + r * 0.12 + math.cos(ang) * rad, cy - r * 0.38 + math.sin(ang) * rad))
    pygame.draw.polygon(surf, claro, pts)

    # --- Pie y peana ---
    pygame.draw.polygon(
        surf, sombra,
        [(cx - r * 0.1, abajo_y), (cx + r * 0.1, abajo_y),
         (cx + r * 0.14, cy + r * 0.2), (cx - r * 0.14, cy + r * 0.2)],
    )
    pygame.draw.rect(surf, oscuro, (cx - int(r * 0.26), cy + int(r * 0.18), int(r * 0.52), int(r * 0.1)))
    pygame.draw.rect(surf, dorado, (cx - int(r * 0.52), cy + int(r * 0.26), int(r * 1.04), int(r * 0.14)), border_radius=3)
    pygame.draw.rect(surf, claro, (cx - int(r * 0.52), cy + int(r * 0.26), int(r * 1.04), int(r * 0.14)), lw, border_radius=3)
    pygame.draw.rect(surf, dorado, (cx - int(r * 0.66), cy + int(r * 0.4), int(r * 1.32), int(r * 0.12)), border_radius=3)
    pygame.draw.rect(surf, claro, (cx - int(r * 0.66), cy + int(r * 0.4), int(r * 1.32), int(r * 0.12)), lw, border_radius=3)

    # --- Chispas alrededor ---
    for i in range(8):
        a = i * (math.pi * 2 / 8) + 0.4
        x = cx + math.cos(a) * r * 1.05
        y = cy - r * 0.3 + math.sin(a) * r * 0.85
        pygame.draw.circle(surf, claro, (int(x), int(y)), max(1, r // 12))


def miniatura_objeto(
    surf: pygame.Surface, rect: pygame.Rect, tipo: str, clave: str, color: tuple
) -> None:
    """Previsualizacion del objeto: como se vera de verdad en la mesa."""
    cx, cy = rect.centerx, rect.y + 38
    if tipo == "mesa":
        ancho, alto = 132, 62
        x0, y0 = cx - ancho // 2, cy - alto // 2
        pygame.draw.rect(surf, (14, 18, 30), (x0 - 4, y0 - 4, ancho + 8, alto + 8), border_radius=6)
        pygame.draw.rect(surf, color, (x0, y0, ancho, alto), border_radius=4)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 16, 2)
        pygame.draw.line(surf, (255, 255, 255), (cx, y0), (cx, y0 + alto), 2)
        for gx in (x0, x0 + ancho):
            pygame.draw.line(surf, (255, 255, 255), (gx, cy - 12), (gx, cy + 12), 3)
    elif tipo == "pala":
        pygame.draw.circle(surf, (10, 12, 20), (cx, cy), 26)
        pygame.draw.circle(surf, color, (cx, cy), 24)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 24, 3)
        if clave == "pala_pro":
            pygame.draw.line(surf, (255, 255, 255), (cx - 12, cy - 6), (cx + 12, cy - 6), 2)
            pygame.draw.line(surf, (255, 255, 255), (cx - 12, cy + 6), (cx + 12, cy + 6), 2)
        elif clave == "pala_fuego":
            for a in range(6):
                ang = a * 1.05
                pygame.draw.circle(
                    surf, (255, 200, 90),
                    (cx + math.cos(ang) * 17, cy + math.sin(ang) * 17), 4,
                )
        elif clave == "pala_canela":
            pts = []
            for i in range(10):
                ang = -math.pi / 2 + i * math.pi / 5
                rad = 12 if i % 2 == 0 else 6
                pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
            pygame.draw.polygon(surf, S.C_GOLD, pts)
    else:  # puck
        pygame.draw.circle(surf, (10, 12, 20), (cx, cy), 20)
        pygame.draw.circle(surf, color, (cx, cy), 18)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 18, 3)
        if clave == "puck_oro":
            pygame.draw.circle(surf, (255, 240, 170), (cx - 6, cy - 6), 5)
        elif clave == "puck_fuego":
            for a in range(5):
                ang = a * 1.26
                pygame.draw.circle(
                    surf, (255, 160, 70),
                    (cx + math.cos(ang) * 24, cy + math.sin(ang) * 24), 3,
                )
        elif clave == "puck_canela":
            for a in range(3):
                ang = a * 2.09
                pygame.draw.line(
                    surf, (214, 140, 255),
                    (cx + math.cos(ang) * 7, cy + math.sin(ang) * 7),
                    (cx + math.cos(ang) * 14, cy + math.sin(ang) * 14), 3,
                )


def tarjeta_cosmetica(
    surf: pygame.Surface,
    rect: pygame.Rect,
    nombre: str,
    color: tuple,
    precio: int,
    poseido: bool,
    equipado: bool,
    hover: bool,
    tipo: str = "mesa",
    clave: str = "",
) -> None:
    """Tarjeta de un objeto de aspecto, con miniatura de como se ve."""
    col = S.C_PANEL_ALT if hover else S.C_PANEL
    panel(surf, rect, color=col, border=color if (hover or equipado) else S.C_BORDER,
          radius=10, width=2 if (hover or equipado or poseido) else 1)
    # Miniatura de como se ve de verdad.
    miniatura_objeto(surf, rect, tipo, clave, color)
    # Nombre DEBAJO de la miniatura (no encima) y estado en el pie de la tarjeta.
    text(surf, nombre, (rect.centerx, rect.y + 82), 15, color, True, center=True)
    # Estado
    if equipado:
        estado, c = "EN USO AHORA", S.C_GOOD
    elif poseido:
        pygame.draw.circle(surf, S.C_GOOD, (rect.centerx - 46, rect.bottom - 13), 5)
        estado, c = "YA ADQUIRIDO", S.C_GOOD
    elif precio <= 0:
        estado, c = "SOLO SI GANAS EL TORNEO", S.C_DANGER
    else:
        estado, c = f"{precio} monedas", S.C_ACCENT
    text(surf, estado, (rect.centerx + (6 if poseido and not equipado else 0), rect.bottom - 21),
         12, c, True, center=True)
