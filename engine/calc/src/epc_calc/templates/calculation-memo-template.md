# MEMORIA DE CÁLCULOS ELÉCTRICOS
## [NOMBRE DEL PROYECTO]

**Proyecto:** [Nombre del proyecto / obra]
**Dirección:** [Dirección completa]
**Comitente:** [Nombre del comitente / propietario]
**Profesional Responsable:** [Nombre, matrícula, COPIME/COPIBA/COPINA]
**Fecha de emisión:** [DD/MM/AAAA]
**Revisión:** [Rev. 0 / Rev. A / etc.]

---

## ÍNDICE

1. [Objeto y alcance](#1-objeto-y-alcance)
2. [Datos de la instalación](#2-datos-de-la-instalación)
3. [Referencias normativas](#3-referencias-normativas)
4. [Esquema de conexión a tierra](#4-esquema-de-conexión-a-tierra)
5. [Cargas y demanda de potencia](#5-cargas-y-demanda-de-potencia)
6. [Corrientes de cortocircuito](#6-corrientes-de-cortocircuito)
7. [Dimensionamiento de conductores BT](#7-dimensionamiento-de-conductores-bt)
8. [Protecciones BT](#8-protecciones-bt)
9. [Caídas de tensión](#9-caídas-de-tensión)
10. [Canalizaciones](#10-canalizaciones)
11. [Tableros eléctricos](#11-tableros-eléctricos)
12. [Cableado MT](#12-cableado-mt) *(completar si aplica)*
13. [Protecciones MT](#13-protecciones-mt) *(completar si aplica)*
14. [Sistema de puesta a tierra](#14-sistema-de-puesta-a-tierra)
15. [Verificaciones finales](#15-verificaciones-finales)
16. [Conclusiones](#16-conclusiones)
17. [Anexos](#17-anexos)

---

## 1. OBJETO Y ALCANCE

**Objeto:**
La presente Memoria de Cálculos tiene por objeto justificar el dimensionamiento de la
instalación eléctrica del inmueble indicado, verificando el cumplimiento de las normas
y reglamentaciones vigentes.

**Alcance:**
[Describir qué incluye la memoria: instalación BT de vivienda, subestación transformadora,
línea MT de alimentación, sistema de puesta a tierra, etc. Indicar qué queda excluido.]

**Tipo de instalación:**
- [ ] Instalación nueva
- [ ] Ampliación de instalación existente
- [ ] Remodelación / adecuación

---

## 2. DATOS DE LA INSTALACIÓN

### 2.1 Datos del inmueble

| Parámetro | Valor |
|-----------|-------|
| Destino | [Vivienda / Oficina / Local / Industrial / Mixto] |
| Clasificación de personas | [BA1 / BA2 / BA3 / BA4 / BA5] |
| Condición de evacuación | [BD1 / BD2 / BD3 / BD4] |
| Superficie total | [____ m²] |
| Número de unidades funcionales | [____] |
| Número de plantas | [____] |
| Sectores / locales principales | [Describir] |

### 2.2 Datos de la alimentación eléctrica

| Parámetro | Valor |
|-----------|-------|
| Empresa distribuidora | [Nombre] |
| Tensión de alimentación | [220/380 V BT / ____ kV MT] |
| Potencia suministrada (kW) | [____] |
| Corriente máxima contratada (A) | [____] |
| Potencia de cc en el punto de conexión (MVA) | [____] |
| Tipo de medición | [Monofásica 2H / Trifásica 3H / Trifásica 4H] |
| Tipo de tarifa / categoría | [____] |

### 2.3 Datos del transformador (si aplica)

| Parámetro | Valor |
|-----------|-------|
| Potencia nominal | [____ kVA] |
| Tensión primaria (MT) | [____ kV] |
| Tensión secundaria (BT) | [____ V] |
| Tensión de cortocircuito (ucc) | [____  %] |
| Grupo de conexión | [Dyn11 / Dyn5 / etc.] |
| Pérdidas en vacío | [____ W] |
| Pérdidas en carga | [____ W] |
| Resistencia total (R_T) | [____ mΩ] |
| Reactancia total (X_T) | [____ mΩ] |
| Impedancia total (Z_T) | [____ mΩ] |

---

## 3. REFERENCIAS NORMATIVAS

Las siguientes normas y reglamentaciones son aplicables a la presente memoria:

| Norma | Título | Edición |
|-------|--------|---------|
| AEA 90364-2 | Definiciones y terminología | [Año] |
| AEA 90364-4 | Medidas de protección para garantizar la seguridad | [Año] |
| AEA 90364-4-42 | Protección contra efectos térmicos | [Año] |
| AEA 90364-5 | Selección e instalación de materiales eléctricos | [Año] |
| AEA 90364-7-770 | Viviendas unifamiliares (hasta 63 A, BA2/BD1) | 2017 |
| AEA 90364-7-771 | Viviendas, oficinas y locales (unitarios) | 2006 |
| AEA 90909-0 | Corrientes de cortocircuito — Cálculo | [Año] |
| AEA 90909-1 | Corrientes de cortocircuito — Informe técnico | 2005 |
| IRAM 2178-2 | Cables MT con aislamiento XLPE (hasta 33 kV) | [Año] |
| IEC 60364-5-52 | Tablas de intensidades admisibles | [Año] |
| IEC 60909 | Corrientes de cortocircuito — Cálculo | [Año] |
| NFPA 70B | Recommended Practice for Electrical Equipment Maintenance | 2026 |
| NFPA 70E | Standard for Electrical Safety in the Workplace | 2027 |
| [Otras normas locales aplicables] | | |

---

## 4. ESQUEMA DE CONEXIÓN A TIERRA

**Norma de referencia:** AEA 90364-7-771 §771.3 / AEA 90364-7-770 §770.3

### 4.1 Esquema adoptado

- [X] Esquema **TT** (neutro de la distribuidora puesto a tierra; masas de la instalación
  puestas a tierra independiente). *Habitual en Argentina.*
- [ ] Esquema **TN-S** (neutro y conductor PE separados desde el transformador)
- [ ] Esquema **TN-C-S** (TN-C en la red; TN-S en la instalación)
- [ ] Esquema **IT** (neutro aislado de tierra; uso en locales especiales)

**Justificación de la elección:**
[Indicar tipo de suministro de la distribuidora, existencia o no de conductor PE en la
acometida, requisitos especiales del local, etc.]

### 4.2 Resistencia de puesta a tierra de protección requerida

Con esquema TT, la condición de protección es:
> **RTP × IΔn ≤ UL**

| Parámetro | Valor | Fuente |
|-----------|-------|--------|
| Tensión de contacto límite UL | [50 V / 25 V] | AEA 771.18.4 |
| Sensibilidad DDR seleccionada IΔn | [30 mA / 300 mA] | Diseño |
| **RTP máxima admitida** | **[UL / IΔn] Ω** | Calculado |

**Resistividad del terreno estimada (ρ):** ____ Ω·m *(tipo de suelo: [____])*

### 4.3 Diseño del electrodo de puesta a tierra

| Elemento | Descripción | Resistencia calculada |
|----------|-------------|----------------------|
| Jabalina principal | [Longitud × diámetro, material] | ____ Ω |
| Jabalinas adicionales (paralelo) | [Número y separación] | ____ Ω |
| Anillo perimetral (si aplica) | [Longitud y sección conductor] | ____ Ω |
| **RTP resultante** | | **____ Ω** |

**Verificación:** RTP (____ Ω) × IΔn (____ mA) = ____ V ≤ UL (____ V) ✓ / ✗

---

## 5. CARGAS Y DEMANDA DE POTENCIA

**Norma de referencia:** AEA 90364-7-771 §771.8 / §771.9

### 5.1 Grado de electrificación adoptado

| Unidad / Sector | Superficie (m²) | Destino | Grado | Referencia |
|-----------------|-----------------|---------|-------|-----------|
| [Unidad 1] | [____] | [Vivienda/Oficina] | [Mínimo/Medio/Elevado/Superior] | AEA 771.8.2/3 |
| [Unidad 2] | | | | |
| **Total edificio** | | | | |

### 5.2 Número mínimo de circuitos (conforme AEA 771.8)

| Tipo de circuito | Cód. | Mínimo normativo | Cantidad diseñada |
|-----------------|------|-----------------|-------------------|
| Iluminación uso general | IL | [____] | [____] |
| Iluminación trifásica específica | ITE | [____] | [____] |
| Tomacorrientes uso general | TG | [____] | [____] |
| Tomacorrientes uso especial | TE | [____] | [____] |
| Cocina / horno | CC | [____] | [____] |
| Calefacción / AA | CC | [____] | [____] |
| [Otros según proyecto] | CC | [____] | [____] |

### 5.3 Planilla de cargas instaladas

| N° | Circuito / Carga | Tipo | Pot. unitaria (W) | Cant. | Pot. total (W) | cos_φ | kVA |
|----|-----------------|------|-------------------|-------|----------------|-------|-----|
| 1 | Iluminación general | IL | [____] | [____] | [____] | 0,95 | [____] |
| 2 | Tomacorrientes gral | TG | [____] | [____] | [____] | 0,85 | [____] |
| 3 | Cocina eléctrica | CC | [____] | 1 | [____] | 1,00 | [____] |
| 4 | AA / Split | CC | [____] | [____] | [____] | 0,85 | [____] |
| 5 | [Carga específica] | CC | [____] | [____] | [____] | [____] | [____] |
| | **TOTAL INSTALADO** | | | | **[____] W** | | **[____] kVA** |

### 5.4 Coeficientes de simultaneidad y demanda de potencia máxima simultánea

| Sector / Columna | P_instalada (W) | Coef. simult. | P_diseño (W) | cos_φ_diseño | I_diseño (A) |
|-----------------|----------------|---------------|--------------|--------------|--------------|
| [Unidad 1] | [____] | [____] | [____] | [____] | [____] |
| [Unidad 2] | [____] | [____] | [____] | [____] | [____] |
| Servicios comunes | [____] | [____] | [____] | [____] | [____] |
| **Edificio completo** | **[____]** | **[____]** | **[____]** | **[____]** | **[____]** |

> Referencia de coeficientes: AEA 90364-7-771 Tabla 771.9.X

**Corriente de diseño de la acometida:**
- Id = P_diseño / (√3 × 380 × cos_φ) = ____ / (√3 × 380 × ____) = **____ A**

---

## 6. CORRIENTES DE CORTOCIRCUITO

**Norma de referencia:** AEA 90909-0 / AEA 90909-1; IEC 60909

### 6.1 Datos del sistema en el punto de conexión

| Parámetro | Símbolo | Valor | Fuente |
|-----------|---------|-------|--------|
| Tensión nominal de la red BT | Un | 380 V | — |
| Potencia de cc en el punto de conexión | Scc | ____ MVA | Distribuidora |
| Impedancia de red equivalente (en barras BT) | Zred | ____ mΩ | Calculado |
| Factor de tensión (Icc máx) | c | 1,10 | AEA 90909 |
| Factor de tensión (Icc mín) | c | 0,95 | AEA 90909 |

### 6.2 Impedancias de los elementos del sistema

| Elemento | R (mΩ) | X (mΩ) | Z (mΩ) | Referencia |
|----------|--------|--------|--------|-----------|
| Red equivalente (en bornes BT trafo) | [____] | [____] | [____] | Scc distribuidora |
| Transformador MT/BT | [____] | [____] | [____] | Placa / cálculo |
| Conductor de acometida / línea BT | [____] | [____] | [____] | Tablas fabricante |
| **Impedancia total en barras TP** | **[____]** | **[____]** | **[____]** | — |

### 6.3 Corrientes de cortocircuito calculadas

#### En barras del Tablero Principal

| Magnitud | Fórmula | Resultado | Uso |
|----------|---------|-----------|-----|
| Icc máx trifásica | c × Un / (√3 × Z_min) | **____ kA** | Capacidad de ruptura |
| Icc mín bifásica | 0,866 × Icc máx | **____ kA** | — |
| Icc mín monofás. (fin de circuito más largo) | c × Un / (2 × Z_total) | **____ A** | Disparo magnético |

#### En tableros secundarios (resumen)

| Tablero | Distancia (m) | Sección conductor | Icc máx (A) | Icc mín (A) |
|---------|--------------|-------------------|-------------|-------------|
| TP — Tablero Principal | — | — | **[____]** | **[____]** |
| TS-1 — [Nombre] | [____] m | [____] mm² | [____] | [____] |
| TS-2 — [Nombre] | [____] m | [____] mm² | [____] | [____] |

---

## 7. DIMENSIONAMIENTO DE CONDUCTORES BT

**Norma de referencia:** AEA 90364-7-771 §771.13, §771.16; IEC 60364-5-52

### 7.1 Criterios de dimensionamiento

Los conductores son dimensionados cumpliendo simultáneamente:
1. Capacidad de conducción de corriente: Iz ≥ Id
2. Protección contra sobrecarga: In ≤ Iz y I₂ ≤ 1,45 × Iz
3. Protección térmica en cortocircuito: I²t ≤ K² × S²
4. Caída de tensión: ΔU ≤ límite normativo (ver Etapa 9)

### 7.2 Planilla de dimensionamiento de circuitos

| N° | Circuito | Id (A) | Método inst. | Iz₀ (A) | k₁ | k₂ | Iz (A) | S_adopt (mm²) | In_prot (A) | Iz ≥ In? | I₂ ≤ 1,45Iz? |
|----|---------|--------|-------------|---------|----|----|--------|--------------|------------|----------|--------------|
| 1 | [IL-1: Ilum. Planta Baja] | [____] | [A1] | [____] | [____] | [____] | [____] | **[____]** | [____] | [✓/✗] | [✓/✗] |
| 2 | [TG-1: TC Estar/Comedor] | [____] | [A1] | [____] | [____] | [____] | [____] | **[____]** | [____] | [✓/✗] | [✓/✗] |
| 3 | [CC-1: Cocina] | [____] | [A1] | [____] | [____] | [____] | [____] | **[____]** | [____] | [✓/✗] | [✓/✗] |
| 4 | [Línea Ppal Unidad 1] | [____] | [B1] | [____] | [____] | [____] | [____] | **[____]** | [____] | [✓/✗] | [✓/✗] |
| 5 | [Acometida general] | [____] | [D1] | [____] | [____] | [____] | [____] | **[____]** | [____] | [✓/✗] | [✓/✗] |

> **k₁**: factor de corrección por temperatura ambiente
> **k₂**: factor de corrección por agrupamiento
> **Iz₀**: intensidad de referencia de la tabla IEC 60364-5-52 según método de instalación

### 7.3 Verificación de protección térmica frente a cortocircuito

| Circuito | Sección (mm²) | K | K²S² (A²s) | I²t_prot (A²s) | ¿Cumple? |
|---------|--------------|---|------------|----------------|----------|
| [____] | [____] | [115/135] | [____] | [____] | [✓/✗] |

> **K = 115**: Cu-PVC | **K = 135**: Cu-XLPE | **K = 76**: Al-XLPE

### 7.4 Conductor de protección (PE)

| Circuito | S_fase (mm²) | S_PE (mm²) | Norma |
|---------|-------------|------------|-------|
| [____] | ≤16 | = S_fase | AEA 771.18 |
| [____] | 16–35 | = 16 | AEA 771.18 |
| [____] | >35 | = S_fase/2 | AEA 771.18 |

---

## 8. PROTECCIONES BT

**Norma de referencia:** AEA 90364-7-771 §771.17, §771.18, §771.19

### 8.1 Planilla de protecciones

| N° | Circuito | Tipo dispositivo | In (A) | Curva | Polos | Iccr (kA) | Icc_prot (kA) | IΔn (mA) | Tipo DDR |
|----|---------|-----------------|--------|-------|-------|-----------|---------------|----------|---------|
| 1 | [IL-1] | ITM | [____] | B | 1+N | [____] | [____] | 30 | AC |
| 2 | [TG-1] | ITM | [____] | C | 1+N | [____] | [____] | 30 | AC |
| 3 | [CC-1] | ITM | [____] | C | 2 | [____] | [____] | 30 | A |
| 4 | [Línea Ppal] | ITM | [____] | C | 4 | [____] | [____] | — | — |

> **Iccr ≥ Icc máx** en el punto de instalación — verificación obligatoria

### 8.2 Coordinación de protecciones

**Selectividad amperimétrica:**

| Nivel | Dispositivo | In (A) | Ratio In_aguas_arr / In_aguas_abajo | ¿Selectivo? |
|-------|------------|--------|-------------------------------------|-------------|
| Acometida → TP | [____] / [____] | [____] / [____] | [____] | [✓/✗] |
| TP → TS | [____] / [____] | [____] / [____] | [____] | [✓/✗] |
| TS → Circuito | [____] / [____] | [____] / [____] | [____] | [✓/✗] |

**Protección diferencial:**
- DDR de columna: IΔn = ____ mA, tipo ____, retardo ____ s (selectividad en tiempo)
- DDR de circuito terminal: IΔn = 30 mA, tipo ____, instantáneo

### 8.3 Protección contra sobretensiones (SPD)

| Ubicación | Tipo SPD | Nivel de protección Up (kV) | Nivel de instalación | Norma |
|-----------|---------|----------------------------|---------------------|-------|
| Tablero Principal | Tipo 2 | ≤ 2,5 | I | IEC 61643-11 |
| [Equipos sensibles] | Tipo 3 | ≤ 1,5 | II | IEC 61643-11 |

---

## 9. CAÍDAS DE TENSIÓN

**Norma de referencia:** AEA 90364-7-771 §771.19.7

### 9.1 Límites admisibles

| Tipo de circuito | ΔU máx admisible | Tensión de referencia |
|-----------------|------------------|-----------------------|
| Alumbrado | 3% | 220 V (monofásico) → 6,6 V |
| Otros usos | 5% | 380 V (trifásico) → 19 V |

### 9.2 Planilla de caídas de tensión

| N° | Circuito | Tipo | I (A) | L (m) | S (mm²) | R (Ω/km) | X (Ω/km) | cos_φ | ΔU (V) | ΔU (%) | ΔU acum (%) | ¿Cumple? |
|----|---------|------|-------|-------|---------|----------|----------|-------|---------|---------|------------|---------|
| 1 | Acometida | — | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [✓/✗] |
| 2 | Línea principal | — | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [✓/✗] |
| 3 | IL-1 | IL | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [✓/✗] |
| 4 | TG-1 | TG | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [✓/✗] |
| 5 | CC-1 | CC | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [____] | [✓/✗] |

> **Fórmula monofásica:** ΔU = 2 × I × L × (R_km × cos_φ + X_km × sin_φ) / 1000 [V]
> **Fórmula trifásica:** ΔU = √3 × I × L × (R_km × cos_φ + X_km × sin_φ) / 1000 [V]
> **ΔU acumulada** = suma de ΔU desde origen hasta el punto en cuestión

---

## 10. CANALIZACIONES

**Norma de referencia:** AEA 90364-7-771 §771.12, §771.14, §771.15

### 10.1 Descripción de canalizaciones adoptadas

| Zona / Circuito | Tipo de canalización | Material | Diámetro / Dim. | IP | Observaciones |
|----------------|---------------------|----------|-----------------|-----|---------------|
| Embutida en losa/pared | Cañería PVC rígido | PVC | [____] mm | IP40 | |
| A la vista (interior) | Cable canal | PVC | [____]×[____] mm | IP40 | |
| Subterránea | Conducto HDPE corrugado | HDPE | [____] mm | IP67 | Directamente enterrado |
| Bandeja portacables | Bandeja perforada | Acero galv. | [____]×[____] mm | — | |
| [Otra] | | | | | |

### 10.2 Verificación de factor de llenado de cañerías

| Tramo | Diámetro cañería (mm) | Área interior (mm²) | Cables alojados | Área cables (mm²) | Factor llenado | ¿Cumple ≤40%? |
|-------|----------------------|--------------------|-----------------|--------------------|----------------|---------------|
| [____] | [____] | [____] | [Describir] | [____] | [____]% | [✓/✗] |

### 10.3 Ambientes especiales

| Ambiente | Clasificación | Tipo de canalización requerida | Secciones de norma |
|----------|--------------|-------------------------------|-------------------|
| Baño | BA2 (con niños) | PVC con sellados | AEA 771-B.1 y 771-B.2 |
| Lavadero / húmedo | BA2 | PVC estanco o acero | AEA 771-B.2 |
| Exterior | — | PVC UV o acero inox | AEA 771-B.3 |
| [Otro especial] | | | |

---

## 11. TABLEROS ELÉCTRICOS

**Norma de referencia:** AEA 90364-7-771 §771.20

### 11.1 Listado de tableros

| Cód. | Nombre | Alimentación | Potencia (kW) | Corriente (A) | Cantidad ctes. |
|------|--------|-------------|---------------|--------------|----------------|
| TP | Tablero Principal | Acometida | [____] | [____] | [____] |
| TS-1 | [Tablero Unidad 1] | TP | [____] | [____] | [____] |
| TS-2 | [Tablero Unidad 2] | TP | [____] | [____] | [____] |
| TSC | [Tablero Serv. Com.] | TP | [____] | [____] | [____] |

### 11.2 Características constructivas de tableros

| Parámetro | Tablero Principal (TP) | Tableros Unidad (TS) |
|-----------|----------------------|----------------------|
| Tipo | Tablero seccional general | Tablero de unidad |
| Material envolvente | [Acero / ABS] | [Acero / ABS] |
| Grado de protección IP | [IP__] | [IP__] |
| Resistencia a impacto IK | [IK__] | [IK__] |
| Tensión nominal | 380/220 V | 220 V |
| Icc máx admitida | [____] kA | [____] kA |
| Espacio de reserva | [____]% | [____]% |
| Corte del neutro | Bipolar / Tetrapolar | Bipolar |

### 11.3 Barras colectoras del Tablero Principal

| Barra | Material | Sección (mm²) | Corriente admisible (A) | ¿Cumple Icc? |
|-------|----------|--------------|------------------------|-------------|
| Fase L1 | Cu | [____] | [____] | [✓/✗] |
| Fase L2 | Cu | [____] | [____] | [✓/✗] |
| Fase L3 | Cu | [____] | [____] | [✓/✗] |
| Neutro N | Cu | [____] | [____] | [✓/✗] |
| Tierra PE | Cu | [____] | [____] | [✓/✗] |

---

## 12. CABLEADO MT

*(Completar solo si la instalación incluye alimentación o distribución en media tensión)*

**Norma de referencia:** IRAM 2178-2 / IEC 60502-2; IEC 60287

### 12.1 Datos del cable MT seleccionado

| Parámetro | Valor | Fuente |
|-----------|-------|--------|
| Fabricante / Modelo | [CIMET OPTEL TERMOLITE MT / ZEROTOX MT] | HT fabricante |
| Norma de fabricación | [IRAM 2178-2 / IEC 60502-2] | |
| Tensión nominal Uo/U (Um) | [____/____  (____) kV] | |
| Material conductor | [Cu / Al] | |
| Sección del conductor | [____] mm² | |
| Tipo de aislamiento | XLPE | |
| Temperatura máx. en servicio | 90 °C | IEC 60502-2 |
| Temperatura máx. en cc (1 s) | 250 °C | IEC 60502-2 |
| Pantalla metálica | [Alambres Cu / Cinta Cu] — [____] mm² | HT fabricante |
| Armadura (si aplica) | [Flejes acero / Sin armadura] | |
| Cubierta exterior | [PVC ST2 / PE ST7] | |
| Resistencia conductor a 90°C | [____] Ω/km | HT fabricante |
| Reactancia inductiva (trébol/plana) | [____] Ω/km | HT fabricante |

### 12.2 Capacidad de conducción (ampacity MT)

| Condición | Imax (A) | Factor k₁ (T°) | Factor k₂ (agrup.) | Factor k₃ (terreno) | Iz final (A) |
|-----------|----------|----------------|--------------------|--------------------|-------------|
| Enterrado directo, 20°C, aislado | [____] | [____] | [____] | [____] | **[____]** |
| Enterrado en conducto | [____] | [____] | [____] | [____] | **[____]** |
| Al aire, 40°C | [____] | [____] | [____] | — | **[____]** |

**Corriente de diseño:** Id = [____] A ≤ Iz = [____] A ✓ / ✗

### 12.3 Verificación de pantalla metálica frente a cortocircuito

| Parámetro | Valor |
|-----------|-------|
| Icc monofásica máxima en la línea MT | [____] kA |
| Tiempo de apertura de protección MT | [____] s |
| Sección mínima de pantalla: S = Icc × √t / 141 | [____] mm² |
| Sección de pantalla del cable | [____] mm² |
| **¿Cumple?** | **[✓/✗]** |

### 12.4 Caída de tensión en línea MT

| Tramo | I (A) | L (m) | R (Ω/km) | X (Ω/km) | cos_φ | ΔU (V) | ΔU (%) |
|-------|-------|-------|----------|----------|-------|---------|--------|
| [Tramo 1] | [____] | [____] | [____] | [____] | [____] | [____] | [____] |
| **Total** | | | | | | **[____] V** | **[____]%** |

**Límite admisible:** [____]% (coordinado con distribuidora)
**Resultado:** [____]% ≤ [____]% ✓ / ✗

---

## 13. PROTECCIONES MT

*(Completar solo si la instalación incluye alimentación o distribución en media tensión)*

**Norma de referencia:** IEC 60265; IEC 60282; Reglamento técnico distribuidora

### 13.1 Fusibles MT (protección de transformadores)

| Parámetro | Valor | Verificación |
|-----------|-------|-------------|
| Corriente nominal del transformador | In_T = Sn / (√3 × Un_MT) = [____] A | — |
| Corriente nominal del fusible | In_F ≥ 1,5 × In_T = [____] A | Cumple: [✓/✗] |
| Tensión nominal del fusible | Un_F ≥ 1,05 × Un_red = [____] kV | Cumple: [✓/✗] |
| Poder de ruptura (PRF) | [____] kA | ≥ Icc_MT máx: [✓/✗] |
| Fabricante / modelo | [____] | — |

### 13.2 Interruptores automáticos MT y relés de protección

| Función | Relé ANSI | Ajuste | Tiempo de disparo |
|---------|-----------|--------|-------------------|
| Sobreintensidad de tiempo inverso | 51 | I> = [____] A; t = [____] s | [____] s |
| Sobreintensidad instantánea | 50 | I>> = [____] A | < 100 ms |
| Diferencial de transformador | 87T | Id diferencial = [____]% | < 100 ms |
| Tensión mínima (subtensión) | 27 | U< = [____] % Un | [____] s |
| Tensión máxima (sobretensión) | 59 | U> = [____] % Un | [____] s |
| Falla a tierra (tierra restringida) | 64 | [____] | [____] ms |

---

## 14. SISTEMA DE PUESTA A TIERRA

**Norma de referencia:** AEA 90364-7-771 §771.18, Anexo C; AEA 90364-4

### 14.1 Componentes del sistema

| Componente | Descripción | Sección / Dimensión | Material |
|-----------|-------------|--------------------|---------| 
| Electrodo (jabalinas) | [Número × longitud × diámetro] | [____] mm de diám. | [Acero cobreado] |
| Conductor de puesta a tierra (CT) | Desde jabalina hasta barra PE del TP | [____] mm² | Cu desnudo o aislado |
| Barra PE del tablero principal | Barra de cobre, borneras | [____] mm² | Cu |
| Conductor PE de columna | En líneas principales | [____] mm² | Cu |
| Conductor PE de circuitos terminales | En todos los circuitos | [____] mm² | Cu |
| Conductor de equipotencialidad principal | A masas metálicas (tuberías, estructuras) | [____] mm² | Cu |
| Conductor de equipotencialidad suplem. | En baños / piletas (si aplica) | [____] mm² | Cu |

### 14.2 Verificación de la resistencia de puesta a tierra

| Resistividad del terreno medida / estimada | ρ = [____] Ω·m |
|--------------------------------------------|----------------|
| RTP calculada | [____] Ω |
| IΔn del DDR | [____] mA |
| Tensión de contacto resultante: Uc = RTP × IΔn | [____] V |
| Tensión límite admisible UL | [____] V |
| **Resultado:** Uc ≤ UL | **[✓/✗]** |

---

## 15. VERIFICACIONES FINALES

### 15.1 Resumen de verificaciones normativas

| Verificación | Resultado | Norma | Obs. |
|-------------|-----------|-------|------|
| Grado de electrificación y mínimo de circuitos | [✓/✗] | AEA 771.8 | |
| Capacidad de conducción: Iz ≥ Id en todos los circuitos | [✓/✗] | AEA 771.16 | |
| Protección contra sobrecarga: In ≤ Iz | [✓/✗] | AEA 771.19.2 | |
| Protección contra sobrecarga: I₂ ≤ 1,45 Iz | [✓/✗] | AEA 771.19.2 | |
| Protección térmica cc: I²t ≤ K²S² | [✓/✗] | AEA 771.19.3 | |
| Iccr ≥ Icc máx en todos los dispositivos | [✓/✗] | AEA 771.17 | |
| Icc mín > umbral disparo magnético (o fusible) | [✓/✗] | AEA 771.19.3 | |
| ΔU ≤ 3% (alumbrado) y ΔU ≤ 5% (otros) | [✓/✗] | AEA 771.19.7 | |
| Resistencia de puesta a tierra: RTP × IΔn ≤ UL | [✓/✗] | AEA 771.18.4 | |
| Factor de llenado de cañerías ≤ 40% | [✓/✗] | AEA 771.12 | |
| Espacio de reserva en tableros ≥ 20% | [✓/✗] | AEA 771.20 | |
| DDR 30 mA en circuitos terminales de vivienda | [✓/✗] | AEA 771.18.2 | |
| Secciones mínimas normativas (1,5 mm² IL; 2,5 mm² TG) | [✓/✗] | AEA 771.13 | |

### 15.2 Pruebas y ensayos previstos

| Ensayo | Instrumento | Resultado esperado | Realizado |
|--------|------------|-------------------|-----------|
| Continuidad de conductores PE | Telurímetro / Resistivímetro | < 1 Ω | [ ] |
| Resistencia de aislamiento (fases - tierra) | Megóhmetro 500 V | ≥ 1 MΩ | [ ] |
| Resistencia de puesta a tierra | Telurímetro (caída de potencial) | ≤ RTP_max | [ ] |
| Verificación de polaridad | Multímetro | Correcta | [ ] |
| Prueba funcional DDR (botón test) | — | Apertura instantánea | [ ] |
| Prueba de disparo DDR (corriente real) | Probador DDR | IΔ ≤ IΔn / 2 (a los 300 ms) | [ ] |
| Tensión de alimentación en BT | Multímetro | 220/380 V ± 5% | [ ] |

---

## 16. CONCLUSIONES

La instalación eléctrica proyectada cumple con los requisitos establecidos en:
- AEA 90364-7-[770/771] y las normas referenciadas en la misma
- [Otras normas aplicables]

El dimensionamiento adoptado garantiza:
1. La seguridad de las personas contra contactos directos e indirectos
2. La protección de los conductores contra sobrecarga y cortocircuito
3. La selectividad de las protecciones
4. Las caídas de tensión dentro de los límites admisibles
5. Un sistema de puesta a tierra adecuado al esquema adoptado

[Agregar comentarios sobre condicionantes especiales, observaciones del proyectista,
aspectos que quedan pendientes de definición final, etc.]

---

**[Ciudad], [fecha]**

**Firma del Profesional Responsable:**

___________________________
[Nombre y Apellido]
Ingeniero Electricista / Electromecánico
Matrícula N°: [____]
Consejo Profesional: [COPIME / COPIBA / etc.]

---

## 17. ANEXOS

### Anexo A — Esquemas unifilares
*(Adjuntar planos de cada tablero y esquema unifilar general)*

### Anexo B — Esquema de conexión a tierra
*(Adjuntar diagrama del sistema de puesta a tierra)*

### Anexo C — Tablas de intensidades admisibles utilizadas
*(Reproducir las tablas de IEC 60364-5-52 / AEA 771.16 empleadas)*

### Anexo D — Hojas técnicas de cables
*(Adjuntar hojas técnicas de los fabricantes para cables BT y MT)*

### Anexo E — Hojas técnicas de dispositivos de protección
*(Adjuntar curvas tiempo-corriente de ITM y DDR; tablas de coordinación en cascada)*

### Anexo F — Protocolo de pruebas y mediciones
*(Completar con resultados de las mediciones in situ)*

### Anexo G — Referencias a hojas de cálculo / software utilizado
*(Indicar software o planillas de cálculo empleadas y sus versiones)*
