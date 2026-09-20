"""兼容 TypeSafe Jev 的 HTTP server。agent 由外部注入，不 import laya。"""
import json
import logging
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

log = logging.getLogger("layalib.server")

_ALLOWED = {"noul", "choice", "score"}
_MODELS = {
    "models": [
        {"name": "jev-latest", "description": "Jev-compatible system one", "release_date": "2026-09-15"},
        {"name": "laya", "description": "Laya multilingual system one", "release_date": "2026-09-15"},
    ]
}


def make_server(agent, host="127.0.0.1", port=0):
    """绑定 host:port（port=0 由 OS 分配），返回 ThreadingHTTPServer。"""
    httpd = ThreadingHTTPServer((host, port), _Handler)
    httpd.agent = agent
    return httpd


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        t0 = time.monotonic()
        path = self.path.split("?", 1)[0]
        if path != "/v1/models":
            self._reply(404, {"detail": "Not Found"}, t0, path)
            return
        self._reply(200, _MODELS, t0, path)

    def do_POST(self):
        t0 = time.monotonic()
        path = self.path.split("?", 1)[0]
        if path != "/v1/systemone":
            self._reply(404, {"detail": "Not Found"}, t0, path)
            return
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._reply(422, _err(["body"], "Invalid JSON", "json_invalid"), t0, path)
            return
        err = _validate(payload)
        if err is not None:
            self._reply(422, err, t0, path)
            return
        questions = payload["questions"]
        for q in questions.values():
            if "instructions" not in q:
                q["instructions"] = ""
        try:
            result = self.server.agent.system_one(payload["state"], questions)
        except Exception:
            log.exception("agent.system_one failed")
            self._reply(500, {"detail": "Internal Server Error"}, t0, path)
            return
        if "model" not in result:
            result["model"] = "laya"
        if "usage" not in result:
            result["usage"] = {"input_tokens": 0, "output_tokens": 0}
        self._reply(200, result, t0, path)

    def _reply(self, code, obj, t0, path):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        log.info("%s %s %s %.1fms", self.command, path, code, (time.monotonic() - t0) * 1000)


def _err(loc, msg, err_type):
    return {"detail": [{"loc": loc, "msg": msg, "type": err_type}]}


def _validate(payload):
    if not isinstance(payload, dict):
        return _err(["body"], "Object required", "type_error")
    if "state" not in payload:
        return _err(["body", "state"], "Field required", "missing")
    if "questions" not in payload:
        return _err(["body", "questions"], "Field required", "missing")
    questions = payload["questions"]
    if not isinstance(questions, dict) or not questions:
        return _err(["body", "questions"], "Nonempty object required", "value_error")
    for qid, q in questions.items():
        if not isinstance(q, dict) or q.get("type") not in _ALLOWED:
            return _err(["body", "questions", qid, "type"], "Invalid type", "value_error")
    return None
