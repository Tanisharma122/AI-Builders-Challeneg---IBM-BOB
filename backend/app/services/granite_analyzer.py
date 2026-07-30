"""
IBM Granite 3.0 viral segment analyzer.

Responsibilities
----------------
1. Build a structured prompt from a FullTranscript.
2. Call ibm-granite/granite-3.0-8b-instruct via HuggingFace InferenceClient.
3. Strip markdown fences, validate JSON against the strict schema, parse to
   GraniteAnalysis Pydantic model.
4. Persist result to {OUTPUT_DIR}/{job_id}/granite_analysis.json.

Retry logic (S2-T04)
--------------------
_call_granite_api is wrapped with tenacity exponential-backoff retry:
- 3 attempts max
- Wait 4–30 s between attempts (exponential)
- Retries on HfHubHTTPError (rate-limit 429) and transient network errors.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import jsonschema
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from app.config import settings
from app.models.granite_output import GraniteAnalysis, ViralClip
from app.models.transcript import FullTranscript

logger = logging.getLogger(__name__)

# ── Load JSON Schema once at module level ─────────────────────────────────────

_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "granite_output_schema.json"
_GRANITE_SCHEMA: dict = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))

# ── Custom exception ──────────────────────────────────────────────────────────


class GraniteOutputValidationError(Exception):
    """Raised when Granite's raw response fails JSON Schema validation."""


# ── Token budget ──────────────────────────────────────────────────────────────

_MAX_TRANSCRIPT_CHARS = 18_000  # ~6 000 tokens; keeps us inside 8 192 ctx window


# ── Prompt builder ────────────────────────────────────────────────────────────


def _build_prompt(transcript: FullTranscript) -> str:
    """
    Construct the system + user prompt for Granite.

    The prompt instructs the model to return ONLY a raw JSON object —
    no markdown fences, no prose before or after.
    """
    # Compact transcript text — use segment-level text (not word-level) to save tokens
    segments_payload = [
        {"id": s.id, "start": s.start_time, "end": s.end_time, "text": s.text}
        for s in transcript.segments
    ]
    transcript_json = json.dumps(
        {"duration": transcript.duration, "language": transcript.language,
         "segments": segments_payload},
        separators=(",", ":"),
    )

    # Truncate if too long
    if len(transcript_json) > _MAX_TRANSCRIPT_CHARS:
        logger.warning(
            "Transcript for job '%s' exceeds %d chars; truncating.",
            transcript.job_id,
            _MAX_TRANSCRIPT_CHARS,
        )
        transcript_json = transcript_json[:_MAX_TRANSCRIPT_CHARS]

    example_output = json.dumps(
        {
            "clips": [
                {
                    "rank": 1,
                    "start_time": 12.5,
                    "end_time": 72.0,
                    "hook_text": "You won't believe this simple trick",
                    "script_commentary": "Strong emotional hook opens the segment...",
                    "virality_score": 87,
                    "virality_reasoning": "High shareability due to surprising reveal..."
                }
            ]
        },
        indent=2,
    )

    return (
        "You are a viral content strategist and short-form video expert. "
        "Analyse the transcript below and identify the top 5 segments most likely "
        "to go viral on YouTube Shorts, Instagram Reels, or TikTok.\n\n"
        "RULES:\n"
        "- Each clip must be between 15 and 90 seconds long (end_time - start_time).\n"
        "- Clips must not overlap.\n"
        "- Return ONLY a raw JSON object. No markdown fences. No text before or after.\n"
        "- The JSON must match this exact structure (example):\n\n"
        f"{example_output}\n\n"
        "TRANSCRIPT (JSON):\n"
        f"{transcript_json}\n\n"
        "Return only the JSON object with the top 5 viral clips. Nothing else."
    )


# ── HuggingFace API call (with tenacity retry) ────────────────────────────────


