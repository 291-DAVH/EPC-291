"""Reglas de ingeniería de las Partes 4 y 5 de AEA 90364 (edición 2006), que están escaneadas (sin texto).

El texto sale de OCR, que pierde tildes y desfigura las tablas. Por eso cada regla lleva una `verificacion`:
  - "ocr":    la `cita` se buscó en el OCR de la página PDF indicada (sin tildes ni vocales, para tolerar
              errores del OCR). Los números en prosa se contrastaron además con la imagen de la página.
  - "visual": los valores de la tabla se leyeron sobre la imagen de la página (100-120 dpi) porque el OCR
              las desfigura. La `cita` es el título de la tabla, verificado contra el OCR.
Se registra la página PDF y la página impresa de la norma (p. ej. 54-5).

Cada regla: R(grupo, id, tema, regla, tipo, parametros, aplica_a, norma, clausula, pdf, impresa, cita,
verificacion, tabla=None). `norma` es el sufijo del documento: "4-41", "4-43", "5-51", "5-52", "5-54".
"""
import os
import re
import unicodedata

PDF = {"4": "AEA_90364-4.pdf", "5": "AEA_90364-5.pdf"}
REGLAS_OCR = []
ALL = ["viviendas", "oficinas", "locales"]
TODO = ["viviendas", "oficinas", "locales", "industrias"]


def R(grupo, id_, tema, regla, tipo, params, aplica, norma, clausula, pdf, impresa, cita, verif, tabla=None):
    REGLAS_OCR.append(dict(grupo=grupo, id=f"{grupo}.{id_}", tema=tema, regla=regla, tipo=tipo, parametros=params,
                           aplica_a=aplica, norma=norma, clausula=clausula, pdf=pdf, impresa=impresa, cita=cita,
                           verificacion=verif, tabla=tabla))


def esqueleto(t):
    """Texto sin tildes, en minúsculas, solo letras y dígitos, sin vocales (tolera errores de OCR).
    La 'ñ' se escribe como 'fi' (así la lee el OCR) y el '6' entre letras (una 'ó' mal leída) se descarta."""
    t = t.lower().replace("ñ", "fi")
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"(?<=[a-z])6(?=[a-z])", "", t)
    return re.sub(r"[aeiou]", "", re.sub(r"[^a-z0-9]", "", t))


UMBRAL = 0.88      # similitud mínima de la cita con el mejor tramo de la página (el OCR confunde letras sueltas)


def verificar_cita(dir_ocr, parte, pdf, cita):
    """True si la cita figura en el OCR de la página PDF, con tolerancia a errores de lectura de letras sueltas."""
    import difflib
    ruta = os.path.join(dir_ocr, f"n{parte}_p{pdf:03d}.txt")
    pagina = esqueleto(open(ruta, encoding="utf-8", errors="ignore").read())
    c = esqueleto(cita)
    if c in pagina:
        return True
    n = len(c)
    sm = difflib.SequenceMatcher(None, autojunk=False)
    sm.set_seq2(c)
    for i in range(0, max(1, len(pagina) - n + 1)):
        sm.set_seq1(pagina[i:i + n + 3])
        if sm.real_quick_ratio() >= UMBRAL and sm.quick_ratio() >= UMBRAL and sm.ratio() >= UMBRAL:
            return True
    return False


# ============================================================== puesta a tierra (Cap. 54)
G = "puesta_a_tierra"
R(G, "tt_ra_maxima", "Resistencia de puesta a tierra de protección (esquema TT)",
  "El valor máximo permanente de la resistencia de puesta a tierra de protección es 40 Ω.", "obligatorio",
  {"ra_max_ohm": 40, "tension_limite_v": 24}, TODO, "5-54", "541.3", 244, "54-4",
  "debe ser menor o igual a 40 ohm", "ocr")
R(G, "tt_ra_tabla_54_1", "Resistencia máxima de la toma de tierra de las masas (esquema TT)",
  "La Ra máxima depende de la corriente diferencial asignada IΔn; para IΔn ≤ 30 mA y 100–300 mA el valor de la columna 3 es 40 Ω.",
  "obligatorio", {"columna_adoptada": 3, "ra_max_general_ohm": 40}, TODO, "5-54", "Tabla 54.1", 245, "54-5",
  "Valores máximos de resistencia de puesta a tierra de protección para un esquema TT", "visual",
  tabla={"unidades": {"IΔn": "A", "Ra": "Ω"},
         "columnas": ["IΔn [A]", "col1 Ra para UL=50 V [Ω]", "col2 Ra para UL=24 V [Ω]", "col3 Ra máximo permitido [Ω]"],
         "filas": [[20, 2.5, 1.2, 0.6], [10, 5, 2.4, 1.2], [5, 10, 4.8, 2.4], [3, 17, 8, 4],
                   [1, 50, 24, 12], [0.5, 100, 48, 24], [0.3, 167, 80, 40], [0.1, 500, 240, 40],
                   [0.03, 1666, 800, 40]],
         "nota": "Sensibilidad baja: 3 A a 20 A; media: 100 mA a 1 A; alta: hasta 30 mA inclusive. La columna 3 es la adoptada por la norma."})
R(G, "electrodos_materiales_resistencia", "Materiales de los electrodos de tierra",
  "Los materiales y dimensiones de los electrodos se eligen para resistir la corrosión y tener resistencia mecánica adecuada.",
  "obligatorio", {}, TODO, "5-54", "542.2.1", 245, "54-5",
  "deberán ser seleccionados para resistir la corrosión y tener adecuada resistencia mecánica", "ocr")
