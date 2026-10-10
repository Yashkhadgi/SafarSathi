#!/bin/sh
set -eu

mkdir -p memory data/embeddings logs

if [ ! -f data/embeddings/.kb-built ]; then
    echo "Validating and building the knowledge base..."
    python scripts/validate_kb.py
    python scripts/build_knowledge_base.py
    touch data/embeddings/.kb-built
fi
if [ "${LEGACY_GRADIO:-0}" = "1" ]; then
    echo "Starting legacy Gradio UI..."
    exec python ui/app.py
fi

echo "Starting SafarSathi FastAPI 2.0 backend..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 7860
