#!/bin/sh
set -e

exec xvfb-run -a -s "-screen 0 ${XVFB_SCREEN:-1920x1080x24}" \
    uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
