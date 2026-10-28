# ROADMAP — Módulo de Cálculos Eléctricos

## Alcance y Referencias Normativas

Este roadmap cubre el dimensionamiento eléctrico completo para instalaciones en inmuebles
(BT y MT), ordenado por dependencia de cálculo. Cada etapa usa los resultados de la anterior.

### Normas principales aplicables
- **AEA 90364-2**: Definiciones y terminología
- **AEA 90364-4**: Medidas de protección — conceptos generales
- **AEA 90364-4-42**: Protección contra efectos térmicos
- **AEA 90364-5**: Selección e instalación de materiales eléctricos
- **AEA 90364-7-770**: Viviendas unifamiliares hasta 63 A (BA2/BD1)
- **AEA 90364-7-771**: Viviendas, oficinas y locales (unitarios) — norma general BT
- **AEA 90909-0/1**: Corrientes de cortocircuito en sistemas trifásicos CA
- **IRAM 2178-2 / IEC 60502-2**: Cables de MT con aislamiento XLPE
- **IRAM 63004**: Cables preensamblados de MT
- **IRAM 63005**: Cables ECOPEX protegidos de MT
- **NFPA 70B 2026**: Mantenimiento de instalaciones eléctricas
- **NFPA 70E 2027**: Seguridad eléctrica en el trabajo
- **IEC 60364-5-52**: Tablas de intensidades admisibles (referenciadas por AEA 90364)

---

## ETAPA 0 — Datos de partida (prerequisito universal)

Antes de cualquier cálculo se deben relevar y documentar los siguientes datos. Sin ellos
ningún paso posterior puede completarse.

### 0.1 Datos del inmueble / instalación
- Destino y clasificación (vivienda / oficina / local / industrial / mixto)
- Clasificación de personas (BA1…BA5 según AEA 90364-7-771, §771.10-771.11)
- Condiciones de evacuación (BD1…BD4)
- Superficie por sector y por unidad
- Número de unidades / plantas / sectores
- Potencias instaladas previstas (equipos fijos y cargas específicas)

### 0.2 Datos de la red de alimentación
- Tensión nominal de alimentación (BT: 220/380 V; MT: 3,3 / 6,6 / 13,2 / 33 kV)
- Frecuencia (50 Hz)
- Potencia de cortocircuito en el punto de conexión (Scc, en MVA) — proveída por distribuidora
- Tipo de neutro en la red de la distribuidora (TT / TN-S / TN-C)
- Corriente de cc máxima en origen (Icc máx, proporcionada o estimada desde Scc)
- Corriente de cc mínima en origen (Icc mín, normalmente = Icc máx / 2 para estimación)

### 0.3 Datos del transformador (si hay subestación propia MT/BT)
- Potencia nominal (kVA)
- Tensión de cortocircuito (ucc %)
- Pérdidas en vacío y en carga (W)
- Grupo de conexión (Dyn11, etc.)
- Resistencia y reactancia de devanados

---

## ETAPA 1 — Esquema de conexión a tierra

**Depende de**: Etapa 0 (datos de red)
**Norma**: AEA 90364-7-771 §771.3; AEA 90364-4

El esquema condiciona todas las protecciones contra contactos indirectos (DDR, desconexión
automática) y los valores de resistencia admitidos.

### 1.1 Selección del esquema
- Esquema TT: obligatorio cuando la distribuidora no provee el conductor neutro de tierra
  (esquema habitual en Argentina para la mayoría de distribuidoras)
- Esquema TN-S / TN-C-S: cuando la distribuidora provee el conductor PE
- Esquema IT: locales especiales (hospitalarios, quirófanos)
- La Sección 771 exige el Esquema de Conexión a Tierra (ECT) conforme §771.3.2

