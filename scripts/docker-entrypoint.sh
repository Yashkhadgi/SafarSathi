#!/bin/sh
set -eu

mkdir -p memory data/embeddings logs

if [ ! -f data/embeddings/.kb-built ]; then
    echo "Validating and building the knowledge base..."
    python scripts/validate_kb.py
    python scripts/build_knowledge_base.py
    touch data/embeddings/.kb-built
fi

exec python ui/app.py
