# PetHatch Protocol v0.1

PetHatch separates pet assets from app/runtime behavior.

## Asset Contract

A pet pack is a directory:

```text
my-pet/
  pet.json
  spritesheet.webp
  contact-sheet.png
  preview.gif
```

The spritesheet follows the Codex/OpenPets 9-row atlas:

| Row | Animation | Required | Meaning |
| --- | --- | --- | --- |
| 0 | `idle` | yes | Calm resting state |
| 1 | `running-right` | yes | Drag or movement to the right |
| 2 | `running-left` | yes | Drag or movement to the left |
| 3 | `waving` | yes | Greeting or attention |
| 4 | `jumping` | yes | Playful jump |
| 5 | `failed` | yes | Error, blocked, cancelled |
| 6 | `waiting` | yes | Waiting for user input, quota reset, or approval |
| 7 | `running` | yes | Active work |
| 8 | `review` | yes | Done, review, or attention |

Default frame size is `192x208`. The atlas is normally `1536x1872`.

## Runtime State Contract

Runtimes should keep core states small:

```text
idle
running
review
waiting
failed
message
done
```

These states map onto required animations. Rich app semantics should be carried as `reason`, `metrics`, or surface/badge data.

## Event Extensions

Pet packs may declare event mappings:

```json
{
  "quota.limit": {
    "animation": "waiting",
    "tone": "critical",
    "threshold": ">=95% used or <=15% remaining"
  }
}
```

Runtimes may ignore unknown events. This keeps packs compatible with Codex Pets and OpenPets while allowing richer products to react to quota and session context.

`events` is recommended, not required. A pack without `events` is still a valid base pet pack; runtimes should then map their own core states to the required 9-row animations.

`tone` uses a small shared vocabulary:

| Tone | Meaning |
| --- | --- |
| `neutral` | Background, healthy, or resting state |
| `working` | Active work or progress |
| `attention` | User input, approval, or awareness needed |
| `done` | Completed or ready for review |
| `warning` | Non-blocking pressure or fatigue |
| `critical` | Limit, failure, or blocked state |
| `care` | Gentle health/rest suggestion |
| `system` | System-level mode such as keep-awake |

Recommended event families:

- `agent.*`: `idle`, `running`, `waiting`, `review`, `failed`.
- `quota.*`: `healthy`, `active`, `pressure`, `limit`.
- `session.*`: `long`, `rest_suggested`.
- `system.*`: `keep_awake_on`, `update_available`.

Recommended event meanings:

| Event | Suggested animation | Meaning |
| --- | --- | --- |
| `quota.pressure` | `review` | A quota window is getting tight, but work can continue. |
| `quota.limit` | `waiting` | A quota window is exhausted or nearly exhausted. |
| `session.long` | `review` | A focused work session has crossed a runtime-defined duration threshold. |
| `session.rest_suggested` | `waiting` | The runtime has decided the user should rest. This may combine session length, quota pressure, time of day, or user preference. |
| `system.keep_awake_on` | `idle` | The machine is intentionally kept awake. |
| `system.update_available` | `waving` | A runtime or adapter update is available. |

Thresholds are descriptive hints, not executable rules. Runtimes own the real detection logic. An event such as `session.rest_suggested` may be compositional; the runtime emits it only after its own conditions are met.

## Token And Rest Signals

Token/quota and rest reminders should not create new required animation rows.

Use:

- `quota.pressure` -> `review`
- `quota.limit` -> `waiting`
- `session.long` -> `review`
- `session.rest_suggested` -> `waiting`

Surface renderers may show compact badges such as `15%`, `5h`, `7d`, or `60m`, but the pet pack only declares semantic event mappings.

`waiting` is intentionally broad. It may mean resource-blocked, interaction-blocked, or approval-blocked. The semantic distinction belongs in `tone`, `reason`, metrics, or a runtime-owned detail surface rather than in extra required animation rows.
