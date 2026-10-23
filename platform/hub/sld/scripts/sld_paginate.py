"""Genera un SLD en una o varias hojas a partir de UN solo xlsx.
Uso: python sld_paginate.py <lib> <input.xlsx> <out_dir> <NAME> <lamina.svg> <mod_block.svg> [max_salidas=18]
Reparte las raices (y sus descendientes) en hojas de hasta max_salidas circuitos hoja;
si entra en una hoja, genera solo <NAME>."""
import sys, os, subprocess, openpyxl
lib, xlsx, out, name, lam, mod = sys.argv[1:7]
maxl = int(sys.argv[7]) if len(sys.argv) > 7 else 18
here = os.path.dirname(os.path.abspath(__file__))
wb = openpyxl.load_workbook(xlsx)
rows = list(wb['CIRCUITOS'].iter_rows(values_only=True))
hi = next(i for i, r in enumerate(rows) if r and r[0] == 'TAG')
hdr = list(rows[hi]); pcol = hdr.index('PARENT_TAG')
data = [r for r in rows[hi+1:] if r and r[0]]
tags = {str(r[0]).strip() for r in data}
kids = {}
for r in data:
    if r[pcol]: kids.setdefault(str(r[pcol]).strip(), []).append(str(r[0]).strip())
def leaves(t): return 1 if t not in kids else sum(leaves(k) for k in kids[t])
roots = [str(r[0]).strip() for r in data if not r[pcol] or str(r[pcol]).strip() not in tags]
groups, cur, cnt = [], [], 0
for t in roots:
    n = leaves(t)
    if cur and cnt + n > maxl:
        groups.append(cur); cur, cnt = [], 0
    cur.append(t); cnt += n
if cur: groups.append(cur)
env = dict(os.environ)
TABLA = f'{name}_TABLA'                      # tabla de cálculo: lámina propia, con todos los circuitos
nombres_diag = [name if len(groups) == 1 else f'{name}_H{k}' for k in range(1, len(groups) + 1)]
todos = ','.join(nombres_diag + [TABLA])     # una fila de rótulo por lámina (diagramas + tabla)
for i, g in enumerate(groups, 1):
    env['SLD_INDEX'] = str(i); env['SLD_TOTAL'] = str(len(groups) + 1)
    env['SLD_NAMES'] = todos
    env.pop('SLD_SOLO_TABLA', None)
    env['SLD_SIN_TABLA'] = '1'
    if len(groups) == 1:
        nm = name
        for k in ('SLD_SUBSET','SLD_TITLE_SUFFIX','SLD_PREV','SLD_NEXT'): env.pop(k, None)
    else:
        nm = f'{name}_H{i}'
        env['SLD_SUBSET'] = ','.join(g)
        env['SLD_TITLE_SUFFIX'] = f'(hoja {i} de {len(groups)})'
        env['SLD_PREV'] = str(i-1) if i > 1 else ''
        env['SLD_NEXT'] = str(i+1) if i < len(groups) else ''
    res = subprocess.run([sys.executable, os.path.join(here, 'sld_generator.py'), lib, xlsx, out, nm, lam, mod],
                         env=env, capture_output=True, text=True)
    print(res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr.strip()[-300:])
    for ln in res.stderr.splitlines():
        if ln.startswith('AVISO'): print('  ' + ln)
    if res.returncode: sys.exit(res.returncode)

# hoja de tabla de cálculo (todos los circuitos, sin diagrama)
env = dict(os.environ)
env['SLD_NAMES'] = todos
env['SLD_INDEX'] = str(len(groups) + 1); env['SLD_TOTAL'] = str(len(groups) + 1)
env['SLD_SOLO_TABLA'] = '1'
env.pop('SLD_SIN_TABLA', None)
for k in ('SLD_SUBSET', 'SLD_PREV', 'SLD_NEXT'): env.pop(k, None)
env['SLD_TITLE_SUFFIX'] = '(tabla de cálculo)'
res = subprocess.run([sys.executable, os.path.join(here, 'sld_generator.py'), lib, xlsx, out, TABLA, lam, mod],
                     env=env, capture_output=True, text=True)
print(res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr.strip()[-300:])
for ln in res.stderr.splitlines():
    if ln.startswith('AVISO'): print('  ' + ln)
if res.returncode: sys.exit(res.returncode)
