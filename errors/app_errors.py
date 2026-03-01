class EmbedForgeError(Exception):
    """Base application error."""


class UnsafeEditTargetError(EmbedForgeError):
    """Raised when the user tries to edit a message that should not be editable."""


class PlanLimitError(EmbedForgeError):
    """Raised when a Free plan usage limit has been reached."""


class FeatureUnavailableError(EmbedForgeError):
    """Raised when a plan-gated feature is unavailable."""

