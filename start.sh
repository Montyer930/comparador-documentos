#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv/bin"

port=$(
  "$VENV/python3" -c "
import socket
for p in range(8000, 8100):
    with socket.socket() as s:
        if s.connect_ex(('localhost', p)) != 0:
            print(p)
            break
"
)

echo "Iniciando Comparador de Documentos en http://localhost:$port"
exec "$VENV/uvicorn" backend.main:app --host 0.0.0.0 --port "$port" --reload
