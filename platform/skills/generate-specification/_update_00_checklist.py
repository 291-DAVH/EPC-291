#!/usr/bin/env python3
from pathlib import Path

BASE = Path.home() / "mnt/generar-pliego/knowledge/templates"

DISCIPLINES = {
    "bloques": {
        "label": "Eléctrica",
        "campos_extra": "| Tensión de alimentación | {{TENSION_ALIMENTACION}} (ej.: 380/220 V — 50 Hz) |\n| Nivel de tensión MT (si aplica) | {{TENSION_MT}} (ej.: 13,2 kV) |\n",
        "checklist": [
            ("01",  "Memoria Descriptiva",            "01_MEMORIA_DESCRIPTIVA.md",             "SIEMPRE"),
            ("02",  "Marco Normativo",                "02_MARCO_NORMATIVO.md",                  "SIEMPRE"),
            ("03",  "Ingeniería de Detalle",          "03_INGENIERIA_DETALLE.md",               "SIEMPRE"),
            ("04",  "Condiciones Generales",          "04_CONDICIONES_GENERALES.md",            "SIEMPRE"),
            ("05A", "Tableros de baja tensión",       "05A_TABLEROS_BT.md",                     "SI APLICA"),
            ("05B", "Cables y conductores",           "05B_CABLES_CONDUCTORES.md",              "SI APLICA"),
            ("05C", "Bandejas porta cables",          "05C_BANDEJAS_PORTACABLES.md",            "SI APLICA"),
            ("05D", "Canalizaciones / bajo calzada",  "05D_CANALIZACIONES_SUBTERRANEAS.md",     "SI APLICA"),
            ("05E", "Puesta a tierra",                "05E_PUESTA_A_TIERRA.md",                 "SI APLICA"),
            ("05F", "Iluminación",                    "05F_ILUMINACION.md",                     "SI APLICA"),
            ("05G", "Tomacorrientes y servicios",     "05G_TOMACORRIENTES.md",                  "SI APLICA"),
            ("05H", "Media tensión",                  "05H_MEDIA_TENSION.md",                   "SI APLICA"),
            ("06",  "Pruebas y commissioning",        "06_PRUEBAS_COMMISSIONING.md",            "SIEMPRE"),
            ("07",  "Documentación as-built",         "07_DOCUMENTACION_ASBUILT.md",            "SIEMPRE"),
            ("08",  "Capacitación",                   "08_CAPACITACION.md",                     "SI APLICA"),
            ("09",  "Responsabilidades",              "09_RESPONSABILIDADES.md",                "SIEMPRE"),
        ],
    },
    "templates_civil": {
        "label": "Civil",
        "campos_extra": "",
        "checklist": [
            ("01",  "Memoria Descriptiva",            "01_MEMORIA_DESCRIPTIVA.md",              "SIEMPRE"),
            ("02",  "Marco Normativo",                "02_MARCO_NORMATIVO.md",                  "SIEMPRE"),
            ("03",  "Ingeniería de Detalle",          "03_INGENIERIA_DETALLE.md",               "SIEMPRE"),
            ("04",  "Condiciones Generales",          "04_CONDICIONES_GENERALES.md",            "SIEMPRE"),
            ("05A", "Obras preliminares / demolición","05A_05A_OBRAS_PRELIMINARES.md",           "SI APLICA"),
            ("05B", "Hormigón estructural",           "05B_05B_HORMIGON.md",                    "SI APLICA"),
            ("05C", "Fundaciones",                    "05C_05C_FUNDACIONES.md",                 "SI APLICA"),
            ("05D", "Pavimentos y exteriores",        "05D_05D_PAVIMENTOS_EXTERIORES.md",       "SI APLICA"),
            ("06",  "Pruebas y commissioning",        "06_PRUEBAS_COMMISSIONING.md",            "SIEMPRE"),
            ("07",  "Documentación as-built",         "07_DOCUMENTACION_ASBUILT.md",            "SIEMPRE"),
            ("08",  "Capacitación",                   "08_CAPACITACION.md",                     "SI APLICA"),
            ("09",  "Responsabilidades",              "09_RESPONSABILIDADES.md",                "SIEMPRE"),
        ],
    },
    "templates_combate_de_incendios": {
        "label": "Protección Contra Incendios",
        "campos_extra": "",
        "checklist": [
            ("01",  "Memoria Descriptiva",            "01_MEMORIA_DESCRIPTIVA.md",              "SIEMPRE"),
            ("02",  "Marco Normativo",                "02_MARCO_NORMATIVO.md",                  "SIEMPRE"),
            ("03",  "Ingeniería de Detalle",          "03_INGENIERIA_DETALLE.md",               "SIEMPRE"),
            ("04",  "Condiciones Generales",          "04_CONDICIONES_GENERALES.md",            "SIEMPRE"),
            ("05A", "Red hidráulica contra incendios","05A_05A_RED_HIDRAULICA.md",               "SI APLICA"),
            ("05B", "Sistema de rociadores",          "05B_05B_ROCIADORES.md",                  "SI APLICA"),
            ("05C", "Gabinetes y mangueras",          "05C_05C_GABINETES_MANGUERAS.md",         "SI APLICA"),
            ("05D", "Pruebas específicas CI",         "05D_05D_PRUEBAS_INCENDIO.md",            "SI APLICA"),
            ("06",  "Pruebas y commissioning",        "06_PRUEBAS_COMMISSIONING.md",            "SIEMPRE"),
            ("07",  "Documentación as-built",         "07_DOCUMENTACION_ASBUILT.md",            "SIEMPRE"),
            ("08",  "Capacitación",                   "08_CAPACITACION.md",                     "SI APLICA"),
            ("09",  "Responsabilidades",              "09_RESPONSABILIDADES.md",                "SIEMPRE"),
        ],
    },
    "templates_deteccion_de_incendios": {
        "label": "Detección de Incendios",
        "campos_extra": "",
        "checklist": [
            ("01",  "Memoria Descriptiva",            "01_MEMORIA_DESCRIPTIVA.md",              "SIEMPRE"),
            ("02",  "Marco Normativo",                "02_MARCO_NORMATIVO.md",                  "SIEMPRE"),
            ("03",  "Ingeniería de Detalle",          "03_INGENIERIA_DETALLE.md",               "SIEMPRE"),
            ("04",  "Condiciones Generales",          "04_CONDICIONES_GENERALES.md",            "SIEMPRE"),
            ("05A", "Central de detección / FACP",   "05A_05A_CENTRAL_DETECCION.md",           "SI APLICA"),
            ("05B", "Dispositivos de detección",      "05B_05B_DISPOSITIVOS_DETECCION.md",      "SI APLICA"),
            ("05C", "Canalizaciones de detección",    "05C_05C_CANALIZACIONES_DETECCION.md",    "SI APLICA"),
            ("06",  "Pruebas y commissioning",        "06_PRUEBAS_COMMISSIONING.md",            "SIEMPRE"),
            ("07",  "Documentación as-built",         "07_DOCUMENTACION_ASBUILT.md",            "SIEMPRE"),
            ("08",  "Capacitación",                   "08_CAPACITACION.md",                     "SI APLICA"),
            ("09",  "Responsabilidades",              "09_RESPONSABILIDADES.md",                "SIEMPRE"),
        ],
    },
    "templates_hvac": {
        "label": "HVAC",
        "campos_extra": "",
        "checklist": [
            ("01",  "Memoria Descriptiva",            "01_MEMORIA_DESCRIPTIVA.md",              "SIEMPRE"),
            ("02",  "Marco Normativo",                "02_MARCO_NORMATIVO.md",                  "SIEMPRE"),
            ("03",  "Ingeniería de Detalle",          "03_INGENIERIA_DETALLE.md",               "SIEMPRE"),
            ("04",  "Condiciones Generales",          "04_CONDICIONES_GENERALES.md",            "SIEMPRE"),
            ("05A", "Equipos HVAC (UTA, splits, etc.)","05A_05A_EQUIPOS_HVAC.md",              "SI APLICA"),
            ("05B", "Ductos y difusores",             "05B_05B_DUCTOS_DIFUSORES.md",            "SI APLICA"),
            ("05C", "Tableros y control HVAC",        "05C_05C_TABLEROS_HVAC.md",               "SI APLICA"),
            ("05D", "Pruebas específicas HVAC",       "05D_05D_PRUEBAS_HVAC.md",                "SI APLICA"),
            ("06",  "Pruebas y commissioning",        "06_PRUEBAS_COMMISSIONING.md",            "SIEMPRE"),
            ("07",  "Documentación as-built",         "07_DOCUMENTACION_ASBUILT.md",            "SIEMPRE"),
            ("08",  "Capacitación",                   "08_CAPACITACION.md",                     "SI APLICA"),
            ("09",  "Responsabilidades",              "09_RESPONSABILIDADES.md",                "SIEMPRE"),
        ],
    },
    "templates_termomecanica": {
        "label": "Termomecánica",
        "campos_extra": "",
        "checklist": [
            ("01",  "Memoria Descriptiva",            "01_MEMORIA_DESCRIPTIVA.md",              "SIEMPRE"),
            ("02",  "Marco Normativo",                "02_MARCO_NORMATIVO.md",                  "SIEMPRE"),
            ("03",  "Ingeniería de Detalle",          "03_INGENIERIA_DETALLE.md",               "SIEMPRE"),
            ("04",  "Condiciones Generales",          "04_CONDICIONES_GENERALES.md",            "SIEMPRE"),
            ("05A", "Ventilación mecánica",           "05A_05A_VENTILACION_MECANICA.md",        "SI APLICA"),
            ("05B", "Equipos termomecánicos",         "05B_05B_EQUIPOS_TERMOMECANICOS.md",      "SI APLICA"),
            ("06",  "Pruebas y commissioning",        "06_PRUEBAS_COMMISSIONING.md",            "SIEMPRE"),
            ("07",  "Documentación as-built",         "07_DOCUMENTACION_ASBUILT.md",            "SIEMPRE"),
            ("08",  "Capacitación",                   "08_CAPACITACION.md",                     "SI APLICA"),
            ("09",  "Responsabilidades",              "09_RESPONSABILIDADES.md",                "SIEMPRE"),
        ],
    },
}


