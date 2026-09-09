"""
Local-AI layer (optional): explanation + interactive chat, via Ollama.

Strict rule: this module NEVER calculates a financial value. It only turns
numbers that src/analytics, src/ml, and src/valuation already computed into
plain-English text, or answers follow-up questions about them. If Ollama
isn't running, every caller gets a clear ConnectionError rather than a crash
- this feature is optional by design so the rest of the project stays free
and doesn't require it.

Performance notes (tuned after real-world testing showed slow, vague
replies):
  - `keep_alive` is set on every call so Ollama keeps the model resident in
    memory between requests. Ollama's default is to unload a model after 5
    minutes idle, and reloading a 3-8B model from disk costs 10-30+ seconds
    - that reload was very likely the "replying very late" symptom, not
      generation speed itself.
  - `options.num_predict` caps response length. An uncapped model will
    happily ramble for 500+ tokens, which is slow AND reads as vague
    (padding with generic hedging to fill space). Capping forces concise,
    concrete answers.
  - `options.temperature` is lowered from Ollama's default (0.8) to 0.3.
    Lower temperature = more deterministic, fact-grounded phrasing instead
    of generic-sounding hedges - directly targets the "vague" complaint.
  - The chat endpoint streams tokens back to the frontend as they're
    generated (see `chat_stream` + backend/routers/ai_analyst.py), so the
    user sees the answer forming immediately instead of staring at
    "Thinking..." for the full generation time.

Model choice: configurable via the OLLAMA_MODEL env var.
  - "llama3.2:3b"          (default) - fast, ~2GB, good for quick explanations
                             on modest hardware (CPU-only laptops included).
  - "qwen2.5:7b-instruct"  - noticeably better financial reasoning and
                             instruction-following for the chat tab; needs
                             ~5-6GB RAM/VRAM. Recommended if your machine
                             can handle it: `ollama pull qwen2.5:7b-instruct`
                             then `export OLLAMA_MODEL=qwen2.5:7b-instruct`.
  - "phi3.5"               - middle ground on size/quality.
Any Ollama-compatible model works; these three are just a sane menu.
"""
import json
import os
import urllib.request
import urllib.error

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
GENERATE_URL = f"{OLLAMA_HOST}/api/generate"
CHAT_URL = f"{OLLAMA_HOST}/api/chat"

# Keep the model loaded in memory for 30 minutes of inactivity instead of
# Ollama's 5-minute default - avoids repeated cold-start reload latency
# during a working session. Tune down if you're tight on RAM/VRAM and
# running other things alongside it.
KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "30m")

# Response length/focus tuning - see module docstring for why.
GEN_OPTIONS = {
    "temperature": 0.3,
    "top_p": 0.9,
    "num_predict": 220,   # roughly 3-5 sentences; hard stop against rambling
}
CHAT_OPTIONS = {
    "temperature": 0.3,
    "top_p": 0.9,
    "num_predict": 320,   # a little more room for follow-up chat answers
}

SYSTEM_STYLE_RULES = (
    "Style rules: be concrete and specific - always reference the actual "
    "numbers given to you by name (e.g. 'EV/EBITDA of 11.1x', not 'a high "
    "multiple'). Do not use generic filler like 'this is an estimate' more "
    "than once. Do not hedge repeatedly. Get to the point in the first "
    "sentence, then support it. Never invent a number that wasn't given to you."
)


class OllamaUnavailable(ConnectionError):
    pass


def _post(url: str, payload: dict, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError) as e:
        raise OllamaUnavailable(
            f"Couldn't reach Ollama at {OLLAMA_HOST} — is `ollama serve` running "
            f"and have you run `ollama pull {MODEL}`? ({e})"
        ) from e
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        raise OllamaUnavailable(f"Ollama returned an error ({e.code}): {body}") from e


