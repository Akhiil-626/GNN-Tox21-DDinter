import React, { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import { Sparkles, Layers, Network, Eye } from "lucide-react";

const STATEMENT_LINES = [
  "Compounds come in thousands of forms.",
  "Combinations multiply the risk.",
  "When it could all be screened and explained.",
];

const TAG_PILLS = [
  { icon: Layers, label: "Assay plate / screening", color: "text-cyan border-cyan/30 bg-cyan/10" },
  { icon: Network, label: "Relation chart / prescription", color: "text-violet border-violet/30 bg-violet/10" },
  { icon: Eye, label: "Saliency / explainable", color: "text-mint border-mint/30 bg-mint/10" },
];

export const Statement: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start 0.85", "end 0.35"],
  });

  return (
    <section
      ref={containerRef}
      className="relative py-24 sm:py-32 bg-[#060A18] overflow-hidden border-t border-white/5"
    >
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-40">
        <div className="h-[400px] w-[600px] rounded-full bg-gradient-to-r from-cyan/10 via-violet/15 to-mint/10 blur-[120px]" />
      </div>

      <div className="relative z-10 mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center">
        {/* Eyebrow */}
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-xs font-mono text-cyan mb-8">
          <Sparkles className="h-3 w-3" />
          <span>[ Hypothesis to Verification ]</span>
        </div>

        {/* 3-line scroll-revealed statement */}
        <div className="space-y-4 sm:space-y-6">
          {STATEMENT_LINES.map((line, lineIdx) => {
            const start = lineIdx * 0.25;
            const end = start + 0.35;
            return (
              <ScrollLine key={line} text={line} progress={scrollYProgress} start={start} end={end} />
            );
          })}
        </div>

        {/* Rotating tag pills */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-14 flex flex-wrap items-center justify-center gap-3"
        >
          {TAG_PILLS.map((pill) => {
            const Icon = pill.icon;
            return (
              <div
                key={pill.label}
                className={`flex items-center gap-2 rounded-full border px-4 py-1.5 text-xs font-mono font-medium backdrop-blur-md transition-all ${pill.color}`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{pill.label}</span>
              </div>
            );
          })}
        </motion.div>

        {/* Closing Tagline */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.45 }}
          className="mt-8"
        >
          <p className="font-display text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white">
            C-FOOTPRINT <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan via-violet to-mint">makes it visible.</span>
          </p>
        </motion.div>
      </div>
    </section>
  );
};

interface ScrollLineProps {
  text: string;
  progress: any;
  start: number;
  end: number;
}

const ScrollLine: React.FC<ScrollLineProps> = ({ text, progress, start, end }) => {
  const opacity = useTransform(progress, [start, end], [0.55, 1.0]);
  const y = useTransform(progress, [start, end], [12, 0]);

  return (
    <motion.p
      style={{ opacity, y }}
      className="font-display text-2xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white leading-tight"
    >
      {text}
    </motion.p>
  );
};
