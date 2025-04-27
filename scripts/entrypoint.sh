#!/bin/sh
set -ex

echo "Starting initial indexing..."
python scripts/initial_indexing.py

echo "Initial indexing done."

echo "Running query processor..."
python src/query_processor/query_processor.py "what does _useAttributes do?"

echo "Done!"
