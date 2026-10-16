import { useEffect, useRef } from "react";

const finePointer = "(hover: hover) and (pointer: fine)";
const reducedMotion = "(prefers-reduced-motion: reduce)";

/** Pointer-driven depth without an animation dependency or React re-renders. */
export function usePremiumStageMotion(enabled: boolean) {
  const stageRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const stage = stageRef.current;
    if (
      !enabled
      || !stage
      || !window.matchMedia(finePointer).matches
      || window.matchMedia(reducedMotion).matches
    ) return;

    const cleanups: Array<() => void> = [];
    const cards = stage.querySelectorAll<HTMLElement>(
      ".premium-redesign-plan-card",
    );

    cards.forEach((card) => {
      let frame = 0;
      const move = (event: PointerEvent) => {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
          const bounds = card.getBoundingClientRect();
          const x = (event.clientX - bounds.left) / bounds.width;
          const y = (event.clientY - bounds.top) / bounds.height;
          card.style.setProperty("--glow-x", `${x * 100}%`);
          card.style.setProperty("--glow-y", `${y * 100}%`);
          card.style.setProperty("--tilt-x", `${(0.5 - y) * 7}deg`);
          card.style.setProperty("--tilt-y", `${(x - 0.5) * 8}deg`);
        });
      };
      const reset = () => {
        cancelAnimationFrame(frame);
        card.style.setProperty("--tilt-x", "0deg");
        card.style.setProperty("--tilt-y", "0deg");
        card.style.setProperty("--glow-x", "50%");
        card.style.setProperty("--glow-y", "0%");
      };
      card.addEventListener("pointermove", move);
      card.addEventListener("pointerleave", reset);
      cleanups.push(() => {
        cancelAnimationFrame(frame);
        card.removeEventListener("pointermove", move);
        card.removeEventListener("pointerleave", reset);
      });
    });

    const hero = stage.querySelector<HTMLElement>(".premium-redesign-hero");
    if (hero) {
      const move = (event: PointerEvent) => {
        const bounds = hero.getBoundingClientRect();
        hero.style.setProperty(
          "--hero-x",
          `${((event.clientX - bounds.left) / bounds.width) * 100}%`,
        );
        hero.style.setProperty(
          "--hero-y",
          `${((event.clientY - bounds.top) / bounds.height) * 100}%`,
        );
      };
      hero.addEventListener("pointermove", move);
      cleanups.push(() => hero.removeEventListener("pointermove", move));
    }

    return () => cleanups.forEach((cleanup) => cleanup());
  }, [enabled]);

  return stageRef;
}
