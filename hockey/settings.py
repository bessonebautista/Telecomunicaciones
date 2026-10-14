"""Constantes del juego de hockey de aire.

La fisica es SIEMPRE la misma para todas las mesas y palas: lo unico que
cambia de una mesa a otra es como se ven. Aqui solo hay medidas y numeros.
"""

from __future__ import annotations

# --- Ventana ---------------------------------------------------------------
WINDOW_TITLE = "Hockey de Aire"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 760
FPS = 60

# --- Mesa ------------------------------------------------------------------
TABLE_W = 900.0  # ancho del rink (entre lineas de fondo)
TABLE_H = 540.0  # alto del rink
TABLE_X = 95.0  # margen izquierdo del rink en pantalla
TABLE_Y = 150.0  # margen superior del rink en pantalla
WALL = 14.0  # grosor de la pared
GOAL_W = 168.0  # altura de la porteria
GOAL_DEPTH = 26.0  # fondo de la porteria
RINK_CENTER_Y = TABLE_H / 2.0

# --- Objetos ---------------------------------------------------------------
PUCK_R = 15.0
PADDLE_R = 40.0
PUCK_MAX_SPEED = 1250.0
PUCK_MIN_SPEED = 150.0  # por debajo, la mesa "frena" la puck
PUCK_FRICTION = 0.55  # por segundo, rozamiento continuo con la mesa
PUCK_RESTITUTION = 0.94
PADDLE_BOUNCE = 1.02
PADDLE_MAX_SPEED = 1150.0
SERVE_DELAY = 0.9  # pausa antes de sacar
POINT_PAUSE = 1.6  # pausa tras un gol
GOALS_TO_WIN = 5

# --- Consumibles -----------------------------------------------------------
# Ninguno dura toda la partida: todos tienen tiempo.
ITEMS = (
    "monstruo",
    "escudo",
    "musculos",
    "rafaga",
    "hielo",
    "gigante",
)

# --- Tienda ----------------------------------------------------------------
# Los consumibles se compran antes del partido. Si no tienes monedas, la
# partida empieza sin ninguno.
ITEM_PRICES = {
    "monstruo": 60,
    "escudo": 80,
    "musculos": 70,
    "rafaga": 55,
    "hielo": 65,
    "gigante": 90,
}

# Los objetos de aspecto se compran con monedas y los mejores solo con ganar.
COSMETIC_PRICES = {
    "mesa_hielo": 120,
    "mesa_metal": 150,
    "pala_pro": 140,
    "pala_fuego": 160,
    "puck_oro": 200,
    "puck_fuego": 180,
}

# --- Sonidos ---------------------------------------------------------------
SAMPLE_RATE = 44100
SAMPLE_SIZE = -16
CHANNELS = 2
BUFFER = 512

# --- Colores ---------------------------------------------------------------
C_BG_TOP = (14, 18, 34)
C_BG_BOTTOM = (30, 40, 66)
C_TEXT = (238, 242, 250)
C_TEXT_DIM = (150, 164, 190)
C_PANEL = (16, 22, 38)
C_PANEL_ALT = (26, 34, 54)
C_BORDER = (52, 66, 94)
C_ACCENT = (255, 208, 96)
C_P1 = (94, 200, 255)
C_P2 = (255, 106, 122)
C_DANGER = (255, 92, 92)
C_GOOD = (120, 240, 160)
C_GOLD = (255, 196, 60)
