---
name: "size-feeder"
description: "Dimensiona y verifica alimentadores y circuitos seccionales en BT segun AEA 90364-7-771 (Ed. 2006), con formulario de entrada previo, criterios de caida de 1 %, 3 % y 5 %, búsqueda Al y, si no cumple, Cu XLPE. Arma la Memoria de Calculo y la Sintesis de Proyecto (Markdown, sin PDF)."
---

# AEA 90364-7-771 - Dimensionamiento de alimentadores (paso a paso)

## Paso 0 - Formulario de entrada (siempre primero)
Antes de calcular, presentar al usuario este formulario y esperar sus respuestas. No calcular con datos inventados. Los campos marcados (obligatorio) no tienen valor por defecto.

**Datos de partida**
- Potencia activa P (kW): (obligatorio)
- Tensión nominal U (V): 380 trifásica o 220 monofásica. (obligatorio)
- Longitud del tendido L (m): (obligatorio)
- Configuración: número de ternas en paralelo, 1, 2 o 4. (obligatorio)
- Material del conductor: Al o Cu. (obligatorio)
- Aislación: XLPE (valor por defecto) u otra.
- Tipo de cable: unipolar flexible clase 5 (fijo por regla).
- Tipo de canalización: conducto enterrado (método D1), directamente enterrado (D2), bandeja u otra. (obligatorio)

**Datos de instalación**
- Profundidad de zanja (m): 0,70 por defecto.
- Temperatura del terreno (°C): 25 por defecto.
- Resistividad térmica del terreno (K·m/W): 1,0 por defecto.
- Separación entre conductos o cables: en contacto por defecto (hipótesis conservadora, señalarlo en la MC).

**Protección**
- Icu del MCCB (kA): 36 por defecto (mínimo de fabricación), a confirmar con la Icc en cabecera.
- Icc mínima en el extremo (kA): opcional. Si no se da, queda pendiente.

**Criterio de caída**: se calculan siempre 1 %, 3 % y 5 %. El cliente elige el final.

**Fijos por regla (no se preguntan)**
- cos φ = 0,85 y sen φ = 0,53 (valores que propone 771.19.7). Se presentan como criterio de proyecto.
- Número de ternas: solo 1, 2 o 4. Nunca 3.
- Cable unipolar flexible clase 5: Iz0 × 0,95.
- Un solo MCCB común para todas las alternativas de cable.
- Sin bloque de firmas en MC ni en SP.

Si el usuario no responde un campo obligatorio, preguntar solo por esos campos. Si responde "lo que sea" o "tú decide" en un campo obligatorio, adoptar un valor razonable y declararlo como supuesto en la MC.

## Principio
El cálculo se hace en etapas. Cada etapa usa solo los datos ya conocidos. El cable concreto (sección, formación) no se nombra hasta la etapa de selección. Se calcula todo antes de concluir si cumple.

## Etapa 1 - Corriente de proyecto
IB = P / (√3 · U · cos φ).

## Etapa 2 - Criterio de caída de tensión
ΔU_adm = U · criterio, para 1 %, 3 % y 5 %.
Comentario obligatorio en la MC: la norma (771.13.b, Nota) establece que en ningún caso la caída de tensión en los circuitos seccionales debe exceder el 1 %. El 3 % (terminales de iluminación) y el 5 % (circuitos que alimentan solo motores) corresponden a circuitos terminales. Queda a elección del cliente decidir si usa 1 %, 3 % o 5 % como criterio final.

## Etapa 3 - Método de cálculo de la caída
Con cos φ = 0,85 se usa el método general (771.19.7 a): ΔU = √3 · I · L(km) · (R · cos φ + X · sen φ), con I = IB / N.
- R a 90 °C = R20 · (1 + α · 70), con α = 0,00403 para Al y 0,00393 para Cu.
- R20 clase 2 (IEC 60228, Ω/km). Al: 70 mm² 0,443; 95: 0,320; 120: 0,253; 150: 0,206; 185: 0,164; 240: 0,125; 300: 0,100. Cu: 70 mm² 0,268; 95: 0,193; 120: 0,153; 150: 0,124; 185: 0,0991; 240: 0,0754; 300: 0,0601.
- X típica 0,08 Ω/km para unipolares en trébol en contacto (confirmar con ficha del fabricante).
- IEC 60228 define la clase 5 solo para cobre. Para Al flexible se usan los R20 de clase 2 y se advierte en la MC.
El GDC (771.19.7 c) está tabulado solo para cos φ = 0,8 (trifásico Cu 0,035, Al 0,055). No usarlo con cos φ = 0,85.

## Etapa 4 - Sección mínima por capacidad de conducción
Iz = N · Iz0 · 0,95 · k1 · k_rho · k_agr · fs >= IB. Iz0,min = IB / (N · 0,95 · k1 · k_rho · k_agr · fs). Tabular para N = 1, 2 y 4, para Al y Cu. Si ninguna sección alcanza para un N, indicarlo.

### Corriente base Iz0
Tabla 771.16.V (D1, caño enterrado) y 771.16.VI (D2, directamente enterrado), 25 °C, 1 K·m/W, 0,7 m, 3 conductores cargados.
Sección mm²: 4 / 6 / 10 / 16 / 25 / 35 / 50 / 70 / 95 / 120 / 150 / 185 / 240 / 300
- Al XLPE, D1: 33 / 41 / 53 / 69 / 88 / 106 / 127 / 156 / 186 / 211 / 238 / 267 / 308 / 349 A
- Al XLPE, D2: 40 / 52 / 67 / 88 / 115 / 137 / 162 / 198 / 239 / 272 / 305 / 347 / 403 / 456 A
- Cu XLPE, D1: 42 / 52 / 69 / 89 / 114 / 138 / 163 / 202 / 239 / 272 / 307 / 344 / 398 / 449 A
- Cu XLPE, D2: 51 / 64 / 87 / 113 / 148 / 177 / 209 / 256 / 308 / 351 / 393 / 447 / 519 / 586 A
En la Tabla 771.16.VI usar siempre la columna "3x". Las "2x" son bipolares. Para PVC o secciones de 400 mm² o más, pedir las tablas al usuario.

