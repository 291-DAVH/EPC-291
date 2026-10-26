import zipfile, os, sys
ROOT = sys.argv[1]          # plugin/iec60617-symbol-generator folder inside the project
CATALOG = sys.argv[2]       # catalog xlsx to put at zip root
OUT = sys.argv[3]           # output .plugin
SRC = os.path.join(os.path.dirname(os.path.dirname(ROOT)), 'src')
tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(ROOT, '.claude-plugin', 'plugin.json'), '.claude-plugin/plugin.json')
    z.write(os.path.join(ROOT, 'README.md'), 'README.md')
    z.write(CATALOG, 'catalogo_simbolos.xlsx')
    for dp, dn, fn in os.walk(SRC):
        for f in fn:
            if f.endswith(('.xlsx', '.bak')):
                continue
            full = os.path.join(dp, f)
            z.write(full, 'src/' + os.path.relpath(full, SRC).replace(os.sep, '/'))
os.replace(tmp, OUT)
with zipfile.ZipFile(OUT) as z:
    assert z.testzip() is None
    print('entries', len(z.namelist()))
