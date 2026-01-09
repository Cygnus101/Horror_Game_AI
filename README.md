# Horror House Survival

A 2-room survival horror game built with Python 3.11+ and Pygame. Survive five days while managing sanity, hunger, thirst, and a fragile torch battery.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pygame
```

## Run

```bash
python3 main.py
```

## Controls

- WASD / Arrow Keys: Move
- TAB: Switch room (Living Room <-> Bathroom)
- E: Interact (door, TV, fan, stash, sink)
- 1: Eat food
- 2: Drink water
- 3: Drink strange liquid
- T: Toggle TV (near TV)
- F: Toggle Fan (near Fan)
- B: Ground in Bathroom (near sink/mirror zone)
- L or Right Mouse: Toggle torch
- SPACE: Swing axe (Day 5 only)
- R: Restart after death
- ESC: Quit

## Design Notes

- **Rooms**: Two rooms only, rendered with the provided 960x540 backgrounds.
- **Dog**: Follows on Days 1–2 and barks (beep) only when the Dead Girl is real.
- **Torch**: Banishes the Dead Girl if the beam hits her; no effect on hallucinations or the tentacle monster.
- **Clues**: Real ghost casts a shadow and causes smooth sanity drain; hallucinations are semi-transparent and cause sanity spikes. Fan reduces cue clarity.
- **Death**: Jumpscare screen shows the killer and summary (time, cause, liquid uses, TV time, noise peak).

## Assets

The game uses the provided assets in `assets/`:

```
assets/
  backgrounds/
    living_room.png
    bathroom.png
  sprites/
    man.png
    dog.png
    dead_dog.png
    girl_ghost.png
    girl_ghost_red_eyes.png
    tentacle_monster.png
```

If an asset is missing, a placeholder is used so the game still runs.
