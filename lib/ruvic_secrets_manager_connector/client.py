"""Cliente de lectura de secretos para AWS Secrets Manager.

Capacidades:
- get_secret():       obtiene el valor de un secreto.
- list_secrets():      lista los secretos disponibles (metadatos, no valores).
- rotate_secret():     dispara una rotación inmediata de un secreto (opcional).

Las credenciales SIEMPRE provienen de variables de entorno
RUVIC_SECRETS_MANAGER_* (ver config.SecretsManagerConfig.from_env).
Prohibido hardcodearlas.
"""

from __future__ import annotations

from typing import Any

import boto3  # type: ignore[import-untyped]
from botocore.config import Config as BotoConfig  # type: ignore[import-untyped]
from botocore.exceptions import (  # type: ignore[import-untyped]
    BotoCoreError,
    ClientError,
    EndpointConnectionError,
)

from .config import SecretsManagerConfig
from .exceptions import (
    SecretsManagerAuthError,
    SecretsManagerConnectorError,
    SecretsManagerDataError,
    SecretsManagerNetworkError,
)
from .logging_utils import get_logger

_AUTH_ERROR_CODES = {
    "AccessDeniedException",
    "UnrecognizedClientException",
    "InvalidClientTokenId",
    "InvalidSignatureException",
}
_NOT_FOUND_ERROR_CODES = {"ResourceNotFoundException"}
_MAX_LIST_LIMIT = 100


def _require_secret_id(secret_id: Any) -> str:
    if secret_id is not None and not isinstance(secret_id, str):
        raise SecretsManagerDataError(f"secret_id debe ser un string, no {type(secret_id).__name__}.")
    return (secret_id or "").strip()


def _wrap_client_error(exc: ClientError, not_found_message: str) -> SecretsManagerConnectorError:
    """Traduce un error de la API de AWS a una excepción propia, sin
    dejar escapar nunca el tipo crudo del SDK."""
    code = exc.response.get("Error", {}).get("Code", "")
    if code in _AUTH_ERROR_CODES:
        return SecretsManagerAuthError(
            "Credenciales inválidas o sin permiso IAM suficiente para esta "
            "operación. Revisa la policy adjunta al usuario o rol."
        )
    if code in _NOT_FOUND_ERROR_CODES:
        return SecretsManagerDataError(not_found_message)
    if code == "InvalidRequestException":
        return SecretsManagerDataError(f"Solicitud inválida: {exc}")
    return SecretsManagerDataError(f"Error de datos ({code}): {exc}")