### 1.2 Resistencia de puesta a tierra de protección (RTP)
- En esquema TT: RTP × IΔn ≤ UL (AEA 771.3.I: 50 V columna 1; 24 V columna 2; valor adoptado = mín(0,5·24/IΔn; 40 Ω))
  Ejemplo: con DDR de 30 mA → RTP ≤ 40 Ω (adoptado; 1666 Ω con 50 V); con DDR de 300 mA → RTP ≤ 40 Ω (166 Ω con 50 V)
  Función: `aea_earthing.ra_maxima`
- Valor máximo permitido según tabla de AEA 771.3.3 en función de IΔn
- Electrodo mínimo: jabalina de 2400 mm (AEA 771, Anexo C); verificar resistividad del terreno

### 1.3 Cálculo de electrodo de puesta a tierra
- Resistividad del terreno ρ (Ω·m) — medida o estimada por tipo de suelo
- Fórmulas para jabalinas simples, paralelas y anillos
- Verificar que RTP cumpla el requisito del DDR previsto

---

## ETAPA 2 — Cargas y demanda (potencia de diseño)

**Depende de**: Etapa 0 (datos del inmueble)
**Norma**: AEA 90364-7-771 §771.8, §771.9; AEA 90364-7-770 §770.7, §770.8

### 2.1 Grado de electrificación
Determina el número mínimo de circuitos y puntos de utilización.
- Viviendas (AEA 771.8.2): Mínimo / Medio / Elevado / Superior
- Oficinas (AEA 771.8.3): Mínimo / Medio / Elevado / Superior
- Locales de otras características (AEA 771.8.5)
- El grado se fija en función de la superficie y del destino

### 2.2 Número mínimo de circuitos y puntos de utilización
- Conforme a las tablas de AEA 771.8 según grado de electrificación y superficie
- Definir circuitos: iluminación general (IL), tomacorrientes uso general (TG), uso especial (TE),
  ITE (iluminación trifásica específica), cargas específicas (CC: cocina, calefón, etc.)

### 2.3 Coeficientes de simultaneidad
- Para viviendas: coeficientes de la tabla de AEA 771.9.1 según cantidad de viviendas
- Para circuitos específicos de cargas particulares: AEA 771.9.2
- Para el edificio completo (columna + red): AEA 771.9.3 y 771.9.4

### 2.4 Demanda de potencia máxima simultánea
- P_diseño = Σ (P_nominal × coef_sim × cos_φ)
- Corriente de diseño: Id = P_diseño / (√3 × U × cos_φ) (trifásico)
  Id = P_diseño / (U × cos_φ) (monofásico)
- Determinar cos_φ total de la instalación

### 2.5 Compensación de reactiva (si aplica)
- Si cos_φ es inferior al exigido por la distribuidora (normalmente 0,85)
- Q_C a instalar para mejorar a cos_φ objetivo

---

## ETAPA 3 — Corrientes de cortocircuito

**Depende de**: Etapas 0, 1
**Norma**: AEA 90909-0 / AEA 90909-1 (IT); IEC 60909

Los valores de Icc mínima y máxima son necesarios para dimensionar protecciones y verificar
la protección térmica de conductores.

### 3.1 Método de cálculo (AEA 90909 / IEC 60909)
- Factor de tensión c (1,10 para Icc máx; 0,95 para Icc mín en BT)
- Impedancia equivalente de la red en el punto de estudio (Zeq)
- Contribuciones: red pública, transformador, conductores, motores

### 3.2 Icc máxima (Icc máx) — condición de calentamiento
- Sirve para verificar la capacidad de ruptura (Iccr) de interruptores y fusibles
- Icc máx = c × Un / (√3 × Z_min)  [para trifásico]
- Calcular en barras del tablero principal y en cada nodo relevante (cuadros secundarios)

### 3.3 Icc mínima (Icc mín) — condición de disparo
- Sirve para verificar que la protección actúa ante el cc más desfavorable
- Falla monofásica o bifásica a tierra al final del circuito más largo
- Icc mín ≈ 0,8 × Un / (2 × Zt) para estimación simplificada en BT
- Debe superar el umbral de disparo magnético del interruptor (10×In para curva C; 5-10×In curva B)

