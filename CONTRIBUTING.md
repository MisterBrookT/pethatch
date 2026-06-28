# Contributing

PetHatch accepts pet packs that can run in Codex/OpenPets-compatible runtimes.

## Add A Pet

Create a folder:

```text
pets/my-pet/
  pet.json
  spritesheet.webp
  contact-sheet.png
  preview.gif
```

Update `manifest.json` with the new pet.

Run:

```bash
python3 scripts/validate-pets.py
```

Test locally by copying your pet into the shared local pet directory:

```bash
mkdir -p ~/.codex/pets/my-pet
cp pets/my-pet/pet.json ~/.codex/pets/my-pet/pet.json
cp pets/my-pet/spritesheet.webp ~/.codex/pets/my-pet/spritesheet.webp
```

Then open a compatible runtime such as Codex Pets or OpenPets.

## Required Asset Contract

- `spritesheet.webp` or `spritesheet.png`.
- 8 columns and 9 rows.
- Recommended size: `1536x1872`.
- Required animation rows:
  - `idle`
  - `running-right`
  - `running-left`
  - `waving`
  - `jumping`
  - `failed`
  - `waiting`
  - `running`
  - `review`

The canonical cell size is `192x208`. The recommended atlas size is `1536x1872`.

## Minimal `pet.json`

Use `pets/xiaochai/pet.json` as the reference. Required fields:

```json
{
  "schemaVersion": "0.1.0",
  "id": "my-pet",
  "displayName": "My Pet",
  "description": "A short description.",
  "license": {
    "assets": "CC-BY-4.0"
  },
  "spritesheet": {
    "path": "spritesheet.webp",
    "columns": 8,
    "rows": 9,
    "cellWidth": 192,
    "cellHeight": 208,
    "width": 1536,
    "height": 1872
  },
  "animations": [
    { "name": "idle", "row": 0, "frames": 6 },
    { "name": "running-right", "row": 1, "frames": 8 },
    { "name": "running-left", "row": 2, "frames": 8 },
    { "name": "waving", "row": 3, "frames": 4 },
    { "name": "jumping", "row": 4, "frames": 5 },
    { "name": "failed", "row": 5, "frames": 8 },
    { "name": "waiting", "row": 6, "frames": 6 },
    { "name": "running", "row": 7, "frames": 6 },
    { "name": "review", "row": 8, "frames": 6 }
  ]
}
```

## Events

Use `events` to describe richer runtime behavior. Do not add required rows for every product-specific state.

Good:

```json
{
  "quota.limit": { "animation": "waiting", "tone": "critical" }
}
```

Avoid:

```json
{
  "animation": "codex_5h_token_15_percent_warning"
}
```

## Asset Rights

Only submit assets you are allowed to share.

Do not submit:

- copyrighted characters without permission
- brand logos or marks without permission
- generated fan art that cannot be redistributed
- assets with unclear source/license

Declare the asset license in `pet.json` under `license.assets`.