class SecretsManagerClient:
    """Cliente de lectura de secretos de AWS Secrets Manager.

    Args:
        config: configuración de conexión. Si se omite, se lee de las
            variables de entorno RUVIC_SECRETS_MANAGER_* (comportamiento
            estándar en el runtime de la plataforma).

    Ejemplo:
        >>> client = SecretsManagerClient()  # lee RUVIC_SECRETS_MANAGER_* del entorno
        >>> client.get_secret("prod/db/password")
        'super-secreto-real'
    """

    def __init__(self, config: SecretsManagerConfig | None = None) -> None:
        self.config = config or SecretsManagerConfig.from_env()
        self._logger = get_logger()
        self._client: Any = None

    # ------------------------------------------------------------------ #
    # Conexión
    # ------------------------------------------------------------------ #

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        self._client = boto3.client(
            "secretsmanager",
            aws_access_key_id=self.config.access_key_id,
            aws_secret_access_key=self.config.secret_access_key,
            region_name=self.config.region,
            config=BotoConfig(
                connect_timeout=self.config.connect_timeout,
                read_timeout=max(self.config.connect_timeout, 30),
                retries={"max_attempts": 2, "mode": "standard"},
            ),
        )
        return self._client

    def _check_prefix(self, secret_id: str) -> None:
        if self.config.secret_name_prefix and not secret_id.startswith(
            self.config.secret_name_prefix
        ):
            raise SecretsManagerDataError(
                f"El secreto {secret_id!r} no coincide con el prefijo permitido "
                f"{self.config.secret_name_prefix!r} configurado para este conector."
            )

    def ping(self) -> bool:
        """Verifica la conexión listando hasta 1 secreto.

        Returns:
            True si la conexión funciona.

        Raises:
            SecretsManagerAuthError / SecretsManagerNetworkError /
            SecretsManagerDataError.
        """
        self.list_secrets(max_results=1)
        self._logger.info("Ping exitoso a Secrets Manager en %s", self.config.region)
        return True

    # ------------------------------------------------------------------ #
    # Capacidad 1: obtener un secreto
    # ------------------------------------------------------------------ #

    def get_secret(self, secret_id: str) -> str:
        """Obtiene el valor de un secreto.

        Args:
            secret_id: nombre o ARN del secreto (ej. "prod/db/password").

        Returns:
            El valor del secreto como string (texto plano o el JSON
            almacenado, según cómo se haya guardado).

        Ejemplo:
            >>> client.get_secret("prod/db/password")
            'super-secreto-real'
        """
        secret_id = _require_secret_id(secret_id)
        if not secret_id:
            raise SecretsManagerDataError("secret_id no puede estar vacío.")
        self._check_prefix(secret_id)
        client = self._get_client()
        try:
            response = client.get_secret_value(SecretId=secret_id)
        except ClientError as exc:
            raise _wrap_client_error(
                exc, f"El secreto {secret_id!r} no existe o no es accesible."
            ) from exc
        except (EndpointConnectionError, BotoCoreError) as exc:
            raise SecretsManagerNetworkError(f"No se pudo obtener el secreto: {exc}") from exc
        self._logger.info("Secreto %s obtenido", secret_id)
        return response.get("SecretString", "")

    # ------------------------------------------------------------------ #
    # Capacidad 2: listar secretos (metadatos, no valores)
    # ------------------------------------------------------------------ #

    def list_secrets(self, max_results: int = 50) -> list[dict[str, Any]]:
        """Lista los secretos disponibles (solo metadatos, nunca valores).

        Args:
            max_results: máximo de secretos a retornar (default 50,
                máximo 100).

        Returns:
            Lista de dicts: {"name", "arn", "description",
            "last_changed_date"}.

        Ejemplo:
            >>> client.list_secrets()
            [{'name': 'prod/db/password', 'arn': 'arn:aws:secretsmanager:...', ...}]
        """
        try:
            max_results = max(1, min(int(max_results), _MAX_LIST_LIMIT))
        except (TypeError, ValueError) as exc:
            raise SecretsManagerDataError(
                f"max_results inválido: {max_results!r}. Debe ser un número entero."
            ) from exc
        client = self._get_client()
        try:
            response = client.list_secrets(MaxResults=max_results)
        except ClientError as exc:
            raise _wrap_client_error(exc, "No se pudieron listar los secretos.") from exc
        except (EndpointConnectionError, BotoCoreError) as exc:
            raise SecretsManagerNetworkError(f"No se pudieron listar los secretos: {exc}") from exc

        secrets = response.get("SecretList", [])
        if self.config.secret_name_prefix:
            secrets = [s for s in secrets if s["Name"].startswith(self.config.secret_name_prefix)]

        result = [
            {
                "name": s["Name"],
                "arn": s["ARN"],
                "description": s.get("Description"),
                "last_changed_date": s["LastChangedDate"].isoformat()
                if s.get("LastChangedDate")
                else None,
            }
            for s in secrets
        ]
        self._logger.info("Se listaron %d secreto(s)", len(result))
        return result

    # ------------------------------------------------------------------ #
    # Capacidad 3: rotar un secreto (opcional)
    # ------------------------------------------------------------------ #

    def rotate_secret(self, secret_id: str) -> str:
        """Dispara una rotación inmediata de un secreto.

        Requiere que el secreto ya tenga configurada una función Lambda
        de rotación en AWS — este método solo dispara el proceso, no lo
        configura.

        Args:
            secret_id: nombre o ARN del secreto a rotar.

        Returns:
            El ARN del secreto cuya rotación se disparó.

        Ejemplo:
            >>> client.rotate_secret("prod/db/password")
            'arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/db/password-AbCdEf'
        """
        secret_id = _require_secret_id(secret_id)
        if not secret_id:
            raise SecretsManagerDataError("secret_id no puede estar vacío.")
        self._check_prefix(secret_id)
        client = self._get_client()
        try:
            response = client.rotate_secret(SecretId=secret_id)
        except ClientError as exc:
            raise _wrap_client_error(
                exc, f"El secreto {secret_id!r} no existe, no es accesible, o no tiene rotación configurada."
            ) from exc
        except (EndpointConnectionError, BotoCoreError) as exc:
            raise SecretsManagerNetworkError(f"No se pudo rotar el secreto: {exc}") from exc
        self._logger.info("Rotación disparada para el secreto %s", secret_id)
        return response["ARN"]