### 3.4 Corriente de cc en transformador MT/BT
- Icc en bornes BT del transformador = (Sn × c) / (√3 × Un × ucc/100)
- Verificar que protecciones BT tengan Iccr ≥ Icc máx calculada

---

## ETAPA 4 — Cableado BT: dimensionamiento de conductores

**Depende de**: Etapas 2, 3
**Norma**: AEA 90364-7-771 §771.13, §771.16; IEC 60364-5-52

El dimensionamiento se hace por tres criterios en paralelo; la sección final es el MÁXIMO
de los tres resultados.

### 4.1 Criterio de capacidad de conducción de corriente (ampacity)
- Seleccionar método de instalación conforme AEA 771.12:
  - A1: conductores en tubería empotrada en pared
  - A2: cables unipolares en tubería empotrada en pared
  - B1/B2: tubería sobre pared o techo
  - C: cables sobre bandeja o directamente sobre pared
  - D1/D2: cables subterráneos (directamente enterrados o en conductos)
  - E/F: cables al aire
- Intensidad de referencia Iz₀ de la tabla correspondiente (AEA 771.16 / IEC 60364-5-52)
- Factores de corrección:
  - k₁: temperatura ambiente (tabla por tipo de aislación y temperatura de referencia)
  - k₂: agrupamiento (número de circuitos en paralelo o en bandejas)
  - k₃: tipo de suelo / resistividad térmica (para instalaciones subterráneas)
- Iz = Iz₀ × k₁ × k₂ × k₃ ≥ Id (Intensidad de diseño del circuito)
- Sección mínima de conductor de protección (PE) según AEA 771.18 (tabla proporcional a S_fase)

### 4.2 Criterio de protección contra sobrecarga
- Condición 1: In ≤ Iz (corriente nominal del dispositivo de protección ≤ capacidad del cable)
- Condición 2: I₂ ≤ 1,45 × Iz (corriente de fusión efectiva ≤ 1,45 veces la capacidad)
  donde I₂ es la corriente de actuación convencional del dispositivo

### 4.3 Criterio de caída de tensión (verificación)
- Ver Etapa 6. La sección puede resultar mayor para cumplir el límite de caída de tensión.

### 4.4 Criterio de protección contra cortocircuito (energía de paso)
- I²t ≤ K² × S²
  donde K = factor del conductor (115 para Cu-PVC, 135 para Cu-XLPE, 76 para Al-XLPE)
  I²t = energía específica del dispositivo de protección (dato del fabricante)
- Verificar para el cc máximo en el punto de protección

### 4.5 Secciones mínimas normativas (AEA 771.13)
- Circuitos de iluminación uso general: S_min = 1,5 mm² Cu
- Circuitos de tomacorrientes uso general: S_min = 2,5 mm² Cu
- Circuitos de uso especial y cargas fijas: según corriente del circuito
- Línea de alimentación / principal: según carga total

---

## ETAPA 5 — Protecciones BT

**Depende de**: Etapas 2, 3, 4
**Norma**: AEA 90364-7-771 §771.17, §771.18, §771.19

### 5.1 Protección contra sobrecarga
- Interruptor termomagnético (ITM) o fusible con In tal que:
  Id ≤ In ≤ Iz  y  I₂ ≤ 1,45 × Iz
- Curva de disparo según carga: B (electrónica, iluminación), C (uso general), D/K (motores)
- Número de polos: monopolar (circuitos terminales), bipolar (circuitos con N), tripolar/tetrapolar (trifásicos)

### 5.2 Protección contra cortocircuito
- Capacidad de ruptura (Iccr) del dispositivo ≥ Icc máx en el punto de instalación
- Verificar que el tiempo de desconexión sea tal que I²t ≤ K²S² (protección térmica del cable)
- Para interruptores con zona de no-disparo magnético: verificar actuación ante Icc mín

