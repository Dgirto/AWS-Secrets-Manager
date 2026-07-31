---
name: secrets_manager
description: >
  Usa la librería ruvic_secrets_manager_connector para leer secretos
  gestionados en AWS Secrets Manager - obtener el valor de un secreto
  (get_secret), listar los secretos disponibles (list_secrets), y
  disparar una rotación inmediata (rotate_secret, opcional). Úsala
  cuando el usuario pida consultar o rotar un secreto/credencial
  almacenado en AWS.
triggers:
- secrets manager
- aws secrets
- secreto aws
- credencial aws
- rotar secreto
---

# Conector AWS Secrets Manager (ruvic_secrets_manager_connector)

Librería Python de lectura de secretos de AWS. Está **preinstalada en
el runtime** cuando el conector está configurado (si no, instálala con
`pip install git+https://github.com/Dgirto/AWS-Secrets-Manager.git#subdirectory=lib`).

## Regla crítica de credenciales

El código generado **NUNCA hardcodea credenciales**. Siempre se leen de
variables de entorno, disponibles cuando el conector `secrets_manager`
está configurado:

| Variable | Contenido |
|----------|-----------|
| `RUVIC_SECRETS_MANAGER_ACCESS_KEY_ID` | Access Key ID de AWS |
| `RUVIC_SECRETS_MANAGER_SECRET_ACCESS_KEY` | Secret Access Key de AWS |
| `RUVIC_SECRETS_MANAGER_REGION` | Región de AWS |
| `RUVIC_SECRETS_MANAGER_SECRET_NAME_PREFIX` | (opcional) prefijo permitido |
| `RUVIC_SECRETS_MANAGER_CONNECT_TIMEOUT` | (opcional) timeout en segundos |

Si estas variables NO existen, el conector no está configurado: no
generes código que lo use; indica al usuario que lo configure en
**Settings → Conectores**.

## Este conector expone valores reales de secretos

`get_secret` devuelve el **valor real** del secreto en texto plano.
**Nunca imprimas, loguees ni muestres el valor completo de un secreto
en la salida al usuario a menos que te lo pida explícitamente y
entienda que lo va a ver en texto plano.** Si el usuario solo necesita
confirmar que un secreto existe o ver metadatos, usá `list_secrets` en
vez de `get_secret`.

## Conexión (siempre igual)

```python
from ruvic_secrets_manager_connector import SecretsManagerClient

client = SecretsManagerClient()  # lee RUVIC_SECRETS_MANAGER_* del entorno automáticamente
```

## Capacidad 1 — Obtener un secreto

```python
valor = client.get_secret("prod/db/password")
```

## Capacidad 2 — Listar secretos (solo metadatos)

```python
secretos = client.list_secrets()
for s in secretos:
    print(s["name"], s["last_changed_date"])
```

## Capacidad 3 — Rotar un secreto (opcional)

```python
client.rotate_secret("prod/db/password")
```

Requiere que el secreto ya tenga una función Lambda de rotación
configurada en AWS.

## Manejo de errores

```python
from ruvic_secrets_manager_connector import (
    SecretsManagerAuthError, SecretsManagerDataError, SecretsManagerNetworkError,
)

try:
    valor = client.get_secret("prod/db/password")
except SecretsManagerAuthError:
    print("Credenciales inválidas o sin permiso IAM suficiente")
except SecretsManagerNetworkError:
    print("No se pudo alcanzar Secrets Manager — reintenta en unos segundos")
except SecretsManagerDataError as e:
    print(f"Error de datos: {e}")  # ej. el secreto no existe o el prefijo no coincide
```

## Buenas prácticas al generar código

1. Lee credenciales SOLO de las variables `RUVIC_SECRETS_MANAGER_*` (el constructor de `SecretsManagerClient` ya lo hace).
2. Nunca imprimas `RUVIC_SECRETS_MANAGER_SECRET_ACCESS_KEY` en logs ni en la salida.
3. **No expongas el valor devuelto por `get_secret` sin que el usuario lo haya pedido explícitamente sabiendo que va a verlo en texto plano.**
4. `rotate_secret` dispara un cambio real de credencial: no la llames sin que el usuario lo haya pedido explícitamente.
5. Usá `list_secrets` para explorar qué secretos existen antes de pedir uno específico con `get_secret` — evita adivinar nombres de secretos.
