---
name: "request-quotation"
description: "getCotizacion(lista, proveedores<=10): cotiza materiales eléctricos en distribuidoras de Argentina y devuelve un Excel comparativo, un proveedor por columna, con hipervínculos."
---

# getCotizacion

Firma: `getCotizacion(lista: [{descripcion, cant, um}], maxProveedores = 10) -> Cotizacion_Comparativa_Proveedores.xlsx`

Usar cuando el usuario pasa una lista de materiales eléctricos (descripción, cantidad, U/M) y pide precios reales con links verificables y/o una comparación de costos entre proveedores. Por convención del usuario, las capacidades se nombran como funciones (getXxx).

Si el usuario invoca la skill sin lista, mirar primero la carpeta conectada (puede haber fotos de placas/tableros de las que se deduce el equipo) y, si no hay lista, pedirla (descripción, cantidad, U/M) en una sola pregunta corta.

## Reglas del usuario
- Solo comercios/distribuidoras reales de Argentina (preferir Buenos Aires, pero buscar en todo el país) con tienda online o catálogo público de precios. Un vendedor extranjero que muestra precios en ARS (p. ej. WiAutomation, que figura como empresa suiza) NO entra como columna: se informa solo en la hoja Notas con su link, precio y la aclaración.
- MercadoLibre únicamente como ÚLTIMA opción, si el producto no está en ninguna web de distribuidor.
- Máximo 10 proveedores (columnas). Cada proveedor es una COLUMNA; en cada celda va solo el precio (número) con hipervínculo directo al producto. Sin texto extra en la celda.
- Todo precio debe tener su link: el usuario lo usa para verificar y comprar. No inventar precios, URLs, marcas ni modelos.
- Celdas sin precio pero con producto publicado:
  - Si la web dice stock disponible y no muestra precio: poner la palabra `STOCK` en la celda, con hipervínculo al producto, para que el usuario llame a pedir cotización.
  - Si la web solo tiene botón "Cotizar"/"Consultar" (sin precio ni stock): poner `COTIZAR` con hipervínculo al producto.
  - No usar STOCK si la web no lo dice explícitamente. Si el stock figura 0 / "Sin stock", cotizar igual el precio pero anotarlo en la fila y en Notas.
- Marcas pedidas por el usuario: cotizarlas siempre como filas separadas aunque no se encuentren (fila queda A COTIZAR con nota). Si el usuario nombra una marca sin línea de producto (p. ej. Allen-Bradley para ATS), dejar la fila y anotar que no se halló línea.
- Orden de búsqueda cuando no hay lo pedido: (1) el modelo exacto; (2) equivalente razonable de la misma marca; (3) otras marcas que el usuario pidió; (4) ÚLTIMO RECURSO, otro fabricante con las mismas características técnicas que dio el usuario (fila "ALTERNATIVA"); (5) MercadoLibre; (6) si no hay en ningún lado, capacidad mayor (p. ej. 80/100 A) en filas "MAYOR CAPACIDAD". Las filas alternativas o de mayor capacidad son opciones distintas: no se suman entre sí.
- Cada fila sin precio lleva en una columna extra "A QUIÉN PEDIR COSTO (link)" un hipervínculo a quién consultar.

