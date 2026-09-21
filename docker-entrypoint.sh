#!/bin/sh
set -e

# Xvfb sobe em background e o uvicorn fica como PID 1: xvfb-run como processo principal
# do container inicia o X mas nao chega a executar o comando, e falha sem log.
DISPLAY_NUM="${DISPLAY_NUM:-99}"
Xvfb ":${DISPLAY_NUM}" -screen 0 "${XVFB_SCREEN:-1920x1080x24}" -nolisten tcp &

for _ in $(seq 1 50); do
    [ -e "/tmp/.X11-unix/X${DISPLAY_NUM}" ] && break
    sleep 0.2
done

if [ ! -e "/tmp/.X11-unix/X${DISPLAY_NUM}" ]; then
    echo "Xvfb nao iniciou em :${DISPLAY_NUM}" >&2
    exit 1
fi

export DISPLAY=":${DISPLAY_NUM}"

exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
