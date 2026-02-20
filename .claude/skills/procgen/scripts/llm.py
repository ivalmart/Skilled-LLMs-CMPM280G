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


def _escape_newlines(text):
    out = []
    in_str = False
    esc = False
    for c in text:
        if esc:
            out.append(c)
            esc = False
            continue
        if c == "\\":
            esc = True
            out.append(c)
            continue
        if c == '"':
            in_str = not in_str
            out.append(c)
            continue
        if in_str and c == "\n":
            out.append("\\n")
            continue
        if in_str and c == "\t":
            out.append("\\t")
            continue
        out.append(c)
    return "".join(out)


def _parse(text):
    if not text:
        raise json.JSONDecodeError("empty response from LLM", "", 0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # fix unescaped newlines inside JSON strings (common with code fields)
    try:
        return json.loads(_escape_newlines(text))
    except json.JSONDecodeError:
        pass
    # strip markdown fences
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            try:
                return json.loads(_escape_newlines(m.group(1)))
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
    best_end = -1
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
                best_end = i + 1
                chunk = text[start:best_end]
                try:
                    return json.loads(chunk)
                except json.JSONDecodeError:
                    pass
                try:
                    return json.loads(_escape_newlines(chunk))
                except json.JSONDecodeError:
                    break
    # if we found a balanced brace pair, try fixing truncated strings
    if best_end > start:
        chunk = text[start:best_end]
        try:
            return json.loads(_escape_newlines(chunk))
        except json.JSONDecodeError:
            pass
    # last resort: try first { to last } and fix truncation
    end = text.rfind("}")
    if end > start:
        fragment = text[start:end + 1]
        if fragment.count('"') % 2 == 1:
            fragment += '"'
        try:
            return json.loads(fragment)
        except json.JSONDecodeError:
            pass
        try:
            return json.loads(_escape_newlines(fragment))
        except json.JSONDecodeError:
            pass
    # truncated response with no closing brace — try to close it
    if start >= 0:
        fragment = text[start:]
        # close any open string
        if fragment.count('"') % 2 == 1:
            fragment += '"'
        # close open arrays/objects
        opens = fragment.count("[") - fragment.count("]")
        fragment += "]" * max(opens, 0)
        opens = fragment.count("{") - fragment.count("}")
        fragment += "}" * max(opens, 0)
        try:
            return json.loads(fragment)
        except json.JSONDecodeError:
            pass
    print(f"  [llm] parse failed (first 300 chars): {text[:300]}", file=sys.stderr, flush=True)
    raise json.JSONDecodeError("could not parse JSON from response", text, 0)



def call(prompt, cls):
    schema = json.dumps(cls.model_json_schema(), indent=2)
    resp = _get().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": f"{prompt}\n\nRespond with ONLY a single JSON object (no other text) matching this schema:\n{schema}"}],
        temperature=0,
        max_tokens=4096,
    )
    text = resp.choices[0].message.content
    data = _parse(text)
    return cls.model_validate(data)
