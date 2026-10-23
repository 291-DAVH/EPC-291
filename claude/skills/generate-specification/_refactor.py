#!/usr/bin/env python3
"""
_refactor.py — Renombra todo el framework a kebab-case inglés.
Usa solo rename() (sin copy+delete) para funcionar sin permisos de borrado.
"""
import os
from pathlib import Path

BASE = Path.home() / "mnt/generar-pliego"
TMPL = BASE / "knowledge/templates"

# ── 1. Rename discipline folders (same-level rename = pure rename syscall)
DIR_RENAMES = [
    (TMPL / "bloques",                           TMPL / "electrical"),
    (TMPL / "templates_civil",                   TMPL / "civil"),
    (TMPL / "templates_combate_de_incendios",     TMPL / "fire-suppression"),
    (TMPL / "templates_deteccion_de_incendios",   TMPL / "fire-detection"),
    (TMPL / "templates_hvac",                     TMPL / "hvac"),
    (TMPL / "templates_termomecanica",            TMPL / "thermomechanical"),
    (BASE / "knowledge/extraido",                 BASE / "knowledge/extracted"),
    (BASE / "knowledge/pliegos_armados",          BASE / "knowledge/assembled"),
]

# ── 2. Subdirectory renames (bloques → blocks within each discipline)
# After step 1, civil/bloques → civil/blocks, etc.
SUBDIR_RENAMES = [
    ("civil",               "bloques", "blocks"),
    ("fire-suppression",    "bloques", "blocks"),
    ("fire-detection",      "bloques", "blocks"),
    ("hvac",                "bloques", "blocks"),
    ("thermomechanical",    "bloques", "blocks"),
]

# ── 3. File renames within each discipline folder
# Format: (current_name, new_name)
SHARED_BLOCKS = [
    ("00_DATOS_PROYECTO.md",       "00-project-data.md"),
    ("01_MEMORIA_DESCRIPTIVA.md",  "01-descriptive-report.md"),
    ("02_MARCO_NORMATIVO.md",      "02-standards-codes.md"),
    ("03_INGENIERIA_DETALLE.md",   "03-detail-engineering.md"),
    ("04_CONDICIONES_GENERALES.md","04-general-conditions.md"),
    ("06_PRUEBAS_COMMISSIONING.md","06-testing-commissioning.md"),
    ("07_DOCUMENTACION_ASBUILT.md","07-asbuilt-docs.md"),
    ("08_CAPACITACION.md",         "08-training.md"),
    ("09_RESPONSABILIDADES.md",    "09-responsibilities.md"),
]

DISC_SPECIFIC = {
    "electrical": [
        ("05A_TABLEROS_BT.md",                   "05a-lv-switchboards.md"),
        ("05B_CABLES_CONDUCTORES.md",            "05b-cables-conductors.md"),
        ("05C_BANDEJAS_PORTACABLES.md",          "05c-cable-trays.md"),
        ("05D_CANALIZACIONES_SUBTERRANEAS.md",   "05d-underground-conduits.md"),
        ("05E_PUESTA_A_TIERRA.md",               "05e-grounding.md"),
        ("05F_ILUMINACION.md",                   "05f-lighting.md"),
        ("05G_TOMACORRIENTES.md",                "05g-power-outlets.md"),
        ("05H_MEDIA_TENSION.md",                 "05h-medium-voltage.md"),
    ],
    "civil": [
        ("05A_05A_OBRAS_PRELIMINARES.md",        "05a-preliminary-works.md"),
        ("05B_05B_HORMIGON.md",                  "05b-concrete.md"),
        ("05C_05C_FUNDACIONES.md",               "05c-foundations.md"),
        ("05D_05D_PAVIMENTOS_EXTERIORES.md",     "05d-pavements-exterior.md"),
    ],
    "fire-suppression": [
        ("05A_05A_RED_HIDRAULICA.md",            "05a-hydraulic-network.md"),
        ("05B_05B_ROCIADORES.md",               "05b-sprinklers.md"),
        ("05C_05C_GABINETES_MANGUERAS.md",       "05c-fire-hose-cabinets.md"),
        ("05D_05D_PRUEBAS_INCENDIO.md",          "05d-fire-testing.md"),
    ],
    "fire-detection": [
        ("05A_05A_CENTRAL_DETECCION.md",         "05a-facp.md"),
        ("05B_05B_DISPOSITIVOS_DETECCION.md",    "05b-detection-devices.md"),
        ("05C_05C_CANALIZACIONES_DETECCION.md",  "05c-detection-conduits.md"),
    ],
    "hvac": [
        ("05A_05A_EQUIPOS_HVAC.md",              "05a-hvac-equipment.md"),
        ("05B_05B_DUCTOS_DIFUSORES.md",          "05b-ducts-diffusers.md"),
        ("05C_05C_TABLEROS_HVAC.md",             "05c-hvac-panels.md"),
        ("05D_05D_PRUEBAS_HVAC.md",              "05d-hvac-testing.md"),
    ],
    "thermomechanical": [
        ("05A_05A_VENTILACION_MECANICA.md",      "05a-mechanical-ventilation.md"),
        ("05B_05B_EQUIPOS_TERMOMECANICOS.md",    "05b-thermomechanical-equipment.md"),
    ],
}

# ── 4. Root-level script renames
ROOT_RENAMES = [
    (BASE / "armar_pliego.py",                   BASE / "assemble-spec.py"),
    (TMPL / "TEMPLATE_PLIEGO_ELECTRICO_FORD.md", TMPL / "template-ford-electrical-reference.md"),
]


def safe_rename(src, dst):
    if not src.exists():
        print(f"  SKIP (not found): {src.name}")
        return False
    if dst.exists():
        print(f"  SKIP (dest exists): {dst.name}")
        return False
    src.rename(dst)
    print(f"  ✓ {src.name}  →  {dst.name}")
    return True


print("=" * 60)
print("  STEP 1 — Rename discipline directories")
print("=" * 60)
for src, dst in DIR_RENAMES:
    safe_rename(src, dst)

print("\n" + "=" * 60)
print("  STEP 2 — Rename 'bloques' subdirs to 'blocks'")
print("=" * 60)
for disc, old_sub, new_sub in SUBDIR_RENAMES:
    src = TMPL / disc / old_sub
    dst = TMPL / disc / new_sub
    safe_rename(src, dst)

print("\n" + "=" * 60)
print("  STEP 3 — Rename block files")
print("=" * 60)
for disc, extra_renames in DISC_SPECIFIC.items():
    # Determine blocks directory
    disc_dir = TMPL / disc
    if (disc_dir / "blocks").exists():
        blocks_dir = disc_dir / "blocks"
    elif disc_dir.exists():
        blocks_dir = disc_dir  # electrical has no subdir now
    else:
        print(f"  SKIP discipline {disc}: dir not found")
        continue

    print(f"\n  [{disc}] → {blocks_dir.relative_to(BASE)}")
    all_renames = SHARED_BLOCKS + extra_renames
    for old, new in all_renames:
        safe_rename(blocks_dir / old, blocks_dir / new)

print("\n" + "=" * 60)
print("  STEP 4 — Root-level renames")
print("=" * 60)
for src, dst in ROOT_RENAMES:
    safe_rename(src, dst)

print("\n  Done.\n")
