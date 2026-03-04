"""RAGAS-inspired response evaluation using direct Anthropic API calls.

Three metrics:
  faithfulness        — fraction of answer claims supported by retrieved contexts
  answer_relevancy    — does the answer address the question asked
  context_utilization — did the answer draw from the contexts vs parametric memory
"""

import asyncio
import json
import re
from typing import Any

import httpx

from .config import ANTHROPIC_API_KEY

_API_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-haiku-4-5-20251001"
_TIMEOUT = 45
_MAX_CONTEXT_CHARS = 2000  # per context passage, to avoid token overflow


def _headers() -> dict[str, str]:
    return {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


def _fmt_contexts(contexts: list[str]) -> str:
    truncated = [c[:_MAX_CONTEXT_CHARS] + ("...[truncated]" if len(c) > _MAX_CONTEXT_CHARS else "") for c in contexts]
    return "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(truncated))


async def _call_haiku(client: httpx.AsyncClient, system: str, user: str, max_tokens: int = 512) -> str:
    payload = {
        "model": _MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    resp = await client.post(_API_URL, headers=_headers(), json=payload)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def _extract_json(text: str) -> Any:
    """Extract the first JSON object or array from LLM output."""
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract JSON from: {text[:300]!r}")


# ---------------------------------------------------------------------------
# Metric: faithfulness
# ---------------------------------------------------------------------------

_CLAIM_EXTRACTION_SYSTEM = """\
You are a precise fact-extraction assistant. Extract every specific, verifiable
factual claim from the given answer. A claim is a statement asserting something
as true: a measurement, a named technology, a comparative assertion, a causal
relationship, a date, a company action, etc.

Output ONLY a JSON object in this exact format (no other text):
{"claims": ["claim 1", "claim 2", ...]}

Rules:
- Include only substantive, checkable claims — not vague statements like "this is important".
- If the answer contains no verifiable claims, return {"claims": []}.
"""

_CLAIM_VERIFICATION_SYSTEM = """\
You are a strict fact-checker. For each claim, determine whether the provided
context passages directly support it. "Supported" means the context explicitly
states or clearly implies the claim. Do NOT use outside knowledge — judge only
what the contexts contain.

Output ONLY a JSON object in this exact format (no other text):
{"verdicts": [{"claim": "...", "supported": true, "reason": "one sentence"}, ...]}
"""


async def _faithfulness(
    client: httpx.AsyncClient, question: str, contexts: list[str], answer: str
) -> dict[str, Any]:
    try:
        # Step A: extract claims
        raw = await _call_haiku(
            client,
            _CLAIM_EXTRACTION_SYSTEM,
            f"Answer: {answer}",
            max_tokens=512,
        )
        parsed = _extract_json(raw)
        claims: list[str] = parsed.get("claims", [])

        if not claims:
            return {
                "score": 1.0,
                "claims_total": 0,
                "claims_supported": 0,
                "verdicts": [],
                "reasoning": "No verifiable claims found in answer.",
                "error": None,
            }

        # Step B: batch-verify all claims; use 256 tokens per claim to avoid truncation
        claims_text = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(claims))
        batch_max_tokens = min(4096, max(1024, len(claims) * 256))
        raw = await _call_haiku(
            client,
            _CLAIM_VERIFICATION_SYSTEM,
            f"Contexts:\n{_fmt_contexts(contexts)}\n\nClaims to verify:\n{claims_text}",
            max_tokens=batch_max_tokens,
        )
        try:
            parsed = _extract_json(raw)
            verdicts: list[dict] = parsed.get("verdicts", [])
        except ValueError:
            # Batch response truncated — fall back to verifying each claim individually
            verdicts = []
            _SINGLE_SYSTEM = _CLAIM_VERIFICATION_SYSTEM.replace(
                "Output ONLY a JSON object in this exact format (no other text):\n"
                '{"verdicts": [{"claim": "...", "supported": true, "reason": "one sentence"}, ...]}',
                'Output ONLY a JSON object: {"claim": "...", "supported": true, "reason": "one sentence"}',
            )
            for claim in claims:
                try:
                    r = await _call_haiku(
                        client, _SINGLE_SYSTEM,
                        f"Contexts:\n{_fmt_contexts(contexts)}\n\nClaim: {claim}",
                        max_tokens=128,
                    )
                    v = _extract_json(r)
                    verdicts.append({"claim": claim, "supported": v.get("supported", False), "reason": v.get("reason", "")})
                except Exception:
                    verdicts.append({"claim": claim, "supported": False, "reason": "parse error"})

        supported = sum(1 for v in verdicts if v.get("supported", False))
        total = len(verdicts) or len(claims)
        score = round(supported / total, 3) if total else 1.0

        return {
            "score": score,
            "claims_total": total,
            "claims_supported": supported,
            "verdicts": verdicts,
            "error": None,
        }

    except httpx.HTTPStatusError as exc:
        return {"score": None, "error": f"Anthropic API {exc.response.status_code}: {exc.response.text[:200]}"}
    except httpx.TimeoutException:
        return {"score": None, "error": "Anthropic API timeout"}
    except (ValueError, KeyError, TypeError) as exc:
        return {"score": None, "error": f"Parse error: {exc}"}


# ---------------------------------------------------------------------------
# Metric: answer relevancy
# ---------------------------------------------------------------------------

_RELEVANCY_SYSTEM = """\
You are an expert evaluator assessing whether an answer addresses the question asked.

Score relevancy 0.0–1.0:
  1.0 — fully addresses the question, no off-topic content
  0.7 — mostly on-topic with minor gaps or tangents
  0.4 — partially addresses the question; key aspects missing
  0.1 — barely addresses the question; mostly off-topic
  0.0 — completely ignores the question

Output ONLY a JSON object (no other text):
{"score": <float 0.0-1.0>, "reasoning": "<one or two sentences>"}
"""


async def _answer_relevancy(
    client: httpx.AsyncClient, question: str, contexts: list[str], answer: str
) -> dict[str, Any]:
    try:
        raw = await _call_haiku(
            client,
            _RELEVANCY_SYSTEM,
            f"Question: {question}\n\nAnswer: {answer}",
        )
        parsed = _extract_json(raw)
        score = max(0.0, min(1.0, float(parsed["score"])))
        return {"score": round(score, 3), "reasoning": parsed.get("reasoning", ""), "error": None}

    except httpx.HTTPStatusError as exc:
        return {"score": None, "error": f"Anthropic API {exc.response.status_code}: {exc.response.text[:200]}"}
    except httpx.TimeoutException:
        return {"score": None, "error": "Anthropic API timeout"}
    except (ValueError, KeyError, TypeError) as exc:
        return {"score": None, "error": f"Parse error: {exc}"}


# ---------------------------------------------------------------------------
# Metric: context utilization
# ---------------------------------------------------------------------------

_CTX_UTIL_SYSTEM = """\
You are evaluating how much an answer draws from retrieved context passages
versus relying on general parametric knowledge.

Score context utilization 0.0–1.0:
  1.0 — answer is clearly grounded in the contexts; key points trace to passages
  0.7 — answer uses contexts substantially but adds some general knowledge
  0.4 — answer uses contexts for minor details; primarily driven by general knowledge
  0.1 — answer barely references the contexts
  0.0 — answer is entirely from general knowledge; contexts are ignored

Output ONLY a JSON object (no other text):
{"score": <float 0.0-1.0>, "reasoning": "<one or two sentences>"}
"""


async def _context_utilization(
    client: httpx.AsyncClient, question: str, contexts: list[str], answer: str
) -> dict[str, Any]:
    try:
        raw = await _call_haiku(
            client,
            _CTX_UTIL_SYSTEM,
            f"Contexts:\n{_fmt_contexts(contexts)}\n\nAnswer: {answer}",
        )
        parsed = _extract_json(raw)
        score = max(0.0, min(1.0, float(parsed["score"])))
        return {"score": round(score, 3), "reasoning": parsed.get("reasoning", ""), "error": None}

    except httpx.HTTPStatusError as exc:
        return {"score": None, "error": f"Anthropic API {exc.response.status_code}: {exc.response.text[:200]}"}
    except httpx.TimeoutException:
        return {"score": None, "error": "Anthropic API timeout"}
    except (ValueError, KeyError, TypeError) as exc:
        return {"score": None, "error": f"Parse error: {exc}"}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def evaluate_response(question: str, contexts: list[str], answer: str) -> str:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        faith, relevancy, ctx_util = await asyncio.gather(
            _faithfulness(client, question, contexts, answer),
            _answer_relevancy(client, question, contexts, answer),
            _context_utilization(client, question, contexts, answer),
        )

    scores = [m["score"] for m in (faith, relevancy, ctx_util) if m.get("score") is not None]
    composite = round(sum(scores) / len(scores), 3) if scores else None

    result = {
        "question": question,
        "metrics": {
            "faithfulness": faith,
            "answer_relevancy": relevancy,
            "context_utilization": ctx_util,
        },
        "composite_score": composite,
        "eval_model": _MODEL,
    }
    return json.dumps(result, ensure_ascii=False, indent=2)