def _is_retryable(exc: BaseException) -> bool:
    """Return True for rate-limit (429) and transient network errors."""
    try:
        from huggingface_hub.errors import HfHubHTTPError  # type: ignore
    except ImportError:
        try:
            from huggingface_hub.utils import HfHubHTTPError  # type: ignore
        except ImportError:
            return False

    if isinstance(exc, HfHubHTTPError):
        return "429" in str(exc) or "503" in str(exc) or "502" in str(exc)

    # Also retry on generic connection/timeout errors
    import requests.exceptions as req_exc  # type: ignore
    return isinstance(exc, (req_exc.ConnectionError, req_exc.Timeout))


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _call_granite_api(prompt: str) -> tuple[str, int]:
    """
    Send *prompt* to ibm-granite/granite-3.0-8b-instruct via HuggingFace
    InferenceClient and return ``(raw_text, tokens_used)``.

    Raises
    ------
    RuntimeError
        If USE_OLLAMA is False and HF_API_KEY is empty.
    """
    if settings.use_ollama:
        return _call_ollama(prompt)

    if not settings.hf_api_key:
        raise RuntimeError(
            "HF_API_KEY is not set. Cannot call Granite API. "
            "Set USE_OLLAMA=true to use a local model."
        )

    from huggingface_hub import InferenceClient  # type: ignore

    client = InferenceClient(
        model="ibm-granite/granite-3.0-8b-instruct",
        token=settings.hf_api_key,
    )

    response = client.text_generation(
        prompt,
        max_new_tokens=2048,
        temperature=0.2,
        do_sample=True,
        stop_sequences=["<|user|>", "<|system|>"],
    )

    # InferenceClient returns a string directly for text_generation
    raw_text: str = response if isinstance(response, str) else response.generated_text
    # Token count is not always exposed; default to 0 if unavailable
    tokens_used: int = getattr(response, "details", None) and getattr(
        response.details, "generated_tokens", 0
    ) or 0

    return raw_text.strip(), tokens_used


# Best available models in preference order (matched against what Ollama has)
_OLLAMA_MODEL_PREFERENCE = [
    "granite3-dense:8b",
    "llama3.1:8b",
    "llama3.2:3b",
    "phi4-mini:latest",
    "gemma3:1b",
]


def _get_ollama_model() -> str:
    """Return the best available Ollama model from the running server."""
    import urllib.request
    try:
        r = urllib.request.urlopen(
            f"{settings.ollama_base_url}/api/tags", timeout=5
        )
        available = {m["name"] for m in json.loads(r.read()).get("models", [])}
        for pref in _OLLAMA_MODEL_PREFERENCE:
            if pref in available:
                logger.info("Using Ollama model: %s", pref)
                return pref
        # fallback: use whatever is first
        if available:
            first = next(iter(available))
            logger.warning("No preferred model found; using: %s", first)
            return first
    except Exception as exc:
        logger.warning("Could not query Ollama model list: %s", exc)
    return _OLLAMA_MODEL_PREFERENCE[1]  # llama3.1:8b as safe default


