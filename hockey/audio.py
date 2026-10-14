"""Sonidos y musica generados por codigo.

No se descarga nada: cada efecto y la musica del menu son ondas sintetizadas
con la libreria estandar. Asi el juego va suelto en una carpeta y no depende
de ficheros de audio externos.
"""

from __future__ import annotations

import io
import math
import random
import struct

try:
    import pygame

    _AVAILABLE = True
except ImportError:  # pragma: no cover
    _AVAILABLE = False

# Frecuencia de trabajo. La misma para efectos y musica, para que el mixer no
# tenga que ir cambiando de formato.
RATE = 22050


def _mixer_ready() -> bool:
    if not _AVAILABLE:
        return False
    try:
        if not pygame.mixer.get_init():
            return False
    except pygame.error:
        return False
    return True


def _tone(
    freq: float,
    ms: int,
    volume: float = 0.30,
    kind: str = "sine",
    freq_end: float | None = None,
    decay: float = 6.0,
) -> bytes:
    """Construye un efecto monocromo de un tono, con envolvente de caida."""
    n = int(22050 * ms / 1000)
    data = bytearray()
    phase = 0.0
    for i in range(n):
        t = i / 22050.0
        env = math.exp(-decay * t)
        if env > 1.0:
            env = 1.0
        if freq_end is not None and freq > 0:
            f = freq + (freq_end - freq) * (i / max(1, n))
        else:
            f = freq
        phase += 2.0 * math.pi * f / 22050.0
        if kind == "square":
            s = 1.0 if math.sin(phase) >= 0.0 else -1.0
        elif kind == "saw":
            s = ((phase / (2 * math.pi)) % 1.0) * 2.0 - 1.0
        elif kind == "noise":
            s = random.uniform(-1.0, 1.0)
        else:
            s = math.sin(phase)
        val = int(max(-1.0, min(1.0, s * env * volume)) * 32000)
        data += struct.pack("<h", val)
    return bytes(data)


def _stereo(mono: bytes) -> bytes:
    out = bytearray()
    for i in range(0, len(mono) - 3, 4):
        sample = mono[i : i + 2]
        out += sample + sample
    return bytes(out)


# --- Musica del menu -------------------------------------------------------
# Una melododia de 8 compases en La menor, al estilo de los menus de arcade:
# bajo, arpegio, melodia y bateria. Todo sintetizado, sin ficheros.

# 4 acordes, 2 compases cada uno. Cada acorde es (fundamental del bajo, triada).
_PROGRESION = (
    (45, (57, 60, 64)),  # Am
    (41, (53, 57, 60)),  # F
    (48, (60, 64, 67)),  # C
    (43, (55, 59, 62)),  # G
)

# Melodia: una nota por corchea (8 por compas). None = silencio.
# Los numeros son grados MIDI. La primera frase es la melododia principal y
# la segunda responde un poco mas arriba, para que no suene plano.
_MELODIA_A = (
    (76, None, None, 81, None, 79, 76, None),   # Am
    (72, None, 69, None, 72, None, 74, None),   # F
    (76, None, 79, None, 76, 72, None, None),   # C
    (74, None, 71, None, 74, None, 69, None),   # G
)
_MELODIA_B = (
    (81, None, 79, None, 76, None, 72, None),
    (74, None, 72, None, 69, None, 72, None),
    (79, None, 76, None, 72, None, 76, None),
    (78, None, 74, None, 71, None, 74, None),
)


