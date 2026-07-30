/**
 * Fenêtre affichée lorsqu'un like réciproque crée un match.
 *
 * La fenêtre :
 *
 * - bloque l'interaction avec l'arrière-plan ;
 * - utilise un véritable élément dialog sémantique ;
 * - n'affiche aucune donnée privée ;
 * - permet de continuer la découverte.
 */

import { useEffect, useRef } from "react";

import type { MatchCelebrationData } from "../../types/interactions";

interface MatchModalProps {
  match: MatchCelebrationData;
  onClose: () => void;
  onOpenConversation: () => void;
  isOpeningConversation?: boolean;
}

export function MatchModal({
  match,
  onClose,
  onOpenConversation,
  isOpeningConversation = false,
}: MatchModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  /**
   * Ouvre automatiquement la fenêtre lorsque le composant
   * est ajouté dans l'arbre React.
   */
  useEffect(() => {
    const dialogElement = dialogRef.current;

    if (!dialogElement) {
      return;
    }

    if (!dialogElement.open) {
      dialogElement.showModal();
    }

    return () => {
      if (dialogElement.open) {
        dialogElement.close();
      }
    };
  }, []);

  /**
   * Ferme proprement le dialog avant de prévenir le parent.
   */
  function handleClose(): void {
    const dialogElement = dialogRef.current;

    if (dialogElement?.open) {
      dialogElement.close();
    }

    onClose();
  }

  return (
    <dialog
      ref={dialogRef}
      className="match-modal"
      aria-labelledby="match-modal-title"
      onCancel={(event) => {
        event.preventDefault();
        handleClose();
      }}
    >
      <div className="match-modal__content">
        <button
          type="button"
          className="match-modal__close"
          aria-label="Fermer la fenêtre"
          onClick={handleClose}
        >
          ×
        </button>

        <div
          className="match-modal__symbol"
          aria-hidden="true"
        >
          ♥
        </div>

        <p className="section-heading__eyebrow">
          Connexion réciproque
        </p>

        <h2 id="match-modal-title">
          C’est un match avec {match.displayName} !
        </h2>

        <p>
          Vous vous êtes mutuellement appréciés. Mbolo pourra
          maintenant vous permettre de poursuivre cette connexion
          dans un espace protégé.
        </p>

        <div className="match-modal__privacy-note">
          <span aria-hidden="true">◇</span>

          <p>
            Aucune adresse e-mail ni information privée n’est
            révélée automatiquement.
          </p>
        </div>

        <div className="match-modal__actions">
          <button
            type="button"
            className="match-modal__message"
            disabled={isOpeningConversation}
            aria-busy={isOpeningConversation}
            onClick={onOpenConversation}
          >
            {isOpeningConversation
              ? "Ouverture…"
              : "Envoyer un message"}
            <span aria-hidden="true">→</span>
          </button>

          <button
            type="button"
            className="match-modal__continue"
            disabled={isOpeningConversation}
            onClick={handleClose}
          >
            Continuer la découverte
          </button>
        </div>
      </div>
    </dialog>
  );
}