def build_content(label, campos_extra, checklist):
    header_rows = [
        "| Campo | Valor |",
        "|---|---|",
        "| Proyecto | {{NOMBRE_PROYECTO}} |",
        "| Número de Contrato / Licitación | {{NRO_CONTRATO}} |",
        "| Planta / Sitio | {{PLANTA_SITIO}} |",
        "| Área / Sector | {{AREA_SECTOR}} |",
    ]
    if campos_extra:
        for row in campos_extra.strip().split("\n"):
            header_rows.append(row)
    header_rows += [
        "| Empresa contratante | Ford Argentina S.C.A. |",
        "| Dirección de Obra | {{NOMBRE_DO}} |",
        "| Fecha de emisión | {{FECHA_EMISION}} |",
        "| Revisión | {{REV}} |",
    ]

    checklist_rows = [
        "### Checklist de Bloques — Marcar lo que aplica al proyecto",
        "",
        "> _Tildar [x] los bloques a incluir. Los marcados **SIEMPRE** van en todos los pliegos._",
        "",
        "| Bloque | Descripción | Archivo | Uso | ¿Incluir? |",
        "|--------|-------------|---------|-----|:---------:|",
    ]
    for num, desc, fname, uso in checklist:
        if uso == "SIEMPRE":
            check = "[x]"
            uso_fmt = "**SIEMPRE**"
        else:
            check = "[ ]"
            uso_fmt = "SI APLICA"
        checklist_rows.append(f"| {num} | {desc} | `{fname}` | {uso_fmt} | {check} |")

    lines = [
        "<!-- BLOQUE: 00 | USO: SIEMPRE -->",
        "",
        f"## BLOQUE 00 — DATOS DEL PROYECTO",
        f"> _Disciplina: {label} — Completar todos los campos antes de armar el pliego._",
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


for folder_key, disc in DISCIPLINES.items():
    if folder_key == "bloques":
        target = BASE / "bloques" / "00_DATOS_PROYECTO.md"
    else:
        target = BASE / folder_key / "bloques" / "00_DATOS_PROYECTO.md"

    content = build_content(disc["label"], disc["campos_extra"], disc["checklist"])
    target.write_text(content, encoding="utf-8")
    print(f"✓ {disc['label']:40s} → {target.relative_to(BASE)}")

print("\nTodos los BLOQUE 00 actualizados con checklist.")
