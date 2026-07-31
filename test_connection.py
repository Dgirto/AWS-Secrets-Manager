"""Prueba de conexión estándar del conector secrets_manager.

Firma estándar Ruvic: def test_connection() -> tuple[bool, str]
- Lee la configuración EXCLUSIVAMENTE de las env vars RUVIC_SECRETS_MANAGER_*.
- Nunca lanza excepciones; retorna (ok, mensaje).

Ejecutable también como script para pruebas locales:
    python test_connection.py
"""

from __future__ import annotations


def test_connection() -> tuple[bool, str]:
    """Conecta a Secrets Manager y lista un secreto usando las env vars
    RUVIC_SECRETS_MANAGER_*."""
    try:
        from ruvic_secrets_manager_connector import (
            SecretsManagerAuthError,
            SecretsManagerClient,
            SecretsManagerDataError,
            SecretsManagerNetworkError,
        )
    except ImportError:
        return (
            False,
            "La librería ruvic-secrets-manager-connector no está instalada. "
            "Instala con: pip install git+https://github.com/Dgirto/"
            "AWS-Secrets-Manager.git#subdirectory=lib",
        )

    try:
        client = SecretsManagerClient()  # valida que existan las env vars
    except ValueError as exc:
        return False, str(exc)

    try:
        client.ping()
    except SecretsManagerAuthError as exc:
        return False, f"Autenticación fallida: {exc}"
    except SecretsManagerNetworkError as exc:
        return False, f"Error de red: {exc}"
    except SecretsManagerDataError as exc:
        return False, f"Error de datos: {exc}"
    except Exception as exc:  # red de seguridad: jamás propagar
        return False, f"Error inesperado: {exc}"

    return (
        True,
        f"Conexión exitosa a Secrets Manager en la región {client.config.region!r}",
    )


if __name__ == "__main__":
    ok, message = test_connection()
    print(f"{'OK' if ok else 'FALLO'}: {message}")
    raise SystemExit(0 if ok else 1)
