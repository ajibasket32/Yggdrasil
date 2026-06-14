class RAGError(Exception):
    """Base error for memory and retrieval infrastructure failures."""


class MemoryNotFoundError(RAGError):
    """The requested canonical memory does not exist in the player scope."""


class QdrantError(RAGError):
    """Qdrant could not complete a vector operation."""


class IndexDispatchError(RAGError):
    """A durable index job could not be announced to the worker broker."""