### 5.3 Protección diferencial (DDR)
- Obligatoria en circuitos terminales en viviendas, oficinas y locales (AEA 771.18)
- Sensibilidad estándar: IΔn = 30 mA para contactos directos; 300 mA para incendio
- Esquema TT: DDR obligatorio para todos los circuitos
- Tipo: AC (corrientes sinusoidales), A (incluye DC pulsante), B (DC puro — inversores, FV)
- Selectividad en tiempo entre DDR de columna (retardado) y circuito terminal (instantáneo)

### 5.4 Coordinación de protecciones
- Selectividad (discriminación): el dispositivo más próximo al defecto actúa antes
  - Selectividad amperimétrica: In_aguas_arriba ≥ 1,6 × In_aguas_abajo
  - Selectividad cronométrica: retardo intencional en aguas arriba
- Cascada / backup: cuando Iccr_aguas_abajo < Icc_máx, verificar tablas de coordinación
  del fabricante para uso en cascada
- Protección contra sobretensiones (varistores SPD): Tipo 1 (rayo), Tipo 2 (maniobra) — AEA 771.19.4

---

## ETAPA 6 — Caída de tensión BT

**Depende de**: Etapas 2, 4
**Norma**: AEA 90364-7-771 §771.19.7

### 6.1 Máximos admisibles
- Desde el origen de la instalación hasta cualquier punto de utilización:
  - Circuitos de alumbrado: ΔU_máx = 3%
  - Otros usos: ΔU_máx = 5%
- Los límites aplican sobre la tensión nominal (220 V o 380 V)

### 6.2 Cálculo de caída de tensión
- Circuito monofásico: ΔU = 2 × I × L × (R_km × cos_φ + X_km × sin_φ) / 1000  [V]
- Circuito trifásico: ΔU = √3 × I × L × (R_km × cos_φ + X_km × sin_φ) / 1000  [V]
  donde R_km = resistividad del conductor [Ω/km], X_km = reactancia [Ω/km]
  L = longitud del circuito [m], I = corriente de diseño [A]
- Acumular caídas en cascada: ΔU_total = ΔU_alimentación + ΔU_principal + ΔU_terminal

### 6.3 Ajuste de sección
- Si ΔU_total supera el límite, aumentar la sección hasta cumplir

---

## ETAPA 7 — Canalizaciones BT

**Depende de**: Etapa 4 (secciones definidas), Etapa 0 (condiciones ambientales)
**Norma**: AEA 90364-7-771 §771.12, §771.14, §771.15

### 7.1 Selección del tipo de canalización
- Tipos permitidos y no permitidos: AEA 771.12.1 y 771.12.2
- Cañerías de acero (EMT, pesadas): ámbitos industriales y húmedos
- Cañerías de PVC rígido o flexible: uso general en inmuebles
- Cables canales (canaletas): instalación a la vista
- Bandejas portacables: instalaciones industriales, data centers
- Conductos subterráneos: AEA 771.12.4

### 7.2 Dimensionamiento interior de cañería
- Factor de llenado máximo:
  - 1 cable: 53% del área interior
  - 2 cables: 31% cada uno
  - 3 o más cables: 40% del área total
- Seleccionar diámetro comercial que cumpla factor de llenado
- Radio mínimo de curvatura según tipo de cañería y diámetro (AEA 771.15.3)

### 7.3 Consideraciones especiales (AEA 771.14)
- Corrosión: usar cañería de acero inoxidable o PVC en ambientes corrosivos (BE2, BE3)
- Temperatura: verificar temperatura máxima de operación del material
- Corrientes inducidas: en cañerías metálicas, agrupar fases + neutro + PE en la misma cañería
- Locales húmedos / mojados (Anexo 771-B): sellados de extremos, materiales adecuados
- Locales con riesgo de explosión (BE3): cañería anti-deflagrante, sellados

---

## ETAPA 8 — Tableros eléctricos BT

**Depende de**: Etapas 4, 5
**Norma**: AEA 90364-7-771 §771.20

