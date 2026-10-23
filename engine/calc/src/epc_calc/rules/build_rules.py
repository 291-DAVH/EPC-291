"""Genera los JSON de reglas de ingeniería a partir del texto de las normas AEA.

Cada regla se escribe a mano (valor, tipo, aplicación) y el script comprueba que su `cita` figura
textualmente en la norma, a continuación de la cláusula indicada; si no, falla. Así ninguna regla
queda sin respaldo. Calcula también la página impresa en que está la cita.

Uso: python3 -B build_rules.py <carpeta_con_txt> <carpeta_salida> [<carpeta_ocr>]
  <carpeta_con_txt> contiene AEA_90364-7-771.txt, -770, -701 y -722 (texto extraído de los PDF).
  <carpeta_ocr> contiene el OCR por página de las Partes 4 y 5 (n4_pNNN.txt, n5_pNNN.txt); ver reglas_ocr.py.
  Sin <carpeta_ocr> solo se generan las reglas de la Parte 7.
"""
import json
import os
import re
import sys

NORMAS = {"771": "AEA_90364-7-771.txt", "770": "AEA_90364-7-770.txt",
          "701": "AEA_90364-7-701.txt", "722": "AEA_90364-7-722.txt"}
NOMBRES = {"771": "AEA 90364-7-771", "770": "AEA 90364-7-770", "701": "AEA 90364-7-701", "722": "AEA 90364-7-722"}


def _cita(c):
    """La cita se escribió con los cortes de renglón del PDF ('co- nectarse'); se unifica igual que el texto."""
    return re.sub(r"(?<=[a-záéíóúñ])- (?=[a-záéíóúñ])", "", _norm(c))


def _norm(t):
    t = t.replace("∆", "Δ")                        # ∆ -> Δ
    t = re.sub(r"(?<=[a-záéíóúñ])-\s*\n\s*(?=[a-záéíóúñ])", "", t)   # guion de fin de línea
    return re.sub(r"\s+", " ", t)


class Texto:
    def __init__(self, ruta):
        crudo = open(ruta, encoding="utf-8", errors="ignore").read()
        self.t = _norm(crudo)
        self.edicion = (re.search(r"Edici[óo]n\s+(\d{4})", self.t) or [None, "s/d"])[1]
        self.paginas = [(m.start(), int(m.group(1))) for m in re.finditer(r"P[áa]gina\s+(\d{1,3})\b", self.t)]

    def buscar(self, cita, desde=None):
        ini = 0
        if desde:
            ini = self.t.find(_cita(desde))
            if ini < 0:
                raise SystemExit(f"FALLA: ancla no encontrada: {desde!r}")
        pos = self.t.find(_cita(cita), ini)
        if pos < 0:
            raise SystemExit(f"FALLA: cita no encontrada (desde {desde!r}): {cita!r}")
        pagina = None
        for p, n in self.paginas:       # el marcador "Página N" abre la página N
            if p < pos:
                pagina = n
            else:
                break
        return pos, pagina


REGLAS = []


def R(grupo, id_, tema, regla, tipo, params, aplica, norma, clausula, cita, desde=None, tabla=None):
    REGLAS.append(dict(grupo=grupo, id=f"{grupo}.{id_}", tema=tema, regla=regla, tipo=tipo, parametros=params,
                       aplica_a=aplica, norma=norma, clausula=clausula, cita=cita, desde=desde, tabla=tabla))


V, O, L = ["viviendas", "oficinas", "locales"], "oficinas", "locales"
D771_76 = "Nota 1: Se considera boca al punto de un circuito terminal"
D771_85 = "771.8.5: Criterios generales a) Las bocas de tomacorrientes"