R(G, "electrodos_dimensiones_tabla_54_2", "Dimensiones mínimas de los electrodos enterrados",
  "Dimensiones mínimas de los electrodos enterrados según material, forma y revestimiento.", "obligatorio",
  {}, TODO, "5-54", "Tabla 54.2", 246, "54-6",
  "Dimensiones mínimas que deben cumplir los electrodos de puesta a tierra enterrados en el suelo", "visual",
  tabla={"unidades": {"diametro": "mm", "seccion": "mm²", "espesor": "mm", "recubrimiento": "µm"},
         "columnas": ["material", "superficie", "forma", "diametro_mm", "seccion_mm2", "espesor_mm", "recubrimiento_individual_um", "recubrimiento_medio_um"],
         "filas": [["acero", "galvanizado por inmersión en caliente o inoxidable", "fleje o pletina", None, 100, 3, 70, 70],
                   ["acero", "galvanizado por inmersión en caliente o inoxidable", "perfiles", None, 100, 3, 70, 70],
                   ["acero", "galvanizado por inmersión en caliente o inoxidable", "jabalina redonda para electrodo profundo", 12.6, 124, None, 70, 70],
                   ["acero", "galvanizado por inmersión en caliente o inoxidable", "barra redonda para electrodo de superficie", 10, None, None, None, 50],
                   ["acero", "galvanizado por inmersión en caliente o inoxidable", "caño", 25, 145, 2, 47, 55],
                   ["acero", "recubierto de cobre", "jabalina redonda para electrodo profundo", 15, None, None, 2000, None],
                   ["acero", "cobre depositado por electrólisis", "jabalina redonda para electrodo profundo", 14, None, None, "según IRAM 2309", "según IRAM 2309"],
                   ["cobre", "desnudo", "fleje o pletina", None, 50, 2, None, None],
                   ["cobre", "desnudo", "barra redonda para electrodo de superficie", None, 25, None, None, None],
                   ["cobre", "desnudo", "cable (1,8 mm por cada hilo)", 1.8, 35, None, None, None],
                   ["cobre", "desnudo", "caño", 20, None, 2, None, None],
                   ["cobre", "estañado", "cable (1,8 mm por cada hilo)", 1.8, 25, None, 1, 5],
                   ["cobre", "cincado", "fleje o pletina", None, 50, 2, 20, 40]],
         "notas": ["Cobre desnudo, barra redonda de superficie: 16 mm² si el riesgo de corrosión y daño mecánico es extremadamente bajo.",
                   "Un electrodo es 'de superficie' si se instala a una profundidad que no excede 0,5 m."]})
R(G, "jabalina_minima", "Jabalina de acero galvanizado",
  "Como mínimo se emplea una jabalina JA o JL de 16 x 1500 mm.", "obligatorio",
  {"diametro_mm": 16, "largo_mm": 1500, "jabalina_acero_cobre_min": "JL o JA 14 x 1500 mm"}, TODO, "5-54", "542.2.3", 248, "54-8",
  "Como minimo se debe emplear una jabalina JA o JL 16 x 1500 mm", "ocr")
R(G, "armaduras_no_electrodo", "Armaduras de hormigón armado",
  "No se permiten las armaduras de hormigón armado como electrodo específico de puesta a tierra, aunque sí se equipotencializan.",
  "prohibido", {}, TODO, "5-54", "542.2.3", 248, "54-8",
  "No se permite el empleo de las armaduras de hormigon armado como electrodo especifico de puesta a tierra", "ocr")
R(G, "anillo_cimientos_dos_hincados", "Electrodo de anillo en cimientos (obras nuevas)",
  "Si se usa un conductor desnudo en el fondo de las zanjas de cimientos como electrodo, se incorporan como mínimo dos electrodos hincados en extremos opuestos del anillo, con cámara de inspección y barra de medición.",
  "obligatorio", {"electrodos_hincados_min": 2}, TODO, "5-54", "542.2.3", 248, "54-8",
  "se deberan incorporar como minimo dos electrodos hincados en extremos opuestos del anillo", "ocr")
R(G, "canerias_no_electrodo", "Cañerías metálicas de servicios",
  "Las cañerías de agua, líquidos o gases inflamables, calefacción central, vainas de plomo y otras envolturas de cables no se emplean como electrodos de puesta a tierra.",
  "prohibido", {}, TODO, "5-54", "542.2.6", 248, "54-8",
  "no se deberan emplear como electrodos de puesta a tierra", "ocr")
R(G, "electrodo_camara_inspeccion", "Cámara de inspección de cada electrodo",
  "Cada electrodo finaliza en una cámara de inspección para poder desconectar el conductor que lo vincula al sistema de puesta a tierra.",
  "obligatorio", {}, TODO, "5-54", "542.2.6 Nota 2", 248, "54-8",
  "Cada electrodo debe finalizar en una camara de inspeccion", "ocr")
R(G, "jabalinas_separacion", "Electrodos en paralelo",
  "Si se conectan varias jabalinas en paralelo se recomienda una separación igual o mayor que 2 veces el largo de la jabalina de mayor longitud.",
  "recomendado", {"separacion_min_veces_largo": 2}, TODO, "5-54", "542.2.2 Nota", 247, "54-7",
  "sea igual o mayor que 2 veces el largo de la jabalina de mayor longitud del conjunto", "ocr")
R(G, "verificar_por_medicion", "Verificación de la puesta a tierra",
  "El valor de la resistencia de puesta a tierra se verifica por medición al final de la ejecución de los trabajos y periódicamente según AEA 90364-6-61.",
  "obligatorio", {}, TODO, "5-54", "542.2.2", 247, "54-7",
  "debera ser verificada por medicion al final de la ejecucion de los trabajos", "ocr")
R(G, "conductor_enterrado_tabla_54_3", "Sección mínima de los conductores de puesta a tierra enterrados",
  "Los conductores de puesta a tierra enterrados cumplen 543.1 y las secciones mínimas de la Tabla 54.3.", "obligatorio",
  {"cu_mm2": {"protegido_corrosion_y_mecanica": 4, "protegido_corrosion_sin_mecanica": 16, "sin_proteccion_corrosion": 25},
   "fe_mm2": {"protegido_corrosion_y_mecanica": 10, "protegido_corrosion_sin_mecanica": 16, "sin_proteccion_corrosion": 50}},
  TODO, "5-54", "Tabla 54.3", 249, "54-9", "Secciones minimas de los conductores de puesta a tierra enterrados", "visual",
  tabla={"unidades": {"seccion": "mm²"},
         "columnas": ["protección contra la corrosión", "protegido mecánicamente", "no protegido mecánicamente"],
         "filas": [["protegido contra la corrosión", "4 Cu / 10 Fe", "16 Cu / 16 Fe"],
                   ["no protegido contra la corrosión", "25 Cu / 50 Fe", "25 Cu / 50 Fe"]]})
