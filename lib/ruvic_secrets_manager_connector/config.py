"""Configuración del conector leída desde variables de entorno.

Convención de la plataforma: cada campo del formulario de configuración
llega como variable de entorno {ENV_PREFIX}{CAMPO} en mayúsculas.
Para este conector el prefijo es RUVIC_SECRETS_MANAGER_.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ENV_PREFIX = "RUVIC_SECRETS_MANAGER_"


@dataclass(frozen=True)
class SecretsManagerConfig:
    """Parámetros de conexión a AWS Secrets Manager."""

    access_key_id: str
    secret_access_key: str
    region: str
    secret_name_prefix: str | None = None
    connect_timeout: int = 10

    @classmethod
    def from_env(cls) -> "SecretsManagerConfig":
        """Construye la configuración desde las variables RUVIC_SECRETS_MANAGER_*.

        Raises:
            ValueError: si falta alguna variable obligatoria.

        Ejemplo:
            >>> config = SecretsManagerConfig.from_env()
            >>> config.region
            'us-east-1'
        """
        missing = [
            f"{ENV_PREFIX}{name}"
            for name in ("ACCESS_KEY_ID", "SECRET_ACCESS_KEY", "REGION")
            if not os.environ.get(f"{ENV_PREFIX}{name}")
        ]
        if missing:
            raise ValueError(
                "Faltan variables de entorno del conector secrets_manager: "
                + ", ".join(missing)
                + ". Configura el conector en Settings → Conectores."
            )
        return cls(
            access_key_id=os.environ[f"{ENV_PREFIX}ACCESS_KEY_ID"],
            secret_access_key=os.environ[f"{ENV_PREFIX}SECRET_ACCESS_KEY"],
            region=os.environ[f"{ENV_PREFIX}REGION"],
            secret_name_prefix=os.environ.get(f"{ENV_PREFIX}SECRET_NAME_PREFIX") or None,
            connect_timeout=int(os.environ.get(f"{ENV_PREFIX}CONNECT_TIMEOUT", "10")),
        )