# ------------------------------------------------------------------ circuitos
G = "circuitos"
R(G, "iug_corriente_unitaria", "Circuito de iluminación de uso general (IUG)", "Cada boca de un IUG admite cargas unitarias de hasta 10 A de funcionamiento permanente.", "obligatorio", {"corriente_unitaria_max_a": 10}, V + [O, L], "771", "771.7.6 a) I", "cuya corriente de funcionamiento permanente no sea mayor que 10 A", D771_76)
R(G, "iug_proteccion_max", "Circuito de iluminación de uso general (IUG)", "La protección del IUG es bipolar para una corriente no mayor de 16 A.", "obligatorio", {"proteccion_max_a": 16, "polos_protegidos": "ambos"}, V + [O, L], "771", "771.7.6 a) I", "Estos circuitos contarán con protecciones en ambos polos para una corriente no mayor de 16 A", D771_76)
R(G, "iug_bocas_max", "Circuito de iluminación de uso general (IUG)", "Un IUG tiene como máximo 15 bocas de salida.", "obligatorio", {"bocas_max": 15}, V + [O, L], "771", "771.7.6 a) I", "no mayor de 16 A y el número máximo de bocas de salida será de quince (15)", D771_76)
R(G, "tug_corriente_unitaria", "Circuito de tomacorrientes de uso general (TUG)", "Cada boca de un TUG admite cargas unitarias de no más de 10 A con tomacorrientes 2P+T de 10 A (IRAM 2071), o 16 A con IRAM-IEC 60309.", "obligatorio", {"corriente_unitaria_max_a": 10, "corriente_unitaria_max_iec60309_a": 16}, V + [O, L], "771", "771.7.6 a) II", "podrán co- nectarse cargas unitarias de no más de 10 A", D771_76)
R(G, "tug_proteccion_max", "Circuito de tomacorrientes de uso general (TUG)", "La protección del TUG es bipolar para una corriente no mayor de 20 A.", "obligatorio", {"proteccion_max_a": 20, "polos_protegidos": "ambos"}, V + [O, L], "771", "771.7.6 a) II", "protecciones en ambos polos para una corriente no mayor de 20 A", D771_76)
R(G, "tug_bocas_max", "Circuito de tomacorrientes de uso general (TUG)", "Un TUG tiene como máximo 15 bocas de salida.", "obligatorio", {"bocas_max": 15}, V + [O, L], "771", "771.7.6 a) II", "no mayor de 20 A y el número máximo de bocas de salida será de quince (15)", D771_76)
R(G, "uso_especial_proteccion_y_bocas", "Circuitos de uso especial (IUE y TUE)", "Los circuitos de uso especial tienen protección bipolar de hasta 32 A y un máximo de 12 bocas.", "obligatorio", {"proteccion_max_a": 32, "bocas_max": 12}, V + [O, L], "771", "771.7.6 b)", "protecciones en ambos polos para una corriente no mayor de 32 A y el número máximo de bocas de salida es de doce (12)", D771_76)
R(G, "tue_corriente_unitaria", "Circuito de tomacorrientes de uso especial (TUE)", "Cada boca de un TUE admite cargas unitarias de hasta 20 A con tomacorrientes 2P+T de 20 A (IRAM 2071), o hasta 16 A con IRAM-IEC 60309.", "obligatorio", {"corriente_unitaria_max_a": 20, "corriente_unitaria_max_iec60309_a": 16}, V + [O, L], "771", "771.7.6 b) II", "pueden conec- tarse cargas unitarias, de hasta 20 A por medio de tomacorrientes tipo 2P+T de 20 A", D771_76)
R(G, "iue_a_la_intemperie", "Circuito de iluminación de uso especial (IUE)", "La iluminación de lugares a la intemperie se hace con IUE; se recomienda que esos circuitos sean independientes.", "obligatorio", {"obligatorio_a_la_intemperie": True}, V + [O, L], "771", "771.7.6 b) I", "Este tipo de circuitos debe ser empleado para la iluminación de lugares a la intemperie", D771_76)
R(G, "iluminacion_mayor_10a", "Carga de iluminación mayor de 10 A", "Si la carga de iluminación supera 10 A se usa un IUE (hasta 20 A); por encima, un circuito de carga única (ACU) u otro específico (OCE).", "obligatorio", {"umbral_iug_a": 10, "iue_max_a": 20}, V + [O, L], "771", "771.8.5 b)", "Si la carga fuese superior a los 10 A, podrá optarse por un circuito de iluminación de uso especial (IUE) hasta un consumo de 20 A.", D771_85)
R(G, "apm", "Circuito de pequeños motores monofásicos (APM)", "El APM tiene máximo 15 bocas, 10 A por boca y protección no mayor que 25 A.", "obligatorio", {"bocas_max": 15, "corriente_por_boca_max_a": 10, "proteccion_max_a": 25}, V + [O, L], "771", "771.7.6 c2) I", "El número máximo de bocas será de 15, la carga máxima por boca de 10 A y la protección del circuito no puede ser mayor que 25 A.", D771_76)
R(G, "mbtf", "Circuito de fuentes de muy baja tensión funcional (MBTF)", "El MBTF tiene máximo 15 bocas (en 220 V), 10 A por boca y protección no mayor que 20 A.", "obligatorio", {"bocas_max": 15, "corriente_por_boca_max_a": 10, "proteccion_max_a": 20}, V + [O, L], "771", "771.7.6 c2) III", "El número máximo de bocas (en 220 V) será de 15, la carga máxima por boca de 10 A y la protección del circuito no puede ser mayor que 20 A.", D771_76)
R(G, "ate_bocas_max", "Circuito de tensión estabilizada (ATE)", "El ATE tiene como máximo 15 bocas.", "obligatorio", {"bocas_max": 15}, V + [O, L], "771", "771.7.6 c1) II", "Los circuitos ATE deberán tener como máximo quince (15) bocas", D771_76)
R(G, "ite", "Circuito de iluminación trifásica específica (ITE)", "El ITE tiene máximo 12 bocas por fase o línea y 10 A por boca, con protección omnipolar.", "obligatorio", {"bocas_max_por_fase": 12, "corriente_por_boca_max_a": 10, "proteccion": "omnipolar"}, [O, L], "771", "771.7.6 c2) IV", "El número máximo de bocas por fase o línea será de 12, la carga máxima por boca de 10 A", D771_76)
R(G, "fuentes_comunicaciones_2200va", "Circuito específico de fuentes de comunicación, portería o timbres", "Un mismo circuito de uso específico puede alimentar todas esas fuentes si la suma de sus potencias nominales no supera 2200 VA.", "obligatorio", {"potencia_total_max_va": 2200}, V + [O, L], "771", "771.8.5 j)", "la suma de sus potencias nominales no sea mayor que 2200 VA.", D771_85)
R(G, "tomas_por_boca", "Cantidad de tomacorrientes por boca", "Una boca admite como máximo dos tomacorrientes en caja rectangular (50 x 100 mm) y cuatro en caja cuadrada (100 x 100 mm); nunca más de cuatro.", "obligatorio", {"tomas_max_caja_50x100": 2, "tomas_max_caja_100x100": 4, "tomas_max_por_boca": 4}, V + [O, L], "771", "771.8.5 a)", "pero el número máximo de tomacorrientes por boca es de cuatro (4)", D771_85)
R(G, "caja_de_paso_como_boca", "Caja de paso con más de un circuito", "Una caja de paso o derivación con más de un circuito puede ser boca solo si está a una altura no inferior a 1,80 m.", "obligatorio", {"altura_min_m": 1.8}, V + [O, L], "771", "771.7.6 Nota 1", "si están ubicadas a una altura no inferior a 1,80 m.", D771_76)
R(G, "equilibrio_trifasico", "Equilibrio de cargas en instalaciones trifásicas", "En instalaciones trifásicas se procura mantener el sistema lo más equilibrado posible mediante una adecuada distribución de las cargas.", "recomendado", {}, V + [O, L], "771", "771.8.5 q)", "se procurará mantener el sistema lo más equilibrado posible", D771_85)

# ------------------------------------------------------------------ iluminacion
G = "iluminacion"
R(G, "escaleras_una_boca_cada_5m", "Iluminación de escaleras y rampas", "Escaleras y rampas llevan al menos una boca de iluminación de uso general cada 5 m de longitud o fracción, o en cada descanso.", "obligatorio", {"distancia_max_entre_bocas_m": 5}, V + [O, L], "771", "771.8.5 g)", "como mínimo una boca de iluminación para uso general cada 5 m de longitud, o fracción, o bien en cada descanso", D771_85)
R(G, "ventiladores_cuentan_como_boca", "Ventiladores de techo y extractores", "Ventiladores de techo y extractores pueden conectarse a circuitos de iluminación y se computan como una boca de iluminación.", "obligatorio", {"bocas_computadas": 1}, V + [O, L], "771", "771.8.5 c)", "cualquiera de ellos se computará como una boca de iluminación", D771_85)
R(G, "mbts_comando_ambientes_mojados", "Comando en ambientes mojados", "Los circuitos de comando en ambientes mojados (incluidos tanques cisterna y elevado) se alimentan en muy baja tensión sin puesta a tierra (MBTS).", "obligatorio", {"alimentacion": "MBTS"}, V + [O, L], "771", "771.8.5 l)", "serán ali- mentados con muy baja tensión sin puesta a tierra (MBTS)", D771_85)
R(G, "escuelas_louver", "Luminarias de aulas", "Las luminarias de aulas no llevan lámparas a la vista: cubierta traslúcida o rejilla protectora (louver).", "obligatorio", {}, ["establecimientos educativos"], "771", "771.8.4 i)", "Las luminarias de las aulas no deberán llevar las lámparas a la vista", "771.8.4")
R(G, "luminarias_puertas_acceso_2_5m", "Acceso a equipos en luminarias y soportes", "Las puertas de acceso a equipos eléctricos situadas a menos de 2,50 m de altura sobre el solado se cierran con llave especial o herramienta.", "obligatorio", {"altura_umbral_m": 2.5}, ["alumbrado exterior"], "771", "771-B.8.2.1", "situadas a menos de 2,50 m de altura por encima del solado, deben cerrarse con una llave especial o una herramienta", "771-B.8.2.1: Protección contra los contactos directos")
for grado, ini, a1, a2, a3, mn in (("minimo", "771.8.3.3.3.1", (15, 2), (25, 2), (35, 2), 2), ("medio", "771.8.3.3.3.2", (15, 8), (32, 8), (55, 8), 8), ("elevado", "771.8.3.3.3.3", (15, 36), (32, 36), (55, 36), 36), ("superior", "771.8.3.3.3.4", (15, 90), (32, 90), (55, 90), 90)):
    R(G, f"deposito_densidad_{grado}", f"Puntos de iluminación en depósitos (grado {grado})", f"Salón general de depósitos o industrias de sustancias no inflamables: una boca de uso general cada {a1[0]} m² con luminarias a 2,5-3,5 m, cada {a2[0]} m² a 3,5-5 m y cada {a3[0]} m² por encima de 5 m, con un mínimo de {mn} bocas.", "obligatorio", {"m2_por_boca_altura_2_5_a_3_5": a1[0], "m2_por_boca_altura_3_5_a_5": a2[0], "m2_por_boca_altura_mayor_5": a3[0], "bocas_minimas": mn}, ["depósitos y elaboración de sustancias no inflamables"], "771", ini, f"(como mínimo {'dos' if mn == 2 else mn} bocas)", f"{ini}: Grado de electrificación “{ {'minimo': 'Mínimo'}.get(grado, grado.capitalize()) }”")

