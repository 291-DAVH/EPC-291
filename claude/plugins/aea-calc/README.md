# aea-calc

Low-voltage installation sizing (AEA 90364 / IEC 60364): design current, protection, cable section, voltage drop, short-circuit. Outputs a calculation JSON plus Calculation Memo and Project Synthesis.

- Version: 1.6.0 (calc)
- Entitlement: `feature.calc.electrical`
- Python: openpyxl>=3.1

## Requires
- none

## Skills
- [`size-feeder`](../../skills/size-feeder/SKILL.md) (owner)
- [`dimension-installation`](../../skills/dimension-installation/SKILL.md) (owner)
- [`write-calculation-memo`](../../skills/write-calculation-memo/SKILL.md) (owner)
- [`write-memo-summary`](../../skills/write-memo-summary/SKILL.md) (owner)

## Outputs
- `.json`: internal
- `.md`: internal

See `plugin.json` for the full manifest. Legacy origin: `elec-calc-generator`.
