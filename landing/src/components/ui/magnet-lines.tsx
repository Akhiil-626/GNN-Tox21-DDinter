import React, { useRef, useEffect } from "react";
import { useReducedMotion } from "motion/react";

interface MagnetLinesProps {
  rows?: number;
  columns?: number;
  lineColor?: string;
  lineWidth?: number;
  lineLength?: number;
  className?: string;
  baseAngle?: number;
}

export const MagnetLines: React.FC<MagnetLinesProps> = ({
  rows = 7,
  columns = 18,
  lineColor = "#0E1116",
  lineWidth = 1.5,
  lineLength = 20,
  className = "",
  baseAngle = 0,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mousePos = useRef<{ x: number; y: number } | null>(null);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;

    const handleResize = () => {
      const rect = container.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener("resize", handleResize);

    const handleMouseMove = (e: MouseEvent) => {
      if (shouldReduceMotion) return;
      const rect = container.getBoundingClientRect();
      mousePos.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    };

    const handleMouseLeave = () => {
      mousePos.current = null;
    };

    container.addEventListener("mousemove", handleMouseMove);
    container.addEventListener("mouseleave", handleMouseLeave);

    const render = () => {
      const rect = container.getBoundingClientRect();
      ctx.clearRect(0, 0, rect.width, rect.height);

      const cellW = rect.width / (columns + 1);
      const cellH = rect.height / (rows + 1);

      ctx.strokeStyle = lineColor;
      ctx.lineWidth = lineWidth;
      ctx.lineCap = "round";

      for (let r = 1; r <= rows; r++) {
        for (let c = 1; c <= columns; c++) {
          const cx = c * cellW;
          const cy = r * cellH;

          let angle = (baseAngle * Math.PI) / 180;
          if (mousePos.current && !shouldReduceMotion) {
            const dx = mousePos.current.x - cx;
            const dy = mousePos.current.y - cy;
            const dist = Math.hypot(dx, dy);
            // Influence decreases with distance
            const influence = Math.max(0, 1 - dist / 400);
            const targetAngle = Math.atan2(dy, dx);
            angle = angle * (1 - influence) + targetAngle * influence;
          }

          const half = lineLength / 2;
          const x1 = cx - Math.cos(angle) * half;
          const y1 = cy - Math.sin(angle) * half;
          const x2 = cx + Math.cos(angle) * half;
          const y2 = cy + Math.sin(angle) * half;

          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.stroke();
        }
      }

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener("resize", handleResize);
      container.removeEventListener("mousemove", handleMouseMove);
      container.removeEventListener("mouseleave", handleMouseLeave);
      cancelAnimationFrame(animId);
    };
  }, [rows, columns, lineColor, lineWidth, lineLength, baseAngle, shouldReduceMotion]);

  return (
    <div
      ref={containerRef}
      className={`absolute inset-0 pointer-events-auto overflow-hidden ${className}`}
      aria-hidden="true"
    >
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
};