# ------------------------------------------------------------------ interruptores
G = "interruptores"
R(G, "altura_centro", "Altura de interruptores de efecto", "El centro de la caja del interruptor de efecto se ubica entre 0,9 y 1,3 m del solado terminado; se recomienda 1,10 m y una única altura en todo el inmueble.", "obligatorio", {"altura_min_m": 0.9, "altura_max_m": 1.3, "altura_recomendada_m": 1.1}, V + [O, L], "771", "771.8.6.1", "cuyo centro deberá estar ubicado entre 0,9 y 1,3 m del nivel del solado terminado, siendo recomendable la altura de 1,10 m", "771.8.6.1: Altura y ubicación de los interruptores de efecto")
R(G, "distancia_al_marco", "Ubicación junto a puertas", "La arista de la caja más cercana al marco de la puerta queda a no más de 0,15 m del borde exterior del marco que aloja el cerradero.", "obligatorio", {"distancia_max_al_marco_m": 0.15}, V + [O, L], "771", "771.8.6.1", "a no más de 0,15 m del borde exterior del marco que aloja el cerradero", "771.8.6.1: Altura y ubicación de los interruptores de efecto")
R(G, "pasillos_mayores_3m", "Pasillos de más de 3 m", "En pasillos interiores de más de 3 m se prevén interruptores combinados en cada extremo y en cada acceso intermedio, con no más de 6 m entre interruptores sucesivos.", "obligatorio", {"longitud_umbral_m": 3, "distancia_max_entre_interruptores_m": 6, "distancia_max_al_acceso_m": 0.15}, V + [O, L], "771", "771.8.6.1", "la distancia entre interruptores sucesivos no exceda los 6 m", "771.8.6.1: Altura y ubicación de los interruptores de efecto")
R(G, "ascensores", "Interruptores cerca de ascensores", "Con ascensores en el inmueble, el comando de iluminación se sitúa a menos de 2 m de toda puerta de ascensor y es visible desde el umbral.", "obligatorio", {"distancia_max_a_puerta_ascensor_m": 2}, V + [O, L], "771", "771.8.6.1", "se deberá situar el dispositivo de comando de iluminación a menos de 2 m de toda puerta de ascensor", "771.8.6.1: Altura y ubicación de los interruptores de efecto")
R(G, "no_compartir_caja_con_tomas_bajos", "Interruptores de tomacorrientes comandados", "Los interruptores que comandan tomacorrientes por debajo de 0,90 m pertenecen al circuito de tomacorrientes y no comparten caja con interruptores de iluminación.", "obligatorio", {"altura_umbral_m": 0.9}, V + [O, L], "771", "771.8.5 p)", "los interruptores de efecto para comando de tomacorrientes no podrán compartir la caja con interruptores de efecto del circuito de iluminación", D771_85)
R(G, "garajes_altura_minima", "Garajes con solado a nivel de calle o superior", "En garajes, las bocas de tomacorrientes y los elementos de maniobra y protección se ubican a una altura mínima de 1,5 m sobre el solado; las instalaciones a la vista son metálicas.", "obligatorio", {"altura_min_m": 1.5}, ["garajes"], "771", "771.8.3.4", "deberán estar ubicados a una altura mínima de 1,5 m sobre el nivel de solado.", "771.8.3.4: Locales destinados a garajes")

