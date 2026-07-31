"""Excepciones propias del conector AWS Secrets Manager.

Separan los tres tipos de fallo que el usuario debe distinguir:
autenticación, red/servidor y datos. Nunca exponemos excepciones
crípticas del SDK subyacente.
"""


class SecretsManagerConnectorError(Exception):
    """Error base del conector."""


class SecretsManagerAuthError(SecretsManagerConnectorError):
    """Credenciales inválidas o permisos IAM insuficientes."""


class SecretsManagerNetworkError(SecretsManagerConnectorError):
    """No se pudo alcanzar el servicio Secrets Manager (red/timeout)."""


class SecretsManagerDataError(SecretsManagerConnectorError):
    """La operación es válida pero el secreto/parámetro es inválido."""
