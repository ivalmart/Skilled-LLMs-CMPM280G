import os
import re
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[4] / ".env")

from openai import OpenAI

_client = None
MODEL = os.environ.get("SMALL_MODEL", "anthropic/claude-3.5-haiku")


def _get():
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
            timeout=120,
        )
    return _client


def _parse(text):
    if not text:
        raise json.JSONDecodeError("empty response from LLM", "", 0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # strip markdown fences
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # find outermost JSON object by brace counting
    start = text.find("{")
    if start == -1:
        print(f"  [llm] no JSON in response (first 200 chars): {text[:200]}", file=sys.stderr, flush=True)
        raise json.JSONDecodeError("no JSON found in response", text, 0)
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"' and not escape:
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    break
    # last resort: first { to last }
    end = text.rfind("}")
    if end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    print(f"  [llm] parse failed (first 300 chars): {text[:300]}", file=sys.stderr, flush=True)
    raise json.JSONDecodeError("could not parse JSON from response", text, 0)


def call(prompt, cls):
    schema = json.dumps(cls.model_json_schema(), indent=2)
    resp = _get().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": f"{prompt}\n\nRespond with a single JSON object matching this schema:\n{schema}"}],
        response_format={"type": "json_object"},
    )
    text = resp.choices[0].message.content
    data = _parse(text)
    return cls.model_validate(data)
