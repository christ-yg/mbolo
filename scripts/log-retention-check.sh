#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE_FILE="${MBOLO_COMPOSE_FILE:-compose.production.yaml}"
ENV_FILE="${MBOLO_ENV_FILE:-.env.production}"
EXPECTED_DRIVER="json-file"
EXPECTED_MAX_SIZE="${MBOLO_LOG_MAX_SIZE:-10m}"
EXPECTED_MAX_FILES="${MBOLO_LOG_MAX_FILES:-5}"

echo "[1/3] Validation de Docker Compose"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config --quiet

echo "[2/3] Contrôle de la politique déclarée"
config_json="$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config --format json)"
export MBOLO_COMPOSE_CONFIG_JSON="$config_json"

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 est requis pour valider la configuration Compose."
  exit 1
fi

python3 - "$EXPECTED_DRIVER" "$EXPECTED_MAX_SIZE" "$EXPECTED_MAX_FILES" <<'PY'
import json
import os
import sys

expected_driver, expected_size, expected_files = sys.argv[1:4]
configuration = json.loads(os.environ["MBOLO_COMPOSE_CONFIG_JSON"])
required_services = {"postgres", "redis", "backend", "frontend"}
services = configuration.get("services", {})

missing = required_services.difference(services)
if missing:
    raise SystemExit(f"Services absents: {', '.join(sorted(missing))}")

for name in sorted(required_services):
    logging = services[name].get("logging", {})
    driver = logging.get("driver")
    options = logging.get("options", {})
    max_size = str(options.get("max-size", ""))
    max_files = str(options.get("max-file", ""))

    if driver != expected_driver:
        raise SystemExit(f"{name}: pilote {driver!r}, attendu {expected_driver!r}")
    if max_size != expected_size:
        raise SystemExit(f"{name}: max-size {max_size!r}, attendu {expected_size!r}")
    if max_files != expected_files:
        raise SystemExit(f"{name}: max-file {max_files!r}, attendu {expected_files!r}")

    print(f"✅ {name}: {driver}, {max_size} × {max_files}")
PY

unset MBOLO_COMPOSE_CONFIG_JSON

echo "[3/3] Contrôle des conteneurs actifs"
for service in postgres redis backend frontend; do
  container_id="$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps -q "$service")"

  if [[ -z "$container_id" ]]; then
    echo "❌ $service: conteneur absent. Recréez d'abord les services."
    exit 1
  fi

  actual_driver="$(docker inspect --format '{{.HostConfig.LogConfig.Type}}' "$container_id")"
  actual_size="$(docker inspect --format '{{index .HostConfig.LogConfig.Config "max-size"}}' "$container_id")"
  actual_files="$(docker inspect --format '{{index .HostConfig.LogConfig.Config "max-file"}}' "$container_id")"

  if [[ "$actual_driver" != "$EXPECTED_DRIVER" || "$actual_size" != "$EXPECTED_MAX_SIZE" || "$actual_files" != "$EXPECTED_MAX_FILES" ]]; then
    echo "❌ $service: politique active inattendue ($actual_driver, $actual_size × $actual_files)"
    exit 1
  fi

  echo "✅ $service: politique active"
done

echo "✅ LOG_RETENTION=OK"
echo "ℹ️  Limite par conteneur : ${EXPECTED_MAX_SIZE} × ${EXPECTED_MAX_FILES}"
