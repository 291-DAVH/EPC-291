# epc_receptacles

Receptacles engine of EPC-291. From a JSON document with socket outlets and rectangular rooms it says how many outlets each room needs for its use, where they go along the walls, whether their mounting height complies and what they load. Pure Python, no third-party dependencies, no web, no database.

## What it does

| Step | Method | Source |
|---|---|---|
| Outlets needed | by the use of the room: one per `per_m2` of area, one per `per_m` of perimeter or a fixed number, never fewer than the `min` of the use; the person may fix the count | `data/uses.json` (typical values to verify; the warehouse perimeter rule comes from AEA 90364-7-771) |
| Layout | equal shares of the perimeter walked south, east, north, west; each outlet on its wall, moved `corner_clearance_m` away from a corner | `layout.py` |
| Mounting height | lower edge of the box above the floor, by section of the norm (771 premises, 770 housing) and in wet rooms | `data/uses.json` `mounting`, rules `tomacorrientes.altura_arista_inferior_*` |
| Load and circuits | outlets × power of the outlet; circuits = outlets / the limit of the family (TUG, TUE) | `data/uses.json` `circuits` |
| Drawn outlets | with `positions` the room is checked as drawn: they are counted and compared with what is needed | `pipeline.py` |

Every estimate comes with a `reason`, a `confidence` and a `source`. The numbers a norm decides are in `data/`, never in the code: they are the **typical values to verify** that the norms review of the platform shows to be confirmed once.

## How it is used

```python
import epc_receptacles

result = epc_receptacles.run(document)       # dict, JSON str or bytes
data = result.as_dict()                      # stable JSON-serialisable dict
```

```
python -m epc_receptacles INPUT.json --out DIR [--norm 771|770]
```

Exit code 0 = ok (writes `DIR/<stem>.receptacles.json`), 1 = `ERROR …` on stderr. It writes only inside `--out`. `examples/office.json` is a complete document; `schema/` has the input and output contracts.

## Depends on

Nothing. The platform (`backend/src/epc/modules/receptacles`) calls it in process.

## Known limits

- Rooms are rectangles; the platform sends the bounding box of any other outline and says so.
- The layout does not know where the doors, the furniture or the desks are: it spreads the outlets evenly along the walls. Move them on the plan afterwards.
- The counts per use are typical values, not the text of the norm, except where the `source` says a rule of AEA 90364. Confirm them in the norms review before issuing.
- Special-use outlets (TUE) are placed like the others; each one is its own circuit.
