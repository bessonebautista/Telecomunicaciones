"""Guardado de monedas y objetos desbloqueados.

Se guarda en un fichero JSON dentro de la carpeta del juego, para que el
progreso sobreviva entre sesiones.
"""

from __future__ import annotations

import json
import os
import tempfile

SAVE_NAME = "hockey_save.json"

DEFAULT_DATA = {
    "monedas": 0,
    "objetos": ["mesa_basica", "pala_basica", "puck_clasica"],
    "torneo_ronda": 0,  # ronda maxima alcanzada
    "torneo_ganado": False,
    "partidos_ganados": 0,
    "partidos_perdidos": 0,
    "mejor_racha": 0,
    "sonido": True,
    "dificultad": "Intermedio",
}


def _path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), SAVE_NAME)


def load() -> dict:
    """Carga el progreso. Si algo va mal, devuelve los valores por defecto."""
    data = dict(DEFAULT_DATA)
    data["objetos"] = list(DEFAULT_DATA["objetos"])
    try:
        with open(_path(), "r", encoding="utf-8") as fh:
            guardado = json.load(fh)
    except (OSError, ValueError):
        return data
    if not isinstance(guardado, dict):
        return data
    for key, value in guardado.items():
        if key in data:
            data[key] = value
    if not isinstance(data["objetos"], list) or not data["objetos"]:
        data["objetos"] = list(DEFAULT_DATA["objetos"])
    return data


def save(data: dict) -> None:
    """Guarda de forma atomica para no corromper el fichero."""
    ruta = _path()
    try:
        dirn = os.path.dirname(ruta)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=dirn, delete=False, suffix=".tmp"
        ) as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            tmp = fh.name
        os.replace(tmp, ruta)
    except (OSError, ValueError):
        pass


def reset() -> dict:
    data = dict(DEFAULT_DATA)
    data["objetos"] = list(DEFAULT_DATA["objetos"])
    save(data)
    return data
