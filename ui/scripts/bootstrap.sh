#!/usr/bin/env sh
set -eu
PYTHON="${PYTHON:-python3}"
"$PYTHON" -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
printf '\nReady. Activate it with: . .venv/bin/activate\n'
