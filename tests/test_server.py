"""TypeSafe SDK 打本地 HTTP server。"""
import json
import threading
import urllib.error
import urllib.request

import pytest
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient, RetryPolicy

from layalib.server import make_server

STATE = {"document": "I was charged twice. Please fix this ASAP."}
QUESTIONS = {
    "billing": Noul(instructions="Is this about billing?"),
    "tone": Choice(
        instructions="What is the tone?",
        criteria={"calm": None, "angry": None},
    ),
    "urgency": Score(
        instructions="How urgent is this message?",
        criteria=["Can wait", "Needs attention this week", "Needs attention today"],
    ),
}


class FakeAgent:
    def __init__(self):
        self.state = None
        self.questions = None

    def system_one(self, state, questions):
        self.state = state
        self.questions = questions
        answers = {}
        for qid, q in questions.items():
            t = q["type"]
            if t == "noul":
                answers[qid] = {"type": "noul", "noul": 0.91}
            elif t == "choice":
                keys = list(q["criteria"])
                chosen = keys[0]
                answers[qid] = {
                    "type": "choice",
                    "choice": chosen,
                    "confidence": 0.8,
                    "probabilities": {k: (0.8 if k == chosen else 0.2) for k in keys},
                }
            else:
                crit = q["criteria"]
                answers[qid] = {
                    "type": "score",
                    "score": 1.7,
                    "confidence": 0.7,
                    "legend": {str(i): c for i, c in enumerate(crit)},
                    "probabilities": {str(i): (0.8 if i == 2 else 0.1) for i in range(len(crit))},
                }
        return {"answers": answers}


@pytest.fixture
def running():
    agent = FakeAgent()
    httpd = make_server(agent, host="127.0.0.1", port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd, agent
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def _client(httpd):
    port = httpd.server_address[1]
    return TypeSafeClient(
        api_key="test",
        base_url=f"http://127.0.0.1:{port}",
        retry=RetryPolicy(max_retries=0),
    )


def test_sdk_system_one_noul_choice_score(running):
    httpd, agent = running
    with _client(httpd) as client:
        response = client.system_one(state=STATE, questions=QUESTIONS)
    assert 0 <= response.nouls["billing"].noul <= 1
    assert response.choices["tone"].choice in {"calm", "angry"}
    assert isinstance(response.scores["urgency"].score, (int, float))
    assert agent.state == STATE
    assert agent.questions["billing"]["type"] == "noul"
    assert agent.questions["tone"]["type"] == "choice"
    assert agent.questions["urgency"]["type"] == "score"


def test_sdk_models_list(running):
    httpd, _agent = running
    with _client(httpd) as client:
        result = client.models.list()
    assert len(result.models) >= 1
    model = result.models[0]
    assert model.name
    assert model.description
    assert model.release_date


def test_system_one_missing_questions_is_422(running):
    httpd, _agent = running
    port = httpd.server_address[1]
    body = json.dumps({"state": STATE, "model": "laya"}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/systemone",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req)
    assert exc.value.code == 422
