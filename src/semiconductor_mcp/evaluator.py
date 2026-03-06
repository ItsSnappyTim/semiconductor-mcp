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
            f"<answer>{answer}</answer>",
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
            f"<contexts>\n{_fmt_contexts(contexts)}\n</contexts>\n\n<claims>\n{claims_text}\n</claims>",
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
                        f"<contexts>\n{_fmt_contexts(contexts)}\n</contexts>\n\n<claim>{claim}</claim>",
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
        return {"score": None, "error": f"Anthropic API error (HTTP {exc.response.status_code})"}
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
            f"<question>{question}</question>\n\n<answer>{answer}</answer>",
        )
        parsed = _extract_json(raw)
        score = max(0.0, min(1.0, float(parsed["score"])))
        return {"score": round(score, 3), "reasoning": parsed.get("reasoning", ""), "error": None}

    except httpx.HTTPStatusError as exc:
        return {"score": None, "error": f"Anthropic API error (HTTP {exc.response.status_code})"}
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
            f"<contexts>\n{_fmt_contexts(contexts)}\n</contexts>\n\n<answer>{answer}</answer>",
        )
        parsed = _extract_json(raw)
        score = max(0.0, min(1.0, float(parsed["score"])))
        return {"score": round(score, 3), "reasoning": parsed.get("reasoning", ""), "error": None}

    except httpx.HTTPStatusError as exc:
        return {"score": None, "error": f"Anthropic API error (HTTP {exc.response.status_code})"}
    except httpx.TimeoutException:
        return {"score": None, "error": "Anthropic API timeout"}
    except (ValueError, KeyError, TypeError) as exc:
        return {"score": None, "error": f"Parse error: {exc}"}


# ---------------------------------------------------------------------------
# Draft answer + query refinement (used by research_and_verify)
# ---------------------------------------------------------------------------

_DRAFT_SYSTEM = """\
You are a semiconductor industry expert. Answer the question based STRICTLY on
the provided context passages — do not use outside knowledge. If the contexts
don't support a claim, do not make it. Be specific, cite concrete details from
the contexts, and keep the answer focused and factual.
"""

_REFINE_QUERY_SYSTEM = """\
You are a search query optimizer for semiconductor industry research.
Given an original question and the reason the previous search didn't score well,
generate a single improved search query likely to find more relevant academic
papers or news articles. Output ONLY the improved query string, nothing else.
"""


async def draft_answer(client: httpx.AsyncClient, question: str, contexts: list[str]) -> str:
    """Generate a context-grounded answer using Haiku."""
    raw = await _call_haiku(
        client,
        _DRAFT_SYSTEM,
        f"<question>{question}</question>\n\n<contexts>\n{_fmt_contexts(contexts)}\n</contexts>\n\nAnswer:",
        max_tokens=1024,
    )
    return raw.strip()


async def refine_query(
    client: httpx.AsyncClient, question: str, prev_query: str, issue: str
) -> str:
    """Generate an improved search query based on what the previous one missed."""
    raw = await _call_haiku(
        client,
        _REFINE_QUERY_SYSTEM,
        f"<question>{question}</question>\n<prev_query>{prev_query}</prev_query>\n<issue>{issue}</issue>\n\nImproved query:",
        max_tokens=64,
    )
    words = raw.strip().strip("\"'").split()
    return " ".join(words[:5])


_KEYWORDS_SYSTEM = """\
Convert a natural language question into a concise academic search query (3-6 key terms).
Strip question words (does, is, are, what, how, why), keep technical nouns and verbs.
Output ONLY the search query string, nothing else.
"""

_ENTITY_EXTRACTION_SYSTEM = """\
Extract company or organization names explicitly mentioned in this question.
Output ONLY a JSON array of strings (max 3), e.g. ["ASML", "TSMC", "Huawei"].
If no companies or organizations are named, return [].
"""


async def extract_entities(client: httpx.AsyncClient, question: str) -> list[str]:
    """Extract named company/organization entities from a question using Haiku."""
    try:
        raw = await _call_haiku(
            client,
            _ENTITY_EXTRACTION_SYSTEM,
            f"<question>{question}</question>",
            max_tokens=64,
        )
        result = _extract_json(raw)
        if isinstance(result, list):
            return [str(e) for e in result[:3]]
    except Exception:
        pass
    return []


async def question_to_query(client: httpx.AsyncClient, question: str) -> str:
    """Convert a natural language question into search-friendly keywords (max 5 words)."""
    raw = await _call_haiku(
        client,
        _KEYWORDS_SYSTEM,
        f"<question>{question}</question>\n\nSearch query (3-5 key terms only):",
        max_tokens=32,
    )
    # Hard cap at 5 words to keep arXiv AND query tractable
    words = raw.strip().strip("\"'").split()
    return " ".join(words[:5])


async def _eval_with_client(
    client: httpx.AsyncClient, question: str, contexts: list[str], answer: str
) -> dict[str, Any]:
    """Run all three metrics and return the raw dict (no JSON serialisation)."""
    faith, relevancy, ctx_util = await asyncio.gather(
        _faithfulness(client, question, contexts, answer),
        _answer_relevancy(client, question, contexts, answer),
        _context_utilization(client, question, contexts, answer),
    )
    scores = [m["score"] for m in (faith, relevancy, ctx_util) if m.get("score") is not None]
    composite = round(sum(scores) / len(scores), 3) if scores else None
    return {
        "metrics": {
            "faithfulness": faith,
            "answer_relevancy": relevancy,
            "context_utilization": ctx_util,
        },
        "composite_score": composite,
        "eval_model": _MODEL,
    }


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
