#!/usr/bin/env bash
# Ejecuta un script Python del harness con el intérprete correcto:
#   1) .venv-tools (creado por ./init.sh)  2) python3 real  3) python
# Evita el alias "python3" de Microsoft Store en Windows.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for cand in "$ROOT/.venv-tools/Scripts/python.exe" "$ROOT/.venv-tools/bin/python"; do
  if [[ -x "$cand" ]]; then exec "$cand" "$@"; fi
done
for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >/dev/null 2>&1; then
    exec "$cand" "$@"
  fi
done
echo "py.sh: no se encontró Python >= 3.10" >&2
exit 127
