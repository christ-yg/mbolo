const interactiveSelector = [
  ".discovery-profile-card",
  ".discovery-information-card",
  ".match-card-with-detail",
  ".conversation-list-item",
  ".message-bubble",
].join(",");

type Surface = HTMLElement & { dataset: DOMStringMap };

/** Adds subtle pointer depth without taking over keyboard or touch behaviour. */
export function bindInteractiveSurfaceMotion(root: ParentNode = document) {
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (!finePointer.matches || reducedMotion.matches) return () => undefined;

  const cleanups: Array<() => void> = [];
  root.querySelectorAll<Surface>(interactiveSelector).forEach((surface) => {
    let frame = 0;

    const reset = () => {
      cancelAnimationFrame(frame);
      surface.style.setProperty("--surface-tilt-x", "0deg");
      surface.style.setProperty("--surface-tilt-y", "0deg");
      surface.style.setProperty("--surface-glow-x", "50%");
      surface.style.setProperty("--surface-glow-y", "50%");
    };

    const move = (event: PointerEvent) => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const bounds = surface.getBoundingClientRect();
        const x = (event.clientX - bounds.left) / bounds.width;
        const y = (event.clientY - bounds.top) / bounds.height;
        surface.style.setProperty("--surface-tilt-x", `${(0.5 - y) * 4}deg`);
        surface.style.setProperty("--surface-tilt-y", `${(x - 0.5) * 5}deg`);
        surface.style.setProperty("--surface-glow-x", `${x * 100}%`);
        surface.style.setProperty("--surface-glow-y", `${y * 100}%`);
      });
    };

    surface.dataset.mboloInteractive = "true";
    surface.addEventListener("pointermove", move);
    surface.addEventListener("pointerleave", reset);
    cleanups.push(() => {
      cancelAnimationFrame(frame);
      surface.removeEventListener("pointermove", move);
      surface.removeEventListener("pointerleave", reset);
      delete surface.dataset.mboloInteractive;
      surface.style.removeProperty("--surface-tilt-x");
      surface.style.removeProperty("--surface-tilt-y");
      surface.style.removeProperty("--surface-glow-x");
      surface.style.removeProperty("--surface-glow-y");
    });
  });

  return () => cleanups.forEach((cleanup) => cleanup());
}
