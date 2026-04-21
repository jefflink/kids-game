## What you got

**`index.html`** — your homepage with a dark arcade aesthetic, animated starfield, bouncing color dots, and responsive game cards that show `cover.png` with a hover zoom + play badge. Falls back gracefully to an emoji if the image is missing.

**`games.json`** — the manifest you maintain to list your games.

---

## Your repo structure

```
/                        ← repo root
├── index.html           ← homepage
├── games.json           ← game list (you edit this)
└── data/
    ├── bubble-pop/
    │   ├── main.html    ← the game
    │   └── cover.png    ← cover art (600×400 recommended)
    ├── dino-jump/
    │   ├── main.html
    │   └── cover.png
    └── ...
```

---

## Adding a new game

Just add an entry to `games.json`:

```json
{
  "id": "my-new-game",        ← must match the folder name under /data/
  "title": "My New Game",
  "description": "A short tagline shown on the card.",
  "emoji": "🚀"               ← shown if cover.png is missing
}
```

The `id` field drives everything — the cover path (`data/{id}/cover.png`) and game link (`data/{id}/main.html`) are derived from it automatically.