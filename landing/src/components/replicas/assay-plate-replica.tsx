import React from "react";
import { motion, useReducedMotion } from "motion/react";

interface AssayPlateReplicaProps {
  className?: string;
  isFloating?: boolean;
}

export const AssayPlateReplica: React.FC<AssayPlateReplicaProps> = ({
  className = "",
  isFloating = false,
}) => {
  const shouldReduceMotion = useReducedMotion();

  // Simulated active/safe screening values for Aspirin
  const wellStates = [
    { name: "NR-AR", active: false, score: 0.12 },
    { name: "NR-AR-LBD", active: false, score: 0.08 },
    { name: "NR-AhR", active: false, score: 0.19 },
    { name: "NR-Aromatase", active: false, score: 0.15 },
    { name: "NR-ER", active: false, score: 0.14 },
    { name: "NR-ER-LBD", active: false, score: 0.09 },
    { name: "NR-PPAR-gamma", active: true, score: 0.78 },
    { name: "SR-ARE", active: true, score: 0.65 },
    { name: "SR-ATAD5", active: false, score: 0.05 },
    { name: "SR-HSE", active: false, score: 0.11 },
    { name: "SR-MMP", active: false, score: 0.22 },
    { name: "SR-p53", active: false, score: 0.07 },
  ];

  return (
    <motion.div
      animate={
        isFloating && !shouldReduceMotion
          ? { y: [-6, 6, -6] }
          : { y: 0 }
      }
      transition={{
        duration: 4.8,
        repeat: Infinity,
        ease: "easeInOut",
      }}
      className={`relative bg-[#FFFFFF] text-[#0E1116] border border-[#0E1116] rounded-[12px] p-5 shadow-none select-none font-mono ${className}`}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between pb-3.5 mb-3.5 border-b border-[#0E1116]">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#19B37A] border border-[#0E1116]" />
          <span className="text-xs font-bold tracking-tight text-[#0E1116]">
            Tox21 Screening Plate
          </span>
          <span className="text-[11px] text-[#0E1116]/60 bg-[#F2F4F7] px-2 py-0.5 rounded-[4px] border border-[#0E1116]/30">
            Aspirin (13 atoms)
          </span>
        </div>
        {/* Mandatory "Illustrative example" badge */}
        <span className="text-[10px] font-mono font-semibold tracking-wider uppercase bg-[#D2FF3F] text-[#0E1116] px-2 py-0.5 rounded-[4px] border border-[#0E1116]">
          Illustrative example
        </span>
      </div>

      {/* 12-well Assay Grid */}
      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2.5">
        {wellStates.map((well, idx) => (
          <div
            key={well.name}
            className="flex flex-col p-2 rounded-[6px] border border-[#0E1116]/20 bg-[#F2F4F7] relative overflow-hidden"
          >
            <div className="flex items-center justify-between text-[10px] font-bold text-[#0E1116] mb-1.5">
              <span>{well.name}</span>
              <span
                className={`w-2 h-2 rounded-full border border-[#0E1116]/40 ${
                  well.active ? "bg-[#E5484D]" : "bg-[#19B37A]"
                }`}
              />
            </div>

            {/* Well fill container */}
            <div className="h-7 w-full rounded-[4px] bg-[#FFFFFF] border border-[#0E1116]/30 relative overflow-hidden flex items-end">
              <motion.div
                initial={shouldReduceMotion ? { height: `${well.score * 100}%` } : { height: "0%" }}
                animate={{ height: `${well.score * 100}%` }}
                transition={{
                  duration: 0.9,
                  delay: idx * 0.05,
                  ease: [0.16, 1, 0.3, 1],
                }}
                className={`w-full ${
                  well.active ? "bg-[#2147FF]" : "bg-[#0E1116]/20"
                }`}
              />
            </div>
            <div className="mt-1 flex justify-between items-center text-[9px] text-[#0E1116]/70">
              <span>{well.active ? "Signal" : "Baseline"}</span>
              <span className="font-bold">{well.score.toFixed(2)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Footer */}
      <div className="mt-3.5 pt-3 border-t border-[#0E1116]/20 flex items-center justify-between text-[11px]">
        <span className="text-[#0E1116]/70">Active toxicophore: 2 / 12</span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 font-bold">
            <span className="w-2 h-2 rounded-full bg-[#19B37A]" /> 10 Negative
          </span>
          <span className="flex items-center gap-1 font-bold">
            <span className="w-2 h-2 rounded-full bg-[#E5484D]" /> 2 Positive
          </span>
        </div>
      </div>
    </motion.div>
  );
};
