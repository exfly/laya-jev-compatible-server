
git clone git@github.com:NandhaKishorM/laya.git
git clone git@github.com:valentynkit/jev-plays-pokemon-red.git

mkdir -p models && HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 HF_HUB_DISABLE_XET=1 .venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
p = snapshot_download(
    "convaiinnovations/laya-multilingual",
    local_dir="models/laya-multilingual",
)
print("downloaded", p)
PY