# ------------------------------------------------------------------ tomacorrientes
G = "tomacorrientes"
R(G, "altura_arista_inferior_771", "Altura de cajas de tomacorrientes", "En la Sección 771, la arista inferior de la caja de un tomacorriente sobre zócalo queda a no menos de 0,15 m del solado terminado.", "obligatorio", {"altura_min_m": 0.15, "referencia": "arista inferior de la caja"}, V + [O, L], "771", "771.8.6.2", "la arista inferior quede a no menos de 0,15 m del nivel del solado terminado.", "771.8.6.2: Altura y ubicación de los tomacorrientes")
R(G, "altura_arista_inferior_770", "Altura de cajas de tomacorrientes en viviendas (770)", "En la Sección 770 la arista inferior queda entre 0,2 y 0,3 m del solado terminado.", "obligatorio", {"altura_min_m": 0.2, "altura_max_m": 0.3, "referencia": "arista inferior de la caja"}, ["viviendas"], "770", "770.7.2", "quede entre 0,2 y 0,3 m del nivel del solado (piso) terminado.", "770.7.2 Ubicaciones para los tomacorrientes")
R(G, "mesadas_771", "Tomacorrientes sobre mesadas", "Sobre mesadas de baños, cocinas y lavaderos la arista inferior de la caja queda a no menos de 0,10 m de la mesada, además de respetar las distancias a fuentes de agua (701).", "obligatorio", {"altura_min_sobre_mesada_m": 0.1}, V + [O, L], "771", "771.8.6.2", "a no menos de 0,10 m del nivel de mesada", "771.8.6.2: Altura y ubicación de los tomacorrientes")
R(G, "mesadas_770", "Tomacorrientes sobre mesadas (770)", "Idéntica exigencia en la Sección 770: 0,10 m sobre la mesada.", "obligatorio", {"altura_min_sobre_mesada_m": 0.1}, ["viviendas"], "770", "770.7.2", "a no menos de 0,10 m del nivel de mesada", "770.7.2 Ubicaciones para los tomacorrientes")
R(G, "ninos_bajos_2x10t_771", "Tomacorrientes accesibles a niños", "En viviendas, los tomacorrientes a nivel de zócalo o hasta 0,9 m del solado son 2x10+T (IRAM 2071) con pantalla contra inserción de cuerpos extraños.", "obligatorio", {"altura_umbral_m": 0.9, "tipo": "2x10+T IRAM 2071 con pantalla"}, ["viviendas"], "771", "771.8.6.2", "hasta una altura de 0,9 m del nivel del solado terminado deberán ser de 2x10+T construidos según Norma IRAM 2071", "771.8.6.2: Altura y ubicación de los tomacorrientes")
R(G, "baldeado_771", "Ambientes con limpieza por baldeado", "Donde se baldea, la arista inferior de la caja queda a no menos de 0,20 m del solado (IP20 mínimo); por debajo de ese nivel el conjunto es IP54.", "obligatorio", {"altura_min_m": 0.2, "ip_sobre_altura": "IP20", "ip_bajo_altura": "IP54"}, V + [O, L], "771", "771.8.6.2", "a no menos de 0,20 m del nivel del solado ter- minado", "771.8.6.2: Altura y ubicación de los tomacorrientes")
R(G, "baldeado_770", "Ambientes con limpieza por baldeado (770)", "En la Sección 770 la altura mínima de la arista inferior es 0,30 m del solado terminado.", "obligatorio", {"altura_min_m": 0.3}, ["viviendas"], "770", "770.7.2", "a no menos de 0,30 m del nivel del solado terminado", "770.7.2 Ubicaciones para los tomacorrientes")
R(G, "orificios_hacia_arriba", "Orientación de los tomacorrientes", "Se recomienda no instalar tomacorrientes sobre planos horizontales con los orificios verticales hacia arriba.", "recomendado", {}, V + [O, L], "771", "771.8.6.2", "Se recomienda no instalar los tomacorrientes sobre planos horizontales", "771.8.6.2: Altura y ubicación de los tomacorrientes")
R(G, "mixtas_bajo_090", "Bocas mixtas y tomas bajo 0,90 m", "No se admiten tomacorrientes conectados al circuito de iluminación a menos de 0,90 m del solado terminado.", "prohibido", {"altura_umbral_m": 0.9}, V + [O, L], "771", "771.8.5 p)", "No se permite la instalación de bocas de tomacorrientes conectadas al circuito de iluminación, situadas a menos de 0,90 m del nivel del solado terminado.", D771_85)
R(G, "toilette_toma_en_iluminacion", "Toilette", "En un toilette (baño sin bañera ni ducha) el tomacorriente requerido puede cargarse al circuito de iluminación.", "obligatorio", {}, V + [O, L], "771", "771.8.5 n)", "el tomacorriente requerido en los puntos mínimos de utilización podrá cargarse al circuito de iluminación", D771_85)
R(G, "ate_color_rojo", "Tomacorrientes de circuitos ATE", "Los tomacorrientes IRAM 2071 de circuitos de tensión estabilizada (ATE) son de color rojo.", "obligatorio", {"color": "rojo"}, V + [O, L], "771", "771.7.6 c1) II", "se instalarán tomacorrientes de color rojo", D771_76)
R(G, "escuelas_aulas_pizarron", "Aulas: tomacorrientes junto al pizarrón", "Cada aula lleva dos bocas 2x10+T sobre la pared del pizarrón, una entre 0,2 y 0,4 m del solado y la otra a 2,3 m.", "obligatorio", {"altura_boca_baja_min_m": 0.2, "altura_boca_baja_max_m": 0.4, "altura_boca_alta_m": 2.3, "bocas": 2}, ["establecimientos educativos"], "771", "771.8.4 j)", "Una de estas bocas deberá ubicarse entre 0,2 y 0,4 m del nivel del solado terminado", "771.8.4")
R(G, "escuelas_inicial_1_7m", "Jardines maternales e infantes", "En aulas de Jardines Maternales, de Infantes (Ciclo Inicial) o Ciclo Básico no se instalan tomacorrientes a menos de 1,7 m del solado.", "prohibido", {"altura_min_m": 1.7}, ["establecimientos educativos"], "771", "771.8.4 j)", "no se instalarán bocas de tomacorrientes a alturas infe- riores a los 1,7 m", "771.8.4")
R(G, "deposito_perimetro", "Tomacorrientes en depósitos (salón general)", "Una boca de tomacorrientes de uso general cada 9 m de perímetro, con un mínimo de dos; en grados medio, elevado y superior se agrega una de uso especial cada 18 m, con un mínimo de una.", "obligatorio", {"perimetro_por_boca_uso_general_m": 9, "bocas_minimas_uso_general": 2, "perimetro_por_boca_uso_especial_m": 18, "bocas_minimas_uso_especial": 1}, ["depósitos y elaboración de sustancias no inflamables"], "771", "771.8.3.3.3.1 a 771.8.3.3.3.4", "una boca para tomacorrientes de uso general por cada 9 m, o fracción, de perímetro", "771.8.3.3.3.1: Grado de electrificación “Mínimo”")
R(G, "ev_modo_0_2_interior", "Carga de vehículos eléctricos (Modos 0 y 2, interior)", "Para carga en Modo 0 y Modo 2 en interiores las bocas del circuito de carga son IRAM 2071 de 10 A.", "obligatorio", {"tipo": "IRAM 2071", "corriente_a": 10}, ["vehículos eléctricos"], "722", "722, apartado 3.4.1", "deben ser de tipo IRAM 2071 de 10 A")
R(G, "ev_un_vehiculo_por_modulo", "Carga de vehículos eléctricos", "No se carga más de un vehículo eléctrico en simultáneo por módulo de tomacorriente.", "prohibido", {"vehiculos_max_por_modulo": 1}, ["vehículos eléctricos"], "722", "722, apartado 3.1", "No se permite cargar en simultáneo más de un VE por módulo de tomacorriente.")
R(G, "ev_diferencial_30ma_clase_a", "Protección diferencial de carga de vehículos eléctricos", "Los circuitos de carga del VE se protegen con interruptor diferencial clase A de corriente residual nominal máxima 30 mA.", "obligatorio", {"i_dn_max_ma": 30, "clase": "A"}, ["vehículos eléctricos"], "722", "722, apartado 3.2", "deben estar protegidos por un interruptor diferencial clase A de corriente")
R(G, "ev_modo_3_4_acu", "Estaciones de carga Modos 3 y 4", "En Modo 3 y Modo 4 es obligatoria una estación de carga con circuito dedicado de uso específico ACU.", "obligatorio", {"circuito": "ACU"}, ["vehículos eléctricos"], "722", "722, apartado 3.4.2 y 3.5.2", "es obligatoria la instalación de una estación de carga, con un circuito eléctrico dedicado")
R(G, "ev_ip_intemperie", "Grado IP de carga de vehículos eléctricos a la intemperie", "A la intemperie sin chorro de agua: IP44 o superior; con chorros de agua: IP55 o superior.", "obligatorio", {"ip_sin_chorro": "IP44", "ip_con_chorro": "IP55"}, ["vehículos eléctricos"], "722", "722, apartado 3.5.1 y 3.5.2", "IP mínimo debe ser IP55 o superior")
R(G, "ev_una_acometida", "Acometida para carga de vehículos eléctricos", "No se admite más de una acometida con medición independiente por inmueble.", "prohibido", {"acometidas_max": 1}, ["vehículos eléctricos"], "722", "722, apartado 3.6", "No se admite más de una acometida con medición independiente por inmueble.")