R(G, "barra_medicion_dimensiones", "Barra de medición local",
  "La barra de medición de la cámara de inspección mide como mínimo 30 mm x 3 mm x 100 mm, con al menos 5 perforaciones.",
  "obligatorio", {"ancho_mm": 30, "espesor_mm": 3, "largo_mm": 100, "perforaciones_min": 5}, TODO, "5-54", "542.4", 249, "54-9",
  "30 mm x 3 mm x 100 mm, con por lo menos 5 perforaciones", "ocr")
R(G, "bep_obligatoria", "Barra equipotencial principal (BEP)",
  "Toda instalación prevé una barra equipotencial principal (o barra principal de puesta a tierra) con puntos de conexión individuales para cada conductor.",
  "obligatorio", {}, TODO, "5-54", "542.4.1", 249, "54-9",
  "con puntos de conexion individuales para cada conductor", "ocr")
R(G, "bep_desconexion_individual", "Desconexión de los conductores de la BEP",
  "Cada conductor conectado a la BEP o a la barra principal de puesta a tierra debe poder desconectarse individualmente, y el desmontaje requiere herramienta.",
  "obligatorio", {}, TODO, "5-54", "542.4.2", 250, "54-10",
  "debera poderse desco- nectar individualmente", "ocr")
R(G, "conductor_FE_color", "Conductor de puesta a tierra funcional (FE)",
  "El conductor FE no puede ser verde, amarillo ni bicolor verde-amarillo; se marca con la sigla FE y se recomienda aislación blanca.",
  "recomendado", {"marca": "FE", "color_recomendado": "blanco"}, TODO, "5-54", "542.4.1 Nota 2", 250, "54-10",
  "el conductor debera ser marcado con la sigla FE", "ocr")

# ============================================================== conductores de protección (543, 544)
G = "conductores_proteccion"
R(G, "pe_tabla_54_5", "Sección mínima del conductor de protección PE",
  "Para S ≤ 16 mm² el PE tiene sección S; para 16 < S ≤ 35, 16 mm²; para S > 35, S/2 (mismo material). Con otro material se multiplica por k1/k2.",
  "obligatorio", {"s_le_16": "S", "s_16_a_35_mm2": 16, "s_gt_35": "S/2", "otro_material": "k1/k2"}, TODO, "5-54", "Tabla 54.5", 251, "54-11",
  "Secciones minimas de los conductores de puesta a tierra y de proteccion", "visual",
  tabla={"unidades": {"S": "mm²"},
         "columnas": ["S de línea", "S_PE mismo material", "S_PE otro material"],
         "filas": [["S ≤ 16", "S", "(k1/k2)·S"], ["16 < S ≤ 35", "16", "(k1/k2)·16"], ["S > 35", "S/2", "(k1/k2)·S/2"]],
         "notas": ["k1: valor de k del conductor de línea (Tabla 54.8 o Tabla 43.1); k2: valor de k del PE (Tablas 54.6 a 54.10).",
                   "Para el PEN la reducción de sección solo se permite según las reglas de dimensionamiento del neutro (Cap. 52)."]})
R(G, "pe_formula_adiabatica", "Sección del PE por el calor de la falla",
  "El PE se dimensiona con S = √(I²·t)/k, solo para tiempos de desconexión 0,1 s < t ≤ 5 s; con limitadores o t < 0,1 s se verifica k²S² ≥ I²t del dispositivo.",
  "obligatorio", {"formula": "S = sqrt(I^2 * t) / k", "t_min_s": 0.1, "t_max_s": 5, "verificacion_limitadores": "k^2 * S^2 >= I^2 * t"},
  TODO, "5-54", "543.1.2", 252, "54-12",
  "La seccion del conductor de proteccion no debera ser menor que el valor determinado por", "ocr")
R(G, "pe_seccion_normalizada_superior", "Sección no normalizada del PE",
  "Si el cálculo da una sección no normalizada se adopta la sección normalizada inmediata superior.", "obligatorio", {},
  TODO, "5-54", "543.1.2", 252, "54-12",
  "se deben utilizar conductores de la seccion normalizada inmediatamente superior", "ocr")
R(G, "k_pe_aislado_tabla_54_6", "Factor k: PE aislado, no incorporado al cable ni agrupado",
  "Valores de k del PE aislado (temperatura inicial 40 °C); el menor valor se aplica a PVC de más de 300 mm².", "obligatorio",
  {"temperatura_inicial_c": 40}, TODO, "5-54", "Tabla 54.6", 252, "54-12",
  "Valores de k para conductores de proteccion aislados", "visual",
  tabla={"columnas": ["aislación", "T_inicial_C", "T_final_C", "k_cobre", "k_aluminio", "k_acero"],
         "filas": [["PVC 70 °C", 40, "160/140", "136/126", "90/83", "50/46"], ["PVC 90 °C", 40, "160/140", "136/126", "90/83", "50/46"],
                   ["EPR o XLPE 90 °C", 40, 250, 170, 113, 62], ["Goma 60 °C", 40, 200, 153, 101, 56],
                   ["Goma 85 °C", 40, 220, 160, 106, 58], ["Caucho siliconado", 40, 350, 196, 130, 71]],
         "nota": "Con dos valores, el menor corresponde a PVC de sección mayor que 300 mm²."})
R(G, "k_pe_desnudo_tabla_54_7", "Factor k: PE desnudo en contacto con la cubierta del cable",
  "Valores de k del PE desnudo en contacto con la cubierta del cable y no agrupado con otros cables.", "obligatorio",
  {"temperatura_inicial_c": 40}, TODO, "5-54", "Tabla 54.7", 253, "54-13",
  "Valores de k para conductores de proteccion desnudos", "visual",
  tabla={"columnas": ["cubierta", "T_inicial_C", "T_final_C", "k_cobre", "k_aluminio", "k_acero"],
         "filas": [["PVC", 40, 200, 153, 101, 56], ["Polietileno", 40, 150, 131, 87, 48],
                   ["Polietileno cloro-sulfonado", 40, 220, 160, 106, 58]]})
