/**
 * Carte d'une conversation dans la liste de messagerie.
 *
 * La carte reste volontairement purement visuelle :
 * les permissions et l'accès à la conversation sont validés par Django.
 */

import { Link } from "react-router-dom";

import type { ConversationItem } from "../../types/messaging";


interface ConversationCardProps {
  conversation: ConversationItem;
}


function getInitials(displayName: string): string {
  const parts = displayName
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);

  if (parts.length === 0) {
    return "M";
  }

  return parts
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}


function getPrimaryPhotoUrl(conversation: ConversationItem): string | null {
  const photo = [...conversation.other_profile.photos]
    .sort(
      (first, second) =>
        Number(second.is_primary) - Number(first.is_primary) ||
        first.position - second.position,
    )
    .find((item) => Boolean(item.image_url));

  return photo?.image_url ?? null;
}


function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  const sameDay = (first: Date, second: Date) =>
    first.getFullYear() === second.getFullYear() &&
    first.getMonth() === second.getMonth() &&
    first.getDate() === second.getDate();

  if (sameDay(date, today)) {
    return new Intl.DateTimeFormat("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }

  if (sameDay(date, yesterday)) {
    return "Hier";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
  }).format(date);
}


export function ConversationCard({ conversation }: ConversationCardProps) {
  const profile = conversation.other_profile;
  const lastMessage = conversation.last_message;
  const primaryPhotoUrl = getPrimaryPhotoUrl(conversation);
  const hasUnreadMessages = conversation.unread_count > 0;

  return (
    <Link
      className={
        hasUnreadMessages
          ? "conversation-card conversation-card--unread"
          : "conversation-card"
      }
      to={`/messages/${conversation.id}`}
      aria-label={`Ouvrir la conversation avec ${profile.display_name}`}
    >
      <div className="conversation-card__avatar-wrap">
        <div
          className="conversation-card__avatar"
          aria-label={`Photo de ${profile.display_name}`}
        >
          {primaryPhotoUrl ? (
            <img src={primaryPhotoUrl} alt="" />
          ) : (
            getInitials(profile.display_name)
          )}
        </div>

        {conversation.other_presence.is_online ? (
          <span className="conversation-card__online-dot" aria-label="En ligne" />
        ) : null}
      </div>

      <div className="conversation-card__content">
        <div className="conversation-card__heading">
          <div className="conversation-card__identity">
            <h3>{profile.display_name}</h3>

            {profile.is_verified ? (
              <span
                className="conversation-card__verified"
                title="Profil vérifié"
                aria-label="Profil vérifié"
              >
                ✓
              </span>
            ) : null}
          </div>

          <time dateTime={lastMessage?.created_at ?? conversation.updated_at}>
            {formatDate(lastMessage?.created_at ?? conversation.updated_at)}
          </time>
        </div>

        <p className="conversation-card__preview">
          {lastMessage ? (
            <>
              {lastMessage.is_mine ? <strong>Toi : </strong> : null}
              {lastMessage.body}
            </>
          ) : (
            "Le match est créé. Envoie ton premier message."
          )}
        </p>

        <div className="conversation-card__footer">
          <div className="conversation-card__metadata">
            <span>{profile.city}</span>
            <span aria-hidden="true">·</span>
            <span>{profile.age} ans</span>
          </div>

          <span className="conversation-card__action">
            Ouvrir <span aria-hidden="true">→</span>
          </span>
        </div>
      </div>
    </Link>
  );
}
