#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERREUR : exécute ce contrôle depuis le dépôt Mbolo." >&2
  exit 1
fi

cd "$(git rev-parse --show-toplevel)"

echo "[1/10] Fichiers indispensables"
required_files=(
  .github/workflows/ci.yml
  .github/workflows/container-security.yml
  backend/Dockerfile.production
  backend/requirements/development.txt
  compose.production.yaml
  frontend/Dockerfile.production
  frontend/package-lock.json
  scripts/check-sensitive-files.sh
  scripts/github-actions-pin-check.sh
)
for path in "${required_files[@]}"; do
  [[ -f "${path}" ]] || { echo "ERREUR : ${path} manque." >&2; exit 1; }
done
echo "✅ Socle de sécurité présent"

echo "[2/10] Secrets et artefacts suivis"
bash scripts/check-sensitive-files.sh

echo "[3/10] Actions GitHub épinglées"
bash scripts/github-actions-pin-check.sh

echo "[4/10] Syntaxe des scripts Bash"
mapfile -t shell_scripts < <(git ls-files 'scripts/*.sh' | sort)
(( ${#shell_scripts[@]} > 0 )) || { echo "ERREUR : aucun script Bash suivi." >&2; exit 1; }
for script in "${shell_scripts[@]}"; do
  bash -n "${script}"
done
echo "✅ ${#shell_scripts[@]} script(s) syntaxiquement valide(s)"

echo "[5/10] Modes exécutables des scripts"
while IFS=$'\t' read -r metadata path; do
  mode="${metadata%% *}"
  [[ "${mode}" == "100755" ]] || {
    echo "ERREUR : ${path} doit être exécutable dans Git (mode actuel ${mode})." >&2
    exit 1
  }
done < <(git ls-files --stage 'scripts/*.sh')
echo "✅ Scripts suivis en mode exécutable"

echo "[6/10] Fichiers de verrouillage"
git ls-files --error-unmatch frontend/package-lock.json >/dev/null
grep -qE '^Django==[0-9]' backend/requirements/development.txt
grep -qE '^djangorestframework==[0-9]' backend/requirements/development.txt
echo "✅ Dépendances frontend et backend verrouillées"

echo "[7/10] Runtimes applicatifs minimaux"
backend_user="$(awk 'toupper($1) == "USER" { user=$2 } END { print user }' backend/Dockerfile.production)"
[[ -n "${backend_user}" && "${backend_user}" != "root" && "${backend_user}" != "0" ]] || {
  echo "ERREUR : le backend ne termine pas avec un utilisateur non-root." >&2
  exit 1
}
grep -Eq '^FROM[[:space:]]+nginx:[^[:space:]]+-alpine[[:space:]]+AS[[:space:]]+runtime$' frontend/Dockerfile.production || {
  echo "ERREUR : le runtime frontend doit rester basé sur Nginx Alpine." >&2
  exit 1
}
echo "✅ Backend non-root et runtime frontend minimal"

echo "[8/10] Protections des conteneurs applicatifs"
for setting in 'read_only: true' 'no-new-privileges:true' 'cap_drop:'; do
  grep -Fq "${setting}" compose.production.yaml || {
    echo "ERREUR : protection Compose absente : ${setting}" >&2
    exit 1
  }
done
echo "✅ Lecture seule, privilèges et capacités contrôlés"

echo "[9/10] Moindre privilège dans les workflows"
mapfile -t workflows < <(find .github/workflows -maxdepth 1 -type f \( -name '*.yml' -o -name '*.yaml' \) -print | sort)
for workflow in "${workflows[@]}"; do
  grep -Eq '^permissions:[[:space:]]*$' "${workflow}" || {
    echo "ERREUR : permissions explicites absentes dans ${workflow}." >&2
    exit 1
  }
done
echo "✅ Permissions explicites sur tous les workflows"

echo "[10/10] Interdiction des configurations dangereuses"
dangerous_pattern="DEBUG[[:space:]]*=[[:space:]]*True|ALLOWED_HOSTS[[:space:]]*=[[:space:]]*\\[[[:space:]]*['\"]\\*['\"]|chmod[[:space:]]+777|curl[^|]*\\|[[:space:]]*(ba)?sh|wget[^|]*\\|[[:space:]]*(ba)?sh"
if git grep -nEI "${dangerous_pattern}" -- \
  '*.py' '*.sh' '*.yml' '*.yaml' 'Dockerfile*' \
  ':(exclude)scripts/security-super-gate-check.sh' \
  ':(exclude,glob)backend/**/tests/**' \
  ':(exclude,glob)backend/**/migrations/**' \
  ':(exclude,glob)backend/**/management/commands/seed_*.py'; then
  echo "ERREUR : configuration ou commande dangereuse détectée." >&2
  exit 1
fi
echo "✅ Aucun motif dangereux connu"

echo "✅ SECURITY_SUPER_GATE_20_29=OK"
