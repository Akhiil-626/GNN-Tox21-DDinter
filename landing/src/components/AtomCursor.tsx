import React, { useEffect, useRef } from "react";

export const AtomCursor: React.FC = () => {
  const rootRef = useRef<HTMLDivElement>(null);
  const nucleusRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const electronRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Check fine pointer and hover capability
    const hasFinePointer = window.matchMedia("(pointer: fine) and (hover: hover)").matches;
    if (!hasFinePointer) return;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const root = rootRef.current;
    const nucleus = nucleusRef.current;
    const ring = ringRef.current;
    const electron = electronRef.current;
    if (!root || !nucleus || !ring) return;

    let pointerX = -100;
    let pointerY = -100;
    let ringX = -100;
    let ringY = -100;
    let lastMoveTime = 0;
    let rafId: number | null = null;
    let isField = false;
    let isHovered = false;
    let arcPlaying = false;

    let lastX = 0;
    let lastY = 0;
    let velocity = 0;
    let angle = 0;
    const baseAngleSpeed = (2 * Math.PI) / 144;

    function render(now: number) {
      if (!nucleus || !ring) return;

      if (now - lastMoveTime > 500 && Math.abs(pointerX - ringX) < 0.5 && Math.abs(pointerY - ringY) < 0.5) {
        rafId = null;
        return;
      }

      velocity *= 0.92;
      const speedMultiplier = Math.min(3, 1 + velocity * 0.12);

      if (prefersReducedMotion) {
        ringX = pointerX;
        ringY = pointerY;
      } else {
        ringX += (pointerX - ringX) * 0.18;
        ringY += (pointerY - ringY) * 0.18;

        angle += baseAngleSpeed * speedMultiplier;
        const radius = isHovered ? 22 : 14;
        const elX = Math.cos(angle) * radius;
        const elY = Math.sin(angle) * radius;
        if (electron) {
          electron.style.transform = `translate3d(${elX}px, ${elY}px, 0)`;
        }
      }

      nucleus.style.transform = `translate3d(${pointerX}px, ${pointerY}px, 0)`;
      ring.style.transform = `translate3d(${ringX}px, ${ringY}px, 0)`;

      rafId = requestAnimationFrame(render);
    }

    function startRaf() {
      if (!rafId) {
        lastMoveTime = performance.now();
        rafId = requestAnimationFrame(render);
      }
    }

    const onPointerMove = (e: PointerEvent) => {
      if (root.style.display === "none") {
        root.style.display = "block";
        document.documentElement.classList.add("cf-cursor-hidden");
        ringX = e.clientX;
        ringY = e.clientY;
      }

      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      velocity = Math.sqrt(dx * dx + dy * dy);
      lastX = e.clientX;
      lastY = e.clientY;

      pointerX = e.clientX;
      pointerY = e.clientY;
      lastMoveTime = performance.now();
      startRaf();
    };

    const onPointerOver = (e: PointerEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target) return;

      if (target.closest("input, textarea, select")) {
        isField = true;
        root.style.opacity = "0";
        return;
      } else if (isField) {
        isField = false;
        root.style.opacity = "1";
      }

      if (target.closest("a, button, [role=\"button\"], summary, label[for], select")) {
        if (!isHovered) {
          isHovered = true;
          root.classList.add("cf-cursor-hover");
        }
      }
    };

    const onPointerOut = (e: PointerEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target) return;

      if (target.closest("input, textarea, select")) {
        isField = false;
        root.style.opacity = "1";
      }

      const rel = e.relatedTarget as HTMLElement | null;
      if (!rel || !rel.closest("a, button, [role=\"button\"], summary, label[for], select")) {
        if (isHovered) {
          isHovered = false;
          root.classList.remove("cf-cursor-hover");
        }
      }
    };

    const onPointerDown = () => {
      if (isField) return;
      root.classList.add("cf-cursor-pressed");

      if (!prefersReducedMotion && !arcPlaying) {
        arcPlaying = true;
        const arc = document.createElement("div");
        arc.className = "cf-cursor-arc";
        arc.style.transform = `translate3d(${pointerX}px, ${pointerY}px, 0)`;
        root.appendChild(arc);

        setTimeout(() => {
          arc.remove();
          arcPlaying = false;
        }, 400);
      }
    };

    const onPointerUp = () => {
      setTimeout(() => {
        root.classList.remove("cf-cursor-pressed");
      }, 120);
    };

    const resetState = () => {
      isHovered = false;
      isField = false;
      root.classList.remove("cf-cursor-hover");
      root.classList.remove("cf-cursor-pressed");
      root.style.opacity = "1";
    };

    window.addEventListener("pointermove", onPointerMove, { passive: true });
    document.addEventListener("pointerover", onPointerOver, { passive: true });
    document.addEventListener("pointerout", onPointerOut, { passive: true });
    window.addEventListener("pointerdown", onPointerDown, { passive: true });
    window.addEventListener("pointerup", onPointerUp, { passive: true });
    window.addEventListener("scroll", resetState, { passive: true });
    window.addEventListener("blur", resetState);

    const onVisibilityChange = () => {
      if (document.hidden) resetState();
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("pointerover", onPointerOver);
      document.removeEventListener("pointerout", onPointerOut);
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("scroll", resetState);
      window.removeEventListener("blur", resetState);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      document.documentElement.classList.remove("cf-cursor-hidden");
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <div
      id="cf-atom-cursor"
      ref={rootRef}
      style={{ display: "none" }}
      aria-hidden="true"
    >
      <div ref={ringRef} className="cf-cursor-ring" />
      <div ref={nucleusRef} className="cf-cursor-nucleus" />
      <div ref={electronRef} className="cf-cursor-electron" />
    </div>
  );
};
