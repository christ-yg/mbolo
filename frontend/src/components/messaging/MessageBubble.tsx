/**
 * Bulle individuelle de la messagerie Mbolo.
 *
 * Le backend indique avec is_mine si le message appartient
 * à l'utilisateur actuellement connecté.
 */

import type {
  MessageItem,
} from "../../types/messaging";

interface MessageBubbleProps {
  message: MessageItem;
}

function formatMessageTime(
  value: string,
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(date);
}

function formatMessageDateTime(
  value: string,
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}

export function MessageBubble({
  message,
}: MessageBubbleProps) {
  const formattedTime =
    formatMessageTime(message.created_at);

  const formattedDateTime =
    formatMessageDateTime(
      message.created_at,
    );

  return (
    <article
      className={
        message.is_mine
          ? "message-bubble message-bubble--mine"
          : "message-bubble message-bubble--theirs"
      }
      aria-label={
        message.is_mine
          ? "Ton message"
          : "Message reçu"
      }
    >
      <p className="message-bubble__body">
        {message.body}
      </p>

      <footer className="message-bubble__footer">
        <time
          className="message-bubble__time"
          dateTime={message.created_at}
          title={formattedDateTime}
        >
          {formattedTime}
        </time>

        {message.is_mine && message.read_receipts_available ? (
          <span
            className={
              message.is_read
                ? "message-bubble__read-status message-bubble__read-status--read"
                : "message-bubble__read-status"
            }
            aria-label={
              message.is_read
                ? "Message lu"
                : "Message envoyé"
            }
          >
            <span aria-hidden="true">
              {message.is_read ? "✓✓" : "✓"}
            </span>
            {message.is_read ? "Lu" : "Envoyé"}
          </span>
        ) : message.is_mine ? (
          <span
            className="message-bubble__read-status"
            title="Accusés de lecture disponibles avec Mbolo Plus et Prestige"
          >
            <span aria-hidden="true">✓</span>
            Envoyé
          </span>
        ) : null}
      </footer>
    </article>
  );
}
