class HsmError(RuntimeError):
    """Base error for controlled application failures."""


class ProviderLoadError(HsmError):
    """Raised when an HSM provider or PKCS#11 module cannot be loaded."""


class ProviderNotConnectedError(HsmError):
    """Raised when an operation requires an active provider connection."""


class OperationNotSupportedError(HsmError):
    """Raised when an operation is not supported by the active provider."""


class ValidationError(HsmError):
    """Raised when user supplied data is invalid."""


class StateStoreError(HsmError):
    """Raised when virtual HSM state cannot be loaded or persisted."""


class SessionError(HsmError):
    """Raised for invalid session lifecycle operations."""


class AuthenticationError(HsmError):
    """Raised when USER/SO authentication fails or conflicts."""