R(G, "k_pe_en_cable_tabla_54_8", "Factor k: PE incorporado al cable o agrupado con otros cables",
  "Valores de k del PE incorporado como armadura, o agrupado con otros cables o conductores aislados.", "obligatorio", {},
  TODO, "5-54", "Tabla 54.8", 253, "54-13",
  "Valores de k para conductores de proteccion incorporados", "visual",
  tabla={"columnas": ["aislación", "T_inicial_C", "T_final_C", "k_cobre", "k_aluminio", "k_acero"],
         "filas": [["PVC 70 °C", 70, "160/140", "115/103", "76/68", "42/37"], ["PVC 90 °C", 90, "160/140", "100/86", "66/57", "36/31"],
                   ["EPR o XLPE 90 °C", 90, 250, 143, 94, 52], ["Goma 60 °C", 60, 200, 141, 93, 51],
                   ["Goma 85 °C", 85, 220, 134, 89, 48], ["Caucho siliconado", 180, 350, 132, 87, 47]],
         "nota": "Con dos valores, el menor corresponde a PVC de sección mayor que 300 mm²."})
R(G, "k_cubierta_metalica_tabla_54_9", "Factor k: cubierta metálica del cable como PE",
  "Valores de k de armadura, malla o conductor concéntrico usados como conductor de protección.", "obligatorio", {},
  TODO, "5-54", "Tabla 54.9", 253, "54-13",
  "Valores de k para conductores utilizados como cubierta metalica del cable", "visual",
  tabla={"columnas": ["aislación", "T_inicial_C", "T_final_C", "k_cobre", "k_aluminio", "k_plomo", "k_acero"],
         "filas": [["PVC 70 °C", 60, 200, 141, 93, 26, 51], ["PVC 90 °C", 80, 200, 128, 85, 23, 46],
                   ["EPR o XLPE 90 °C", 80, 200, 128, 85, 23, 46], ["Goma 60 °C", 55, 200, 144, 95, 26, 52],
                   ["Goma 85 °C", 75, 220, 140, 93, 26, 51], ["Mineral con cubierta de PVC", 70, 200, 135, None, None, None],
                   ["Mineral desnudo", 105, 250, 135, None, None, None]]})
R(G, "k_desnudos_tabla_54_10", "Factor k: conductores desnudos sin riesgo para materiales vecinos",
  "Valores de k de conductores desnudos según condiciones (temperatura inicial 40 °C).", "obligatorio", {},
  TODO, "5-54", "Tabla 54.10", 254, "54-14",
  "Valores de k para conductores desnudos donde no existe riesgo", "visual",
  tabla={"columnas": ["condiciones", "T_inicial_C", "k_cobre", "T_max_cobre_C", "k_aluminio", "T_max_aluminio_C", "k_acero", "T_max_acero_C"],
         "filas": [["visible y en área restringida", 40, 224, 500, 122, 300, 81, 500],
                   ["condiciones normales", 40, 153, 200, 101, 200, 56, 200],
                   ["con riesgo de fuego", 40, 131, 150, 87, 150, 48, 150]]})
R(G, "pe_minimo_independiente", "Sección mínima del PE que no forma parte del cable",
  "El PE que no forma parte del cable de alimentación ni comparte envoltura con los conductores de línea tiene como mínimo 2,5 mm² Cu o 16 mm² Al con protección mecánica; 4 mm² Cu o 16 mm² Al sin ella.",
  "obligatorio", {"con_proteccion_mecanica": {"cu_mm2": 2.5, "al_mm2": 16}, "sin_proteccion_mecanica": {"cu_mm2": 4, "al_mm2": 16}},
  TODO, "5-54", "543.1.3", 254, "54-14", "si poseen una proteccion mecanica", "ocr")
R(G, "pe_comun_varios_circuitos", "PE común a varios circuitos",
  "Si el PE es común a varios circuitos se calcula para la condición más desfavorable de corriente de falla y tiempo, o se elige por la Tabla 54.3 con el conductor de línea de mayor sección.",
  "obligatorio", {}, TODO, "5-54", "543.1.4", 254, "54-14",
  "Cuando un conductor de proteccion es comun a varios circuitos", "ocr")
R(G, "pe_tipos_permitidos", "Tipos de conductor de protección",
  "El PE puede ser un conductor de cable multipolar, un conductor aislado bajo envolvente común con los activos, un conductor aislado en perfiles o bandejas, o un conductor desnudo en bandejas.",
  "obligatorio", {}, TODO, "5-54", "543.2.1", 254, "54-14",
  "Los conductores de proteccion pueden ser uno o mas de los siguientes", "ocr")
R(G, "no_usar_como_pe", "Partes metálicas que no pueden ser PE ni equipotencial",
  "No se usan como conductor de protección ni equipotencial: cañerías de agua o de gases/líquidos inflamables, partes de la construcción sometidas a esfuerzos, caños flexibles o doblables a mano, cable portante, vainas y armaduras de ciertos cables, envolturas de canalizaciones y bandejas; sí se equipotencializan.",
  "prohibido", {}, TODO, "5-54", "543.2.3", 255, "54-15",
  "No se permite el empleo de los elementos y partes metalicas que se indican a continuacion", "ocr")
R(G, "pe_sin_dispositivo_de_corte", "Dispositivos de corte en el PE",
  "No se inserta ningún dispositivo de corte o maniobra en el conductor de protección; solo uniones desmontables con herramienta para mediciones.",
  "prohibido", {}, TODO, "5-54", "543.3.3", 255, "54-15",
  "En el conductor de proteccion no debe insertarse ningun dispositivo de corte o maniobra", "ocr")
R(G, "pe_sin_guirnalda", "Masas como parte del circuito de protección",
  "Las masas de equipos no se usan como parte del conductor de protección de otros equipos ni se conectan en serie (guirnalda).",
  "prohibido", {}, TODO, "5-54", "543.3.5", 255, "54-15",
  "no deberan ser empleadas formando parte de los conductores de proteccion de otros materiales", "ocr")
