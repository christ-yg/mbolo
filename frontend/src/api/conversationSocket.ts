/**
 * Client WebSocket d'une conversation privée Mbolo.
 *
 * Ce module est volontairement indépendant de React.
 * Il gère uniquement :
 *
 * - la création de la connexion WebSocket ;
 * - la réception des événements JSON ;
 * - l'envoi d'événements ;
 * - la fermeture volontaire ;
 * - la reconnexion automatique après une coupure involontaire.
 */

/**
 * États publics possibles de la connexion.
 */
export type ConversationSocketState =
  | "connecting"
  | "open"
  | "closed";

/**
 * Structure minimale d'un événement WebSocket.
 *
 * Chaque événement possède obligatoirement un nom dans `event`.
 * Les autres propriétés varient selon le type d'événement.
 *
 * Exemples :
 *
 * {
 *   event: "message.created",
 *   message: { ... }
 * }
 *
 * {
 *   event: "typing.updated",
 *   other_is_typing: true
 * }
 */
export interface ConversationSocketEvent {
  event: string;
  [key: string]: unknown;
}

/**
 * Construit l'URL WebSocket de la conversation.
 *
 * En développement :
 *
 * http://127.0.0.1:5173
 * devient
 * ws://127.0.0.1:8000
 *
 * En production HTTPS :
 *
 * https://mbolo.example
 * devient
 * wss://...
 */
function buildSocketUrl(
  conversationId: string,
): string {
  const protocol =
    window.location.protocol === "https:"
      ? "wss:"
      : "ws:";

  /**
   * VITE_WEBSOCKET_HOST permet de configurer le serveur
   * WebSocket sans modifier le code source.
   *
   * Exemple dans un fichier .env :
   *
   * VITE_WEBSOCKET_HOST=api.mbolo.example
   *
   * En développement local, la valeur par défaut est
   * 127.0.0.1:8000.
   */
  const configuredHost =
    import.meta.env.VITE_WEBSOCKET_HOST?.trim();

  const backendHost =
    configuredHost || "127.0.0.1:8000";

  const encodedConversationId =
    encodeURIComponent(conversationId);

  return (
    `${protocol}//${backendHost}` +
    `/ws/conversations/${encodedConversationId}/`
  );
}

/**
 * Gère une connexion WebSocket privée vers une conversation.
 *
 * Cette classe ne stocke aucun message dans le navigateur.
 * Les messages durables restent enregistrés dans PostgreSQL
 * par le backend Django.
 */
export class ConversationSocket {
  /**
   * Identifiant UUID de la conversation.
   */
  private readonly conversationId: string;

  /**
   * Fonction appelée lorsqu'un événement JSON est reçu.
   */
  private readonly onEvent: (
    event: ConversationSocketEvent,
  ) => void;

  /**
   * Fonction appelée lorsque l'état de la connexion change.
   */
  private readonly onStateChange: (
    state: ConversationSocketState,
  ) => void;

  /**
   * Instance WebSocket actuellement utilisée.
   *
   * null signifie qu'aucune connexion active n'est conservée.
   */
  private socket: WebSocket | null = null;

  /**
   * Identifiant du temporisateur de reconnexion.
   */
  private reconnectTimer: number | null = null;

  /**
   * Nombre de tentatives consécutives de reconnexion.
   *
   * Cette valeur permet d'augmenter progressivement le délai
   * entre les tentatives.
   */
  private reconnectAttempt = 0;

  /**
   * Indique si la connexion a été volontairement fermée.
   *
   * Lorsqu'une page React est démontée, nous fermons le socket.
   * Dans ce cas, il ne faut surtout pas lancer une reconnexion.
   */
  private intentionallyClosed = false;

  /**
   * Initialise le gestionnaire WebSocket.
   *
   * La connexion n'est pas ouverte immédiatement.
   * Il faut appeler ensuite `connect()`.
   */
  constructor(
    conversationId: string,
    onEvent: (
      event: ConversationSocketEvent,
    ) => void,
    onStateChange: (
      state: ConversationSocketState,
    ) => void,
  ) {
    this.conversationId = conversationId;
    this.onEvent = onEvent;
    this.onStateChange = onStateChange;
  }

