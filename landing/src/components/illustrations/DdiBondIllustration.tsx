import React from "react";
import { motion } from "motion/react";

export const DdiBondIllustration: React.FC = () => {
  return (
    <div className="relative rounded-2xl border border-white/10 bg-[#0C1330]/80 p-5 backdrop-blur-xl shadow-2xl">
      <div className="mb-5 flex items-center justify-between border-b border-white/8 pb-3">
        <div>
          <span className="text-[11px] font-mono font-medium tracking-wider text-cyan uppercase">
            Pairwise Interaction Encoder
          </span>
          <h4 className="text-sm font-semibold text-white">Dual-Encoder Molecular Graph</h4>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[11px] font-mono text-muted-foreground">
          Illustrative example
        </span>
      </div>

      {/* Drug nodes and bond */}
      <div className="relative my-4 flex items-center justify-between px-3 sm:px-6">
        {/* Drug A */}
        <motion.div
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-10 flex flex-col items-center rounded-xl border border-cyan/30 bg-[#060A18] p-3 shadow-[0_0_15px_rgba(25,211,255,0.15)]"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan/15 text-cyan font-mono text-xs font-bold border border-cyan/30">
            Rx A
          </div>
          <span className="mt-2 text-xs font-semibold text-white">Warfarin</span>
          <span className="text-[10px] font-mono text-muted-foreground">DDInter: 1,248 pairs</span>
        </motion.div>

        {/* Bond Line with animated pulses */}
        <div className="relative mx-3 flex flex-1 items-center justify-center">
          <div className="h-0.5 w-full bg-white/10" />
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.7, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="absolute h-0.5 w-full origin-left bg-gradient-to-r from-cyan via-violet to-coral shadow-[0_0_8px_rgba(25,211,255,0.6)]"
          />
          <div className="absolute rounded-full border border-cyan/40 bg-[#060A18] px-2.5 py-1 text-[11px] font-mono text-cyan shadow-lg">
            Cross GNN Encoder
          </div>
        </div>

        {/* Drug B */}
        <motion.div
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-10 flex flex-col items-center rounded-xl border border-coral/30 bg-[#060A18] p-3 shadow-[0_0_15px_rgba(255,92,122,0.15)]"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-coral/15 text-coral font-mono text-xs font-bold border border-coral/30">
            Rx B
          </div>
          <span className="mt-2 text-xs font-semibold text-white">Aspirin</span>
          <span className="text-[10px] font-mono text-muted-foreground">DDInter: 1,489 pairs</span>
        </motion.div>
      </div>

      {/* Severity Risk Bars */}
      <div className="mt-6 space-y-3 rounded-xl border border-white/8 bg-[#060A18]/70 p-4">
        <div className="flex items-center justify-between text-xs font-semibold text-white">
          <span>Predicted Severity Distribution</span>
          <span className="font-mono text-xs text-[#FF5C7A] font-bold">Major Risk (72%)</span>
        </div>

        {/* Minor bar */}
        <div>
          <div className="mb-1 flex justify-between text-[11px]">
            <span className="text-muted-foreground">Minor (Low severity)</span>
            <span className="font-mono text-[#35E0A1]">8%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "8%" }}
              transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
              className="h-full rounded-full bg-[#35E0A1] shadow-[0_0_8px_rgba(53,224,161,0.5)]"
            />
          </div>
        </div>

        {/* Moderate bar */}
        <div>
          <div className="mb-1 flex justify-between text-[11px]">
            <span className="text-muted-foreground">Moderate</span>
            <span className="font-mono text-[#FFB84D]">20%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "20%" }}
              transition={{ duration: 0.8, delay: 0.5, ease: "easeOut" }}
              className="h-full rounded-full bg-[#FFB84D] shadow-[0_0_8px_rgba(255,184,77,0.5)]"
            />
          </div>
        </div>

        {/* Major bar */}
        <div>
          <div className="mb-1 flex justify-between text-[11px] font-medium text-[#FF5C7A]">
            <span>Major (Severe Risk / Bleeding)</span>
            <span className="font-mono font-bold">72%</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/5">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "72%" }}
              transition={{ duration: 0.8, delay: 0.6, ease: "easeOut" }}
              className="h-full rounded-full bg-[#FF5C7A] shadow-[0_0_12px_rgba(255,92,122,0.6)]"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