# ------------------------------------------------------------------ canalizaciones
G = "canalizaciones"
D12 = "771.12.3.1: Generalidades"
R(G, "ortogonalidad", "Recorrido de canalizaciones", "El recorrido respeta la ortogonalidad del ambiente (líneas verticales y horizontales o paralelas a las aristas); no se permiten tendidos en diagonal.", "obligatorio", {"diagonal_permitida": False}, V + [O, L], "771", "771.12.3.1", "No se permiten los tendidos en diagonal.", D12)
R(G, "distancia_cajas_a_marcos_solados_techos", "Ubicación de cajas respecto de marcos, solados y techos", "El borde de la caja más cercano queda a no más de 0,25 m del marco de aberturas, 0,30 m del cielorraso o techo y 0,20 m del solado.", "obligatorio", {"a_marco_max_m": 0.25, "a_cielorraso_max_m": 0.3, "a_solado_max_m": 0.2}, V + [O, L], "771", "771.12.3.1", "a no más de 0,25 m de la arista externa de cada marco de aberturas colocadas en obra, a no más de 0,30 m de los cielorrasos o techos y no más de 0,20 m de los solados.", D12)
R(G, "curvas_max_entre_cajas", "Cantidad de curvas", "Entre bocas, cajas o gabinetes se admiten como máximo tres curvas.", "obligatorio", {"curvas_max": 3}, V + [O, L], "771", "771.12.3.1", "En todos los casos se respetará la cantidad máxima de tres curvas entre bocas, cajas o gabinetes.", D12)
R(G, "distancia_entre_curvas", "Distancia entre curvas consecutivas", "La distancia mínima entre dos curvas consecutivas no es menor que diez veces el diámetro exterior del caño.", "obligatorio", {"distancia_min_en_diametros_exteriores": 10}, V + [O, L], "771", "771.12.3.8.5", "no será menor que diez veces el diámetro exterior del caño", "Tabla 771.12.VIII - Radios de curvatura para curvas construidas en fábrica")
R(G, "cajas_de_paso_distancia", "Cajas de paso en tramos largos", "En tramos rectos horizontales sin derivación se coloca al menos una caja cada 12 m, y en tramos verticales una cada 15 m.", "obligatorio", {"horizontal_max_m": 12, "vertical_max_m": 15}, V + [O, L], "771", "771.12.3.8.3", "como mínimo una caja cada 12 m y en tramos verticales un mínimo de una caja cada 15 m", "771.12.3.8.3: Colocación de cajas de paso, de derivación y de paso y derivación")
R(G, "sujecion_flexibles", "Sujeción de cañerías curvables", "Las cañerías curvables se sujetan a intervalos regulares que no superan un metro.", "obligatorio", {"separacion_max_m": 1}, V + [O, L], "771", "771.12.3.3.4 b)", "que no superen el metro de distancia entre ellos", "771.12.3.3.4: Prescripciones adicionales para cañerías curvables")
R(G, "llenado_max_caños_no_tabulados", "Ocupación máxima de canalizaciones", "Para casos no previstos en la Tabla 771.12.IX y conductos no circulares, el área ocupada por los conductores (con aislación) no supera el 35 % de la sección interna menor del conducto; es decir, 65 % de capacidad libre.", "obligatorio", {"ocupacion_max_pct": 35, "reserva_libre_min_pct": 65}, V + [O, L], "771", "771.12.3.13.4", "no será mayor que el 35 % de la sección interna menor del conducto", "771.12.3.13.4: Medidas mínimas de conductos y cajas")
R(G, "diametro_min_principal_seccional", "Diámetro mínimo de caños para circuitos principales y seccionales", "Circuitos principales o seccionales: diámetro interno mínimo 15 mm (RL 19 / RS 19) o sección mínima 200 mm² en otras formas.", "obligatorio", {"diametro_interno_min_mm": 15, "designacion": "RL 19 / RS 19", "seccion_min_otras_formas_mm2": 200}, V + [O, L], "771", "771.12.3.13.4", "el diámetro interno mínimo de los caños de sección circular será de 15 mm (RL 19 y RS 19) y la sección mínima para otras formas será de 200 mm²", "771.12.3.13.4: Medidas mínimas de conductos y cajas")
R(G, "diametro_min_terminales", "Diámetro mínimo de caños para circuitos terminales", "Circuitos terminales: diámetro interno mínimo 13 mm (RL 16 / RS 16) o sección mínima 150 mm² en otras formas.", "obligatorio", {"diametro_interno_min_mm": 13, "designacion": "RL 16 / RS 16", "seccion_min_otras_formas_mm2": 150}, V + [O, L], "771", "771.12.3.13.4", "será de 13 mm (RL 16 y RS 16) y la sección mínima para otras formas será de 150 mm²", "771.12.3.13.4: Medidas mínimas de conductos y cajas")
R(G, "tablero_principal_a_seccional", "Cañería entre tablero principal y primer seccional", "La cañería que vincula el tablero principal con el primer seccional (incluidas columnas montantes) es de diámetro mínimo R19 (3/4\").", "obligatorio", {"designacion_min": "R19", "pulgadas": 0.75}, V + [O, L], "771", "771.8.5 t)", "dicha cañería deberá ser de diámetro mínimo R19", "t) Cuando en una instalación exista cañería que vincule el tablero principal")
R(G, "recomendacion_r25_viviendas", "Cañería del tablero principal al seccional en viviendas (770)", "En viviendas se recomienda proyectar esa canalización con cañería R25 (1\") por la incertidumbre de cargas futuras.", "recomendado", {"designacion": "R25", "pulgadas": 1}, ["viviendas"], "770", "770.7.1", "se recomienda proyectar esta canalización con cañería de diámetro R25")
R(G, "un_conductor_en_caño_metalico", "Un solo conductor por caño metálico", "No se admite un solo conductor aislado o cable unipolar dentro de un caño metálico.", "prohibido", {}, V + [O, L], "771", "771.12.3.13.4", "No está permitida la instalación de un solo conductor aislado o un cable unipolar por dentro de un caño metálico.", "771.12.3.13.4: Medidas mínimas de conductos y cajas")
R(G, "un_conductor_en_caño_no_metalico", "Un conductor por caño no metálico en tramos rectos", "Con un solo conductor por caño no metálico, en tramos rectos sin curvas, el diámetro interno es al menos 1,5 veces el diámetro exterior máximo del conductor.", "obligatorio", {"relacion_diametro_min": 1.5}, V + [O, L], "771", "771.12.3.13.4", "el diámetro interno del caño será como mínimo 1,5 veces el diámetro exterior máximo del conductor o cable alojado.", "771.12.3.13.4: Medidas mínimas de conductos y cajas")
R(G, "perfiles_ocupacion", "Perfiles registrables y canales", "El llenado de perfiles registrables no supera 45 % con cuplas exteriores o 35 % con cuplas interiores.", "obligatorio", {"ocupacion_max_cuplas_exteriores_pct": 45, "ocupacion_max_cuplas_interiores_pct": 35}, V + [O, L], "771", "771.12.3.10.2", "no debe superar el 45 % de ocupación, si las cuplas de unión de los tramos de perfil son instaladas en el exterior del perfil, o el 35 % si las cuplas de unión son interiores", "771.12.3.10")
R(G, "columnas_luminarias_35pct", "Entrada de cables en columnas de iluminación exterior", "Los cables no ocupan más del 35 % de la sección interior de los caños de entrada y salida.", "obligatorio", {"ocupacion_max_pct": 35}, ["alumbrado exterior"], "771", "771-B.8.3.7", "Los cables no deberán ocupar más del 35 % de la sección interior de los caños.", "La entrada y salida de todo tipo de cables (alimentación, señalización")
R(G, "curvas_fabrica_tabla", "Radios de curvatura de curvas de fábrica (caño liviano o semipesado)", "Radio mínimo y máximo de curvas lisas (CL) o roscadas (CR) según el diámetro nominal.", "obligatorio", {"unidad": "mm", "campos": ["designacion_IRAM_mm", "radio_min", "radio_max"]}, V + [O, L], "771", "Tabla 771.12.VIII", "Tabla 771.12.VIII - Radios de curvatura para curvas construidas en fábrica", "Tabla 771.12.VIII - Radios de curvatura para curvas construidas en fábrica",
  tabla=[{"diametro_nominal": a, "designacion_iram_mm": b, "radio_min_mm": c, "radio_max_mm": d} for a, b, c, d in (('5/8"', 16, 35, 45), ('3/4"', 19, 42, 52), ('7/8"', 22, 50, 55), ('1"', 25, 59, 69), ('1 1/4"', 32, 74, 84), ('1 1/2"', 38, 90, 100), ('2"', 51, 120, 130))])