  /**
   * Ouvre la connexion WebSocket.
   */
  connect(): void {
    /**
     * Évite d'ouvrir deux connexions simultanées avec
     * la même instance.
     */
    if (
      this.socket?.readyState === WebSocket.OPEN ||
      this.socket?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    this.intentionallyClosed = false;
    this.onStateChange("connecting");

    const socketUrl =
      buildSocketUrl(this.conversationId);

    const socket =
      new WebSocket(socketUrl);

    this.socket = socket;

    /**
     * Connexion acceptée par Django Channels.
     */
    socket.onopen = () => {
      /**
       * Nous vérifions que cet événement appartient encore
       * au socket courant.
       *
       * Une ancienne connexion pourrait parfois terminer
       * son cycle après qu'une nouvelle a déjà été créée.
       */
      if (this.socket !== socket) {
        socket.close(
          1000,
          "stale_connection",
        );
        return;
      }

      this.reconnectAttempt = 0;
      this.onStateChange("open");
    };

    /**
     * Réception d'une trame envoyée par Django Channels.
     */
    socket.onmessage = (
      messageEvent: MessageEvent,
    ) => {
      try {
        const parsed =
          JSON.parse(
            String(messageEvent.data),
          ) as ConversationSocketEvent;

        /**
         * Un événement valide doit posséder un nom textuel.
         */
        if (
          typeof parsed !== "object" ||
          parsed === null ||
          typeof parsed.event !== "string"
        ) {
          return;
        }

        this.onEvent(parsed);
      } catch {
        /**
         * Une trame non JSON ou malformée est ignorée.
         *
         * Elle ne doit jamais faire planter la page React.
         */
      }
    };

    /**
     * Fermeture de la connexion.
     */
    socket.onclose = () => {
      /**
       * Ignore la fermeture d'une ancienne instance qui
       * n'est plus le socket courant.
       */
      if (this.socket !== socket) {
        return;
      }

      this.socket = null;
      this.onStateChange("closed");

      /**
       * Une reconnexion est planifiée seulement lorsque
       * la fermeture n'a pas été demandée par l'application.
       */
      if (!this.intentionallyClosed) {
        this.scheduleReconnect();
      }
    };

    /**
     * Une erreur WebSocket est généralement suivie d'un
     * événement `close`.
     *
     * Nous fermons explicitement la connexion afin de
     * déclencher le mécanisme normal de reconnexion.
     */
    socket.onerror = () => {
      if (this.socket === socket) {
        socket.close();
      }
    };
  }

  /**
   * Envoie un événement JSON au serveur.
   *
   * Retourne :
   *
   * - true si l'événement a été envoyé ;
   * - false si la connexion n'est pas encore ouverte.
   */
  send(
    event: ConversationSocketEvent,
  ): boolean {
    if (
      this.socket?.readyState !==
      WebSocket.OPEN
    ) {
      return false;
    }

    try {
      this.socket.send(
        JSON.stringify(event),
      );

      return true;
    } catch {
      return false;
    }
  }

  /**
   * Ferme volontairement la connexion.
   *
   * Cette méthode doit être appelée lorsque l'utilisateur :
   *
   * - quitte la conversation ;
   * - change de page ;
   * - se déconnecte ;
   * - détruit le composant React associé.
   */
  close(): void {
    this.intentionallyClosed = true;

    if (this.reconnectTimer !== null) {
      window.clearTimeout(
        this.reconnectTimer,
      );

      this.reconnectTimer = null;
    }

    const currentSocket = this.socket;

    this.socket = null;

    if (
      currentSocket &&
      (
        currentSocket.readyState ===
          WebSocket.OPEN ||
        currentSocket.readyState ===
          WebSocket.CONNECTING
      )
    ) {
      currentSocket.close(
        1000,
        "page_closed",
      );
    }

    this.onStateChange("closed");
  }

  /**
   * Planifie une reconnexion avec délai progressif.
   *
   * Délais approximatifs :
   *
   * tentative 1 : 1 seconde
   * tentative 2 : 2 secondes
   * tentative 3 : 4 secondes
   * tentative 4 : 8 secondes
   * suivantes   : 15 secondes maximum
   *
   * Cette stratégie évite de saturer le serveur lorsqu'il
   * est momentanément indisponible.
   */
  private scheduleReconnect(): void {
    /**
     * Empêche plusieurs temporisateurs de reconnexion
     * d'exister en même temps.
     */
    if (this.reconnectTimer !== null) {
      return;
    }

    const exponentialDelay =
      1000 * 2 ** this.reconnectAttempt;

    const delay =
      Math.min(
        exponentialDelay,
        15000,
      );

    this.reconnectAttempt += 1;

    this.reconnectTimer =
      window.setTimeout(() => {
        this.reconnectTimer = null;

        if (this.intentionallyClosed) {
          return;
        }

        this.connect();
      }, delay);
  }
}
