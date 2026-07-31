"""Conector Ruvic de lectura de secretos gestionados en AWS Secrets Manager."""

from .client import SecretsManagerClient
from .config import ENV_PREFIX, SecretsManagerConfig
from .exceptions import (
    SecretsManagerAuthError,
    SecretsManagerConnectorError,
    SecretsManagerDataError,
    SecretsManagerNetworkError,
)
from .logging_utils import setup_logging

__all__ = [
    "ENV_PREFIX",
    "SecretsManagerAuthError",
    "SecretsManagerClient",
    "SecretsManagerConfig",
    "SecretsManagerConnectorError",
    "SecretsManagerDataError",
    "SecretsManagerNetworkError",
    "setup_logging",
]

__version__ = "1.0.0"
