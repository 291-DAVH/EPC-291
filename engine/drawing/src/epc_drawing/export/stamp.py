"""Stamp a DXF master before it leaves the workspace: the delivered copy records its issue data in the drawing itself.

  python -m epc_drawing.export.stamp <master.dxf> <stamped.dxf> KEY=VALUE [KEY=VALUE ...]

The master is never modified. The values go into the DXF header as custom properties (CUSTOMPROPERTY pairs, shown by
CAD programs under "Drawing properties"), e.g. EPC_CLIENT_REV, EPC_INTERNAL_REV, EPC_TRANSMITTAL, EPC_SOURCE_SHA256,
EPC_ENGINE_VERSION, EPC_PLUGINS.
"""
import hashlib
import sys
from pathlib import Path
from typing import Dict

PREFIX = "EPC_"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp_dxf(src: Path, dst: Path, props: Dict[str, str]) -> Path:
    import ezdxf
    doc = ezdxf.readfile(str(src))
    cv = doc.header.custom_vars
    for tag in [t for t, _ in cv if t.startswith(PREFIX)]:          # re-stamping replaces, never duplicates
        cv.remove(tag)
    cv.append(PREFIX + "SOURCE_SHA256", sha256_of(src))
    for k, v in props.items():
        cv.append(k if k.startswith(PREFIX) else PREFIX + k, str(v))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(dst))
    return Path(dst)


def read_stamp(path: Path) -> Dict[str, str]:
    import ezdxf
    return {t: v for t, v in ezdxf.readfile(str(path)).header.custom_vars if t.startswith(PREFIX)}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    kv = dict(a.split("=", 1) for a in sys.argv[3:])
    print("OK", stamp_dxf(Path(sys.argv[1]), Path(sys.argv[2]), kv))
