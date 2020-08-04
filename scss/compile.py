#!/usr/bin/env python3
import sass
import subprocess
import shutil
import os
from pathlib import Path

def runcmd(cmd):
    if os.name == "nt":
        return subprocess.check_output(cmd, shell=True)
    proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    return proc.communicate()

local_path = Path(__file__).resolve().parent
node_bin = Path(runcmd("npm bin")[0].decode('utf-8').rstrip())
print(f"assuming npm bin directory \"{node_bin}\". Is this correct?")
if input("[yY/nN]: ").lower() == "n":
    node_bin = local_path.parent / 'node_modules' / '.bin'
    print(f"this? \"{node_bin}\"")
    if input("[yY/nN]: ").lower() == "n":
        node_bin = input("input bin directory: ")

for bsv in [d for d in local_path.iterdir() if 'bs' in d.name]:
    scss = bsv / f'{bsv.name}-jf.scss'
    css = bsv / f'{bsv.name}-jf.css'
    min_css = bsv.parents[1] / 'jellyfin_accounts' / 'data' / 'static' / f'{bsv.name}-jf.css'
    with open(css, 'w') as f:
        f.write(sass.compile(filename=str(scss.resolve()),
                             output_style='expanded',
                             precision=6))
    if css.exists():
        print(f'{bsv.name}: Compiled.')
        runcmd(f'{str((node_bin / "postcss").resolve())} {str(css.resolve())} --replace --use autoprefixer')
        print(f'{bsv.name}: Prefixed.')
        runcmd(f'{str((node_bin / "cleancss").resolve())} --level 1 --format breakWith=lf --output {str(min_css.resolve())} {str(css.resolve())}')
        if min_css.exists():
            print(f'{bsv.name}: Minified and copied to {str(min_css.resolve())}.')

for v in [('bootstrap', 'bs5'), ('bootstrap4', 'bs4')]:
    new_path = str((local_path.parent / 'jellyfin_accounts' / 'data' / 'static' / (v[1] + '.css')).resolve())
    shutil.copy(str((local_path.parent / 'node_modules' / v[0] / 'dist' / 'css' / 'bootstrap.min.css').resolve()),
                new_path)
    print(f'Copied {v[1]} to {new_path}')

