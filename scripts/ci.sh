set -euo pipefail
export LAYA_ML_DIR=models/laya-multilingual
uv sync --dev

uv run pytest poc
uv run pytest tests
uv run python3 poc/multilingual.py
