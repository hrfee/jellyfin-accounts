#!/usr/bin/env python3

import subprocess
import os
from pathlib import Path


def runcmd(cmd):
    if os.name == "nt":
        return subprocess.check_output(cmd, shell=True)
    proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    return proc.communicate()


print('Installing npm packages')

if os.name == "nt":
    print("Note: npm on windows installs all packages in the root directory, so things might get ugly.")

root_path = Path(__file__).parents[1]
runcmd(f'npm install --prefix {root_path}')

if (root_path / 'node_modules' / 'cleancss').exists():
    print(f'Installed successfully in {str((root_path / "node_modules").resolve())}.')

