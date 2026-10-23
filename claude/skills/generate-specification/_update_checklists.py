#!/usr/bin/env python3
"""Updates 00-project-data.md in all disciplines with new kebab-case filenames."""
from pathlib import Path

BASE = Path.home() / "mnt/generar-pliego/knowledge/templates"

DISCIPLINES = {
    "electrical": {
        "label": "Electrical",
        "dir": BASE / "electrical",
        "extra_fields": "| Supply voltage | {{SUPPLY_VOLTAGE}} (e.g.: 380/220 V — 50 Hz) |\n| MV voltage level (if applicable) | {{MV_VOLTAGE}} (e.g.: 13.2 kV) |\n",
        "checklist": [
            ("01", "Descriptive Report",           "01-descriptive-report.md",       "ALWAYS"),
            ("02", "Standards & Codes",             "02-standards-codes.md",           "ALWAYS"),
            ("03", "Detail Engineering",            "03-detail-engineering.md",        "ALWAYS"),
            ("04", "General Conditions",            "04-general-conditions.md",        "ALWAYS"),
            ("05a", "LV Switchboards",              "05a-lv-switchboards.md",          "IF APPLICABLE"),
            ("05b", "Cables & Conductors",          "05b-cables-conductors.md",        "IF APPLICABLE"),
            ("05c", "Cable Trays",                  "05c-cable-trays.md",              "IF APPLICABLE"),
            ("05d", "Underground Conduits / Below Road", "05d-underground-conduits.md","IF APPLICABLE"),
            ("05e", "Grounding",                    "05e-grounding.md",                "IF APPLICABLE"),
            ("05f", "Lighting",                     "05f-lighting.md",                 "IF APPLICABLE"),
            ("05g", "Power Outlets & Services",     "05g-power-outlets.md",            "IF APPLICABLE"),
            ("05h", "Medium Voltage",               "05h-medium-voltage.md",           "IF APPLICABLE"),
            ("06",  "Testing & Commissioning",      "06-testing-commissioning.md",     "ALWAYS"),
            ("07",  "As-Built Documentation",       "07-asbuilt-docs.md",              "ALWAYS"),
            ("08",  "Training",                     "08-training.md",                  "IF APPLICABLE"),
            ("09",  "Responsibilities",             "09-responsibilities.md",          "ALWAYS"),
        ],
    },
    "civil": {
        "label": "Civil",
        "dir": BASE / "civil/blocks",
        "extra_fields": "",
        "checklist": [
            ("01", "Descriptive Report",            "01-descriptive-report.md",        "ALWAYS"),
            ("02", "Standards & Codes",             "02-standards-codes.md",           "ALWAYS"),
            ("03", "Detail Engineering",            "03-detail-engineering.md",        "ALWAYS"),
            ("04", "General Conditions",            "04-general-conditions.md",        "ALWAYS"),
            ("05a", "Preliminary Works / Demolition","05a-preliminary-works.md",       "IF APPLICABLE"),
            ("05b", "Structural Concrete",          "05b-concrete.md",                 "IF APPLICABLE"),
            ("05c", "Foundations",                  "05c-foundations.md",              "IF APPLICABLE"),
            ("05d", "Pavements & Exterior Works",   "05d-pavements-exterior.md",       "IF APPLICABLE"),
            ("06",  "Testing & Commissioning",      "06-testing-commissioning.md",     "ALWAYS"),
            ("07",  "As-Built Documentation",       "07-asbuilt-docs.md",              "ALWAYS"),
            ("08",  "Training",                     "08-training.md",                  "IF APPLICABLE"),
            ("09",  "Responsibilities",             "09-responsibilities.md",          "ALWAYS"),
        ],
    },
    "fire-suppression": {
        "label": "Fire Suppression",
        "dir": BASE / "fire-suppression/blocks",
        "extra_fields": "",
        "checklist": [
            ("01", "Descriptive Report",            "01-descriptive-report.md",        "ALWAYS"),
            ("02", "Standards & Codes",             "02-standards-codes.md",           "ALWAYS"),
            ("03", "Detail Engineering",            "03-detail-engineering.md",        "ALWAYS"),
            ("04", "General Conditions",            "04-general-conditions.md",        "ALWAYS"),
            ("05a", "Hydraulic Fire Network",       "05a-hydraulic-network.md",        "IF APPLICABLE"),
            ("05b", "Sprinkler System",             "05b-sprinklers.md",               "IF APPLICABLE"),
            ("05c", "Fire Hose Cabinets",           "05c-fire-hose-cabinets.md",       "IF APPLICABLE"),
            ("05d", "Fire System Testing",          "05d-fire-testing.md",             "IF APPLICABLE"),
            ("06",  "Testing & Commissioning",      "06-testing-commissioning.md",     "ALWAYS"),
            ("07",  "As-Built Documentation",       "07-asbuilt-docs.md",              "ALWAYS"),
            ("08",  "Training",                     "08-training.md",                  "IF APPLICABLE"),
            ("09",  "Responsibilities",             "09-responsibilities.md",          "ALWAYS"),
        ],
    },
    "fire-detection": {
        "label": "Fire Detection",
        "dir": BASE / "fire-detection/blocks",
        "extra_fields": "",
        "checklist": [
            ("01", "Descriptive Report",            "01-descriptive-report.md",        "ALWAYS"),
            ("02", "Standards & Codes",             "02-standards-codes.md",           "ALWAYS"),
            ("03", "Detail Engineering",            "03-detail-engineering.md",        "ALWAYS"),
            ("04", "General Conditions",            "04-general-conditions.md",        "ALWAYS"),
            ("05a", "FACP / Detection Panel",       "05a-facp.md",                     "IF APPLICABLE"),
            ("05b", "Detection Devices",            "05b-detection-devices.md",        "IF APPLICABLE"),
            ("05c", "Detection Conduits",           "05c-detection-conduits.md",       "IF APPLICABLE"),
            ("06",  "Testing & Commissioning",      "06-testing-commissioning.md",     "ALWAYS"),
            ("07",  "As-Built Documentation",       "07-asbuilt-docs.md",              "ALWAYS"),
            ("08",  "Training",                     "08-training.md",                  "IF APPLICABLE"),
            ("09",  "Responsibilities",             "09-responsibilities.md",          "ALWAYS"),
        ],
    },
    "hvac": {
        "label": "HVAC",
        "dir": BASE / "hvac/blocks",
        "extra_fields": "",
        "checklist": [
            ("01", "Descriptive Report",            "01-descriptive-report.md",        "ALWAYS"),
            ("02", "Standards & Codes",             "02-standards-codes.md",           "ALWAYS"),
            ("03", "Detail Engineering",            "03-detail-engineering.md",        "ALWAYS"),
            ("04", "General Conditions",            "04-general-conditions.md",        "ALWAYS"),
            ("05a", "HVAC Equipment (AHU, splits)","05a-hvac-equipment.md",            "IF APPLICABLE"),
            ("05b", "Ducts & Diffusers",            "05b-ducts-diffusers.md",          "IF APPLICABLE"),
            ("05c", "HVAC Panels & Controls",       "05c-hvac-panels.md",              "IF APPLICABLE"),
            ("05d", "HVAC Testing",                 "05d-hvac-testing.md",             "IF APPLICABLE"),
            ("06",  "Testing & Commissioning",      "06-testing-commissioning.md",     "ALWAYS"),
            ("07",  "As-Built Documentation",       "07-asbuilt-docs.md",              "ALWAYS"),
            ("08",  "Training",                     "08-training.md",                  "IF APPLICABLE"),
            ("09",  "Responsibilities",             "09-responsibilities.md",          "ALWAYS"),
        ],
    },
    "thermomechanical": {
        "label": "Thermomechanical",
        "dir": BASE / "thermomechanical/blocks",
        "extra_fields": "",
        "checklist": [
            ("01", "Descriptive Report",            "01-descriptive-report.md",        "ALWAYS"),
            ("02", "Standards & Codes",             "02-standards-codes.md",           "ALWAYS"),
            ("03", "Detail Engineering",            "03-detail-engineering.md",        "ALWAYS"),
            ("04", "General Conditions",            "04-general-conditions.md",        "ALWAYS"),
            ("05a", "Mechanical Ventilation",       "05a-mechanical-ventilation.md",   "IF APPLICABLE"),
            ("05b", "Thermomechanical Equipment",   "05b-thermomechanical-equipment.md","IF APPLICABLE"),
            ("06",  "Testing & Commissioning",      "06-testing-commissioning.md",     "ALWAYS"),
            ("07",  "As-Built Documentation",       "07-asbuilt-docs.md",              "ALWAYS"),
            ("08",  "Training",                     "08-training.md",                  "IF APPLICABLE"),
            ("09",  "Responsibilities",             "09-responsibilities.md",          "ALWAYS"),
        ],
    },
}


