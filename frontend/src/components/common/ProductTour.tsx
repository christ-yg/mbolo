import { useEffect, useState } from "react";

import "./ProductTour.css";

const steps = [
  { icon: "♥", eyebrow: "RENCONTRES INTELLIGENTES", title: "Des connexions qui ont du sens", body: "Compatibilité, intentions et centres d’intérêt donnent du contexte à chaque profil.", points: ["Découverte locale", "Profils vérifiés", "Compatibilité"] },
  { icon: "◆", eyebrow: "TRUST BY DESIGN", title: "Une sécurité visible et rassurante", body: "MBOLO intègre la protection du compte, la modération et la confidentialité au parcours.", points: ["2FA", "Signalement", "Contrôle des données"] },
  { icon: "✦", eyebrow: "MODÈLE DURABLE", title: "Une offre Premium adaptée au Gabon", body: "Plus, Prestige, Boost et Mobile Money bâtissent une monétisation claire et évolutive.", points: ["Airtel Money", "Moov Money", "Infrastructure scalable"] },
] as const;

export function ProductTour() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!open) return undefined;
    const close = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [open]);

  const current = steps[step];
  function next() {
    if (step === steps.length - 1) { setOpen(false); setStep(0); }
    else setStep((value) => value + 1);
  }

  return (
    <>
      <button type="button" className="product-tour-trigger" onClick={() => setOpen(true)} aria-label="Ouvrir la visite guidée MBOLO"><span aria-hidden="true">✦</span><span>Visite guidée</span></button>
      {open ? (
        <div className="product-tour-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setOpen(false)}>
          <section className="product-tour" role="dialog" aria-modal="true" aria-labelledby="product-tour-title">
            <button type="button" className="product-tour__close" onClick={() => setOpen(false)} aria-label="Fermer">×</button>
            <div className="product-tour__icon" aria-hidden="true">{current.icon}</div>
            <p className="product-tour__eyebrow">{current.eyebrow}</p>
            <h2 id="product-tour-title">{current.title}</h2>
            <p className="product-tour__body">{current.body}</p>
            <div className="product-tour__points">{current.points.map((point) => <span key={point}>✓ {point}</span>)}</div>
            <div className="product-tour__footer">
              <div className="product-tour__progress" aria-label={`Étape ${step + 1} sur ${steps.length}`}>{steps.map((_, index) => <span key={index} className={index === step ? "is-active" : ""} />)}</div>
              <button type="button" onClick={next}>{step === steps.length - 1 ? "Explorer MBOLO" : "Continuer →"}</button>
            </div>
          </section>
        </div>
      ) : null}
    </>
  );
}