R(G, "pen_prohibido_en_inmuebles", "Conductor PEN (esquema TN-C)",
  "El conductor PEN (TN-C) está prohibido en instalaciones en inmuebles; solo se permite en distribución pública y desde un transformador propio hasta el tablero principal de BT.",
  "prohibido", {"esquema": "TN-C"}, TODO, "5-54", "543.4 Nota 1", 255, "54-15",
  "estan prohibidos para instalaciones en inmuebles", "ocr")
R(G, "pen_seccion_minima", "Sección mínima del conductor PEN",
  "El PEN solo se usa en instalaciones fijas y tiene como mínimo 10 mm² Cu o 16 mm² Al; debe estar aislado para la tensión más elevada.",
  "obligatorio", {"cu_mm2": 10, "al_mm2": 16}, TODO, "5-54", "543.4.1", 256, "54-16",
  "debera tener una seccion no menor que 10", "ocr")
R(G, "pen_separacion_n_pe", "Separación de N y PE desde el PEN",
  "Desde el punto en que N y PE se derivan del PEN, aguas abajo el neutro no se conecta a ninguna parte puesta a tierra ni al PE.",
  "obligatorio", {}, TODO, "5-54", "543.4.3", 256, "54-16",
  "el conductor neutro se conecte a otra parte de la instalacion puesta a tierra", "ocr")
R(G, "pe_junto_a_activos_con_sobreintensidad", "PE con protección por sobreintensidad",
  "Si se usan protecciones de sobreintensidad contra choques eléctricos, el PE va en la misma canalización que los activos (solo TN-S o IT con masas colectivas).",
  "obligatorio", {"esquemas": ["TN-S", "IT masas colectivas"]}, TODO, "5-54", "543.6", 256, "54-16",
  "los conductores de proteccion deben instalarse en la misma canalizacion", "ocr")
R(G, "pe_reforzado_fuga_10ma", "PE reforzado con corriente de fuga mayor que 10 mA",
  "Con corriente en el PE mayor que 10 mA (equipos fijos) el PE tiene como mínimo 10 mm² Cu o 16 mm² Al en todo su recorrido, o se instala un segundo PE.",
  "obligatorio", {"corriente_fuga_umbral_ma": 10, "cu_mm2": 10, "al_mm2": 16}, TODO, "5-54", "543.7", 256, "54-16",
  "los conductores de proteccion deberan ser reforzados", "ocr")
R(G, "equipotencial_principal", "Conductor equipotencial principal",
  "Sección no menor que la mitad del PE de mayor sección de la instalación, con mínimo 6 mm² Cu, 16 mm² Al o 50 mm² acero; puede limitarse a 25 mm² Cu.",
  "obligatorio", {"fraccion_del_pe_mayor": 0.5, "min_cu_mm2": 6, "min_al_mm2": 16, "min_acero_mm2": 50, "max_cu_mm2": 25},
  TODO, "5-54", "544.1.1", 257, "54-17",
  "Los conductores equipotenciales principales, deberan tener una seccion no menor que la mitad", "ocr")
R(G, "equipotencial_suplementario_masa_masa", "Equipotencial suplementario entre masas",
  "Entre dos masas, la sección no es menor que la más pequeña de los conductores de protección conectados a ellas.",
  "obligatorio", {}, TODO, "5-54", "544.2.1", 257, "54-17",
  "no sera menor que la mas pequena de las secciones", "ocr")
R(G, "equipotencial_suplementario_masa_extrana", "Equipotencial suplementario a masa extraña",
  "Entre una masa y una masa extraña, la sección equivalente no es menor que la mitad de la del PE conectado a esa masa.",
  "obligatorio", {"fraccion_del_pe": 0.5}, TODO, "5-54", "544.2.2", 257, "54-17",
  "no sera menor que la mitad de la del conductor de proteccion conectado a esa masa", "ocr")

# ============================================================== identificación de conductores (514)
G = "colores"
R(G, "neutro_pe", "Colores del neutro y del conductor de protección",
  "El neutro es azul claro o celeste; el PE es bicolor verde-amarillo.", "obligatorio",
  {"neutro": "azul claro o celeste", "pe": "verde-amarillo"}, TODO, "5-51", "514.3.1", 45, "51-19",
  "Conductor Neutro: Color Azul claro o celeste", "visual")
R(G, "lineas", "Colores de los conductores de línea",
  "L1 castaño (marrón), L2 negro, L3 rojo.", "obligatorio", {"L1": "castaño (marrón)", "L2": "negro", "L3": "rojo"},
  TODO, "5-51", "514.3.3", 45, "51-19", "Línea 1 (L1) Color Castaño (Marrón)", "visual")
R(G, "pen_marcado", "Conductor PEN aislado",
  "El PEN aislado es verde-amarillo en toda su longitud con marcas azul claro en los extremos (combinación adoptada en la República Argentina).",
  "obligatorio", {"color": "verde-amarillo", "marcas_extremos": "azul claro"}, TODO, "5-51", "514.3.2", 45, "51-19",
  "verde-amarillo en toda su longitud y ademas con marcas azul claro en sus extremos", "ocr")
R(G, "cubierta_verde_amarilla_no_activos", "Cables con cubierta verde o amarilla",
  "No se permiten cables con envoltura verde o amarilla como conductores activos; esos colores de envoltura solo para conductores de protección.",
  "prohibido", {}, TODO, "5-51", "514.3.3", 45, "51-19",
  "No se permite el empleo de cables multipolares o unipolares segun IRAM 2178 o 2268 o 62266", "ocr")

