"""Validación local del conector secrets_manager: ejercita las 2
capacidades de solo lectura (get_secret, list_secrets).

Uso:
    python validate_local.py

Requiere las variables RUVIC_SECRETS_MANAGER_* exportadas en el
entorno, y el nombre de un secreto de prueba ya existente (editá
TEST_SECRET_NAME abajo). rotate_secret NO se ejerce acá por defecto
(requiere que el secreto tenga una función Lambda de rotación
configurada) — probalo por separado si corresponde.
"""

from ruvic_secrets_manager_connector import SecretsManagerClient, setup_logging

TEST_SECRET_NAME = "ruvic-test-secret"  # <-- reemplaza por un secreto de prueba real

setup_logging("INFO")
client = SecretsManagerClient()

print("== 1. Listar secretos ==")
secretos = client.list_secrets()
for s in secretos[:5]:
    print(f"  {s['name']}")

print("== 2. Obtener secreto de prueba ==")
valor = client.get_secret(TEST_SECRET_NAME)
print(f"  longitud del valor: {len(valor)} caracteres (no se imprime el contenido)")

print("\nTodo OK: list_secrets y get_secret funcionan.")
