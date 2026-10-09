import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { bindInteractiveSurfaceMotion } from "./interactiveSurfaceMotion";

const revealSelector = [
  ".route-stage main > section",
  ".route-stage main > article",
  ".route-stage main > form",
  ".route-stage main > header",
  ".route-stage main > div",
].join(",");

/** Progressive motion shared by every page, with reduced-motion support. */
export function PremiumMotion() {
  const location = useLocation();

  useEffect(() => {
    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const elements = [
      ...document.querySelectorAll<HTMLElement>(revealSelector),
    ];
    const releaseInteractiveMotion = bindInteractiveSurfaceMotion();

    if (reducedMotion || !("IntersectionObserver" in window)) {
      elements.forEach((element) => element.classList.add("is-motion-visible"));
      return releaseInteractiveMotion;
    }

    elements.forEach((element, index) => {
      element.classList.add("mbolo-motion-reveal");
      element.style.setProperty("--motion-order", String(index % 6));
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-motion-visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -8%", threshold: 0.08 },
    );

    elements.forEach((element) => observer.observe(element));
    return () => {
      observer.disconnect();
      releaseInteractiveMotion();
    };
  }, [location.pathname]);

  return null;
}
