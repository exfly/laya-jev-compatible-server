"""laya-multilingual 最小 POC：一次 forward pass，多语言 billing 工单。"""
import logging
import os
import sys
import time

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")
sys.path.insert(0, "laya")

log = logging.getLogger("laya.poc.multilingual")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

PASS_THRESHOLD = 6

QUESTIONS = {
    "dept": {
        "type": "choice",
        "instructions": "Which team should handle `message`?",
        "criteria": {
            "billing": "invoices, payments, refunds",
            "technical": "bugs, outages, integrations",
            "sales": "pricing, demos, new purchases",
            "hr": "hiring, leave, payroll",
        },
    },
    "refund": {
        "type": "noul",
        "instructions": "Does the customer ask for money back?",
    },
}

BILLING_SAMPLES = [
    ("english", "I was charged twice for invoice 4411, please refund it today."),
    ("german", "Ich wurde zweimal fuer Rechnung 4411 belastet, bitte erstatten Sie den Betrag."),
    ("french", "J'ai ete facture deux fois pour la facture 4411, remboursez-moi s'il vous plait."),
    ("spanish", "Me cobraron dos veces la factura 4411, por favor devuelvanme el dinero."),
    ("hindi", "मुझसे इनवॉइस 4411 के लिए दो बार शुल्क लिया गया, कृपया पैसे वापस करें।"),
    ("japanese", "請求書4411で二重に請求されました。返金してください。"),
    ("chinese", "发票4411被重复扣款，请退款。"),
    ("russian", "С меня дважды списали деньги по счёту 4411, верните деньги."),
]


def model_dir():
    """LAYA_ML_DIR 优先，否则 models/laya-multilingual（相对 cwd）。"""
    return os.environ.get("LAYA_ML_DIR") or os.path.join("models", "laya-multilingual")


def load_agent(model_dir, device=None):
    """加载 laya Agent；device=None 让 Agent 自己选。"""
    import laya

    log.info("load path=%s device=%s", model_dir, device)
    agent = laya.load(model_dir, device=device)
    log.info("loaded on %s", agent.device)
    return agent


def predict_one(agent, text):
    """对一条工单做 forward pass，返回 answers。"""
    return agent.predict({"message": text}, QUESTIONS)["answers"]


def evaluate(agent, samples=None):
    """跑 billing 样本，dept==billing 计正确。"""
    samples = BILLING_SAMPLES if samples is None else samples
    rows = []
    correct = 0
    for lang, text in samples:
        t0 = time.time()
        answers = predict_one(agent, text)
        ms = (time.time() - t0) * 1000
        dept = answers["dept"]["choice"]
        refund = answers["refund"]["noul"]
        ok = dept == "billing"
        correct += int(ok)
        p = max(answers["dept"]["probabilities"].values())
        log.info(
            "%-9s dept=%-10s p=%.2f refund=%s %.0fms %s",
            lang,
            dept,
            p,
            refund,
            ms,
            "OK" if ok else "miss",
        )
        rows.append({"lang": lang, "dept": dept, "refund": refund, "ok": ok, "ms": ms})
    total = len(samples)
    passed = correct >= PASS_THRESHOLD
    log.info("summary correct=%d/%d passed=%s", correct, total, passed)
    return {"correct": correct, "total": total, "rows": rows, "passed": passed}


def main():
    path = model_dir()
    weights = os.path.join(path, "model.safetensors")
    if not os.path.isfile(weights):
        log.error("no weights at %s", weights)
        sys.exit(2)
    agent = load_agent(path)
    result = evaluate(agent)
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