def _call_ollama(prompt: str) -> tuple[str, int]:
    """Call local Ollama server using the best available model."""
    import urllib.request

    model = _get_ollama_model()

    # Use the /api/chat endpoint with messages for better instruction following
    payload = json.dumps({
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a viral content strategist. You ONLY output raw JSON. "
                    "No markdown, no explanation, no code fences. Just the JSON object."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048,
            "stop": ["\n\n\n"],
        },
    }).encode()

    req = urllib.request.Request(
        f"{settings.ollama_base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode())

    raw = data.get("message", {}).get("content", "")
    return raw.strip(), 0


# ── Response validator / parser ───────────────────────────────────────────────

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_LEADING_PROSE_RE = re.compile(r"^[^{\[]*", re.DOTALL)


def _strip_fences(raw: str) -> str:
    """Remove markdown code fences if present, returning raw JSON."""
    m = _FENCE_RE.search(raw)
    if m:
        return m.group(1).strip()
    # If no fences, strip any leading prose before the first { or [
    cleaned = _LEADING_PROSE_RE.sub("", raw).strip()
    return cleaned if cleaned else raw.strip()


def _sanitise_clip(clip: dict, rank: int) -> dict:
    """
    Fill in any empty string fields the LLM left blank so schema validation
    doesn't reject an otherwise valid clip.
    """
    fallbacks = {
        "hook_text": f"Viral moment #{rank}",
        "script_commentary": "See transcript segment for details.",
        "virality_reasoning": "High engagement potential.",
    }
    for field, fallback in fallbacks.items():
        if not clip.get(field, "").strip():
            logger.warning(
                "Clip rank=%s has empty '%s'; substituting fallback.", rank, field
            )
            clip[field] = fallback
    return clip


def _validate_and_parse(raw: str, job_id: str, duration: float) -> dict:
    """
    Strip fences → sanitise empty strings → validate JSON Schema →
    clamp timestamps → return dict.

    Raises
    ------
    GraniteOutputValidationError
        On JSON decode error or schema validation failure.
    """
    cleaned = _strip_fences(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise GraniteOutputValidationError(
            f"Granite response is not valid JSON: {exc}\n"
            f"Raw (first 500 chars): {raw[:500]}"
        ) from exc

    # Sanitise empty string fields BEFORE schema validation so a single
    # blank hook_text / commentary doesn't fail the entire job.
    if isinstance(data.get("clips"), list):
        data["clips"] = [
            _sanitise_clip(c, c.get("rank", i + 1))
            for i, c in enumerate(data["clips"])
        ]

    try:
        jsonschema.validate(instance=data, schema=_GRANITE_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise GraniteOutputValidationError(
            f"Granite JSON failed schema validation: {exc.message}\n"
            f"Path: {list(exc.absolute_path)}"
        ) from exc

    # Post-validation: clamp timestamps against actual video duration
    # and discard clips shorter than 5 s
    valid_clips = []
    for clip in data["clips"]:
        st = max(0.0, min(float(clip["start_time"]), duration))
        et = max(0.0, min(float(clip["end_time"]), duration))
        if et - st < 5.0:
            logger.warning(
                "[%s] Discarding clip rank=%s — duration %.1fs < 5s.",
                job_id, clip.get("rank"), et - st,
            )
            continue
        clip["start_time"] = round(st, 3)
        clip["end_time"] = round(et, 3)
        valid_clips.append(clip)

    data["clips"] = valid_clips
    return data


# ── Public orchestrator ───────────────────────────────────────────────────────


def analyze_transcript(transcript: FullTranscript, job_id: str) -> GraniteAnalysis:
    """
    Run the full Granite analysis pipeline for *transcript*.

    1. Build prompt.
    2. Call Granite API (with retry).
    3. Validate and parse response.
    4. Persist ``granite_analysis.json`` to the job output directory.

    Returns
    -------
    GraniteAnalysis
    """
    logger.info("[%s] Starting Granite analysis …", job_id)

    prompt = _build_prompt(transcript)
    raw_text, tokens_used = _call_granite_api(prompt)

    logger.debug("[%s] Raw Granite response (500 chars): %s", job_id, raw_text[:500])

    parsed = _validate_and_parse(raw_text, job_id, transcript.duration)

    clips = [ViralClip(**c) for c in parsed["clips"]]
    analysis = GraniteAnalysis(
        job_id=job_id,
        clips=clips,
        model_used=(
            f"ollama/{_get_ollama_model()}"
            if settings.use_ollama
            else "ibm-granite/granite-3.0-8b-instruct"
        ),
        tokens_used=tokens_used,
    )

    # Persist to disk
    job_output_dir = settings.output_dir / job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)
    analysis_path = job_output_dir / "granite_analysis.json"
    analysis_path.write_text(analysis.model_dump_json(indent=2), encoding="utf-8")
    logger.info(
        "[%s] Granite analysis saved to '%s' (%d clips).",
        job_id, analysis_path, len(clips),
    )

    return analysis


def load_analysis(job_id: str) -> GraniteAnalysis:
    """Load a previously persisted GraniteAnalysis from disk."""
    path = settings.output_dir / job_id / "granite_analysis.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No Granite analysis found for job '{job_id}' at '{path}'."
        )
    return GraniteAnalysis.model_validate_json(path.read_text(encoding="utf-8"))