### 8.1 Tipos de tableros
- Tablero seccional general (reemplaza al tablero unificado de la edición 2002)
- Tablero de distribución de columna (por edificio / por planta)
- Tablero de unidad (tablero de cada local / vivienda)
- Tablero de comandos / automatización (si aplica)

### 8.2 Barras colectoras
- Sección de barras de cobre: Ib_barra ≥ 1,25 × Icc de paso (térmica) y Icc máx (dinámica)
- Separación entre fases: verificar tensión de aislamiento
- Color de fases: L1=marrón, L2=negro, L3=gris, N=azul, PE=verde-amarillo (IRAM)

### 8.3 Requisitos constructivos (AEA 771.20.4 y 771.20.5)
- Grado de protección mínimo IP según ubicación:
  - Interior seco: IP30
  - Interior húmedo / baños / cocinas: IP44
  - Exterior: IP55
- Espacio de reserva: mínimo 20% del área de montaje en tableros nuevos
- Corte bipolar obligatorio en circuitos monofásicos de vivienda
  Tripolar en trifásico, tetrapolar cuando hay neutro
- No se admiten fusibles como protección principal en viviendas
  (sí se permiten en locales con personal instruido)

---

## ETAPA 9 — Cableado MT: dimensionamiento

**Depende de**: Etapas 0 (datos de red MT), 3 (Icc)
**Norma**: IRAM 2178-2 / IEC 60502-2; AEA 90364-5 (aplicaciones MT)
**Referencia de producto**: CIMET OPTEL TERMOLITE MT, ZEROTOX MT, ECOPEX MT

### 9.1 Tensión nominal del cable
- Seleccionar Uo/U (Um) según tensión del sistema:
  - 3,3 kV (3,6 kV): Uo/U=2,3/3,3 — Categoría II (cable doble pantalla)
  - 6,6 kV (7,2 kV): Uo/U=3,8/6,6 o 5,2/6,6 (Cat I / Cat II)
  - 13,2 kV (15 kV): Uo/U=8,7/15
  - 33 kV (36 kV): Uo/U=19/33 — verificar disponibilidad TERMOLITE/ZEROTOX
- Categoría I: sin restricciones de tiempo en caso de falla monofásica a tierra
- Categoría II: operación hasta 8h/año con una fase a tierra (requisito usual de distribuidoras)

### 9.2 Material del conductor
- Cobre: mayor conductividad, menor sección para igual corriente
- Aluminio: menor peso y costo, menor conductividad (sección ~1,6 veces mayor)
- Verificar con tablas CIMET OPTEL (Hoja Técnica 15/22/23/25/27/40) la sección disponible

### 9.3 Capacidad de conducción (ampacity MT)
- Depende de: sección, material, método de instalación, temperatura terreno/aire, agrupamiento
- Método de cálculo conforme IEC 60287 (referenciado en IEC 60502-2 / IRAM 2178-2)
- Temperatura máxima de servicio:
  - XLPE: 90°C normal; 250°C en cc (1 s)
  - PVC: 70°C normal; 160°C en cc (1 s)

### 9.4 Dimensionamiento de la pantalla metálica del cable
- La pantalla debe soportar la corriente de cortocircuito monofásica durante el tiempo de
  apertura de la protección
- Sección estándar pantalla: 6 mm² (cables unipolares) / 12 mm² (tripolares) — CIMET
- Si Icc exigida > capacidad de pantalla estándar, solicitar pantalla reforzada
- Fórmula: S_pantalla ≥ Icc × √t / K  [mm²]
  K = 141 para Cu blando; tiempo t = tiempo de apertura de protección MT [s]

### 9.5 Reactancia e impedancia del cable MT
- Resistencia (R): Ω/km a 90°C = R_20 × (1 + α × ΔT); datos en hoja técnica del fabricante
- Reactancia inductiva (X): depende de la disposición (trébol o plana) y de la separación entre cables
- Usar datos de la hoja técnica para calcular caída de tensión y verificar criterio de estabilidad

