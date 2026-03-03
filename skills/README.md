# Skills Folder

Organize skills by audience/type:

```text
skills/
  general/
    your-skill/
      SKILL.md
  economists/
    your-skill/
      SKILL.md
```

You can also keep uncategorized skills at:

```text
skills/your-skill/SKILL.md
```

## Rules

- Every installable skill must have `SKILL.md`.
- Skill folder names must be globally unique across all types.
- Keep secrets out of skills.

## Selection Examples

List catalog:

```bash
./scripts/bootstrap.sh --list
```

Install one type:

```bash
./scripts/bootstrap.sh --target both --scope global --type economists
```

Install two explicit skills:

```bash
./scripts/bootstrap.sh --target both --scope global --skills skill-a,skill-b
```