# ============================================================== conductores (524, 525)
G = "conductores"
R(G, "secciones_minimas_tabla_52_24", "Sección mínima de conductores (por razones mecánicas)",
  "Secciones mínimas en instalaciones fijas con conductores aislados: iluminación 1,5 mm² Cu; tomacorrientes 2,5 mm² Cu; otros de conexión fija 1,5 mm² Cu; aluminio 10 mm²; comando y señalización 1 mm² Cu.",
  "obligatorio", {"iluminacion_cu_mm2": 1.5, "tomacorrientes_cu_mm2": 2.5, "conexion_fija_otros_cu_mm2": 1.5, "aluminio_mm2": 10,
                  "comando_senalizacion_cu_mm2": 1, "comando_electronico_min_mm2": 0.1,
                  "pe_aislado_cu_mm2": 2.5, "pat_desnudo_cu_mm2": 4,
                  "flexible_mbt_aplicaciones_especiales_cu_mm2": 0.75, "flexible_otras_cu_mm2": 1.5},
  TODO, "5-52", "Tabla 52.24", 116, "52-62", "Sección mínima de conductores", "visual",
  tabla={"unidades": {"seccion": "mm²"},
         "columnas": ["tipo de canalización", "utilización del circuito", "material", "sección mínima"],
         "filas": [["instalación fija, cables y conductores aislados", "iluminación", "cobre", 1.5],
                   ["instalación fija, cables y conductores aislados", "tomacorrientes", "cobre", 2.5],
                   ["instalación fija, cables y conductores aislados", "conexión fija distinta de las anteriores", "cobre", 1.5],
                   ["instalación fija, cables y conductores aislados", "cualquier tipo de circuito", "aluminio", "10 (nota 1)"],
                   ["instalación fija, cables y conductores aislados", "comando y señalización", "cobre", "1 (nota 2)"],
                   ["instalación fija, conductores desnudos", "conductor de puesta a tierra (electrodo a BPT)", "cobre", "4 (ver Cap. 54)"],
                   ["instalación fija, conductores desnudos", "conductor de protección", "cobre", "2,5 (ver Cap. 54)"],
                   ["conexiones flexibles", "para un equipo específico", "cobre", "según IRAM o IEC del producto"],
                   ["conexiones flexibles", "muy baja tensión para aplicaciones especiales", "cobre", 0.75],
                   ["conexiones flexibles", "cualquier otra aplicación", "cobre", "1,5 (nota 3)"]],
         "notas": ["1. Los terminales para conexiones de aluminio se ensayan y aprueban para ese uso.",
                   "2. En señalización y comando de equipos electrónicos se permite 0,1 mm².",
                   "3. En cables flexibles multipolares de siete o más conductores se aplica la nota 2."]})
R(G, "neutro_igual_a_linea", "Neutro con la misma sección que los conductores de línea",
  "El neutro tiene como mínimo la sección de línea en monofásicos de dos conductores, en monofásicos de tres conductores y polifásicos con línea ≤ 16 mm² Cu o 25 mm² Al, y con armónicas de 3.º orden entre 15 % y 33 %.",
  "obligatorio", {"linea_max_cu_mm2": 16, "linea_max_al_mm2": 25, "armonica_min_pct": 15, "armonica_max_pct": 33},
  TODO, "5-52", "524.2.1", 116, "52-62",
  "en sistemas monofasicos de dos conductores, cualquiera que sea la seccion de los conductores", "ocr")
R(G, "neutro_reducido", "Neutro de sección reducida",
  "Con línea mayor que 16 mm² Cu o 25 mm² Al el neutro puede ser menor si está protegido contra sobrecorrientes y tiene al menos 16 mm² Cu o 25 mm² Al (usualmente no menos del 50 % de la línea).",
  "recomendado", {"min_cu_mm2": 16, "min_al_mm2": 25, "fraccion_usual_min": 0.5}, TODO, "5-52", "524.2.2", 117, "52-63",
  "la seccion del conductor neutro debe ser por lo menos igual a 16", "ocr")
R(G, "neutro_armonicas_145", "Neutro con armónicas mayores que 33 %",
  "Con tasa de tercera armónica mayor que 33 % el neutro se dimensiona para 1,45 veces la corriente de empleo de los conductores de línea.",
  "obligatorio", {"armonica_umbral_pct": 33, "factor_corriente_neutro": 1.45}, TODO, "5-52", "524.2.3", 117, "52-63",
  "igual a 1,45 veces la corriente prevista de utilizacion en los conductores de linea", "ocr")
R(G, "neutro_no_comun", "Neutro común a varios circuitos",
  "El neutro no puede ser común a varios circuitos.", "prohibido", {}, TODO, "5-52", "524.2.4", 117, "52-63",
  "El conductor neutro no puede ser comun a varios circuitos", "ocr")
R(G, "caida_tension_iluminacion", "Caída de tensión máxima en iluminación",
  "La caída de tensión entre el origen de la instalación y cualquier punto de utilización no supera 3 % en circuitos de iluminación (total o parcial).",
  "obligatorio", {"du_max_pct": 3}, TODO, "5-52", "525 1)", 117, "52-63",
  "Circuitos destinados total o parcialmente a la iluminacion: 3 %", "ocr")
R(G, "caida_tension_motores", "Caída de tensión máxima en motores",
  "Circuitos solo de motores: 5 % en régimen y 15 % durante el arranque.", "obligatorio",
  {"du_regimen_pct": 5, "du_arranque_pct": 15}, TODO, "5-52", "525 2)", 117, "52-63",
  "5 % en regimen y 15 % durante el arranque", "ocr")
R(G, "caida_tension_otras_cargas", "Caída de tensión máxima en otras cargas",
  "Circuitos solo de cargas distintas de iluminación y motores: 5 % en régimen.", "obligatorio", {"du_regimen_pct": 5},
  TODO, "5-52", "525 3)", 117, "52-63",
  "cargas electricas distintas de la iluminacion y los motores electricos: 5% en regimen", "ocr")
R(G, "caida_tension_seccionales_recomendado", "Caída de tensión en circuitos seccionales",
  "Se recomienda que la caída en los circuitos seccionales no exceda 1 %, quedando 2 % para terminales que no alimentan motores.",
  "recomendado", {"du_seccional_pct": 1, "du_terminal_pct": 2}, TODO, "5-52", "525 Nota", 117, "52-63",
  "se recomienda que la caida de tension en los circuitos seccionales no exceda del 1 %", "ocr")

