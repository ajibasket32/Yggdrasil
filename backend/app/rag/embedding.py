import hashlib
import math
import re

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class DeterministicTextEmbedder:
    """Create stable lexical vectors without a provider or network dependency."""

    def __init__(self, dimensions: int = 256) -> None:
        if dimensions < 16:
            raise ValueError("Embedding dimensions must be at least 16")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        """Return a normalized signed feature-hash vector."""
        tokens = TOKEN_PATTERN.findall(text.lower())
        features = [(token, 2.0) for token in tokens] + [
            (f"{left}:{right}", 1.0)
            for left, right in zip(tokens, tokens[1:], strict=False)
        ]
        vector = [0.0] * self.dimensions
        for feature, weight in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += weight
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]