### 9.6 Caída de tensión MT
- ΔU_MT = √3 × I × L × (R × cos_φ + X × sin_φ) / 1000  [V]
- Límite: normalmente 2-3% en la línea MT (coordinar con la distribuidora)

---

## ETAPA 10 — Protecciones MT

**Depende de**: Etapas 3 (Icc MT), 9 (cable MT)
**Norma**: IEC 60265, IEC 60282; reglamentación de la distribuidora

### 10.1 Fusibles MT (IEC 60282)
- Tipo: fusible de alto poder de ruptura (APR) para protección de transformadores MT/BT
- Corriente nominal: In_fusible ≥ In_transformador × 1,5 (margen para arranques)
- Tensión nominal: Un_fusible ≥ Un_red × 1,05
- Poder de ruptura: PRF ≥ Icc máx en el punto de conexión

### 10.2 Interruptores automáticos MT (IA MT) + Relés
- Celda de llegada (interruptor de cabecera)
- Celda de transformador (con fusibles o IA)
- Relé de sobreintensidad (50/51): protección contra sobrecarga y cc
- Relé diferencial de transformador (87T): protección interna
- Relé de tensión mínima (27) y máxima (59)
- Coordinación de selectividad con la red de la distribuidora

### 10.3 Coordinación protecciones MT y BT
- El interruptor BT del transformador actúa en cc BT antes de que actúe la protección MT
- Verificar que el fusible MT no actúe ante cortocircuitos en la red BT (selectividad total)

---

## ETAPA 11 — Tipos de circuitos (síntesis normativa)

Esta etapa es un compendio de las tipologías de circuitos conforme AEA 90364-7-771 §771.7.

### 11.1 Clasificación de líneas (AEA 771.7)
| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| Línea de alimentación | Desde medidor/límite de propiedad hasta TSGG | Acometida |
| Línea principal | Desde TSGG hasta tablero de unidad | Columna de edificio |
| Circuito seccional | Desde tablero unidad hasta subtablero o cuadro parcial | Planta baja a planta alta |
| Circuito terminal | Último tramo hasta el punto de utilización | Circuito a tomacorrientes |

### 11.2 Clasificación de circuitos terminales (AEA 771.7.6)
| Código | Denominación | Protección | Sección mín | Bocas máx |
|--------|-------------|------------|-------------|-----------|
| IL | Iluminación uso general | 10 A (vivienda) / 16 A (oficina) | 1,5 mm² Cu | 10 (viv.) / 30 (of.) |
| ITE | Iluminación trifásica específica | 16 A (local instruido) | 1,5 mm² Cu | 30 |
| TG | Tomacorrientes uso general | 16 A (vivienda y of.) | 2,5 mm² Cu | 6 (viv.) / 20 (of.) |
| TE | Tomacorrientes uso especial | 16 A | 2,5 mm² Cu | 6 |
| CC | Cargas específicas fijas | Según carga | Según carga | 1 |

### 11.3 Circuitos de uso especial más frecuentes (CC)
- Cocina eléctrica (horno + anafe): ≥ 16 A; sección ≥ 2,5 mm² (recomendado 4 mm²)
- Calefón / termotanque eléctrico: ≥ 16 A; sección ≥ 2,5 mm²
- Lavarropa: ≥ 16 A; con DDR 30 mA (zona húmeda)
- Aire acondicionado split: según potencia; típico 16-20 A, sección 2,5-4 mm²
- Bomba de agua: ≥ In_motor; protección con curva D o guardamotor
- Carga de VE (Sección 722): circuito dedicado ≥ 32 A (Modo 3/4) + DDR

---

## ETAPA 12 — Puesta a tierra: verificaciones y diseño del sistema

**Depende de**: Etapas 1, 5 (protecciones definidas)
**Norma**: AEA 90364-7-771 §771.18, Anexo C (puesta a tierra)

