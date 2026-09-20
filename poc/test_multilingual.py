"""laya-multilingual POC 单测：不加载真实权重。"""
import logging
import os

import pytest

from multilingual import (
    BILLING_SAMPLES,
    PASS_THRESHOLD,
    QUESTIONS,
    evaluate,
    main,
    model_dir,
    predict_one,
)

LANGS = {
    "english",
    "german",
    "french",
    "spanish",
    "hindi",
    "japanese",
    "chinese",
    "russian",
}


def _answers(dept, refund=0.7, p=0.9):
    probs = {k: 0.01 for k in QUESTIONS["dept"]["criteria"]}
    probs[dept] = p
    return {
        "answers": {
            "dept": {"choice": dept, "probabilities": probs},
            "refund": {"noul": refund},
        }
    }


def _agent_for_langs(ok_langs):
    class Agent:
        def predict(self, state, questions):
            text = state["message"]
            lang = next(l for l, t in BILLING_SAMPLES if t == text)
            dept = "billing" if lang in ok_langs else "technical"
            return _answers(dept)

    return Agent()


def test_questions_has_dept_choice_and_refund_noul():
    assert "dept" in QUESTIONS
    assert QUESTIONS["dept"]["type"] == "choice"
    keys = QUESTIONS["dept"]["criteria"]
    assert set(keys) == {"billing", "technical", "sales", "hr"}
    assert QUESTIONS["refund"]["type"] == "noul"


def test_billing_samples_eight_langs_nonempty():
    assert len(BILLING_SAMPLES) == 8
    langs = [lang for lang, text in BILLING_SAMPLES]
    assert set(langs) == LANGS
    assert len(set(langs)) == 8
    for lang, text in BILLING_SAMPLES:
        assert isinstance(text, str) and text.strip()


def test_pass_threshold_is_six():
    assert PASS_THRESHOLD == 6


def test_model_dir_respects_laya_ml_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("LAYA_ML_DIR", str(tmp_path / "custom"))
    assert model_dir() == str(tmp_path / "custom")
    monkeypatch.delenv("LAYA_ML_DIR")
    assert model_dir() == os.path.join("models", "laya-multilingual")


def test_predict_one_forwards_state_questions_and_returns_answers():
    captured = {}

    class Agent:
        def predict(self, state, questions):
            captured["state"] = state
            captured["questions"] = questions
            return _answers("billing", refund=0.82)

    answers = predict_one(Agent(), "please refund invoice 4411")
    assert captured["state"] == {"message": "please refund invoice 4411"}
    assert captured["questions"] == QUESTIONS
    assert answers["dept"]["choice"] == "billing"
    assert answers["refund"]["noul"] == 0.82


def test_evaluate_six_of_eight_passes(caplog):
    caplog.set_level(logging.INFO, logger="laya.poc.multilingual")
    ok_langs = {lang for lang, _ in BILLING_SAMPLES[:6]}
    result = evaluate(_agent_for_langs(ok_langs))
    assert result["correct"] == 6
    assert result["total"] == 8
    assert result["passed"] is True
    assert len(result["rows"]) == 8
    for row in result["rows"]:
        assert {"lang", "dept", "refund", "ok", "ms"} <= set(row)
        assert isinstance(row["ms"], (int, float))
    for lang, _ in BILLING_SAMPLES:
        assert lang in caplog.text


def test_evaluate_five_of_eight_fails(caplog):
    caplog.set_level(logging.INFO, logger="laya.poc.multilingual")
    ok_langs = {lang for lang, _ in BILLING_SAMPLES[:5]}
    result = evaluate(_agent_for_langs(ok_langs))
    assert result["correct"] == 5
    assert result["total"] == 8
    assert result["passed"] is False
    assert sum(1 for r in result["rows"] if r["ok"]) == 5
    assert "5" in caplog.text and "8" in caplog.text


def test_main_no_weights_exits_2(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.ERROR, logger="laya.poc.multilingual")
    monkeypatch.setenv("LAYA_ML_DIR", str(tmp_path))
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
