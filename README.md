# layalib

Laya 的 TypeSafe Jev 兼容 HTTP server：`POST /v1/systemone`、`GET /v1/models`。兼容 [typesafe-sdk](https://docs.typesafe.ai/sdk/python)。协议细节见 [docs/server.md](docs/server.md)。

## 启动

Python ≥ 3.12。`cwd` 必须是仓库根。

```bash
uv sync
bash scripts/prepare.sh          # 拉 models/laya-multilingual
uv run layalib                   # 默认 127.0.0.1:8000
```

缺权重 `sys.exit(2)`。

| env | 默认 | 作用 |
|-----|------|------|
| `LAYA_HOST` | `127.0.0.1` | bind |
| `LAYA_PORT` | `8000` | bind |
| `LAYA_ML_DIR` | `models/laya-multilingual` | checkpoint |
| `LAYA_DEVICE` | `cpu` | torch device |

```bash
LAYA_PORT=8001 uv run layalib
```

## 试一把

```bash
curl -sS http://127.0.0.1:8000/v1/models
```

```bash
curl -sS http://127.0.0.1:8000/v1/systemone \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer test' \
  -d '{
    "state": {"document": "I was charged twice. Please fix this ASAP."},
    "model": "laya",
    "questions": {
      "billing": {"type": "noul", "instructions": "Is this ticket about billing?"},
      "tone": {
        "type": "choice",
        "instructions": "What is the customer tone?",
        "criteria": {"calm": null, "frustrated": null, "angry": null}
      },
      "urgency": {
        "type": "score",
        "instructions": "How urgent is this ticket?",
        "criteria": ["can wait", "this week", "today"]
      }
    }
  }'
```

SDK：

```python
from typesafe_sdk import Choice, Noul, Score, RetryPolicy, TypeSafeClient

with TypeSafeClient(
    api_key="test",
    base_url="http://127.0.0.1:8000",
    retry=RetryPolicy(max_retries=0),
) as client:
    r = client.system_one(
        state={"document": "I was charged twice. Please fix this ASAP."},
        questions={
            "billing": Noul(instructions="Is this ticket about billing?"),
            "tone": Choice(
                instructions="What is the customer's tone?",
                criteria={"calm": None, "frustrated": None, "angry": None},
            ),
            "urgency": Score(
                instructions="How urgent is this ticket?",
                criteria=["can wait", "this week", "today"],
            ),
        },
    )
    print(r.nouls["billing"].noul, r.choices["tone"].choice, r.scores["urgency"].score)
```

## 测试

```bash
bash scripts/ci.sh
```
