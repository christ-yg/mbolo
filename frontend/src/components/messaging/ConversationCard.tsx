/**
 * Carte d'une conversation dans la liste de messagerie.
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


function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const today = new Date();

  const isToday =
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate();

  if (isToday) {
    return new Intl.DateTimeFormat("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }

  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
  }).format(date);
}


export function ConversationCard({
  conversation,
}: ConversationCardProps) {
  const profile = conversation.other_profile;
  const lastMessage = conversation.last_message;

  return (
    <Link
      className="conversation-card"
      to={`/messages/${conversation.id}`}
    >
      <div
        className="conversation-card__avatar"
        aria-hidden="true"
      >
        {getInitials(profile.display_name)}
      </div>

      <div className="conversation-card__content">
        <div className="conversation-card__heading">
          <div>
            <h2>{profile.display_name}</h2>

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

          <time
            dateTime={
              lastMessage?.created_at ??
              conversation.updated_at
            }
          >
            {formatDate(
              lastMessage?.created_at ??
              conversation.updated_at,
            )}
          </time>
        </div>

        <p className="conversation-card__preview">
          {lastMessage ? (
            <>
              {lastMessage.is_mine ? (
                <strong>Vous : </strong>
              ) : null}

              {lastMessage.body}
            </>
          ) : (
            "Vous pouvez maintenant commencer la conversation."
          )}
        </p>

        <div className="conversation-card__metadata">
          <span>{profile.city}</span>
          <span aria-hidden="true">·</span>
          <span>{profile.age} ans</span>
        </div>
      </div>

      <span
        className="conversation-card__arrow"
        aria-hidden="true"
      >
        →
      </span>
    </Link>
  );
}
