"""Punto de entrada del Hockey de Aire.

Uso:
    python main_hockey.py
"""

from __future__ import annotations

import sys

from hockey.game import Game


def main() -> int:
    game = Game()
    try:
        game.run()
    except KeyboardInterrupt:
        game.running = False
    return 0


if __name__ == "__main__":
    sys.exit(main())