def _stream_lines(url: str, payload: dict, timeout: int):
    """Yield parsed JSON objects from an Ollama streaming (NDJSON) response."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except (urllib.error.URLError, TimeoutError) as e:
        raise OllamaUnavailable(
            f"Couldn't reach Ollama at {OLLAMA_HOST} — is `ollama serve` running "
            f"and have you run `ollama pull {MODEL}`? ({e})"
        ) from e
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        raise OllamaUnavailable(f"Ollama returned an error ({e.code}): {body}") from e

    try:
        for raw_line in resp:
            line = raw_line.decode().strip()
            if line:
                yield json.loads(line)
    finally:
        resp.close()


def explain_comparables(target_name: str, peers: list[dict]) -> str:
    peer_lines = "\n".join(
        f"- {p['name']}: {p['similarity_score']*100:.0f}% similarity" for p in peers
    )
    prompt = (
        f"You are a finance analyst explaining a comp set in plain English, "
        f"in 3-4 sentences, no bullet points. Target company: {target_name}. "
        f"Peers found by a cosine-similarity model:\n{peer_lines}\n"
        f"Explain why these companies are reasonable comparables, in plain terms. "
        f"Do not invent any numbers beyond what's given. {SYSTEM_STYLE_RULES}"
    )
    body = _post(GENERATE_URL, {
        "model": MODEL, "prompt": prompt, "stream": False,
        "keep_alive": KEEP_ALIVE, "options": GEN_OPTIONS,
    })
    return body.get("response", "").strip()


def explain_valuation(target_name: str, valuation: dict) -> str:
    v = valuation
    prompt = (
        f"You are a finance analyst explaining a valuation result in plain English, "
        f"in 3-4 sentences, no bullet points. Target company: {target_name}. "
        f"Blended enterprise value range: Low ${v['low_ev_musd']}M, "
        f"Base ${v['base_ev_musd']}M, High ${v['high_ev_musd']}M. "
        f"Methods used: {[m['method'] for m in v['methods']]}. "
        f"Explain what this range means and why it's an estimate, not a guarantee. "
        f"Do not invent any numbers beyond what's given. {SYSTEM_STYLE_RULES}"
    )
    body = _post(GENERATE_URL, {
        "model": MODEL, "prompt": prompt, "stream": False,
        "keep_alive": KEEP_ALIVE, "options": GEN_OPTIONS,
    })
    return body.get("response", "").strip()


def build_context_block(company_name: str, metrics: dict, comps: list[dict], valuation: dict) -> str:
    """A single, dense, factual context string injected as a system message
    so the chat model only ever reasons over numbers we actually computed."""
    comps_lines = "\n".join(
        f"  - {c['name']}: {c['similarity_score']*100:.0f}% similarity, "
        f"revenue ${c.get('revenue_musd', 'n/a')}M"
        for c in comps
    )
    methods_lines = "\n".join(
        f"  - {m['method']}: Low ${m['low_ev_musd']}M / Base ${m['base_ev_musd']}M / High ${m['high_ev_musd']}M"
        for m in valuation.get("methods", [])
    )
    return (
        f"You are an M&A analyst assistant embedded in a comps/valuation tool. "
        f"Answer ONLY using the facts below — never invent a number that isn't here. "
        f"If asked something the data doesn't cover, say so plainly. Keep answers concise "
        f"(2-5 sentences unless the user asks for more detail). {SYSTEM_STYLE_RULES}\n\n"
        f"TARGET COMPANY: {company_name}\n"
        f"KEY METRICS: revenue ${metrics.get('revenue_musd')}M, EBITDA ${metrics.get('ebitda_musd')}M, "
        f"EBITDA margin {metrics.get('ebitda_margin_pct')}%, EV ${metrics.get('enterprise_value_musd')}M, "
        f"EV/Revenue {metrics.get('ev_revenue')}x, EV/EBITDA {metrics.get('ev_ebitda')}x, "
        f"P/E {metrics.get('pe_ratio')}x, Debt/EBITDA {metrics.get('debt_to_ebitda')}x\n\n"
        f"TOP COMPARABLE COMPANIES (cosine similarity):\n{comps_lines}\n\n"
        f"VALUATION (blended enterprise value):\n"
        f"  Low ${valuation.get('low_ev_musd')}M / Base ${valuation.get('base_ev_musd')}M / "
        f"High ${valuation.get('high_ev_musd')}M\n{methods_lines}\n"
        f"  Disclaimer: {valuation.get('disclaimer')}"
    )


def chat(system_context: str, messages: list[dict]) -> str:
    """Non-streaming chat call (kept for simplicity where streaming isn't needed)."""
    payload_messages = [{"role": "system", "content": system_context}] + messages
    body = _post(
        CHAT_URL,
        {
            "model": MODEL, "messages": payload_messages, "stream": False,
            "keep_alive": KEEP_ALIVE, "options": CHAT_OPTIONS,
        },
        timeout=90,
    )
    return body.get("message", {}).get("content", "").strip()


def chat_stream(system_context: str, messages: list[dict]):
    """
    Streaming chat call - yields response text chunks as Ollama generates
    them, so the frontend can render tokens live instead of waiting for the
    full answer. This is what actually fixes the "replying very late" feel:
    the model may take the same total time, but the user sees progress
    within a second or two instead of a blank "Thinking..." the whole time.
    """
    payload_messages = [{"role": "system", "content": system_context}] + messages
    for obj in _stream_lines(
        CHAT_URL,
        {
            "model": MODEL, "messages": payload_messages, "stream": True,
            "keep_alive": KEEP_ALIVE, "options": CHAT_OPTIONS,
        },
        timeout=90,
    ):
        chunk = obj.get("message", {}).get("content", "")
        if chunk:
            yield chunk
        if obj.get("done"):
            break
