/**
 * Bulle visuelle d'un message privé.
 */

import type { MessageItem } from "../../types/messaging";


interface MessageBubbleProps {
  message: MessageItem;
}


function formatMessageTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}


export function MessageBubble({
  message,
}: MessageBubbleProps) {
  return (
    <article
      className={
        message.is_mine
          ? "message-bubble message-bubble--mine"
          : "message-bubble message-bubble--theirs"
      }
    >
      <p>{message.body}</p>

      <time dateTime={message.created_at}>
        {formatMessageTime(message.created_at)}
      </time>
    </article>
  );
}
