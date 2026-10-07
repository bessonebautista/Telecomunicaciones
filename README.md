# Hockey de Aire

Hockey de aire 2D visto desde arriba: mueves tu pala con el ratón, la primera
a 5 puntos gana y hay un torneo de cuatro rondas con consumibles y monedas.

## Cómo jugar

Doble clic en **`HOCKEY.bat`**. Si te pide instalar pygame, acepta y listo.

La partida se juega **solo con el ratón**. La puck sale hacia donde mueves la
pala, así que para atacar tienes que arrastrar el ratón hacia el lado
contrario. Si estás quieto, el tiro va hacia la portería del rival.

La guía completa está en **[HOCKEY.md](HOCKEY.md)**.

## Qué hay aquí

```
HOCKEY.bat        doble clic y a jugar
HOCKEY.md         la guía: controles, consumibles, torneo, objetos
hockey/           el juego
  ai.py           el rival y sus 5 niveles de dificultad
  audio.py        efectos y la música del menú, sintetizados por código
  game.py         menús, tienda, torneo y el partido
  physics.py      puck, palas, escudos y porterías
  render.py       dibujado de la mesa, las palas y la interfaz
  tournament.py   las rondas y la economía
tools/            comprobaciones automáticas (no hacen falta para jugar)
```

## Comprobaciones

```bash
pip install -r requirements.txt
python tools/hockey_test.py       # 170 comprobaciones
python tools/hockey_torneo.py     # torneo y economía completos
```

Las dos corren sin abrir ventana.