### Factores de corrección
- k1 (VII a), XLPE: 10 °C 1,11; 20 °C 1,04; 25 °C 1,00; 30 °C 0,97; 35 °C 0,93; 40 °C 0,89; 45 °C 0,83; 50 °C 0,79.
- k_rho (VII b), conductos / directamente enterrados: 0,5: 1,08 / 1,25; 0,8: 1,02 / 1,08; 1,0: 1,00 / 1,00; 1,5: 0,93 / 0,85; 2,0: 0,89 / 0,75; 2,5: 0,85 / 0,67; 3,0: 0,81 / 0,60.
- k_agr conductos (VII d2), en contacto / 0,25 m / 0,5 m / 1,0 m: 1 circuito 1,00; 2 circuitos 0,80 / 0,90 / 0,90 / 0,95; 4 circuitos 0,65 / 0,75 / 0,80 / 0,90.
- k_agr directamente enterrados (VII c), en contacto / 1 diámetro / 0,125 m / 0,25 m / 0,5 m: 1 circuito 1,00; 2 circuitos 0,75 / 0,80 / 0,85 / 0,90 / 0,90; 4 circuitos 0,60 / 0,60 / 0,70 / 0,75 / 0,80.
- Unipolares directamente enterrados separados al menos un diámetro: 1,07 (nota 771.16.2.3.4).
- fs (771.16.2.3.2): 1,0 para 2 o 4 cables por fase con la disposición de 771.12.3.13.1; 0,8 si no se respeta.
- Neutro con THD < 15 % no cuenta como cargado; PE nunca cuenta (nota 8 de la Tabla 771.16.IV).

## Etapa 5 - Aluminio: sección adoptada y verificación
Para N = 1, 2 y 4, tabular Iz, R90, ΔU (V y %) y estado frente a 1 %, 3 % y 5 %. Por cada criterio, adoptar la primera configuración que cumpla capacidad y caída, con el menor N y luego la menor sección. Indicar qué requisito rige. Un conductor CUMPLE solo si Iz >= IB y ΔU <= ΔU_adm.

## Etapa 6 - Cobre XLPE cuando el aluminio no cumple
Si para algún criterio el aluminio no cumple con N hasta 4 y secciones hasta 300 mm², repetir las Etapas 4 y 5 con cobre XLPE. Adoptar la primera configuración que cumpla, con el menor N y luego la menor sección. Presentar la tabla de búsqueda con las descartadas. Los criterios donde el aluminio cumple siguen con aluminio. Si el margen del cobre es menor a 10 % del límite, advertirlo.

## Etapa 7 - Neutro y conductor de protección
- Neutro: 771.16.2.4, sección igual a la de fase (S_N = S). Si el usuario pide neutro reducido, advertir el conflicto y que, según 771.20.5.3, exige protección de sobreintensidad propia con tetrapolar protegido en los cuatro polos.
- PE (771.18.III): S <= 16: S; 16 < S <= 35: 16; S > 35: S/2. Mismo material que la línea.
- PE de otro material (771-C.II): S_PE = (k1/k2) · S/2 para S > 35. k1 Al XLPE 94; k2 Cu XLPE aislado 170.
- Un PE por terna. Sección mínima 2,5 mm².

## Etapa 8 - Protección contra sobrecarga
IB <= In <= Iz, con In = Ir en protecciones regulables (771.19.2.1). Verificar I2 <= 1,45 · Iz, con I2 = 1,3 · In para IEC 60947-2 (In > 63 A). Un único MCCB cuya Ir cumpla con el caso de menor Iz; indicar el margen de Ir sobre IB.

## Etapa 9 - Cortocircuito térmico
Para t entre 0,1 s y 5 s: S >= I · √t / k. k (771.19.II): Al XLPE 94; Cu XLPE 143; Cu PVC 115; Al PVC 76. Verificar sobre un solo conductor. Icc mínima (771.19.2.2.4) pendiente si no hay dato.

## Documentos
- MC: Objeto y Alcance; Marco Regulatorio (con cláusulas); Parámetros de Diseño (con los datos del formulario y los fijos por regla); Cálculo por etapas con fórmula, valores y resultado; Conclusión; Puntos a verificar. Sin firmas.
- SP: Objeto; Alcance; Tabla de Resumen de dos columnas (Requisito Normativo AEA 771-F.1.1 | Datos Técnicos), con identificación, demanda, secciones, IB, protección, ΔU, Icc, canalización y ambiente; máximo tres observaciones. Sin firmas.

## Formato
- Coma decimal. 1 decimal en tensiones, porcentajes y corrientes de cálculo.
- Unidades en el encabezado de columna, no en cada celda.
- Cada celda con valor. Si falta un dato, "No suministrado" o "Pendiente".

## Fuente y límites
- Tablas de AEA 90364-7-771 Edición 2006. Otra edición requiere las tablas del usuario.
- R20 provienen de IEC 60228; X es típico, no normativo.
- No calcula Icc (AEA 90909) ni selectividad.

## Runtime
The code is a Python package from `engine/` (`epc_calc`). In a repository checkout set `PYTHONPATH=engine/calc/src` (use `;` as separator on Windows) or run `pip install -e engine/<area>`; in an installed plugin set `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/lib"`. Run modules with `python -m <module>`.
