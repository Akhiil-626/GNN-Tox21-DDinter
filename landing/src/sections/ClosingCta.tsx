import React, { useRef, useEffect } from "react";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles, BookOpen } from "lucide-react";
import { APP_URL } from "@/lib/links";

export const ClosingCta: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let width = 0;
    let height = 0;
    let mouse = { x: -1000, y: -1000 };

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.resetTransform?.();
      ctx.scale(dpr, dpr);
    };

    resize();
    window.addEventListener("resize", resize);

    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };

    const onMouseLeave = () => {
      mouse.x = -1000;
      mouse.y = -1000;
    };

    window.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseleave", onMouseLeave);

    const spacing = 36;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      const cols = Math.floor(width / spacing) + 1;
      const rows = Math.floor(height / spacing) + 1;

      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          const px = i * spacing;
          const py = j * spacing;

          const dx = mouse.x - px;
          const dy = mouse.y - py;
          const dist = Math.sqrt(dx * dx + dy * dy);

          const maxDist = 180;
          let angle = Math.atan2(dy, dx);
          let length = 6;
          let alpha = 0.12;

          if (dist < maxDist) {
            const factor = 1 - dist / maxDist;
            alpha = 0.12 + factor * 0.5;
            length = 6 + factor * 8;
          }

          const endX = px + Math.cos(angle) * length;
          const endY = py + Math.sin(angle) * length;

          ctx.beginPath();
          ctx.moveTo(px, py);
          ctx.lineTo(endX, endY);
          ctx.strokeStyle = `rgba(25, 211, 255, ${alpha})`;
          ctx.lineWidth = 1;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(px, py, 1.2, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(122, 92, 255, ${alpha + 0.1})`;
          ctx.fill();
        }
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseleave", onMouseLeave);
    };
  }, []);

  return (
    <section className="relative overflow-hidden bg-[#060A18] py-28 sm:py-36 border-t border-white/5">
      {/* Background Interactive Magnet Canvas */}
      <canvas
        ref={canvasRef}
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 h-full w-full opacity-60"
      />

      {/* Mesh Glow */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="h-[450px] w-[700px] rounded-full bg-gradient-to-r from-cyan/15 via-violet/20 to-mint/15 blur-[140px] opacity-70" />
      </div>

      <div className="relative z-10 mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs font-mono text-cyan backdrop-blur-md mb-6"
        >
          <Sparkles className="h-3.5 w-3.5 text-cyan" aria-hidden="true" />
          <span>Local GNN Inference Ready</span>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          className="font-display text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-tight"
        >
          From structure to insight.
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto mt-6 max-w-2xl text-base sm:text-lg text-muted-foreground leading-relaxed"
        >
          Screen candidate compounds, classify pairwise adverse interactions, and inspect multi-drug polypharmacy risk with transparent graph intelligence.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <Button
            asChild
            size="lg"
            className="rounded-full bg-cyan px-8 py-3 text-sm font-semibold text-[#060A18] shadow-[0_0_25px_rgba(25,211,255,0.4)] transition-all hover:bg-cyan/90 hover:scale-[1.02] hover:shadow-[0_0_35px_rgba(25,211,255,0.6)]"
          >
            <a href={APP_URL}>
              Get started
              <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
            </a>
          </Button>

          <Button
            asChild
            variant="outline"
            size="lg"
            className="rounded-full border border-white/15 bg-white/5 px-7 py-3 text-sm font-medium text-white backdrop-blur-md transition-all hover:bg-white/10 hover:border-white/25"
          >
            <a href="#faq">
              <BookOpen className="mr-2 h-4 w-4 text-cyan" />
              Explore FAQ
            </a>
          </Button>
        </motion.div>
      </div>
    </section>
  );
};