# ------------------------------------------------------------------ bandejas
G = "bandejas"
R(G, "reserva_20pct", "Reserva en bandejas portacables", "El ancho de la bandeja suma los diámetros de todos los cables, sus separaciones y una reserva no inferior al 20 %.", "obligatorio", {"reserva_min_pct": 20}, V + [O, L], "771", "771.12.3.9.2", "más un espacio de reserva no inferior al 20 %", "Para el dimensionamiento del ancho de las bandejas")
R(G, "una_capa", "Capas de cables en bandejas", "Se admite una sola capa de cables; los unipolares en formación trébol o cuadrada se consideran una capa.", "obligatorio", {"capas_max": 1}, V + [O, L], "771", "771.12.3.9.2", "no permitiéndose más que una capa de cables", "Para el dimensionamiento del ancho de las bandejas")
R(G, "solo_control_40pct", "Bandejas solo con cables de comando, control y señalización", "La sección transversal ocupada llega hasta el 40 % de la sección útil, para bandejas de lateral no superior a 100 mm.", "obligatorio", {"ocupacion_max_pct": 40, "altura_lateral_max_mm": 100}, V + [O, L], "771", "771.12.3.9.2", "ocupada hasta un 40 % de la sección transversal útil", "Para el dimensionamiento del ancho de las bandejas")
R(G, "separacion_entre_bandejas", "Separación entre líneas de bandejas", "Si hace falta más de una bandeja en planos distintos, la separación mínima es de 0,3 m, reducible hasta 0,2 m aplicando los factores de corrección.", "obligatorio", {"separacion_min_m": 0.3, "separacion_min_con_factores_m": 0.2}, V + [O, L], "771", "771.12.3.9.2", "con una separación mínima de 0,3 m entre cada una", "Para el dimensionamiento del ancho de las bandejas")
R(G, "altura_montaje", "Altura mínima de montaje de bandejas", "Para personal no calificado (BA1-BA3): 2,2 m en interiores, 3,5 m en exteriores y 4 m con circulación vehicular.", "obligatorio", {"interior_min_m": 2.2, "exterior_min_m": 3.5, "con_vehiculos_min_m": 4}, V + [O, L], "771", "771.12.3.9.3", "las alturas mínimas de montaje serán: 2,2 m en interiores, 3,5 m en exteriores y 4 m donde exista circulación", "771.12.3.9.3: Prescripciones de instalación de bandejas portacables en función de las influencias")
R(G, "tapas_hasta_2_2m", "Tapas de protección en bandejas", "Las bandejas más altas llevan tapas hasta una altura de 2,2 m del piso terminado; las que están por debajo de 2,2 m se tapan igual.", "obligatorio", {"altura_tapa_m": 2.2}, V + [O, L], "771", "771.12.3.9.3", "altura de 2,2 m, medida desde el nivel de piso terminado", "771.12.3.9.3: Prescripciones de instalación de bandejas portacables en función de las influencias")

# ------------------------------------------------------------------ enterrados
G = "enterrados"
R(G, "profundidad_cables_directos", "Cables directamente enterrados", "Los cables directamente enterrados van a una profundidad mínima de 0,7 m respecto de la superficie del terreno, con protección mecánica de ladrillos o cubiertas.", "obligatorio", {"profundidad_min_m": 0.7}, V + [O, L], "771", "771.12.4.2.1", "a una profundidad mínima de 0,7 m respecto de la superficie del terreno", "771.12.4.2.1: Tendido directamente enterrado")
R(G, "recubrimiento_conductos", "Conductos enterrados", "Los conductos tienen un recubrimiento mínimo de 0,7 m de tierra de relleno y pendiente mínima de 1 % hacia las cámaras de inspección.", "obligatorio", {"recubrimiento_min_m": 0.7, "pendiente_min_pct": 1}, V + [O, L], "771", "771.12.4.2.2", "recubrimiento mínimo de 0,7 m de tierra de relleno por sobre el conducto", "771.12.4.2.2: Tendido en conductos enterrados")
R(G, "pendiente_conductos", "Pendiente de conductos enterrados", "La pendiente mínima de los conductos enterrados es 1 % hacia las cámaras de inspección.", "obligatorio", {"pendiente_min_pct": 1}, V + [O, L], "771", "771.12.4.2.2", "con pendiente mínima del 1 % hacia las cámaras de inspección", "771.12.4.2.2: Tendido en conductos enterrados")
R(G, "diametro_conductos_tabla", "Diámetro mínimo de conductos enterrados", "Un cable por caño: 50 mm si d ≤ 25 mm, 100 mm si 25 < d ≤ 66 mm, 1,5·d si d > 66 mm. Dos cables: 3·d (mín. 50) / 2,5·d (mín. 100) / 2,5·d. Tres cables: 3·d (mín. 50) / 3·d (mín. 100) / 3·d.", "obligatorio", {"d_es": "diámetro exterior del cable en mm"}, V + [O, L], "771", "Tabla 771.12.XIV", "Tabla 771.12.XIV - Diámetro mínimo de conductos enterrados", "Tabla 771.12.XIV - Diámetro mínimo de conductos enterrados",
  tabla=[{"d_mm": "d <= 25", "un_cable_mm": 50, "dos_cables": "3 d con un mínimo de 50", "tres_cables": "3 d con un mínimo de 50"}, {"d_mm": "25 < d <= 66", "un_cable_mm": 100, "dos_cables": "2,5 d con un mínimo de 100", "tres_cables": "3 d con un mínimo de 100"}, {"d_mm": "d > 66", "un_cable_mm": "1,5 d", "dos_cables": "2,5 d", "tres_cables": "3 d"}])