def build_content(label, extra_fields, checklist, blocks_dir):
    header_rows = [
        "| Field | Value |",
        "|---|---|",
        "| Project | {{PROJECT_NAME}} |",
        "| Contract / Tender No. | {{CONTRACT_NO}} |",
        "| Plant / Site | {{PLANT_SITE}} |",
        "| Area / Sector | {{AREA_SECTOR}} |",
    ]
    if extra_fields:
        for row in extra_fields.strip().split("\n"):
            header_rows.append(row)
    header_rows += [
        "| Contracting company | Ford Argentina S.C.A. |",
        "| Site Manager | {{SITE_MANAGER}} |",
        "| Issue date | {{ISSUE_DATE}} |",
        "| Revision | {{REV}} |",
    ]

    checklist_rows = [
        "### Block Checklist — Mark what applies to this project",
        "",
        "> _Check [x] each block to include. **ALWAYS** blocks are required in every spec._",
        "",
        "| Block | Description | File | Usage | Include? |",
        "|-------|-------------|------|-------|:--------:|",
    ]
    for num, desc, fname, usage in checklist:
        exists = (blocks_dir / fname).exists()
        mark = "[x]" if usage == "ALWAYS" else "[ ]"
        usage_fmt = "**ALWAYS**" if usage == "ALWAYS" else "IF APPLICABLE"
        warn = "" if exists else " ⚠"
        checklist_rows.append(
            f"| {num} | {desc} | `{fname}`{warn} | {usage_fmt} | {mark} |"
        )

    lines = [
        "<!-- BLOCK: 00 | USAGE: ALWAYS -->",
        "",
        "## BLOCK 00 — PROJECT DATA",
        f"> _Discipline: {label} — Fill in all fields before assembling the spec._",
        "",
    ] + header_rows + [
        "",
        "---",
        "",
    ] + checklist_rows + [
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


for disc_key, disc in DISCIPLINES.items():
    target = disc["dir"] / "00-project-data.md"
    content = build_content(disc["label"], disc["extra_fields"], disc["checklist"], disc["dir"])
    target.write_text(content, encoding="utf-8")
    print(f"✓ {disc['label']:25s} → {target.relative_to(Path.home() / 'mnt/generar-pliego')}")

print("\nAll 00-project-data.md files updated.")
