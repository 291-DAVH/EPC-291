<div align="center">

<img src="assets/logo.png" alt="IEC 60617 Symbol Library" width="420"/>

# ⚡ IEC 60617 Symbol Library

**Símbolos eléctricos IEC 60617 en SVG editable y DXF para CAD.**
Unifilares (SLD) y multifilares (MLD), baja y media tensión, con criterios IRAM 4502 / 4503.

[![Version](https://img.shields.io/badge/version-0.4.15-1f6feb?style=for-the-badge)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-2ea44f?style=for-the-badge)](LICENSE)
[![IEC 60617](https://img.shields.io/badge/standard-IEC%2060617-0ea5e9?style=for-the-badge)](assets/)
[![IRAM](https://img.shields.io/badge/IRAM-4502%20%7C%204503-64748b?style=for-the-badge)](assets/)
[![Symbols](https://img.shields.io/badge/symbols-221-f0abfc?style=for-the-badge)](#-qué-incluye)
[![SVG](https://img.shields.io/badge/format-SVG-f97316?style=for-the-badge)](#-qué-incluye)
[![DXF](https://img.shields.io/badge/CAD-DXF-8b5cf6?style=for-the-badge)](#-qué-incluye)

[Contribuir](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Catálogo Excel](src/catalogo_simbolos.xlsx) · [Reportar un problema](.github/ISSUE_TEMPLATE.md)

</div>

---

## ✨ Qué es

Una biblioteca de símbolos listos para usar en diagramas eléctricos. Cada símbolo existe en dos formatos:

- **`.svg`** — vectorial, editable a mano, con puertos de conexión, rótulos variables (`{tag}`, `{rated_current}`…) y marcas de borne.
- **`.dxf`** — generado a partir del SVG, con bloque nombrado igual que el archivo y atributos listos para CAD.

El resultado: un mismo símbolo sirve para el diseño en el editor vectorial y para el plano en AutoCAD / DraftSight / LibreCAD.

## 🧭 Qué incluye

| Biblioteca | Carpeta | Símbolos | Estado |
|---|---|---:|---|
| Unifilar baja tensión | `src/sld-lv-symbol/` | 82 | ✅ |
| Multifilar baja tensión | `src/mld-lv-symbol/` | 102 | ✅ |
| Unifilar media tensión | `src/sld-mv-symbol/` | 37 | ✅ |
| Multifilar media tensión | `src/mld-mv-symbol/` | 0 | 🚧 pendiente |

Familias destacadas: **ACB** y **MCCB** en todas sus variantes (básico, drawout, LSIG, motorizado), **contactores**, **fusibles**, **seccionadores**, **ATS**, **UPS**, **variadores**, **medidores**, **celdas MT** y **tramos de cable**.

Todos los multifilares se dibujan con **paso entre polos de 10 mm** y **retícula de 2,5 mm**, así que 1P, 2P, 3P y 4P quedan alineados en cualquier plano.

## 🚀 Uso rápido

```bash
# Clonar
git clone https://github.com/davillenah/291_E_IEC60617_Symbols_Generator.git
cd 291_E_IEC60617_Symbols_Generator

# Generar el DXF de un símbolo
python tools/svg2dxf_all.py src/mld-lv-symbol/291_E_LV_MLD_IEC60617_acb_2p.svg src/mld-lv-symbol/291_E_LV_MLD_IEC60617_acb_2p.dxf

# Empaquetar el plugin
python tools/build_pkg.py /ruta/absoluta/plugin/iec60617-symbol-generator /ruta/absoluta/src/catalogo_simbolos.xlsx /ruta/absoluta/plugin/iec60617-symbol-generator.plugin
```

Los catálogos JSON (uno por biblioteca) describen cada símbolo: `id`, archivo, puertos, parámetros y equivalencias SLD ↔ MLD.

## 🗂️ Estructura

```
.
├── assets/            Referencia normativa IEC 60617 y logo
├── feedback/          Comentarios y propuestas de mejora
├── plugin/            Manifiesto del plugin y paquete .plugin
├── src/
│   ├── sld-lv-symbol/   unifilares BT   (SVG + DXF + _catalog.json)
│   ├── sld-mv-symbol/   unifilares MT   (SVG + DXF + _catalog.json)
│   ├── mld-lv-symbol/   multifilares BT (SVG + DXF + _catalog.json)
│   ├── mld-mv-symbol/   multifilares MT (pendiente)
│   └── catalogo_simbolos.xlsx           catálogo visual único
└── tools/             Scripts de build (SVG→DXF, paquete, catálogo)
```

## 🛠️ Cómo se trabaja

1. Los **SVG editados a mano no se modifican por script**: sólo se regenera su DXF.
2. Un cambio en un **unifilar se refleja en su multifilar**.
3. Cada símbolo se valida: XML bien formado, bloque DXF con el nombre del archivo y referencias del catálogo resueltas.

Detalles completos en [CONTRIBUTING.md](CONTRIBUTING.md).

## 🤝 Contribuir

¡Bienvenidas las mejoras! Lee [CONTRIBUTING.md](CONTRIBUTING.md), abre una rama, y envía un Pull Request con la [plantilla](.github/pull_request_template.md).

## 📜 Licencia

Distribuido bajo licencia **MIT**. Puedes copiar, modificar y usar el material; conserva el aviso de copyright y el crédito al autor. Ver [LICENSE](LICENSE).

<div align="center">

<sub>Hecho con ⚡ para ingenieros que dibujan tableros.</sub>

</div>
