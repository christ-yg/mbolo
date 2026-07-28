/**
 * Page de confirmation de l'adresse e-mail Mbolo.
 *
 * Cette page récupère le jeton signé présent dans l'URL :
 *
 *     /verify-email?token=...
 *
 * Elle transmet ensuite ce jeton au backend Django afin de
 * confirmer que l'adresse e-mail appartient bien à l'utilisateur.
 *
 * Mesures appliquées :
 *
 * - le jeton n'est pas enregistré dans localStorage ;
 * - le jeton n'est pas enregistré dans sessionStorage ;
 * - le jeton est uniquement conservé temporairement en mémoire ;
 * - l'appel POST est protégé par CSRF ;
 * - les erreurs techniques sont normalisées avant affichage.
 */

import {
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Link,
  useSearchParams,
} from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { verifyEmailAddress } from "../../api/authService";

import "./AuthPagesPremium.css";

/**
 * États possibles de la vérification.
 *
 * loading :
 *     la requête est en cours ;
 *
 * success :
 *     Django a confirmé l'adresse e-mail ;
 *
 * error :
 *     le jeton est absent, invalide, expiré ou déjà inutilisable.
 */
type VerificationStatus =
  | "loading"
  | "success"
  | "error";

export function VerifyEmailPage() {
  /**
   * useSearchParams permet de lire les paramètres situés
   * après le point d'interrogation dans l'URL.
   *
   * Exemple :
   *
   *     /verify-email?token=abc123
   */
  const [searchParams] = useSearchParams();

  /**
   * État visuel actuel de la page.
   */
  const [status, setStatus] =
    useState<VerificationStatus>("loading");

  /**
   * Message présenté à l'utilisateur.
   */
  const [message, setMessage] = useState(
    "Vérification sécurisée de ton adresse e-mail…",
  );

  /**
   * Empêche plusieurs appels involontaires pendant le même
   * cycle d'affichage du composant.
   *
   * React StrictMode peut exécuter certains effets plus d'une fois
   * en environnement de développement afin de détecter les effets
   * de bord non maîtrisés.
   */
  const hasStartedVerification = useRef(false);

  useEffect(() => {
    /**
     * Si la vérification a déjà été lancée pour cette instance
     * du composant, nous ne faisons rien.
     */
    if (hasStartedVerification.current) {
      return;
    }

    hasStartedVerification.current = true;

    /**
     * searchParams.get() retourne :
     *
     * - une chaîne si le paramètre existe ;
     * - null si le paramètre est absent.
     *
     * trim() supprime les espaces accidentels.
     * L'opérateur ?. évite d'appeler trim() sur null.
     */
    const rawToken = searchParams.get("token")?.trim();

    /**
     * Nous refusons immédiatement une URL sans jeton.
     *
     * Après ce contrôle, rawToken est considéré comme une chaîne
     * non vide dans ce bloc d'exécution.
     */
    if (!rawToken) {
      setStatus("error");
      setMessage(
        "Le lien de vérification est incomplet ou invalide.",
      );

      return;
    }

    /**
     * Nous créons une constante explicitement typée string.
     *
     * Cette copie résout l'erreur TypeScript :
     *
     *     string | undefined is not assignable to string
     *
     * TypeScript sait maintenant avec certitude que
     * verificationToken est toujours une chaîne.
     */
    const verificationToken: string = rawToken;

    /**
     * Fonction asynchrone interne chargée de communiquer
     * avec le backend Django.
     */
    async function confirmEmail(): Promise<void> {
      try {
        const result = await verifyEmailAddress({
          token: verificationToken,
        });

        /**
         * Le backend a accepté le jeton.
         */
        if (result.isEmailVerified) {
          setStatus("success");
          setMessage(
            `L’adresse ${result.email} est maintenant vérifiée.`,
          );

          return;
        }

        /**
         * Cas défensif :
         * la requête a réussi, mais Django n'indique pas que
         * l'adresse est effectivement vérifiée.
         */
        setStatus("error");
        setMessage(
          "L’adresse e-mail n’a pas pu être confirmée.",
        );
      } catch (error: unknown) {
        /**
         * Toutes les erreurs Axios ou Django sont transformées
         * en structure stable avant affichage.
         */
        const normalizedError = normalizeApiError(error);

        setStatus("error");
        setMessage(normalizedError.message);
      }
    }

    /**
     * useEffect ne peut pas être directement async.
     *
     * Nous appelons donc la fonction asynchrone avec void afin
     * d'indiquer explicitement que sa Promise n'est pas retournée
     * par l'effet React.
     */
    void confirmEmail();
  }, [searchParams]);

  return (
    <main className="email-verification-page">
      <section className="email-verification-card">
        <div
          className={[
            "email-verification-card__icon",
            `email-verification-card__icon--${status}`,
          ].join(" ")}
          aria-hidden="true"
        >
          {status === "loading"
            ? "…"
            : status === "success"
              ? "✓"
              : "!"}
        </div>

        <p className="section-heading__eyebrow">
          Vérification de sécurité
        </p>

        <h1>
          {status === "loading"
            ? "Vérification en cours"
            : status === "success"
              ? "Adresse confirmée"
              : "Vérification impossible"}
        </h1>

        <p
          className="email-verification-card__message"
          role={status === "error" ? "alert" : "status"}
        >
          {message}
        </p>

        {status === "success" ? (
          <Link
            className="link-button link-button--primary"
            to="/login"
            replace
          >
            Continuer vers la connexion
            <span aria-hidden="true">→</span>
          </Link>
        ) : null}

        {status === "error" ? (
          <div className="email-verification-card__actions">
            <Link
              className="link-button link-button--secondary"
              to="/register"
            >
              Créer un nouveau compte
            </Link>

            <Link
              className="email-verification-card__text-link"
              to="/login"
            >
              Retour à la connexion
            </Link>
          </div>
        ) : null}

        {status === "loading" ? (
          <p className="email-verification-card__note">
            Ne ferme pas cette page pendant la vérification.
          </p>
        ) : null}
      </section>
    </main>
  );
}
