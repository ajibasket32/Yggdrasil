import json
import re

from pydantic import ValidationError

from app.ai.contracts import NarrativeOutput, NarrativeRequest, ProviderGeneration
from app.ai.errors import NarrativeValidationError

FORBIDDEN_PATTERNS = (
    re.compile(
        r"\b(?:damage|experience|xp|gold|currency|loot|drop|turn order|"
        r"combat result|stat allocation|quest reward)\b\s*[:=]\s*[-+]?\d+",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:set|update|write|delete|mutate)\s+"
        r"(?:game|world|quest|character|inventory|combat)\s+state\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:api[_ -]?key|authorization|bearer)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:ignore|reveal|repeat|print)\b.{0,40}"
        r"\b(?:previous instructions|system prompt|developer message)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:quest|relationship|faction|inventory|combat|world)\b.{0,30}"
        r"\b(?:completed|increased|decreased|updated|changed|unlocked)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:you|player|character)\s+(?:gain|gains|receive|receives|lose|loses)"
        r"\s+[-+]?\d+\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
        r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
        re.IGNORECASE,
    ),
)

ALLOWED_TONES = {
    "neutral",
    "warm",
    "wary",
    "cautious",
    "solemn",
    "mysterious",
    "quiet",
    "tense",
    "urgent",
}


class NarrativeValidator:
    """Validate provider output at the narrative-only trust boundary."""

    def validate(
        self,
        request: NarrativeRequest,
        generation: ProviderGeneration,
    ) -> NarrativeOutput:
        try:
            payload = json.loads(generation.content)
            output = NarrativeOutput.model_validate(payload)
        except (json.JSONDecodeError, ValidationError, TypeError) as error:
            raise NarrativeValidationError(
                "Provider output does not match the narrative schema"
            ) from error

        disallowed_ids = output.referenced_entity_ids - request.allowed_entity_ids
        if disallowed_ids:
            raise NarrativeValidationError(
                "Provider output referenced entities outside the request boundary"
            )
        if any(pattern.search(output.text) for pattern in FORBIDDEN_PATTERNS):
            raise NarrativeValidationError("Provider output attempted to encode gameplay authority")
        if output.tone not in ALLOWED_TONES:
            raise NarrativeValidationError("Provider output used an unsupported tone")
        return output