### 12.1 Sistema de puesta a tierra completo
- Electrodo principal (jabalinas, malla, placa)
- Conductor de puesta a tierra (CT): desde electrodo hasta barra PE del tablero principal
- Conductor de protección (PE): en todos los circuitos hasta cada punto de utilización
- Conductor de equipotencialidad principal: a masas metálicas (tuberías, estructuras)
- Conductor de equipotencialidad suplementaria: en locales húmedos (baños, piletas)

### 12.2 Sección del conductor de protección PE
- Si S_fase ≤ 16 mm²: S_PE = S_fase
- Si 16 < S_fase ≤ 35 mm²: S_PE = 16 mm²
- Si S_fase > 35 mm²: S_PE = S_fase / 2

### 12.3 Verificación de protección contra contactos indirectos (esquema TT)
- Tiempo de desconexión máximo admisible en función de la tensión de contacto:
  - UL = 50 V (locales secos) → ta máx según curva de seguridad IEC 60479
  - UL = 25 V (locales húmedos, piletas)
- Con DDR: el tiempo de desconexión es prácticamente instantáneo (< 200 ms)
- Verificar: RTP × IΔn ≤ UL

---

## ETAPA 13 — Verificaciones finales y documentación

### 13.1 Checklist de verificación normativa
- Esquema de distribución conforme AEA 771.6
- Circuitos mínimos conforme grado de electrificación (AEA 771.8)
- Carga total dentro del límite de demanda simultánea
- Icc mín > umbral de disparo magnético en todos los circuitos
- I²t ≤ K²S² en todos los circuitos (protección térmica en cc)
- Caída de tensión ≤ límite normativo en todos los circuitos
- RTP cumple criterio DDR
- Capacidades de ruptura ≥ Icc máx en todos los puntos
- Factor de llenado de cañerías dentro de límites
- Tableros con espacio de reserva

### 13.2 Inspección y pruebas (AEA 771.23)
- Inspección visual previa a energización
- Prueba de continuidad del conductor PE
- Prueba de resistencia de aislamiento (mínimo 1 MΩ entre fase y tierra)
- Prueba de resistencia de puesta a tierra (método de caída de potencial)
- Verificación de polaridad
- Prueba funcional de DDR (botón de test + verificación de apertura)
- Prueba de disparo con corriente diferencial real (opcional, equipos de prueba)

### 13.3 Documentación de entrega
- Memoria de cálculos (ver calculation-memo-template.md)
- Planos unifilares actualizados
- Esquema de conexión a tierra
- Certificado de instalación eléctrica (firmado por profesional matriculado)
- Planilla de cargas (planilla de demanda)
- Protocolo de pruebas y mediciones

---

## Mapa de dependencias resumido

```
ETAPA 0 (Datos de partida)
    │
    ├─► ETAPA 1 (Esquema de tierra)
    │       │
    │       └─► ETAPA 12 (Sistema de tierra)
    │
    ├─► ETAPA 2 (Cargas y demanda)
    │       │
    │       ├─► ETAPA 4 (Conductores BT)
    │       │       │
    │       │       ├─► ETAPA 5 (Protecciones BT)
    │       │       ├─► ETAPA 6 (Caída de tensión)
    │       │       ├─► ETAPA 7 (Canalizaciones)
    │       │       └─► ETAPA 8 (Tableros)
    │       │
    │       └─► ETAPA 11 (Tipos de circuitos)
    │
    ├─► ETAPA 3 (Corrientes de cc)
    │       │
    │       ├─► ETAPA 4 (Conductores BT)
    │       ├─► ETAPA 5 (Protecciones BT)
    │       ├─► ETAPA 9 (Cables MT)
    │       └─► ETAPA 10 (Protecciones MT)
    │
    └─► ETAPA 9 (Cables MT)
            │
            └─► ETAPA 10 (Protecciones MT)

[TODAS LAS ETAPAS] ──► ETAPA 13 (Verificaciones finales)
```
