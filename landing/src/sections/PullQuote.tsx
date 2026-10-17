import React from "react";
import { motion } from "motion/react";
import { Quote } from "lucide-react";

export const PullQuote: React.FC = () => {
  return (
    <section className="relative py-24 sm:py-32 bg-[#060A18] overflow-hidden border-t border-white/5">
      {/* Background radial spotlight */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="h-[300px] w-[500px] rounded-full bg-gradient-to-r from-cyan/15 via-violet/15 to-mint/10 blur-[100px] opacity-60" />
      </div>

      <div className="relative z-10 mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-cyan shadow-[0_0_25px_rgba(25,211,255,0.25)] mb-8"
        >
          <Quote className="h-7 w-7 rotate-180 fill-cyan/20 stroke-cyan" />
        </motion.div>

        <motion.blockquote
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          className="font-display text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight"
        >
          &ldquo;Not in DDInter means{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-coral via-amber to-mint">
            undocumented, not safe.
          </span>&rdquo;
        </motion.blockquote>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
          className="mt-6 flex flex-col items-center justify-center gap-1.5"
        >
          <p className="font-mono text-xs font-semibold tracking-wider text-cyan uppercase">
            C-FOOTPRINT Design Principle
          </p>
          <p className="text-xs sm:text-sm text-muted-foreground max-w-lg">
            Computational screening establishes hypothesis, not clinical clearance. Every missing record is treated as an active unknown requiring empirical validation.
          </p>
        </motion.div>
      </div>
    </section>
  );
};