def _midi_a_hz(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def _env(i: int, n: int, ataque: float = 0.02) -> float:
    """Envolvente de una nota: ataque corto y caida suave hasta silencio."""
    if n <= 0:
        return 0.0
    t = i / n
    if t < ataque:
        return t / ataque
    # Caida exponencial, pero sin cortar de golpe al final.
    return max(0.0, (1.0 - (t - ataque) / (1.0 - ataque)) ** 1.6)


def _nota(midi: int, dur: float, vol: float, onda: str = "square",
         cache: dict = None) -> list[float]:
    """Onda de una nota ya muestreada. Se cachea: casi todas se repiten."""
    clave = (midi, round(dur * 1000), onda)
    if cache is not None and clave in cache:
        return cache[clave]
    n = max(1, int(RATE * dur))
    f = _midi_a_hz(midi)
    out = [0.0] * n
    fase = 0.0
    inc = 2.0 * math.pi * f / RATE
    for i in range(n):
        if onda == "square":
            s = 1.0 if math.sin(fase) >= 0.0 else -1.0
        elif onda == "saw":
            s = ((fase / (2.0 * math.pi)) % 1.0) * 2.0 - 1.0
        elif onda == "tri":
            s = abs(((fase / (2.0 * math.pi)) % 1.0) * 4.0 - 2.0) - 1.0
        else:
            s = math.sin(fase)
        out[i] = s * _env(i, n) * vol
        fase += inc
    if cache is not None:
        cache[clave] = out
    return out


def _bombo(dur: float, vol: float) -> list[float]:
    """Bombo: barrido de tono que cae de 130 Hz a 45 Hz."""
    n = max(1, int(RATE * dur))
    out = [0.0] * n
    fase = 0.0
    for i in range(n):
        t = i / n
        f = 130.0 * (1.0 - t) + 45.0 * t
        fase += 2.0 * math.pi * f / RATE
        out[i] = math.sin(fase) * (1.0 - t) ** 2.2 * vol
    return out


def _caja(dur: float, vol: float) -> list[float]:
    """Caja: ruido con un poco de tono, como un bombo seco."""
    n = max(1, int(RATE * dur))
    out = [0.0] * n
    fase = 0.0
    for i in range(n):
        t = i / n
        fase += 2.0 * math.pi * 190.0 / RATE
        ruido = random.uniform(-1.0, 1.0)
        out[i] = (ruido * 0.75 + math.sin(fase) * 0.25) * (1.0 - t) ** 2.8 * vol
    return out


def _charles(dur: float, vol: float) -> list[float]:
    """Charles: ruido muy corto y agudo."""
    n = max(1, int(RATE * dur))
    return [random.uniform(-1.0, 1.0) * (1.0 - i / n) ** 4.0 * vol for i in range(n)]


def _mezclar(izq: list[float], der: list[float], buf: list[float], t0: int,
             pan: float = 0.5) -> None:
    """Echa una nota dentro de los dos canales, repartida por el paneo.

    ``pan`` va de 0.0 (solo izquierda) a 1.0 (solo derecha). Con 0.5 suena
    igual en los dos lados.
    """
    n = len(izq)
    fin = min(n, t0 + len(buf))
    if t0 < 0:
        t0 = 0
    if fin <= t0:
        return
    # Gains complementarios: lo que se quita de un canal va al otro.
    gi = 1.0 - pan * 0.8
    gd = pan * 0.8
    for i in range(t0, fin):
        v = buf[i - t0]
        izq[i] += v * gi
        der[i] += v * gd


def _wav(izq: list[float], der: list[float]) -> bytes:
    """Envuelve dos canales en un fichero WAV, para que lo sepa leer pygame."""
    n = len(izq)
    datos = bytearray()
    for i in range(n):
        a = int(max(-1.0, min(1.0, izq[i])) * 32000)
        b = int(max(-1.0, min(1.0, der[i])) * 32000)
        datos += struct.pack("<hh", a, b)
    bytes_datos = len(datos)
    cab = b"RIFF" + struct.pack("<I", 36 + bytes_datos) + b"WAVEfmt "
    cab += struct.pack("<IHHIIHH", 16, 1, 2, RATE, RATE * 4, 4, 16)
    cab += b"data" + struct.pack("<I", bytes_datos)
    return cab + bytes(datos)


def _cancion() -> bytes:
    """Construye el loop completo de la musica del menu."""
    bpm = 138.0
    corchea = 60.0 / bpm / 2.0  # duracion de una corchea, en segundos
    corchas_por_compas = 8
    compases = 8
    total = int(RATE * corchea * corchas_por_compas * compases)
    izq = [0.0] * total
    der = [0.0] * total
    cache: dict = {}

    def en(seg: float) -> int:
        return int(seg * RATE)

    def tocar(buf: list[float], seg: float, pan: float = 0.5) -> None:
        _mezclar(izq, der, buf, en(seg), pan)

    for compas in range(compases):
        t0 = compas * corchea * corchas_por_compas
        raiz, triada = _PROGRESION[compas % len(_PROGRESION)]

        # --- Bajo: la fundamental en los golpes 1 y 3, y su octava al final
        # del compas, que es lo que le da el empuje al loop.
        for golpe, octava in ((0, 0), (4, 0), (6, 12), (7, 12)):
            tocar(_nota(raiz + octava, corchea * 1.7, 0.26, "tri", cache),
                  t0 + golpe * corchea)

        # --- Arpegio: las notas del acorde, una por corchea. Se reparten
        # entre los dos canales: suena abierto, no embarrado.
        for paso in range(corchas_por_compas):
            nota = triada[paso % 3] + (12 if paso >= 4 else 0)
            buf = _nota(nota, corchea * 0.85, 0.075, "square", cache)
            tocar(buf, t0 + paso * corchea, 0.15 + (paso % 2) * 0.7)

        # --- Melodia: 4 compases de frase principal y 4 de respuesta.
        frase = _MELODIA_A if compas < 4 else _MELODIA_B
        for paso, midi in enumerate(frase[compas % 4]):
            if midi is None:
                continue
            tocar(_nota(midi, corchea * 1.5, 0.20, "square", cache),
                  t0 + paso * corchea)

        # --- Bateria: bombo en 1, caja en 2 y 4, charles en cada segundo
        # tiempo. Se mueve un poco de un canal a otro para que no suene
        # a una sola parte.
        tocar(_bombo(corchea * 1.1, 0.34), t0)
        for golpe, pan in ((2, 0.42), (6, 0.58)):
            tocar(_caja(corchea * 0.8, 0.15), t0 + golpe * corchea, pan)
        for golpe, pan in ((0, 0.62), (2, 0.38), (4, 0.62), (6, 0.38)):
            tocar(_charles(corchea * 0.35, 0.05), t0 + golpe * corchea, pan)

    return _wav(izq, der)


class Musica:
    """La musica del menu. Es un loop sintetizado, sin ficheros de audio.

    Si el equipo no tiene salida de sonido, todo esto se apaga solo y el juego
    sigue funcionando igual.
    """

    def __init__(self, volumen: float = 0.45) -> None:
        self.volumen = volumen
        self.sonando = False
        self.habilitada = True
        self.cancion: bytes | None = None
        if not _AVAILABLE:
            return
        try:
            if not pygame.mixer.get_init():
                return
        except pygame.error:
            return
        # Se construye una sola vez al arrancar y se reutiliza siempre.
        try:
            self.cancion = _cancion()
        except Exception:  # pragma: no cover - si falla, el juego sigue igual
            self.cancion = None

    @property
    def disponible(self) -> bool:
        return self.cancion is not None

    def tocar(self) -> None:
        """Empieza el loop. No hace nada si ya esta sonando."""
        if not self.habilitada or self.cancion is None or self.sonando:
            return
        try:
            pygame.mixer.music.load(io.BytesIO(self.cancion))
            pygame.mixer.music.set_volume(self.volumen)
            pygame.mixer.music.play(-1)  # -1 = repetir para siempre
            self.sonando = True
        except pygame.error:
            self.sonando = False

    def parar(self) -> None:
        if not self.sonando:
            return
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
        self.sonando = False

    def silence(self) -> None:
        """Silencia la musica sin pararla (para cuando no se nota)."""
        try:
            pygame.mixer.music.set_volume(0.0)
        except pygame.error:
            pass

    def restore(self) -> None:
        try:
            pygame.mixer.music.set_volume(self.volumen)
        except pygame.error:
            pass


class Sounds:
    """Efectos del juego. Si no hay audio, todo el juego funciona igual."""

    def __init__(self) -> None:
        self.enabled = True
        self.bank: dict[str, object] = {}
        if not _AVAILABLE:
            self.enabled = False
            return
        try:
            # Estereo y con un buffer algo mas grande: lo necesita la musica
            # del menu, que va en dos canales y dura varios segundos.
            pygame.mixer.pre_init(RATE, -16, 2, 1024)
            pygame.mixer.init(RATE, -16, 2, 1024)
        except pygame.error:
            self.enabled = False
            return
        self._build()

    def _make(self, mono: bytes):
        if not self._mixer_ready():
            return None
        try:
            return pygame.mixer.Sound(buffer=mono)
        except pygame.error:
            return None

    def _mixer_ready(self) -> bool:
        try:
            return bool(pygame.mixer.get_init())
        except pygame.error:
            return False

    def _build(self) -> None:
        def s(*a, **k):
            return self._make(_tone(*a, **k))

        self.bank = {
            # Pala: golpe seco y corto.
            "pala": s(340, 45, 0.34, "square", 200, 22.0),
            # Rebote en la pared: mas agudo y hueco.
            "pared": s(620, 35, 0.24, "sine", 480, 26.0),
            # Gol:Fanfarria corta ascendente.
            "gol": s(520, 320, 0.34, "square", 1180, 3.2),
            # Gol recibido: caida sonora, el "ay".
            "gol_enemigo": s(560, 300, 0.30, "saw", 150, 4.0),
            # Moneda / compra: dos notas cortas.
            "moneda": s(880, 70, 0.26, "sine", 1320, 9.0),
            # Consumible equipado: brillo ascendente.
            "item": s(420, 180, 0.28, "sine", 1250, 5.0),
            # Consumible se acaba: caida.
            "item_fin": s(700, 200, 0.22, "sine", 220, 6.0),
            # Empezar partido.
            "silbato": s(1180, 260, 0.26, "square", 1560, 4.5),
            # Clic de menu.
            "clic": s(500, 30, 0.18, "square", 400, 30.0),
            # Campeon / victoria de torneo.
            "campeon": s(523, 620, 0.32, "square", 1568, 2.0),
            # Derrota.
            "derrota": s(400, 480, 0.28, "saw", 120, 3.0),
        }

    def play(self, name: str) -> None:
        if not self.enabled or not self._mixer_ready():
            return
        snd = self.bank.get(name)
        if snd is None:
            return
        try:
            snd.play()
        except pygame.error:
            pass

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled
