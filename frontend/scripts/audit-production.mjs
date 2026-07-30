/**
 * Barrière d'audit npm de production de Mbolo.
 *
 * Objectifs de sécurité :
 * - conserver l'échec automatique pour toute vulnérabilité haute ou critique ;
 * - tolérer temporairement un seul avis React Router précisément identifié ;
 * - refuser automatiquement cette dérogation après sa date d'expiration ;
 * - documenter la décision de risque pour l'audit ISO/IEC 27001.
 *
 * Pourquoi cette exception existe :
 * GHSA-qwww-vcr4-c8h2 concerne les API RSC instables de React Router.
 * Mbolo est une SPA Vite et n'utilise aucune API RSC. La version corrigée
 * annoncée (8.3.0) n'est pas encore disponible dans le registre npm au
 * 30 juillet 2026. Revenir à 7.11.0 réintroduirait d'autres vulnérabilités
 * élevées ; cette exception ciblée est donc le choix temporaire le plus sûr.
 */

import { spawnSync } from "node:child_process";

const ALLOWED_ADVISORY_URL =
  "https://github.com/advisories/GHSA-qwww-vcr4-c8h2";
const ALLOWED_ROOT_PACKAGE = "react-router";
const ALLOWED_DEPENDENT_PACKAGE = "react-router-dom";
const WAIVER_EXPIRES_AT = new Date("2026-08-31T23:59:59Z");
const BLOCKING_SEVERITIES = new Set(["high", "critical"]);

if (new Date() > WAIVER_EXPIRES_AT) {
  console.error(
    "La dérogation temporaire React Router a expiré. " +
      "Mettre à niveau vers une version corrigée avant de relancer la CI.",
  );
  process.exit(1);
}

const audit = spawnSync(
  "npm",
  ["audit", "--omit=dev", "--audit-level=high", "--json"],
  {
    encoding: "utf8",
    shell: process.platform === "win32",
  },
);

if (audit.error) {
  console.error("Impossible d'exécuter npm audit :", audit.error.message);
  process.exit(1);
}

let report;

try {
  report = JSON.parse(audit.stdout);
} catch {
  console.error("npm audit n'a pas retourné un rapport JSON exploitable.");
  console.error(audit.stderr);
  process.exit(1);
}

const vulnerabilities = Object.values(report.vulnerabilities ?? {});

const rootWaiverIsExact = (vulnerability) => {
  if (vulnerability.name !== ALLOWED_ROOT_PACKAGE) {
    return false;
  }

  const directAdvisories = vulnerability.via.filter(
    (item) => typeof item === "object" && item !== null,
  );

  return (
    directAdvisories.length === 1 &&
    directAdvisories[0].url === ALLOWED_ADVISORY_URL
  );
};

const dependentWaiverIsExact = (vulnerability) =>
  vulnerability.name === ALLOWED_DEPENDENT_PACKAGE &&
  vulnerability.via.length === 1 &&
  vulnerability.via[0] === ALLOWED_ROOT_PACKAGE;

const blockingVulnerabilities = vulnerabilities.filter((vulnerability) => {
  if (!BLOCKING_SEVERITIES.has(vulnerability.severity)) {
    return false;
  }

  return !(
    rootWaiverIsExact(vulnerability) ||
    dependentWaiverIsExact(vulnerability)
  );
});

if (blockingVulnerabilities.length > 0) {
  console.error("Vulnérabilités de production non autorisées détectées :");

  for (const vulnerability of blockingVulnerabilities) {
    console.error(`- ${vulnerability.name} (${vulnerability.severity})`);
  }

  process.exit(1);
}

const exactRootWaiver = vulnerabilities.some(rootWaiverIsExact);

if (!exactRootWaiver && audit.status !== 0) {
  console.error(
    "npm audit a échoué pour une raison qui ne correspond pas " +
      "à la dérogation documentée.",
  );
  process.exit(1);
}

if (exactRootWaiver) {
  console.warn(
    "Dérogation temporaire appliquée uniquement à GHSA-qwww-vcr4-c8h2. " +
      "Mbolo n'utilise pas les API RSC instables concernées. " +
      "Expiration : 31 août 2026.",
  );
}

console.log(
  "Audit npm validé : aucune autre vulnérabilité haute ou critique " +
    "n'est présente dans les dépendances de production.",
);