# ============================================================== canalizaciones (521.8.8)
G = "curvas_canerias"
R(G, "max_tres_curvas", "Curvas en cañerías",
  "No se admiten más de tres curvas de la cañería entre dos cajas o gabinetes consecutivos; las curvas no terminan en ángulos interiores menores que 90°.",
  "obligatorio", {"curvas_max_entre_cajas": 3, "angulo_interior_min_grados": 90}, TODO, "5-52", "521.8.8", 78, "52-24",
  "No se admitiran mas de tres curvas de la caneria entre cajas o gabinetes consecutivos", "ocr")
R(G, "distancia_entre_curvas", "Distancia entre curvas consecutivas",
  "La distancia mínima entre dos curvas consecutivas es diez veces el diámetro exterior del caño.", "obligatorio",
  {"distancia_min_veces_diametro": 10}, TODO, "5-52", "521.8.8", 78, "52-24",
  "no sera menor que diez veces el diametro exterior del cano", "ocr")
R(G, "radios_metalicos_tabla_52_11", "Radios de curvatura de caños metálicos rígidos",
  "Radio de curvatura mínimo y máximo para caños metálicos rígidos tipo liviano o semipesado (CL/CR).", "obligatorio", {},
  TODO, "5-52", "Tabla 52.11", 78, "52-24", "Radios de curvatura para canos metalicos rigidos", "visual",
  tabla={"unidades": {"radio": "mm"}, "columnas": ["diámetro nominal", "designación IRAM", "radio mínimo [mm]", "radio máximo [mm]"],
         "filas": [["5/8\"", "CL/CR 16", 35, 45], ["3/4\"", "CL/CR 19", 42, 52], ["7/8\"", "CL/CR 22", 50, 55],
                   ["1\"", "CL/CR 25", 59, 69], ["1 1/4\"", "CL/CR 32", 74, 84], ["1 1/2\"", "CL/CR 38", 90, 100],
                   ["2\"", "CL/CR 51", 120, 130]]})
R(G, "radios_sinteticos_tabla_52_12", "Radios mínimos de curvatura de caños sintéticos",
  "Radio mínimo de curvatura de caños de material sintético, rígidos, curvables o curvables autorrecuperables; en curvables corrugados se usa un diámetro un escalón superior.",
  "obligatorio", {}, TODO, "5-52", "Tabla 52.12", 78, "52-24",
  "Radios minimos de curvatura para canos de material sintetico", "visual",
  tabla={"unidades": {"radio": "mm"},
         "columnas": ["diámetro exterior [mm]", "curvable corrugada o anillada", "curvable lisa", "rígida ARL", "rígida MRL"],
         "filas": [[16, 48, 96, 48, 96], [20, 60, 120, 60, 120], [25, 75, 150, 75, 150], [32, 96, 192, None, None],
                   [40, 160, 300, None, None], [50, 200, 480, None, None], [63, 252, 600, None, None]],
         "nota": "Rígidas (curvables con ayuda de equipos): solo 16, 20 y 25 mm."})

# ============================================================== protección contra sobrecorrientes (Cap. 43)
G = "proteccion_sobrecorrientes"
R(G, "coordinacion_ib_in_iz", "Coordinación entre conductor y protección contra sobrecargas",
  "El dispositivo de protección cumple IB ≤ In ≤ IZ e I2 ≤ 1,45·IZ.", "obligatorio",
  {"condicion_1a": "IB <= In", "condicion_1b": "In <= IZ", "condicion_2": "I2 <= 1,45 * IZ"}, TODO, "4-43", "433.1", 158, "43-10",
  "Las condiciones 1) y 2) dadas mas arriba, se pueden interpretar como tres condiciones", "visual")
R(G, "i2_definicion", "Corriente I2 de operación convencional",
  "I2 es la corriente de operación en el tiempo convencional para interruptores automáticos, y la corriente máxima de fusión en el tiempo convencional para fusibles gG.",
  "obligatorio", {}, TODO, "4-43", "433.1", 158, "43-10",
  "la corriente maxima de fusion en los tiempos convencionales, para los fusibles gG", "ocr")
R(G, "temperaturas_tabla_43_1", "Temperaturas características de los conductores",
  "Temperatura máxima en servicio continuo, límite de sobrecarga y límite de cortocircuito según el tipo de aislación.", "obligatorio", {},
  TODO, "4-43", "Tabla 43.1", 154, "43-6", "Temperatura caracteristica de los conductores", "visual",
  tabla={"unidades": {"temperatura": "°C"},
         "columnas": ["aislación", "T servicio continuo", "T límite sobrecarga", "T límite cortocircuito"],
         "filas": [["PVC hasta 300 mm²", 70, 100, 160], ["PVC mayor de 300 mm²", 70, 100, 140],
                   ["PVC hasta 300 mm² (90 °C)", 90, 100, 160], ["PVC mayor de 300 mm² (90 °C)", 90, 100, 140],
                   ["Goma etilén propilénica (EPR)", 90, 130, 250], ["Polietileno reticulado (XLPE)", 90, 130, 250]]})
R(G, "neutro_proteccion_igual_seccion", "Protección del neutro (TT y TN)",
  "Con neutro de sección igual o mayor que la de línea no hace falta detección de sobreintensidad ni corte en el neutro; con neutro menor sí, aunque sin necesidad de cortarlo.",
  "obligatorio", {}, TODO, "4-43", "431.2.1", 155, "43-7",
  "no es necesario prever una deteccion de sobreintensidad ni un dispositivo de desconexion sobre el conductor neutro", "ocr")
R(G, "neutro_it_no_distribuir", "Neutro en esquema IT",
  "En esquemas IT es altamente recomendable no distribuir el neutro.", "recomendado", {}, TODO, "4-43", "431.2.2", 155, "43-7",
  "es altamente recomendable no distribuir el conductor neutro", "ocr")
R(G, "neutro_secuencia_maniobra", "Maniobra del neutro",
  "El neutro no se desconecta antes que los conductores de línea y se conecta al mismo tiempo o antes.", "obligatorio", {}, TODO,
  "4-43", "431.3", 156, "43-8", "el conductor neutro no sea desconectado antes que los conductores de linea", "ocr")
