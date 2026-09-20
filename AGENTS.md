# layalib

laya(is jev Reproductions): Multilingual, non-autoregressive System 1 decision engine. Typed decisions over 100+ languages in a single forward pass — 33 ms — trained with reinforcement learning against strictly proper scoring rules (RLCD), with a router that picks the right checkpoint per request.

## 技术栈

python3、uv、pytest

torch 用 cpu 运行

## 文件目录

1. laya：laya 的源码
2. jev-plays-pokemon-red: 在 PyBoy 上运行的《精灵宝可梦 红》：代码掌控路线和运算，Jev 在大约 100 毫秒内完成分支选择，校准是测量得到的而非假设的。
3. src/layalib：TypeSafe Jev 兼容 HTTP server（`POST /v1/systemone`、`GET /v1/models`）
4. docs/server.md：server 协议、env、SDK 对接

## 要求

1. src/layalib server 要兼容 [typesafe-sdk](https://docs.typesafe.ai/sdk/python)

## 完成条件

1. `bash scripts/ci.sh`

## ref

- jev: TypeSafe's Jev, System One models are a class of AI models built to make fast, structured decisions that software can use directly. A System One model evaluates a state and returns typed answers and probabilities. t’s trained using reinforcement learning for calibrated decisions (RLCD). https://www.langchain.com/blog/building-a-harness-with-jev
