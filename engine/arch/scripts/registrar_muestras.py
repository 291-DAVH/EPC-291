"""Registro de muestras de aprendizaje por hash (SHA-256): cada archivo de `samples/` se estudia una sola vez.

Uso:
  python scripts/registrar_muestras.py                 # registra archivos nuevos y lista los pendientes
  python scripts/registrar_muestras.py --estudiado NOMBRE_O_HASH   # marca un archivo como estudiado

El registro vive en `samples/registro.json`, que nunca se sube a git (la carpeta `samples/` está en .gitignore).
Como la clave es el contenido, un archivo renombrado o copiado no se vuelve a estudiar.
"""
import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MUESTRAS = RAIZ / "samples"
REGISTRO = MUESTRAS / "registro.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def cargar() -> dict:
    if REGISTRO.exists():
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    return {}


def guardar(reg: dict) -> None:
    REGISTRO.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def archivos() -> list:
    return sorted(p for p in MUESTRAS.rglob("*") if p.is_file() and p != REGISTRO)


def escanear() -> int:
    reg = cargar()
    nuevos = 0
    for p in archivos():
        h = sha256(p)
        if h not in reg:
            reg[h] = {"ruta": p.relative_to(MUESTRAS).as_posix(), "tamano": p.stat().st_size,
                      "registrado": dt.date.today().isoformat(), "estudiado": False}
            nuevos += 1
        else:
            reg[h]["ruta"] = p.relative_to(MUESTRAS).as_posix()
    guardar(reg)
    pendientes = [(h, v) for h, v in reg.items() if not v["estudiado"]]
    print(f"Nuevos registrados: {nuevos}. Pendientes de estudiar: {len(pendientes)}")
    for h, v in pendientes:
        print(f"  PENDIENTE  {v['ruta']}  ({v['tamano']} bytes)  {h[:12]}")
    return 0


def marcar(clave: str) -> int:
    reg = cargar()
    for h, v in reg.items():
        if h == clave or h.startswith(clave) or v["ruta"] == clave or Path(v["ruta"]).name == clave:
            v["estudiado"] = True
            v["estudiado_el"] = dt.date.today().isoformat()
            guardar(reg)
            print(f"Marcado como estudiado: {v['ruta']}")
            return 0
    print(f"No encontrado en el registro: {clave}", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--estudiado", metavar="NOMBRE_O_HASH", help="marca un archivo como ya estudiado")
    a = ap.parse_args()
    MUESTRAS.mkdir(exist_ok=True)
    return marcar(a.estudiado) if a.estudiado else escanear()


if __name__ == "__main__":
    sys.exit(main())
