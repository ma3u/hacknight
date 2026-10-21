"""Local server for the Vinland pub quiz frontend: uv run python frontend/server.py

Serves frontend/index.html and puts each question to the agents in AGENTS:
- sandbox: `haystack-enterprise run <pipeline>` with the agent's settings (uses your CLI login, ~3-8 s)
- live:    DEEPSET_API_KEY set and the agent has a `service` -> its deployed service endpoint
The key stays in this process; the browser never sees it. Standard library only.
"""

import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from check import format_question, last_reply, tokens_used  # noqa: E402

PORT = int(os.environ.get("PORT", "8765"))
WORKSPACE = os.environ.get("DEEPSET_WORKSPACE", "vinland")
ENDPOINT = f"https://api.cloud.deepset.ai/api/v1/workspaces/{WORKSPACE}/deployments/v1/chat/completions"
API_KEY = os.environ.get("DEEPSET_API_KEY", "")
CLI = os.environ.get("HAYSTACK_ENTERPRISE_CLI", str(Path.home() / ".local/bin/haystack-enterprise"))

SHORT_PROMPT = "Reply with only the correct option letter."
REASONING = {"reasoning_effort": "low", "max_completion_tokens": 1000}
ONE_LETTER = {"max_completion_tokens": 1, "temperature": 0, "logit_bias": {"32": 100, "33": 100, "34": 100, "35": 100}}
# Deployed services and the model each one serves (see agent.py / agent_luna.py).
SERVICES = {
    "gpt-5.4-mini": ("quiz", f"{WORKSPACE}/6f4d2505-13a4-4b44-b92f-b83485e21ad7"),
    "gpt-5.6-luna": ("quiz-luna", f"{WORKSPACE}/1b152c11-4168-4326-81b9-b8a962f60836"),
}


def variant(model: str, kwargs: dict, note: str, prompt: str = SHORT_PROMPT) -> dict:
    """One AI player: the deployed pipeline (evals/pipeline_variant.py) with this model and settings."""
    service = SERVICES.get(model)
    return {
        "label": model, "model": model,
        "note": f"Service {service[0]} · {note}" if service else note,
        "target": "evals/pipeline_variant.py",
        "env": {"QZ_MODEL": model, "QZ_PROMPT": prompt, "QZ_KWARGS": json.dumps(kwargs)},
        "service": service[1] if service else None,
    }


AGENTS = {
    "gpt-5.6-luna": variant("gpt-5.6-luna", REASONING, "reasoning low"),
    "gpt-5.4": variant("gpt-5.4", REASONING, "reasoning low"),
    "gpt-5.4-mini": variant("gpt-5.4-mini", REASONING, "reasoning low"),
    "gpt-5.4-nano": variant("gpt-5.4-nano", REASONING, "reasoning low"),
    "gpt-5.1": variant("gpt-5.1", REASONING, "reasoning low"),
    "gpt-5-mini": variant("gpt-5-mini", REASONING, "reasoning low"),
    "gpt-4.1": variant("gpt-4.1", ONE_LETTER, "1 Token, logit_bias A-D"),
    "gpt-4o-mini": variant("gpt-4o-mini", ONE_LETTER, "1 Token, logit_bias A-D"),
    "luna-fork": variant("gpt-5.6-luna", {}, "alter Fork: ohne Prompt (kaputt)", prompt=""),
}


def load_questions():
    questions = []
    for name in ("questions.json", "questions_hard.json", "trivia/questions_trivia.json"):
        path = ROOT / "evals" / name
        if path.exists():
            for q, options, answer, *_ in json.loads(path.read_text()):
                questions.append({"question": q, "options": options, "answer": answer})
    return questions


def ask_live(service: str, text: str) -> dict:
    body = json.dumps({"model": service, "messages": [{"role": "user", "content": text}], "stream": False})
    request = urllib.request.Request(ENDPOINT, data=body.encode(), method="POST", headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read())
    reply = data["choices"][0]["message"]["content"] or ""
    return {"reply": reply, "tokens": (data.get("usage") or {}).get("total_tokens")}


def ask_sandbox(agent: dict, text: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "result.json"
        run = subprocess.run(
            [CLI, "run", str(ROOT / agent["target"]), "--io-config", str(ROOT / "agent.io.yaml"),
             "--python", str(ROOT / ".venv/bin/python"), "--query", text, "--output", str(out)],
            capture_output=True, text=True, cwd=ROOT, timeout=90, env={**os.environ, **agent["env"]})
        if run.returncode != 0 or not out.exists():
            raise RuntimeError((run.stdout + run.stderr)[-400:] or "run failed")
        result = json.loads(out.read_text())
    return {"reply": last_reply(result), "tokens": tokens_used(result)}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def log_message(self, fmt, *args):
        if "/api/" in str(args[0] if args else ""):
            super().log_message(fmt, *args)

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/questions":
            questions = load_questions()
            random.shuffle(questions)
            agents = {key: {k: a[k] for k in ("label", "model", "note")} | {"live": bool(API_KEY and a.get("service"))}
                      for key, a in AGENTS.items()}
            return self.send_json({"questions": questions, "agents": agents})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/ask":
            return self.send_json({"error": "not found"}, 404)
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or "{}")
        agent = AGENTS.get(payload.get("agent", "gpt54"))
        if agent is None:
            return self.send_json({"error": "unknown agent"}, 400)
        text = format_question(payload["question"], payload["options"])
        live = bool(API_KEY and agent.get("service"))
        start = time.monotonic()
        try:
            answer = ask_live(agent["service"], text) if live else ask_sandbox(agent, text)
        except Exception as error:  # report any failure to the UI instead of hanging it
            return self.send_json({"error": str(error)[-400:], "seconds": time.monotonic() - start}, 502)
        reply = answer["reply"].strip()
        return self.send_json({
            "reply": reply,
            "letter": reply if re.fullmatch(r"[ABCD]", reply) else None,
            "tokens": answer["tokens"],
            "seconds": round(time.monotonic() - start, 2),
            "mode": "live" if live else "sandbox",
        })


if __name__ == "__main__":
    print(f"⚔️  Vinland pub quiz on http://localhost:{PORT}  ({'live services where deployed' if API_KEY else 'sandbox'} mode)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
