# PetHatch

**An open market for desktop pet packs.**

[中文](README.zh.md)

PetHatch collects small animated pet packs for Codex-compatible desktop pet runtimes, OpenPets-style shared companions, and agent status apps.

It is not tied to Kaji. Kaji can consume PetHatch packs, but every pet should remain useful without Kaji.

<p align="center">
  <img src="pets/xiaochai/contact-sheet.png" width="820" alt="Xiaochai pet contact sheet">
</p>

## Install A Pet

Today, install manually:

```bash
mkdir -p ~/.codex/pets/xiaochai
cp pets/xiaochai/pet.json ~/.codex/pets/xiaochai/pet.json
cp pets/xiaochai/spritesheet.webp ~/.codex/pets/xiaochai/spritesheet.webp
```

`~/.codex/pets/<id>` is the shared local convention used by Codex Pets and OpenPets-compatible runtimes. Other runtimes can read the same folder or import the pack from this repo.

Future CLI target:

```bash
pethatch install xiaochai
```

## Pet Packs

Each pet is a directory:

```text
pets/xiaochai/
  pet.json
  spritesheet.webp
  contact-sheet.png
  preview.gif
```

The core asset format is an 8-column, 9-row atlas of `192x208` cells. The recommended atlas size is `1536x1872` because `8 * 192 = 1536` and `9 * 208 = 1872`.

Required animations:

`idle`, `running-right`, `running-left`, `waving`, `jumping`, `failed`, `waiting`, `running`, `review`.

See [docs/protocol.md](docs/protocol.md).

## Why PetHatch

Existing projects already prove the shape:

- Petdex: gallery, submit flow, manifest, CLI install.
- OpenPets: shared local pet runtime and 9-row Codex Pets bundles.
- clawd-on-desk / Clyde: agent event to animation mapping.
- AgentPet: token usage, session duration, and companion progression.

PetHatch starts smaller: validated pet packs first, richer runtime adapters later.

Product-specific states such as quota pressure, long sessions, or rest reminders should map onto existing animations through `events`. They do not require new sprite rows.

## Validate

```bash
python3 scripts/validate-pets.py
```

## Contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md). Keep pet assets legal to share and include an explicit asset license.

## License

Code and docs are MIT. Pet assets are owned by their contributors under the license declared in each `pet.json`; see [LICENSE-PETS.md](LICENSE-PETS.md).
