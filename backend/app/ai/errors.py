class AIError(Exception):
    """Base error for provider-layer failures."""


class ProviderError(AIError):
    """A provider could not return a usable response."""


class ProviderConfigurationError(AIError):
    """Provider configuration is invalid or incomplete."""


class NarrativeValidationError(AIError):
    """Provider output attempted to cross the narrative-only boundary."""


class BudgetUnavailableError(AIError):
    """The request budget could not be checked safely."""
