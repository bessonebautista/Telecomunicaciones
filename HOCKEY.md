# Hockey de Aire

Juego de hockey de aire en 2D con la **mesa vista desde arriba**. Controlas
tu pala con el **ratón** contra la IA, y al primero que llegue a **5 puntos**
gana. Sin reloj.

Lo que hay:

- **Torneo** de 4 rondas: octavos → cuartos → semifinal → **final**
- **Monedas**: se ganan en el torneo, y cuanto más lejos llegas más ganas
- **Consumibles** que se compran **antes del partido** y duran un rato
- **13 objetos** (5 mesas, 4 palas, 4 pucks) que **solo cambian el aspecto**:
  la física es idéntica en todos
- **Sonidos y música** generados por código (no se descarga nada). La música
  suena en los menús y se para al empezar el partido
- Progreso **guardado** entre sesiones

## Cómo jugar

Doble clic en **`HOCKEY.bat`**. Si te pide instalar pygame, acepta y listo.

## Controles

| | |
|---|---|
| **Ratón** | Mover tu pala y **apuntar** (te quedas en tu mitad) |
| `1`-`6` | Usar consumible (teclas de la partida) |
| **Clic** | Pulsar botones de los menús, saltar la presentación |
| `ESC` | Volver al menú |
| `R` | Reiniciar el partido |
| `S` | Activar o quitar el sonido (y la música) |

**Se juega solo con el ratón.** No hay botón de potencia: el tiro sale siempre
con la misma fuerza.

**La puck sale hacia donde mueves la pala**, como si le dieras con el palo:
si arrastras el ratón hacia arriba y a la derecha, el tiro va en esa
dirección. Si estás quieto, sale hacia la portería del rival por el lado
opuesto al que esté tu pala.

Un roce también cuenta como golpe: la puck no se te pasa de largo.

La pala va clavada donde la dejes y **no tiembla**, aunque tiembles la mano
sobre el ratón. Aun así hay unos pocos píxeles de retardo: es lo que hace que
el control sea estable.

## Los seis consumibles

Ninguno dura toda la partida. Todos tienen tiempo, y **se ven los dos**: el
rival también ve lo que llevas puesto.

| Tecla | Consumible | Qué hace | Tiempo |
|---|---|---|---|
| `1` | **Monstruo** | Al golpear, el puck sale disparado | 14 s |
| `2` | **Escudo** | Muro invisible en tu portería: detiene 2 goles | 18 s |
| `3` | **Músculos** | Cada punto que marcas vale **el doble** | 15 s |
| `4` | **Ráfaga** | Tu pala pega con un 60 % más de fuerza | 10 s |
| `5` | **Hielo** | Al rival le resbala la pala | 12 s |
| `6` | **Gigante** | Tu pala se hace enorme (casi el doble) | 14 s |

**Una compra = un uso.** Cuando pulsas la tecla, la unidad se gasta de tu
bolsa. Cuando se acaba el tiempo, **tienes que volver a comprar**: no se puede
reactivar en bucle ni aunque tengas más unidades compradas.

**Cómo se compran:** `TIENDA` → pestaña `CONSUMIBLES` → clic en la tarjeta.
Los que ya tienes comprados salen con **"YA ADQUIRIDO"**. **No hay ninguno
gratis.**

## La presentación antes de cada partido

En el torneo, antes de empezar cada ronda aparece una pantalla
**"TU vs RIVAL"** con el nombre y el nivel del rival. La final tiene su propio
tratamiento: fondo morado con rayos dorados y dura más. Se salta con `clic` o
`ENTER` si no quieres esperar.

## El torneo y las monedas

| Ronda | Rival | Dificultad | Ganando | Perdiendo |
|---|---|---|---|---|
| Octavos | Rayo | Novato | 100 | 40 |
| Cuartos | Tormenta | Difícil | 170 | 70 |
| Semifinal | Titán | Experto | 260 | 110 |
| Final | Rey Neón | **Imposible** | 730 | 160 |

Si **ganas el torneo entero** te llevas **350 monedas extra** y desbloqueas
los tres objetos mejores: **mesa Suprema**, **pala Canela** y **puck Canela**,
que además se te equipan solos.

Los otros 10 objetos se compran con monedas. Los de campeón no se pueden
comprar con nada.

**Está calibrado para ser difícil.** Midiendo contra un rival simulado que
juega bien y apunta a las esquinas, los partidos contra *Novato* y *Normal*
se ganan de verdad, pero contra *Difícil* ya no, y contra *Experto* e
*Imposible* no se marca ni un solo gol. Es lo que pediste: el torneo tiene
que ser casi imposible de ganar.

## Las mesas y los palos: solo aspecto

Como pediste, la física es **exactamente la misma** en todos. Solo cambia el
dibujado. Hay un test automático que lo comprueba (dos mesas distintas dan la
física idéntica fotograma a fotograma).

- **Mesas**: Básica, Hielo, Metal, Neón, Suprema
- **Palas**: Básica, Pro, Fuego, Canela
- **Pucks**: Clásica, Oro, Fuego, Canela

## Comprobaciones automáticas

```bash
python tools/hockey_test.py      # 170: fisica, raton, IA, consumibles, economia, pantallas
python tools/hockey_torneo.py    # 22: torneo completo y economia
python tools/hockey_fuerza.py    # mide si cada nivel es ganable
python tools/hockey_defensa.py   # mide si la defensa es batible
```

Todas corren sin abrir ventana. Las dos últimas son las que sirven para
saber si el juego está equilibrado: una juega un partido entero contra un
rival humano simulado y la otra lanza tiros colocados contra la portería.

`hockey_fuerza.py` acepta la variable `HOCKEY_SIEMBRAS` para jugar más
partidas por nivel y que la medida no dependa de la suerte:

```bash
set HOCKEY_SIEMBRAS=5
python tools/hockey_fuerza.py
```

## Estructura

```
main_hockey.py        punto de entrada
hockey/
  settings.py         medidas de la mesa, fisica, precios
  cosmetics.py        las 5 mesas, 4 palas y 4 pucks (solo aspecto)
  items.py            los 6 consumibles y su reloj
  physics.py          puck, palas, escudos, porterias
  ai.py               el rival y sus 5 niveles
  tournament.py       bracket, rondas y economía
  save.py             progreso en JSON
  audio.py            sonidos y música del menu, sintetizados
  render.py           dibujado de mesa, palas, puck, logos e interfaz
  game.py             máquina de estados, menus, partido
tools/
  hockey_test.py      comprobaciones
  hockey_torneo.py    torneo completo simulado
  hockey_fuerza.py    equilibrio de la IA en partidos
  hockey_defensa.py   si la defensa es batible
```

El progreso se guarda en `hockey_save.json`, en la misma carpeta. Bórralo
para empezar de cero.

## Un aviso sobre el hockey de aire real

Este juego es una **simplificación arcade**. En el hockey de aire real la
puck va muchísima más rápido, la mesa tiene unas medidas distintas y las
colisiones con la pala son bastante más complejas que un rebote en círculo.
Si algún día quieres algo más fiel, lo que habría que rehacer es `physics.py`
y el radio de golpeo; el resto del juego no se toca.
