# PetHatch

**An open market for desktop pet packs.**

[中文](README.zh.md)

PetHatch collects small animated pet packs for Codex-compatible desktop pet runtimes, OpenPets-style shared companions, and agent status apps.

It is not tied to Kaji. Kaji can consume PetHatch packs, but every pet should remain useful without Kaji.

Gallery: <https://misterbrookt.github.io/pethatch/>

```bash
./bin/pethatch install xiaochai --force
```

<p align="center">
  <img src="pets/xiaochai/contact-sheet.png" width="820" alt="Xiaochai pet contact sheet">
</p>

## Use Locally

List available pets:

```bash
./bin/pethatch list
```

Install Xiaochai:

```bash
./bin/pethatch install xiaochai --force
```

This writes `pet.json` and `spritesheet.webp` to `~/.codex/pets/xiaochai/`.

Run Xiaochai on macOS:

```bash
./bin/pethatch run xiaochai
```

Try the compressed behavior demo:

```bash
./bin/pethatch run xiaochai --demo
```

In demo mode, Xiaochai moves from focus to a 60-minute rest reminder in seconds instead of real minutes.

The runner is configured by `pets/xiaochai/runtime.json`. By default, Xiaochai has two nodes: `focus` and `60m rest`. It uses keyboard/mouse activity as the current activity source, pauses after 15 minutes without input, and treats 10 minutes of no input after a rest reminder as a completed break. The pet uses a small size and slow animation so it can sit on the desktop without dominating the screen.

```bash
./bin/pethatch run xiaochai --size medium
./bin/pethatch run xiaochai --rest-after 900 --rest-duration 600
./bin/pethatch run xiaochai --config path/to/runtime.json
```

`~/.codex/pets/<id>` is the shared local convention used by Codex Pets and OpenPets-compatible runtimes. Other runtimes can read the same folder or import the pack from this repo.

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
./bin/pethatch validate
```

## Contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md). Keep pet assets legal to share and include an explicit asset license.

## License

Code and docs are MIT. Pet assets are owned by their contributors under the license declared in each `pet.json`; see [LICENSE-PETS.md](LICENSE-PETS.md).
