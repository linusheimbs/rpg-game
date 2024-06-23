# RPG Game Project

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Game Play](#game-play)
- [Artwork and Sounds](#credits-for-artwork-and-sounds)
- [Contact](#contact)

## Introduction
This project is an RPG game made in Python, inspired by classic titles like Pokémon and older Final Fantasy games. It features retro-style gameplay with turn-based combat and an engaging storyline.

Inspired by a tutorial video by [ClearCode](https://www.youtube.com/watch?v=fo4e3njyGy0).

## Features
- **Turn-Based Combat**: Engage in strategic battles with a variety of attacks and abilities.
- **Exploration**: Traverse through different terrains and arenas.
- **Inventory System**: Manage monsters (items planned).
- **NPC Interactions**: Interact with various non-playable characters to battle them.
- **Retro Art and Music**: Enjoy a nostalgic gaming experience with pixel art and chiptune music.

## Installation
1. **Clone the repository**:
    ```bash
    git clone https://github.com/umbra998/rpg-game.git
    ```
2. **Navigate to the project directory**:
    ```bash
    cd rpg-game
    ```
3. **Install the required dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
1. **Run the game**:
    ```bash
    python main.py
    ```
2. **Controls**:
   - w,a,s,d to move
   - Space or f to interact/select
   - ESC to go back
   - TAB or i to open inventory

## Game Play
- **Exploration**: Move your character using the w,a,s,d keys. Interact with objects and NPCs using the Space or f key.
- **Combat**: Use a variety of attacks and spells. Each turn, choose your action wisely to defeat your enemies.
- **Progression**: Fight, gain experience, level up, and unlock new abilities.

## Credits for Artwork and Sounds
- **Artwork**: Made by Scarloxy. Find more of their work [here](https://scarloxy.itch.io/mpwsp01).
- **Sounds**:
  - **Fire attack**: [OpenGameArt](https://opengameart.org/content/spell-4-fire)
  - **Slash attack**: [OpenGameArt](https://opengameart.org/content/knife-sharpening-slice-2)
  - **Crack sounds**: [OpenGameArt](https://opengameart.org/content/5-break-crunch-impacts)
  - **Overworld music**: [OpenGameArt](https://opengameart.org/content/nes-overworld-theme)
  - **Notice sound**: [OpenGameArt](https://opengameart.org/content/10-8bit-coin-sounds)
  - **Battle music**: [OpenGameArt](https://opengameart.org/content/boss-battle-1-8-bit-re-upload)

## Planned Changes

### Map:
- [x] Rework the map collisions
- [ ] Create new maps

### Monsters:
- [ ] Rename monsters
- [ ] Change monster abilities for better coherence
- [ ] Add new abilities and elements
- [x] Remove recovery mechanism
- [x] Add power to monsters' abilities
- [ ] Apply power scaling to abilities

### Character:
- [ ] Implement pathfinding for the player
- [ ] Assign unique IDs to all NPCs, not just the nurse

### Battle:
- [x] Add a skip turn button
- [ ] Review and redesign the element system to support multiple elements
- [ ] Rework defense system for better balance
    - [ ] Review and adjust all stat systems, including exp
- [ ] Overhaul catch system
- [x] Completely redesign battle system without a timer, using speed checks
- [x] Implement action queue and execution system
- [ ] Allow monsters to take actions based on available energy
- [x] Improve visual cues for turn indication (might need future changes)

### Sound:
- [ ] Update existing sounds and add new ones

### Other:
- [ ] Optimize sprite rendering based on player proximity to reduce lag
- [x] Create main menu with full functionality and UI
- [x] Design options menu with UI elements
- [ ] Implement save and load functionality and UI
- [ ] Introduce new items to the game

### Bugfixes:
- [x] Fix issue where player actions can cause crashes during action execution
- [x] Resolve bug causing outlines to appear incorrectly during actions
- [x] Address player ability to attack out of sequence by spamming space
- [ ] Investigate intermittent battle stoppages
- [ ] Fix initial player position when movement keys are pressed before loading completes

## Contact
Coming.