R(G, "bajo_construcciones", "Cables subterráneos bajo construcciones", "Van dentro de un conducto que se extiende al menos 0,30 m más allá del perímetro de la construcción.", "obligatorio", {"extension_min_m": 0.3}, V + [O, L], "771", "771.12.4.2.3", "se extienda, como mínimo, 0,30 m más allá del perímetro de la construcción", "771.12.4.2.3: Cables subterráneos debajo de construcciones")
R(G, "cruces_caño_de_reserva", "Cruces de calles internas", "Los cables que cruzan calles internas van en caños protegidos por hormigón y se deja previsto al menos un caño de reserva.", "obligatorio", {"canos_de_reserva_min": 1}, V + [O, L], "771", "771.12.4.2.3", "se dejará previsto como mínimo un caño de reserva", "771.12.4.2.3: Cables subterráneos debajo de construcciones")
R(G, "proteccion_hormigon_pobre", "Protección de caños de PVC enterrados", "Los caños de PVC (IRAM 13350) se recubren en todas sus caras con hormigón pobre 1:5 de espesor mínimo 5 cm.", "obligatorio", {"dosificacion": "1:5", "espesor_min_cm": 5}, V + [O, L], "771", "771.12.4.2.2", "espesor mínimo de 5 cm", "771.12.4.2.2: Tendido en conductos enterrados")

# ------------------------------------------------------------------ tableros
G = "tableros"
D204 = "771.20.4: Forma constructiva de los tableros"
R(G, "reserva_771", "Espacio de reserva en tableros (771)", "Los tableros de hasta 250 A dejan al menos 20 % de la capacidad total en módulos de 18 mm libre para ampliaciones; con módulos de 27 mm o cajas moldeadas, 20 % de cada tipo y como mínimo un interruptor de cada tipo. Sobre 250 A, a criterio del proyectista.", "obligatorio", {"corriente_max_a": 250, "reserva_min_pct": 20, "reserva_minima_un_interruptor_por_tipo": True}, V + [O, L], "771", "771.20.4", "de por lo menos el 20 % de la capacidad total del tablero en módulos de 18 mm", D204)
R(G, "reserva_770", "Espacio de reserva en tableros de viviendas (770)", "En viviendas, el tablero deja al menos 20 % de reserva sobre su capacidad total en módulos de 18 mm.", "obligatorio", {"reserva_min_pct": 20}, ["viviendas"], "770", "770.16.4", "veinte por ciento (20 %) de la capacidad total del tablero en módulos de 18 mm")
R(G, "altura_comandos", "Altura de los elementos de comando", "Las palancas o comandos de dispositivos de maniobra y protección quedan entre 0,40 m y 2 m del piso del local.", "obligatorio", {"altura_min_m": 0.4, "altura_max_m": 2.0}, V + [O, L], "771", "771.20.4", "entre 0,40 m y 2 m", D204)
R(G, "altura_borneras", "Altura de borneras", "Las borneras de conexión quedan a no menos de 0,2 m, medidos desde su parte inferior, del piso terminado.", "obligatorio", {"altura_min_m": 0.2}, V + [O, L], "771", "771.20.4", "deberán estar ubicadas a una altura mínima de 0,2 m, medida desde su parte inferior con respecto al nivel de piso terminado", D204)
R(G, "gabinetes_en_zonas_de_vehiculos", "Cajas y gabinetes en zonas de vehículos", "En accesos y zonas de maniobra de vehículos, el borde inferior de cajas o gabinetes queda a no menos de 1,5 m de la superficie transitada; si no es posible, se protegen contra colisiones.", "obligatorio", {"altura_min_m": 1.5}, V + [O, L], "771", "771.20.4", "con su borde inferior a no menos de 1,5 m de altura con relación a la superficie por donde transitan los vehículos", D204)
R(G, "ip_minimo_viviendas_oficinas", "Grado de protección de tableros", "Tableros de viviendas, oficinas y locales sin personal BA4/BA5: IP41 o IP31D como mínimo, sin partes con tensión accesibles aun con la puerta abierta.", "obligatorio", {"ip_min": "IP41 o IP31D"}, V + [O, L], "771", "771.20.4", "el grado de protección será como mínimo IP41 o IP31D", D204)
R(G, "ip_intemperie_principal", "Tablero principal a la intemperie", "A la intemperie, el grado de protección del tablero principal no es inferior a IP54.", "obligatorio", {"ip_min": "IP54"}, V + [O, L], "771", "771.20.3.1", "el grado de protección no debe ser inferior a IP54", "771.20.3.1")
R(G, "no_en_baños", "Prohibición de tableros en cuartos de baño", "Ni el tablero principal ni los seccionales se instalan en cuartos de baño.", "prohibido", {"ubicacion_prohibida": "cuarto de baño"}, V + [O, L], "771", "771.20.3.1 y 771.20.3.2", "Los tableros principales no se instalarán en los cuartos de baño.", "771.20.3.1")
R(G, "no_en_baños_701", "Prohibición de tableros en baños (701)", "No se permite instalar tableros eléctricos en los cuartos de baño.", "prohibido", {"ubicacion_prohibida": "cuarto de baño"}, V + [O, L], "701", "701.512.4", "No está permitida la instalación de tableros eléctricos en los cuartos de baño.")
R(G, "verificacion_calentamiento", "Verificación térmica de tableros", "En todos los tableros se verifican los límites de calentamiento según IEC 60439-1, 60439-3, IEC TR 60890, 60670-24 o 62208.", "obligatorio", {}, V + [O, L], "771", "771.20.4", "En todos los tableros se debe efectuar una verificación de los límites de calentamiento.", D204)
R(G, "montaje_componentes", "Montaje de componentes", "Los componentes no se montan directamente sobre las caras posteriores o laterales del tablero, sino en soportes o perfiles.", "prohibido", {}, V + [O, L], "771", "771.20.4", "Los componentes eléctricos no podrán montarse directamente sobre las caras posteriores o laterales del tablero", D204)

