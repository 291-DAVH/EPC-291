import sys, openpyxl
SRC, DST_PREFIX = sys.argv[1], sys.argv[2]
H = ['TAG','DESCRIPCION','CARGA','UNIDAD_CARGA','DESTINO','PARENT_TAG','TOPOLOGY','FASE','LONGITUD_m','FP','RENDIMIENTO','KIND','NOTAS']
V = {
 1: dict(tab={'NOMBRE':'TGBT-02 – TABLERO PLANTA BAJA','TENSION_V':380,'SISTEMA':'TN-S','ICC_KA':36,'FP_DEFAULT':0.85,'FRECUENCIA_HZ':50,'PROYECTO':'108-2026-SO000002-E-DU-003'},
    rows=[
     ['C-01','ALIMENTADOR TD-PB PLANTA BAJA',250,'A','TD-PB PLANTA BAJA',None,'single','3F',40,None,None,'mccb','Desde TGBT-01'],
     ['M-01','EXTRACTOR EXT-01',11,'kW','EXTRACTOR EXT-01',None,'dol_ol','3F',30,0.85,0.9,'auto','Motor IE3'],
     ['M-02','BOMBA CALEFACCIÓN BC-01',37,'kW','BOMBA BC-01',None,'star_delta','3F',45,0.86,0.93,'auto','Arranque Y-Δ'],
     ['M-03','CINTA TRANSPORTADORA CT-01',4,'kW','CINTA CT-01',None,'dol','3F',20,0.82,0.85,'auto',None],
     ['G-02','RCCB GRUPO TOMAS PB',None,'A','TOMAS PLANTA BAJA',None,'single','3F',None,None,None,'rccb','Carga = suma hijos'],
     ['G-02-A','Tomas oficina 01',2.5,'kW','TOMAS OF-01','G-02','single','1F',15,0.9,None,'mcb',None],
     ['G-02-B','Tomas oficina 02',2.2,'kW','TOMAS OF-02','G-02','single','1F',18,0.9,None,'mcb',None],
     ['G-02-C','Cocina office',3.5,'kW','COCINA OFFICE','G-02','single','1F',25,0.9,None,'rcbo','RCBO 30 mA'],
     ['C-02','UPS RACK DATOS',15,'kVA','UPS RACK DATOS',None,'single','3F',10,0.9,None,'auto','UPS'],
     ['C-03','MONTACARGAS MC-01',5,'HP','MONTACARGAS MC-01',None,'vfd','3F',35,0.85,0.9,'auto','Rampa 10 s'],
    ]),
 2: dict(tab={'NOMBRE':'TGBT-03 – SALA DE MÁQUINAS','TENSION_V':400,'SISTEMA':'TN-S','ICC_KA':16,'FP_DEFAULT':0.8,'FRECUENCIA_HZ':50,'PROYECTO':'108-2026-SO000003-E-DU-004'},
    rows=[
     ['M-01','BOMBA AGUA FRÍA BAF-01',5.5,'kW','BAF-01',None,'dol_ol','3F',28,0.8,0.88,'auto','Protección térmica'],
     ['M-02','BOMBA AGUA CALIENTE BAC-01',15,'kW','BAC-01',None,'softstarter','3F',30,0.85,0.92,'auto','Rampa 15 s'],
     ['M-03','CHILLER CH-01',30,'kW','CH-01',None,'star_delta','3F',40,0.87,0.93,'auto','Y-Δ t=8 s'],
     ['M-04','VENTILADOR VE-03',3,'kW','VE-03',None,'vfd','3F',22,0.8,0.86,'auto',None],
     ['M-05','COMPRESOR CA-01',7.5,'kW','CA-01',None,'dol_rcd','3F',18,0.85,0.9,'auto','Área húmeda'],
     ['C-01','TABLERO AUXILIAR TA-02',100,'A','TA-02',None,'single','3F',30,None,None,'mccb',None],
     ['G-01','RCCB ALUMBRADO SALA',None,'A','ALUMBRADO SALA MÁQ.',None,'single','3F',None,None,None,'rccb','Carga = suma hijos'],
     ['G-01-A','Iluminación sala 1',0.8,'kW','ILUM. 1','G-01','single','1F',12,0.9,None,'mcb',None],
     ['G-01-B','Iluminación sala 2',0.8,'kW','ILUM. 2','G-01','single','1F',14,0.9,None,'mcb',None],
     ['G-01-C','Toma de servicio sala',1.2,'kW','TOMA SERVICIO','G-01','single','1F',16,0.9,None,'rcbo','RCBO 30 mA'],
     ['C-02','CALEFACTOR SALA',9,'kW','CALEFACTOR SALA',None,'single','3F',25,0.95,None,'auto',None],
    ]),
 3: dict(tab={'NOMBRE':'TGBT-04 – OFICINAS PISO 3','TENSION_V':380,'SISTEMA':'TN-S','ICC_KA':10,'FP_DEFAULT':0.9,'FRECUENCIA_HZ':50,'PROYECTO':'108-2026-SO000004-E-DU-005'},
    rows=[
     ['C-01','SUBTABLERO PISO 3 SP3',160,'A','SP3',None,'single','3F',60,None,None,'mccb',None],
     ['G-03','RCCB GRUPO OFICINAS P3',None,'A','OFICINAS PISO 3',None,'single','3F',None,None,None,'rccb','Carga = suma hijos'],
     ['G-03-A','Oficina 3.01 luz + tomas',2,'kW','OF 3.01','G-03','single','1F',20,0.9,None,'mcb',None],
     ['G-03-B','Oficina 3.02 luz + tomas',2,'kW','OF 3.02','G-03','single','1F',22,0.9,None,'rcbo','RCBO 30 mA'],
     ['G-03-C','Oficina 3.03 luz + tomas',1.8,'kW','OF 3.03','G-03','single','1F',24,0.9,None,'rcbo','RCBO 30 mA'],
     ['G-03-D','Sala de copia / impresoras',1.2,'kW','SALA COPIA','G-03','single','1F',18,0.9,None,'mcb',None],
     ['C-02','SPLIT CLIMATIZACIÓN P3',7,'kW','SPLIT P3',None,'single','3F',30,0.9,None,'auto',None],
     ['M-03','EXTRACTOR BAÑOS EB-03',0.75,'kW','EXTRACTOR EB-03',None,'dol','1F',15,0.8,0.7,'auto',None],
     ['C-03','UPS SERVIDOR PISO 3',5,'kVA','UPS SERVIDOR P3',None,'single','1F',8,0.9,None,'auto','UPS'],
    ]),
}
for n, cfg in V.items():
    wb = openpyxl.load_workbook(SRC)
    ws = wb['TABLERO']
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
        k = row[0].value
        if k in cfg['tab']: row[1].value = cfg['tab'][k]
    wc = wb['CIRCUITOS']
    hdr_row = next(r for r in range(1, wc.max_row+1) if wc.cell(r,1).value == 'TAG')
    cols = {wc.cell(hdr_row, c).value: c for c in range(1, wc.max_column+1)}
    if wc.max_row > hdr_row: wc.delete_rows(hdr_row+1, wc.max_row)
    for i, data in enumerate(cfg['rows']):
        r = hdr_row + 1 + i
        for name, val in zip(H, data):
            wc.cell(r, cols[name]).value = val
    wb.save(f"{DST_PREFIX}_V{n}.xlsx")
    print('ok', n, len(cfg['rows']))
