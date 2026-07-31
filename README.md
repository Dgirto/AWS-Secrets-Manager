# Conector AWS Secrets Manager (CON-070)

Conector Ruvic de lectura de secretos gestionados en AWS. Permite
obtener el valor de un secreto, listar los secretos disponibles
(metadatos, no valores), y opcionalmente disparar una rotación
inmediata.

## Instalación

```bash
pip install git+https://github.com/Dgirto/AWS-Secrets-Manager.git#subdirectory=lib
```

Python 3.10+. Dependencia única: `boto3>=1.34,<2.0`.

## Permisos requeridos en AWS (IAM)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:ruvic/*"
    }
  ]
}
```

Agregá `secretsmanager:RotateSecret` a la lista de `Action` solo si vas
a usar esa capacidad. Se recomienda **restringir el `Resource` por
prefijo** (ej. `secret:ruvic/*`) en vez de dar acceso a todos los
secretos de la cuenta — este conector puede exponer valores reales de
secretos, así que el alcance debe ser el mínimo indispensable.

## Variables de entorno (`RUVIC_SECRETS_MANAGER_*`)

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `RUVIC_SECRETS_MANAGER_ACCESS_KEY_ID` | Sí | Access Key ID de AWS |
| `RUVIC_SECRETS_MANAGER_SECRET_ACCESS_KEY` | Sí | Secret Access Key de AWS |
| `RUVIC_SECRETS_MANAGER_REGION` | Sí | Región de AWS |
| `RUVIC_SECRETS_MANAGER_SECRET_NAME_PREFIX` | No | Restringe (a nivel de código, además de IAM) qué secretos puede leer/rotar el conector |
| `RUVIC_SECRETS_MANAGER_CONNECT_TIMEOUT` | No (default `10`) | Timeout de conexión en segundos |

## Pruebas locales

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ./lib

export RUVIC_SECRETS_MANAGER_ACCESS_KEY_ID=tu-access-key
export RUVIC_SECRETS_MANAGER_SECRET_ACCESS_KEY=tu-secret-key
export RUVIC_SECRETS_MANAGER_REGION=us-east-1

python test_connection.py
python validate_local.py
```

Antes de correr `validate_local.py`, editá `TEST_SECRET_NAME` con el
nombre de un secreto de prueba ya existente en tu cuenta.

## Notas de integración

- `get_secret` y `list_secrets` son de **solo lectura**. `rotate_secret`
  **SÍ modifica** el secreto (dispara su rotación real) — requiere que
  el secreto ya tenga configurada una función Lambda de rotación en
  AWS; este conector solo la dispara, no la configura.
- `list_secrets` **nunca** devuelve valores de secretos, solo metadatos
  (nombre, ARN, descripción, fecha de último cambio) — para obtener un
  valor hay que llamar a `get_secret` explícitamente con el nombre.
- Si configurás `RUVIC_SECRETS_MANAGER_SECRET_NAME_PREFIX`, el conector
  rechaza (a nivel de código) cualquier intento de leer o rotar un
  secreto cuyo nombre no empiece con ese prefijo — es una capa extra
  de seguridad además de la policy IAM, no un reemplazo de ella.
- El valor retornado por `get_secret` puede ser texto plano o un JSON
  serializado como string, según cómo se haya guardado el secreto
  originalmente — el conector no intenta parsearlo ni interpretarlo.
