import React from "react";
import { motion, useReducedMotion } from "motion/react";

interface DdiSeverityReplicaProps {
  className?: string;
}

export const DdiSeverityReplica: React.FC<DdiSeverityReplicaProps> = ({
  className = "",
}) => {
  const shouldReduceMotion = useReducedMotion();

  const probabilities = [
    { label: "Minor", pct: 4, color: "#19B37A" },
    { label: "Moderate", pct: 14, color: "#F2A900" },
    { label: "Major", pct: 82, color: "#E5484D" },
  ];

  return (
    <div
      className={`bg-[#FFFFFF] text-[#0E1116] border border-[#0E1116] rounded-[12px] p-5 shadow-none select-none font-mono ${className}`}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between pb-3.5 mb-3.5 border-b border-[#0E1116]">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#E5484D] border border-[#0E1116]" />
          <span className="text-xs font-bold tracking-tight text-[#0E1116]">
            Pairwise Interaction Assessment
          </span>
        </div>
        <span className="text-[10px] font-mono font-semibold tracking-wider uppercase bg-[#D2FF3F] text-[#0E1116] px-2 py-0.5 rounded-[4px] border border-[#0E1116]">
          Illustrative example
        </span>
      </div>

      {/* Drug Chips Pair */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex-1 bg-[#F2F4F7] border border-[#0E1116] rounded-[6px] p-2.5 text-center">
          <span className="block text-[10px] text-[#0E1116]/60">Drug A</span>
          <span className="block text-sm font-bold text-[#0E1116]">Warfarin</span>
        </div>
        <span className="text-sm font-bold text-[#0E1116] px-1">+</span>
        <div className="flex-1 bg-[#F2F4F7] border border-[#0E1116] rounded-[6px] p-2.5 text-center">
          <span className="block text-[10px] text-[#0E1116]/60">Drug B</span>
          <span className="block text-sm font-bold text-[#0E1116]">Aspirin</span>
        </div>
      </div>

      {/* Predicted Severity Class */}
      <div className="p-3 bg-[#F2F4F7] border border-[#0E1116] rounded-[6px] mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-[#0E1116]/70">Dual-Encoder GNN Prediction:</span>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#E5484D] border border-[#0E1116]" />
            <span className="text-xs font-bold text-[#0E1116]">Major Severity</span>
          </div>
        </div>

        {/* 3 Severity Progress Bars */}
        <div className="space-y-2 mt-2">
          {probabilities.map((item, idx) => (
            <div key={item.label} className="space-y-1">
              <div className="flex justify-between text-[10px]">
                <span className="flex items-center gap-1.5 text-[#0E1116]">
                  <span
                    className="w-2 h-2 rounded-sm border border-[#0E1116]/40"
                    style={{ backgroundColor: item.color }}
                  />
                  {item.label}
                </span>
                <span className="font-bold text-[#0E1116]">{item.pct}%</span>
              </div>
              <div className="h-2 w-full bg-[#FFFFFF] border border-[#0E1116]/30 rounded-[3px] overflow-hidden">
                <motion.div
                  initial={shouldReduceMotion ? { width: `${item.pct}%` } : { width: "0%" }}
                  animate={{ width: `${item.pct}%` }}
                  transition={{
                    duration: 0.8,
                    delay: idx * 0.1,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                  className="h-full"
                  style={{ backgroundColor: item.color }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* DDInter Record Note */}
      <div className="p-2.5 bg-[#FFFFFF] border border-[#0E1116]/30 rounded-[6px] text-[11px] leading-snug text-[#0E1116]">
        <span className="font-bold block text-[10px] text-[#0E1116]/60 mb-0.5">
          DDInter Clinical Evidence:
        </span>
        Increased risk of severe gastrointestinal hemorrhage when co-administered.
      </div>
    </div>
  );
};
