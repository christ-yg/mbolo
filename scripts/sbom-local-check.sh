#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BACKEND_IMAGE="mbolo-backend-sbom:local"
FRONTEND_IMAGE="mbolo-frontend-sbom:local"
SYFT_IMAGE="anchore/syft:v1.44.0"
OUTPUT_DIR="${MBOLO_SBOM_OUTPUT_DIR:-tmp/sbom}"

echo "[1/5] Validation des outils"
command -v docker >/dev/null 2>&1 || {
  echo "ERREUR : Docker est introuvable." >&2
  exit 1
}
docker info >/dev/null 2>&1 || {
  echo "ERREUR : Docker Desktop n'est pas démarré." >&2
  exit 1
}

echo "[2/5] Construction de l'image backend"
docker build \
  --file backend/Dockerfile.production \
  --tag "$BACKEND_IMAGE" \
  .

echo "[3/5] Construction de l'image frontend"
docker build \
  --file frontend/Dockerfile.production \
  --tag "$FRONTEND_IMAGE" \
  .

echo "[4/5] Génération des SBOM CycloneDX"
mkdir -p "$OUTPUT_DIR"

docker run --rm \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  "$SYFT_IMAGE" \
  "$BACKEND_IMAGE" \
  --output cyclonedx-json \
  >"$OUTPUT_DIR/mbolo-backend.cdx.json"

docker run --rm \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  "$SYFT_IMAGE" \
  "$FRONTEND_IMAGE" \
  --output cyclonedx-json \
  >"$OUTPUT_DIR/mbolo-frontend.cdx.json"

echo "[5/5] Validation des deux documents"
docker run --rm \
  --volume "$ROOT_DIR/$OUTPUT_DIR:/sbom:ro" \
  python:3.13-alpine \
  python -c 'import json, pathlib; files=list(pathlib.Path("/sbom").glob("*.cdx.json")); assert len(files)==2; [json.loads(f.read_text()) for f in files]; print("Deux SBOM JSON valides : OK")'

echo "✅ SBOM_CHECK=OK"
echo "ℹ️  Fichiers locaux : $OUTPUT_DIR"
