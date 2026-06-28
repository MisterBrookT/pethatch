# Runtime Adapters

PetHatch is a pet-pack market, not a single runtime.

## Compatible Consumers

- Codex-compatible pet settings: reads `pet.json` and `spritesheet.webp`.
- OpenPets: reads Codex Pets bundles and can map runtime notifications to the 9-row atlas.
- Petdex-like galleries: can index `pet.json`, preview images, tags, and license data.
- Kaji: can emit quota and system events that map to PetHatch event extensions.
- Agent desktop pets: can use the same pack as their visual theme.

## Resolve An Event

PetHatch packs declare optional `events`. A runtime can resolve an event to an animation:

```bash
python3 examples/event-resolver.py pets/xiaochai/pet.json quota.limit
```

Output:

```json
{
  "animation": "waiting",
  "tone": "critical",
  "threshold": ">=95% used or <=15% remaining"
}
```

## Generic Event Mapping Example

A runtime may have its own internal signal names and metrics:

```json
{
  "state": "waiting",
  "internalReason": "provider_window_nearly_exhausted",
  "summary": "A provider quota window is under 15%.",
  "metrics": {
    "provider": "example-provider",
    "remainingFraction": 0.15
  }
}
```

The adapter should translate that runtime-specific signal into a PetHatch event:

```json
{
  "event": "quota.limit",
  "animation": "waiting",
  "tone": "critical"
}
```

Kaji can do this translation for quota and session metrics, but the pack remains useful without Kaji.

See also:

- `examples/kaji-quota-event.json`
- `examples/openpets-notify.json`