R(G, "poder_de_corte", "Poder de corte del dispositivo de protección",
  "La capacidad de ruptura del dispositivo es igual o superior a la corriente presunta de cortocircuito en el lugar de instalación (salvo protección de acompañamiento, 434.5.1).",
  "obligatorio", {}, TODO, "4-43", "432.1 Nota 2", 156, "43-8",
  "La capacidad de ruptura de un dispositivo de proteccion debera ser igual o superior al valor de la corriente presunta", "ocr")
R(G, "aM_no_sobrecarga", "Fusibles aM",
  "Los fusibles aM no protegen contra sobrecargas; solo se usan contra cortocircuitos de aparatos de maniobra.", "prohibido", {}, TODO,
  "4-43", "432.3 Nota 1", 157, "43-9",
  "estos fusibles no deben ser empleados para la proteccion contra sobrecargas", "ocr")

# ============================================================== protección contra choques (Cap. 41)
G = "proteccion_choques"
R(G, "tension_limite_24v", "Tensión límite convencional de contacto",
  "La Reglamentación adopta UL = 24 V para la protección contra contactos indirectos por desconexión automática, en ambientes secos, húmedos y mojados.",
  "obligatorio", {"ul_v": 24}, TODO, "4-41", "413.1.3", 67, "41-47",
  "esta Reglamentacion adopta, como tension limite convencional de contacto", "ocr")
R(G, "tt_solo_diferenciales", "Protección contra contactos indirectos en TT",
  "En el esquema TT solo se usan dispositivos de corriente diferencial; en TN-S también dispositivos de sobrecorriente.",
  "obligatorio", {}, TODO, "4-41", "413.1.3", 67, "41-47",
  "en el ECT TT, solo se podran utilizar para la proteccion contra los contactos indirectos", "ocr")
R(G, "tiempos_tabla_41_3", "Tiempos máximos de desconexión en circuitos terminales (UL = 24 V)",
  "Tiempos máximos de desconexión en circuitos terminales de hasta 32 A según esquema y tensión Uo.", "obligatorio",
  {"alcance": "circuitos terminales hasta 32 A"}, TODO, "4-41", "Tabla 41.3 y 413.1.3.1", 68, "41-48",
  "Tiempos maximos de desconexion para la proteccion contra contacto indirecto", "visual",
  tabla={"unidades": {"tiempo": "s"},
         "columnas": ["esquema", "50<Uo≤120 V ca", "50<Uo≤120 V cc", "120<Uo≤230 V ca", "120<Uo≤230 V cc", "230<Uo≤400 V ca", "230<Uo≤400 V cc"],
         "filas": [["TN", 0.4, "a)", 0.2, 5, 0.06, 0.2], ["TT", 0.2, "a)", 0.06, 0.2, 0.01, 0.02], ["IT", "ver 413.1.5"]],
         "notas": ["Uo: tensión simple en ca o cc, o tensión entre línea y tierra.",
                   "a) La desconexión puede ser requerida por razones distintas a la protección contra choques.",
                   "b) Con protección diferencial no se considera el tiempo de apertura a IΔn sino a 5·IΔn.",
                   "Lectura sobre imagen a 120 dpi; confirmar con la norma impresa antes de usar los valores de 230 V."]})
R(G, "tn_s_tiempo_2s", "Tiempo de desconexión en TN-S (circuitos seccionales)",
  "En TN-S los circuitos seccionales y los no cubiertos por 413.1.3.1 admiten tiempos de desconexión de hasta 2 s (hasta 5 s si la selectividad lo requiere).",
  "obligatorio", {"t_max_s": 2, "t_max_selectividad_s": 5}, TODO, "4-41", "413.1.3.2", 69, "41-49",
  "se admiten tiempos de desconexion que no excedan a 2 s para circuitos sec- cionales", "ocr")
R(G, "tt_tiempo_1s", "Tiempo de desconexión en TT (circuitos seccionales)",
  "En TT los circuitos seccionales y los no cubiertos por 413.1.3.1 admiten tiempos de desconexión de hasta 1 s.",
  "obligatorio", {"t_max_s": 1}, TODO, "4-41", "413.1.3.3", 69, "41-49",
  "se admiten tiempos de desconexion que no excedan de 1 s para circuitos seccio- nales", "ocr")
R(G, "equipotencial_suplementaria_si_no_alcanza", "Falla de desconexión en el tiempo",
  "Si la desconexión automática no alcanza los tiempos requeridos se realiza una vinculación equipotencial suplementaria de protección (413.1.7).",
  "obligatorio", {}, TODO, "4-41", "413.1.3.5", 69, "41-49",
  "se debe realizar una vinculacion equipotencial suplementaria", "ocr")
R(G, "dd_30ma_proteccion_adicional", "Protección complementaria con diferencial de 30 mA",
  "El uso de dispositivos diferenciales con IΔn ≤ 30 mA se reconoce como medida complementaria contra contactos directos, y no exime de las demás medidas.",
  "obligatorio", {"idn_max_ma": 30}, TODO, "4-41", "412.5.1 y 412.5.2", 60, "41-40",
  "es reconocido como medida de proteccion complementaria o adicional contra los", "ocr")
R(G, "dd_30ma_circuitos_obligados", "Circuitos que exigen diferencial de 30 mA",
  "En TT, TN-S y TN-C-S exigen protección complementaria con diferencial IΔn ≤ 30 mA: tomacorrientes de hasta 32 A sin enclavamiento, iluminación con ficha y tomacorriente de hasta 32 A, e iluminación fija con luminarias a 3 m o menos o dentro del volumen de accesibilidad, o a más de 3 m sin mantenimiento BA4/BA5.",
  "obligatorio", {"idn_max_ma": 30, "tomacorrientes_hasta_a": 32, "altura_luminaria_m": 3,
                  "esquemas": ["TT", "TN-S", "TN-C-S"]}, TODO, "4-41", "412.5.3", 60, "41-40",
  "Los circuitos de tomacorrientes que empleen tomacorrientes de corriente nominal igual o inferior a", "ocr")
