"""CAL-022 · aea_catalog — Catálogo único de fórmulas AEA (sin repeticiones) para scripts y skills.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Índice de TODAS las funciones públicas de los módulos `aea_*` y de los módulos previos que
    cubren fórmulas equivalentes, con norma de origen, para que un script o skill localice la
    fórmula sin duplicarla. Se genera por introspección (la fuente de verdad es el docstring
    de cada función), de modo que no puede quedar desactualizado.

USO
    python3 -B aea_catalog.py --md        # tabla Markdown (FORMULAS_AEA.md)
    python3 -B aea_catalog.py --json      # formulas_aea.json
    python3 -B aea_catalog.py --buscar kappa
    from epc_calc.aea_catalog import catalogo, buscar

NORMA DE REFERENCIA
    Ver el campo `norma` de cada módulo.  [VERIFICAR]
"""
import importlib
import inspect
import json
import sys

__version__ = "0.1.0"

#: módulo -> (dominio, norma de origen)
MODULES = {
    "aea_demand": ("Demanda y corrientes de proyecto", "AEA 771 §9, 770 §8"),
    "aea_voltage_drop": ("Caída de tensión (tablas, GDC, límites)", "AEA 771 §19.7, 770 §15.6"),
    "aea_earthing": ("Puesta a tierra, diferenciales y electrodos", "AEA 771 §3, §18, Anexo C"),
    "aea_conductors": ("Conductores: secciones, sobrecarga, armónicos", "AEA 771 §13, §16, §19; 770 §11"),
    "aea_panel_thermal": ("Verificación térmica de tableros", "AEA 770 Anexo B; 771 Anexo H"),
    "aea_icc_factors": ("Factores K de impedancia (Icc)", "AEA IT 90909-1 §2.1–2.2, §2.3, §2.9"),
    "aea_icc_decay": ("κ, μ, λ, q, m, n (Icc)", "AEA IT 90909-1 §2.4–2.8"),
    "aea_special_locations": ("Baños (701) y vehículos eléctricos (722)", "AEA 701, 722"),
    "aea_pipeline": ("Excel de circuitos → dimensionado → JSON", "AEA 771 §13, §16, §19.7"),
    "aea_tables": ("Tablas de capacidad de cables y factores de corrección", "AEA 771 §16 (771.16.I a XI)"),
    "aea_ampacity": ("Capacidad de conducción por aislación, material y método", "AEA 771 §16, §13; IEC 60228"),
    "aea_rules": ("Reglas de ingeniería (alturas, reservas, llenado, circuitos)", "AEA 771, 770, 701, 722"),
    "aea_protection": ("Protección contra contactos indirectos (TN/TT/IT) e I2", "AEA 4-41, 4-43, 771.18"),
    "aea_feeder_report": ("Memoria de cálculo y síntesis del alimentador principal", "AEA 771 §13, §16, §19.7, §18"),
    "aea_export": ("Exportación del cálculo a JSON (sin PDF)", "Contrato con sld-generator"),
}
#: Funciones equivalentes que viven en módulos anteriores (no se duplican).
PREVIOS = {
    "voltage_drop.caida_tension": "ΔU = k·I·L·(R cosφ + X senφ)",
    "short_circuit.factor_c": "factor c", "short_circuit.impedancia_red": "Z_Qt",
    "short_circuit.impedancia_transformador": "Z_T, R_T, X_T",
    "short_circuit.factor_kt": "K_T [65]", "short_circuit.factor_kappa": "κ [68]",
    "short_circuit.corriente_pico": "i_p [67]", "short_circuit.aporte_motor": "I''kM [109]",
    "cable_thermal.seccion_minima_mm2": "S ≥ I√t/k", "cable_thermal.verificar_i2t": "k²S² ≥ I²t",
    "current_and_loads.corriente_monofasica": "I monofásica",
    "current_and_loads.corriente_trifasica": "I trifásica",
}


def catalogo():
    """Lista de dicts {id, modulo, funcion, dominio, norma, resumen, firma}."""
    filas = []
    for nombre, (dominio, norma) in MODULES.items():
        mod = importlib.import_module(f"epc_calc.{nombre}")
        for fn, f in inspect.getmembers(mod, inspect.isfunction):
            if fn.startswith("_") or f.__module__ != f"epc_calc.{nombre}":
                continue
            doc = (inspect.getdoc(f) or "").splitlines()
            filas.append({"id": f"{nombre}.{fn}", "modulo": nombre, "funcion": fn, "dominio": dominio,
                          "norma": norma, "resumen": doc[0] if doc else "",
                          "firma": f"{fn}{inspect.signature(f)}"})
    return filas


def buscar(texto):
    """Filas cuyo id, resumen o dominio contienen `texto` (sin distinguir mayúsculas)."""
    t = texto.lower()
    return [r for r in catalogo() if t in (r["id"] + " " + r["resumen"] + " " + r["dominio"]).lower()]


def a_markdown():
    out = ["# Catálogo de fórmulas AEA (generado por `aea_catalog.py`)", ""]
    actual = None
    for r in catalogo():
        if r["modulo"] != actual:
            actual = r["modulo"]
            out += ["", f"## `{actual}` — {r['dominio']}", f"*Norma:* {r['norma']}", "",
                    "| Función | Fórmula / descripción |", "|---|---|"]
        out.append(f"| `{r['firma']}` | {r['resumen'].replace('|', '/')} |".replace("\n", " "))
    out += ["", "## Ya existentes (no duplicar)", "", "| Función | Fórmula |", "|---|---|"]
    out += [f"| `{k}` | {v} |" for k, v in PREVIOS.items()]
    return "\n".join(out) + "\n"


def main(argv):
    if "--json" in argv:
        print(json.dumps({"version": __version__, "formulas": catalogo(), "previos": PREVIOS},
                         ensure_ascii=False, indent=2))
    elif "--md" in argv:
        print(a_markdown(), end="")
    elif "--buscar" in argv:
        for r in buscar(argv[argv.index("--buscar") + 1]):
            print(f"{r['id']}: {r['resumen']}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
