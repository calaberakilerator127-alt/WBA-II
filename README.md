# War Brawl Arena II (WBA II)

WBA II is a retro-style, team-based wrestling game built with Python and Pygame-CE. It features fluid animations, a deep state-machine based combat system, and a modular architecture designed for future updates and DLC.

## Features

- **Retro Aesthetic**: Classic Street Fighter style graphics and sounds.
- **Team-Based Combat**: Tag-team mechanics and assists.
- **Fluid Animations**: High-performance sprite management and state machine logic.
- **Modular Design**: Easy to extend with new characters and stages.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/calaberakilerator127-alt/WBA-II.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the game:
   ```bash
   python main.py
   ```

## Development Structure

- `src/engine/`: Core game systems (state manager, input, physics).
- `src/entities/`: Fighter and stage objects.
- `src/graphics/`: Rendering and animation systems.
- `assets/`: Image, sound, and font resources.
- `data/`: Move-sets, stats, and configuration files.
