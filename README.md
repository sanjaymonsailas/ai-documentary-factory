# Zombie Horde

Zombie Horde is a browser-first hybrid-casual crowd action prototype built around one satisfying loop:

**aim → multiply → avoid defenses → grow the horde → smash the base → upgrade → repeat**

## Tech

- TypeScript
- Three.js
- Vite
- WebGL
- LocalStorage progression

## Run

```bash
npm install
npm run dev
```

Production build:

```bash
npm run build
```

## Prototype scope

The current vertical slice has five progressively harder levels, three zombie types, multiplier gates, hazards, defense squads, a base attack, a simple Zombie Lab and start-count progression.

The game is deliberately browser-friendly: shared meshes, bounded crowd counts, simple collision logic and lightweight procedural audio.

## Visual target

The project is designed from the supplied Zombie Horde concept reference: a colorful, polished, isometric 3D cartoon crowd game. See `docs/visual-direction.md` and `public/visual-direction.svg`.

This repository should remain focused. New systems should improve the core fantasy instead of turning the game into a management dashboard.
