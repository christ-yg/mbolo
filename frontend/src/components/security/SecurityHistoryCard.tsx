import { useEffect, useState } from "react";
import { getLoginActivity } from "../../api/authService";
import { getAccountSecurityEvents } from "../../api/securityEventService";
import "./SecurityHistoryCard.css";
const labels: Record<string, string> = {
  "auth.login": "Connexion au compte",
  "auth.password_change": "Mot de passe modifié",
  "auth.sessions_revoke": "Autres sessions fermées",
  "auth.email_2fa_settings": "Double authentification mise à jour",
  "auth.login_alert_email_preference": "Alertes par e-mail mises à jour",
  "auth.password_reset_confirm": "Mot de passe réinitialisé",
  "auth.account_deactivate": "Compte désactivé",
};
const outcomes: Record<string, string> = {
  success: "Réussie",
  failure: "Échec",
  blocked: "Bloquée",
  accepted: "Acceptée",
};
const reasons: Record<string, string> = {
  authenticated: "Authentification réussie",
  email_2fa_confirmed: "Code e-mail confirmé",
  invalid_credentials: "Identifiants incorrects",
  rate_limited: "Trop de tentatives",
  invalid_or_expired_code: "Code invalide ou expiré",
  password_changed: "Mot de passe modifié",
  other_sessions_revoked: "Autres sessions fermées",
  enabled: "Option activée",
  disabled: "Option désactivée",
};
function dateLabel(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Date indisponible"
    : new Intl.DateTimeFormat("fr-FR", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date);
}
type Entry = {
  id: string;
  title: string;
  detail: string;
  date: string;
  outcome?: string;
};
export function SecurityHistoryCard({
  kind,
  version,
}: {
  kind: "logins" | "events";
  version: number;
}) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [reload, setReload] = useState(0);
  const [query, setQuery] = useState("");
  const [outcome, setOutcome] = useState("all");
  const [limit, setLimit] = useState(10);
  const isLogin = kind === "logins";
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    const request: Promise<Entry[]> =
      kind === "logins"
        ? getLoginActivity().then((items) =>
            items.map((item) => ({
              id: item.id,
              title: item.device,
              date: dateLabel(item.createdAt),
              detail: `${item.method === "email_2fa" ? "Code e-mail confirmé" : item.method === "password" ? "Mot de passe" : "Autre méthode"} · Empreinte réseau : ${item.ipFingerprint || "indisponible"}`,
            })),
          )
        : getAccountSecurityEvents().then((items) =>
            items.map((item) => ({
              id: item.id,
              title: labels[item.event] ?? "Action de sécurité",
              date: dateLabel(item.createdAt),
              outcome: item.outcome,
              detail: reasons[item.reason] ?? "Autre motif de sécurité",
            })),
          );
    void request
      .then((items) => {
        if (!cancelled) {
          setEntries(items);
          setLimit(10);
        }
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [kind, version, reload]);
  const filtered = entries.filter(
    (entry) =>
      `${entry.title} ${entry.detail} ${entry.date}`
        .toLocaleLowerCase("fr")
        .includes(query.trim().toLocaleLowerCase("fr")) &&
      (isLogin ||
        outcome === "all" ||
        (outcome === "other"
          ? !outcomes[entry.outcome ?? ""]
          : entry.outcome === outcome)),
  );
  return (
    <section
      className="security-action-card security-history"
      aria-label={isLogin ? "Historique des connexions" : "Journal de sécurité"}
      aria-busy={loading}
    >
      <p className="section-heading__eyebrow">
        {isLogin ? "Activité récente" : "Journal de sécurité"}
      </p>
      <h2>
        {isLogin ? "Connexions à mon compte" : "Actions sensibles du compte"}
      </h2>
      <p>
        {isLogin
          ? "L’empreinte réseau permet de comparer les connexions sans afficher l’adresse IP exacte."
          : "Consulte le résultat et le motif des actions de sécurité."}
      </p>
      <div className="security-history__filters">
        <label>
          Rechercher {isLogin ? "une connexion" : "une action"}
          <input
            type="search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setLimit(10);
            }}
          />
        </label>
        {!isLogin && (
          <label>
            Résultat
            <select
              value={outcome}
              onChange={(event) => {
                setOutcome(event.target.value);
                setLimit(10);
              }}
            >
              <option value="all">Tous les résultats</option>
              {Object.entries(outcomes).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
              <option value="other">Non précisé</option>
            </select>
          </label>
        )}
        <button
          type="button"
          disabled={loading}
          onClick={() => setReload((value) => value + 1)}
        >
          {loading ? "Chargement…" : "Actualiser"}
        </button>
      </div>
      <small>Recherche dans les entrées récentes chargées.</small>
      {error && (
        <p role="alert">
          Impossible d’actualiser cet historique. Réessaie avec Actualiser. Les
          données déjà chargées sont conservées.
        </p>
      )}
      {!loading && !error && entries.length === 0 && (
        <p>
          {isLogin
            ? "Aucune connexion récente enregistrée."
            : "Aucune action sensible enregistrée pour le moment."}
        </p>
      )}
      {entries.length > 0 && (
        <>
          <p role="status">
            {filtered.length} résultat(s) sur {entries.length} entrée(s)
            chargée(s)
          </p>
          {filtered.length === 0 && (
            <p>Aucune entrée ne correspond aux filtres.</p>
          )}
          <ul className="security-activity-list">
            {filtered.slice(0, limit).map((entry) => (
              <li key={entry.id}>
                <strong>{entry.title}</strong>
                <span>
                  {!isLogin &&
                    `${outcomes[entry.outcome ?? ""] ?? "Non précisé"} · `}
                  {entry.date}
                </span>
                <small>{entry.detail}</small>
              </li>
            ))}
          </ul>
          {filtered.length > limit && (
            <button
              type="button"
              onClick={() => setLimit((value) => value + 10)}
            >
              Afficher la suite
            </button>
          )}
          {(query || outcome !== "all") && (
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setOutcome("all");
                setLimit(10);
              }}
            >
              Réinitialiser les filtres
            </button>
          )}
        </>
      )}
    </section>
  );
}