# ------------------------------------------------------------------ baños (701)
G = "banos"
R(G, "zona0_ducha_sin_receptaculo", "Zona 0 de duchas sin receptáculo", "La altura de la zona 0 es de 10 cm y su extensión es la misma de la zona 1.", "obligatorio", {"altura_zona0_cm": 10}, V + [O, L], "701", "701.30.2", "la altura de la zona 0 es 10 cm")
R(G, "zona1_altura", "Zona 1: altura", "La zona 1 llega al plano horizontal a 225 cm del punto más alto del piso de la bañera o receptáculo, o al punto de salida de agua más alto, el mayor de los dos.", "obligatorio", {"altura_cm": 225}, V + [O, L], "701", "701.30.3", "el plano horizontal que queda a 225 cm por sobre el punto más alto del piso de la bañera o")
R(G, "zona1_duchador_movil", "Zona 1: duchador móvil", "Con duchador móvil, la superficie vertical de la zona 1 es la circunscripta a 120 cm del punto de conexión a la salida de agua del conducto flexible.", "obligatorio", {"distancia_cm": 120}, V + [O, L], "701", "701.30.3", "a una distancia de 120 cm desde el punto de conexión a la salida de agua del conducto")
R(G, "zona1_ducha_sin_receptaculo_fija", "Zona 1: ducha fija sin receptáculo", "Sin receptáculo y con duchador fijo, la zona 1 se extiende 60 cm horizontales desde la flor de la ducha.", "obligatorio", {"distancia_horizontal_cm": 60}, V + [O, L], "701", "701.30.3", "a una distancia horizontal de 60 cm desde la flor de la ducha")
R(G, "zona2_ancho", "Zona 2", "La zona 2 se extiende 60 cm por fuera del límite exterior de la zona 1, entre el piso y el cielorraso.", "obligatorio", {"ancho_cm": 60}, V + [O, L], "701", "701.30.4", "situada a 60 cm por afuera de la zona 1")
for z, ip in (("0", "IPX7"), ("1", "IPX5"), ("2", "IPX4"), ("3", "IPX1")):
    R(G, f"ip_zona_{z}", f"Grado de protección en zona {z}", f"Los materiales y equipos eléctricos en la zona {z} tienen como mínimo {ip}" + ("; IPX5 en baños públicos o donde se usen chorros de agua." if z in ("2", "3") else "."), "obligatorio", {"ip_min": ip, "ip_min_con_chorros": "IPX5" if z in ("2", "3") else ip}, V + [O, L], "701", "701.512.2", f"en la zona {z}: {ip}")
R(G, "diferencial_30ma", "Protección diferencial de circuitos de baño", "Todos los circuitos terminales de los locales de baño se protegen complementariamente con interruptores diferenciales de IΔn ≤ 30 mA.", "obligatorio", {"i_dn_max_ma": 30}, V + [O, L], "701", "701.412.5", "deberán ser protegidos complementariamente contra los contactos directos por medio de interruptores diferenciales de IΔn ≤ 30 mA")
R(G, "separacion_electrica", "Separación eléctrica en baños", "La protección por separación eléctrica se admite solo para circuitos que alimentan un solo aparato utilizador o un solo tomacorriente.", "obligatorio", {"cargas_max": 1}, V + [O, L], "701", "701.413.5", "Para los circuitos que alimenten un solo tomacorriente.")
R(G, "hidromasaje_alimentacion", "Bañeras de hidromasaje", "Se alimentan en forma fija y permanente desde un diferencial de IΔn ≤ 30 mA exclusivo, con protección termomagnética asociada; el volumen bajo la bañera es zona 1.", "obligatorio", {"i_dn_max_ma": 30, "diferencial_exclusivo": True}, V + [O, L], "771", "771.8.5 s)", "La alimentación a dichas bañeras deberá realizarse en forma fija y permanente desde un interruptor diferencial de IΔn ≤ 30 mA", D771_85)

# ------------------------------------------------------------------ otros
G = "otros"
R(G, "cercas_electrificadas_altura", "Cercas electrificadas", "Las cercas electrificadas cumplen IEC 60335-2-76 y se instalan a una altura mínima de 2,5 m sobre el solado terminado.", "obligatorio", {"altura_min_m": 2.5}, ["viviendas"], "770", "770.7.7", "deben estar instaladas a una altura")

# =============================================================== generación
def main(dir_txt, dir_out, dir_ocr=None):
    textos = {k: Texto(os.path.join(dir_txt, v)) for k, v in NORMAS.items()}
    por_grupo, ids = {}, set()
    for r in REGLAS:
        if r["id"] in ids:
            raise SystemExit("FALLA: id repetido " + r["id"])
        ids.add(r["id"])
        tx = textos[r["norma"]]
        _, pag = tx.buscar(r["cita"], r["desde"])
        reg = {"id": r["id"], "grupo": r["grupo"], "tema": r["tema"], "regla": r["regla"], "tipo": r["tipo"],
               "parametros": r["parametros"], "aplica_a": r["aplica_a"],
               "fuente": {"norma": NOMBRES[r["norma"]], "edicion": tx.edicion, "clausula": r["clausula"],
                          "pagina_impresa": pag, "cita": r["cita"]},
               "estado": "borrador: cita verificada contra el texto del PDF; valores a validar por el usuario"}
        if r["tabla"]:
            reg["tabla"] = r["tabla"]
        por_grupo.setdefault(r["grupo"], []).append(reg)
    if dir_ocr:
        import reglas_ocr as RO
        fallas = []
        for r in RO.REGLAS_OCR:
            if r["id"] in ids:
                raise SystemExit("FALLA: id repetido " + r["id"])
            ids.add(r["id"])
            parte = r["norma"][0]
            if not RO.verificar_cita(dir_ocr, int(parte), r["pdf"], r["cita"]):
                fallas.append(f"{r['id']} (parte {parte}, pág. PDF {r['pdf']}): {r['cita']!r}")
                continue
            estado = ("borrador: valores leídos sobre la imagen de la página; título contrastado con el OCR; a validar por el usuario"
                      if r["verificacion"] == "visual" else
                      "borrador: cita contrastada con el OCR de la página (coincidencia aproximada, sin tildes); a validar por el usuario")
            reg = {"id": r["id"], "grupo": r["grupo"], "tema": r["tema"], "regla": r["regla"], "tipo": r["tipo"],
                   "parametros": r["parametros"], "aplica_a": r["aplica_a"],
                   "fuente": {"norma": "AEA 90364-" + r["norma"], "edicion": "2006", "clausula": r["clausula"],
                              "pagina_impresa": r["impresa"], "pagina_pdf": r["pdf"], "cita": r["cita"],
                              "verificacion": r["verificacion"]},
                   "estado": estado}
            if r["tabla"]:
                reg["tabla"] = r["tabla"]
            por_grupo.setdefault(r["grupo"], []).append(reg)
    if dir_ocr and fallas:
        raise SystemExit("FALLA: citas no halladas en el OCR:\n  " + "\n  ".join(fallas))
    os.makedirs(dir_out, exist_ok=True)
    indice = {"descripcion": "Reglas de ingeniería extraídas de las normas AEA en assets/, una por requisito, con cláusula, página y cita textual.",
              "esquema": {"id": "grupo.nombre", "tipo": "obligatorio | recomendado | prohibido", "parametros": "valores numéricos o textuales de la regla",
                          "aplica_a": "tipos de inmueble o instalación", "fuente": "norma, edición, cláusula, página impresa y cita textual verificada"},
              "grupos": {}}
    for g, lst in por_grupo.items():
        archivo = f"{g}.json"
        json.dump({"grupo": g, "reglas": lst}, open(os.path.join(dir_out, archivo), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        indice["grupos"][g] = {"archivo": archivo, "cantidad": len(lst)}
    indice["total_reglas"] = sum(v["cantidad"] for v in indice["grupos"].values())
    json.dump(indice, open(os.path.join(dir_out, "_indice.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("OK", indice["total_reglas"], "reglas en", len(por_grupo), "grupos")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
