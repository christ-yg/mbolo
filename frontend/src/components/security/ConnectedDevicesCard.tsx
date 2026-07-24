import { type FormEvent, useEffect, useState } from "react";

import { normalizeApiError } from "../../api/apiError";
import {
  getConnectedDevices,
  revokeConnectedDevice,
} from "../../api/connectedDeviceService";
import type { ConnectedDevice } from "../../types/connectedDevices";

import "./ConnectedDevicesCard.css";


export function ConnectedDevicesCard() {
  const [devices, setDevices] = useState<ConnectedDevice[]>([]);
  const [passwords, setPasswords] = useState<Record<string, string>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    setDevices(await getConnectedDevices());
  }

  useEffect(() => {
    void refresh().catch(() => {
      setError("Impossible de charger les appareils connectés.");
    });
  }, []);

  async function submitRevoke(
    event: FormEvent<HTMLFormElement>,
    device: ConnectedDevice,
  ) {
    event.preventDefault();
    setBusyId(device.id);
    setMessage("");
    setError("");

    try {
      await revokeConnectedDevice(
        device.id,
        passwords[device.id] ?? "",
      );

      setPasswords((current) => ({
        ...current,
        [device.id]: "",
      }));

      await refresh();
      setMessage("L’appareil sélectionné a été déconnecté.");
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="security-action-card connected-devices-card">
      <p className="section-heading__eyebrow">Sessions actives</p>
      <h2>Appareils connectés</h2>

      <p className="connected-devices-card__intro">
        La clé de session n’est jamais affichée ni enregistrée en clair.
        Tu peux fermer individuellement un appareil que tu ne reconnais pas.
      </p>

      {message ? (
        <div className="form-alert form-alert--success" role="status">
          <span aria-hidden="true">✓</span>
          <p>{message}</p>
        </div>
      ) : null}

      {error ? (
        <div className="form-alert form-alert--error" role="alert">
          <span aria-hidden="true">!</span>
          <p>{error}</p>
        </div>
      ) : null}

      {devices.length ? (
        <div className="connected-device-list">
          {devices.map((device) => (
            <form
              key={device.id}
              className={[
                "connected-device-item",
                device.isCurrent
                  ? "connected-device-item--current"
                  : "",
              ].join(" ")}
              onSubmit={(event) => submitRevoke(event, device)}
            >
              <div className="connected-device-item__header">
                <strong>{device.device}</strong>

                {device.isCurrent ? (
                  <span className="connected-device-item__badge">
                    Appareil actuel
                  </span>
                ) : (
                  <span className="connected-device-item__badge connected-device-item__badge--other">
                    Autre session
                  </span>
                )}
              </div>

              <dl className="connected-device-item__details">
                <div>
                  <dt>Dernière activité</dt>
                  <dd>
                    {new Intl.DateTimeFormat("fr-FR", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    }).format(new Date(device.lastSeenAt))}
                  </dd>
                </div>

                <div>
                  <dt>Empreinte réseau</dt>
                  <dd>{device.ipFingerprint || "indisponible"}</dd>
                </div>
              </dl>

              {!device.isCurrent ? (
                <div className="connected-device-item__actions">
                  <label>
                    Mot de passe actuel
                    <input
                      type="password"
                      autoComplete="current-password"
                      required
                      value={passwords[device.id] ?? ""}
                      onChange={(event) =>
                        setPasswords((current) => ({
                          ...current,
                          [device.id]: event.target.value,
                        }))
                      }
                    />
                  </label>

                  <button disabled={busyId !== null}>
                    {busyId === device.id
                      ? "Déconnexion…"
                      : "Déconnecter cet appareil"}
                  </button>
                </div>
              ) : (
                <p className="connected-device-item__current-note">
                  Cette session est celle utilisée actuellement.
                </p>
              )}
            </form>
          ))}
        </div>
      ) : (
        <p>
          Aucun appareil enregistré. Reconnecte-toi pour initialiser
          le registre sécurisé.
        </p>
      )}
    </section>
  );
}
