import React, { useEffect, useRef } from "react";

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  ring: boolean;
  colorIndex: number;
}

export const MolecularGraphCanvas: React.FC<{ className?: string }> = ({ className }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let isVisible = true;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Node count ~42
    const nodeCount = 42;
    let width = 0;
    let height = 0;
    let nodes: Node[] = [];

    // Colors: cyan #19D3FF, violet #7A5CFF, mint #35E0A1, amber #FFB84D
    const colors = [
      { r: 25, g: 211, b: 255 },  // cyan
      { r: 122, g: 92, b: 255 },  // violet
      { r: 53, g: 224, b: 161 },  // mint
      { r: 255, g: 184, b: 77 },  // amber
    ];

    const initNodes = () => {
      nodes = [];
      for (let i = 0; i < nodeCount; i++) {
        nodes.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.4,
          vy: (Math.random() - 0.5) * 0.4,
          radius: Math.random() > 0.75 ? 3.2 : 2.0,
          ring: Math.random() > 0.65,
          colorIndex: Math.floor(Math.random() * colors.length),
        });
      }
    };

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.resetTransform?.();
      ctx.scale(dpr, dpr);
      if (nodes.length === 0) {
        initNodes();
      }
    };

    resize();
    window.addEventListener("resize", resize);

    const observer = new IntersectionObserver(
      (entries) => {
        isVisible = entries[0].isIntersecting;
        if (isVisible && !reducedMotion && !animationFrameId) {
          animationFrameId = requestAnimationFrame(render);
        }
      },
      { threshold: 0.05 }
    );
    observer.observe(canvas);

    const handleVisibilityChange = () => {
      isVisible = document.visibilityState === "visible";
      if (isVisible && !reducedMotion && !animationFrameId) {
        animationFrameId = requestAnimationFrame(render);
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);

    const maxDist = 110;
    const maxDistSq = maxDist * maxDist;

    const render = () => {
      if (!isVisible) {
        animationFrameId = 0;
        return;
      }

      ctx.clearRect(0, 0, width, height);

      // Draw bonds (edges)
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const distSq = dx * dx + dy * dy;

          if (distSq < maxDistSq) {
            const dist = Math.sqrt(distSq);
            const alpha = (1 - dist / maxDist) * 0.28;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = `rgba(25, 211, 255, ${alpha})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }

      // Draw nodes (atoms)
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (!reducedMotion) {
          n.x += n.vx;
          n.y += n.vy;

          if (n.x < -10) n.x = width + 10;
          if (n.x > width + 10) n.x = -10;
          if (n.y < -10) n.y = height + 10;
          if (n.y > height + 10) n.y = -10;
        }

        const c = colors[n.colorIndex];

        // Glow halo
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + 3.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${c.r}, ${c.g}, ${c.b}, 0.15)`;
        ctx.fill();

        // Node circle
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${c.r}, ${c.g}, ${c.b}, 0.8)`;
        ctx.fill();

        if (n.ring) {
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius + 4, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(${c.r}, ${c.g}, ${c.b}, 0.35)`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }

      if (!reducedMotion) {
        animationFrameId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", resize);
      observer.disconnect();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 h-full w-full opacity-65 ${className ?? ""}`}
    />
  );
};