## Proceso
1. Crear la lista de tareas. Avisar en una frase qué se va a hacer. Cuando la búsqueda se alarga, avisar el avance al usuario con SendUserMessage (qué se halló, qué falta).
2. Interpretar los ítems (19mm = 3/4"; 16mm = 5/8"; 9,5mm = 3/8"; tomacable = grampa de jabalina). Si la U/M del usuario parece incorrecta (ej. "m" para una térmica), mantenerla y anotarlo. Para equipos (ATS, etc.), traducir las características pedidas (polos, tensión, corriente, retorno automático, enclavamiento, manual/auto, señalización) y verificarlas contra ficha técnica.
3. Búsqueda. WebSearch devuelve casi solo títulos/URLs, no precios; los precios salen de WebFetch o del navegador integrado sobre páginas de tienda. Usar `allowed_domains: ["com.ar"]` para sesgar a Argentina.
   - Easy (VTEX): `https://www.easy.com.ar/api/catalog_system/pub/products/search?ft=<UNA_PALABRA>`
   - Paternal SRL (WooCommerce, CABA): `https://paternalsrl.com.ar/?s=<termino>&post_type=product`
   - Electromisiones (PrestaShop, Misiones): páginas de categoría. Usar el precio de lista (entre paréntesis).
   - Electricidad Centro (Tiendanube): categorías por marca
   - EBA Eléctrica Buenos Aires (PrestaShop): navegador integrado para búsqueda. Muestra precio de lista (con IVA) y stock.
   - Casa Magnani / MGN (Schneider): búsqueda `https://magnani.com.ar/s/?q=<termino>`. Mayoría sin precio, solo COTIZAR.
   - Leimat (Tiendanube, energía solar): páginas de producto con precio.
   - Electricidad MAVA, Treselec (conmutadoras), Ingeniería Boggio, Jalux (distribuidor Siemens).
   - Sodimac AR y Casa Wurm: página de producto.
   - Bloquean WebFetch o no cargan: ElectroTucumán, Pelba, Lumen, IMCOFUE, Electrojoma, e631, Complementos Eléctricos, La Eléctrica, LIESA, Distribuidores del Sud, CHINT Argentina, Mercado Shops. Informarlo como pendiente manual.
   - MercadoLibre exige iniciar sesión: nunca ingresar credenciales; decirle al usuario que puede iniciar sesión él mismo en el navegador integrado y reintentar. Si los resultados de WebSearch muestran precio en el título, anotarlo solo como pista.
   - Las categorías se truncan en ~10-30 productos; usar `?page=N` o un prompt acotado al ítem.
   - La shell del contenedor no llega a estos sitios (proxy); usar WebFetch o el navegador integrado.
4. Verificar contra la página de producto cuando listado y producto puedan diferir; preferir el valor de la página de producto.
5. Equivalencias: si el producto exacto no existe, usar el más cercano solo si es razonable y anotarlo en la hoja Notas.

## Excel (openpyxl; verificar con LibreOffice → csv)
Hoja "Comparativo": ITEM | DESCRIPCIÓN | CANT | U/M | <un proveedor por columna> | PROMEDIO PRECIO UNIT | PRECIO MÍNIMO | SUBTOTAL (promedio x cant) | A QUIÉN PEDIR COSTO (link).
- Celdas de precio: valor numérico + `cell.hyperlink = url`, formato `$ #,##0.00`, fuente azul subrayada. Celdas STOCK/COTIZAR: texto con hipervínculo y misma fuente. Encabezado de columna = nombre del comercio.
- Fórmulas: promedio `=IFERROR(AVERAGE(rango),"A COTIZAR")`, mínimo `=IF(COUNT(rango)=0,"A COTIZAR",MIN(rango))`, subtotal `=IF(ISNUMBER(prom),prom*cant,"A COTIZAR")`. AVERAGE/COUNT ignoran el texto STOCK/COTIZAR. Fila TOTAL con SUM solo si las filas son ítems que se compran juntos; si son opciones alternativas, no totalizar y agregar la nota "cada fila es una opción distinta (no se suman entre sí)".
- Hoja "Totales por proveedor": ítems con precio (COUNT) y, si corresponde, total con SUMPRODUCT precio×cantidad.
- Hoja "Notas": fecha del relevamiento, precios con impuestos o no, criterio de Electromisiones (lista), equivalencias, ítems sin precio y a quién pedirlos, vendedores no argentinos descartados (con su precio y link), características requeridas a verificar en ficha técnica, sitios no accesibles/bloqueados y MercadoLibre.
- Congelar paneles en E2, anchos razonables, wrap en descripción.
- Entregar con SendUserFile y, si hay carpeta conectada, copiar también allí con device_commit_files.

## Cierre
Resumir en pocas líneas: cuántos proveedores, ítems sin precio o con un solo proveedor (y a quién pedirlos), equivalencias/alternativas a revisar, stock 0 donde corresponda, y que los precios son de la fecha del relevamiento. No afirmar "STOCK" que la web no diga. Terminar con lista "Sources:".
