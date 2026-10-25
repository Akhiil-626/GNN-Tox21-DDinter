import React from "react";
import { motion, useReducedMotion } from "motion/react";
import { MEAN_METRICS_DATA } from "@/data/metrics-data";

interface MiniPerformanceCardProps {
  className?: string;
}

export const MiniPerformanceCard: React.FC<MiniPerformanceCardProps> = ({
  className = "",
}) => {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      className={`bg-[#FFFFFF] text-[#0E1116] border border-[#0E1116] rounded-[12px] p-5 shadow-none select-none font-mono ${className}`}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between pb-3.5 mb-3.5 border-b border-[#0E1116]">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#2147FF] border border-[#0E1116]" />
          <span className="text-xs font-bold tracking-tight text-[#0E1116]">
            Scaffold-Split Benchmark Summary
          </span>
        </div>
        <span className="text-[10px] font-mono font-semibold tracking-wider uppercase bg-[#D2FF3F] text-[#0E1116] px-2 py-0.5 rounded-[4px] border border-[#0E1116]">
          Illustrative example
        </span>
      </div>

      {/* Mean ROC-AUC comparison table */}
      <div className="space-y-2 mb-3.5">
        {MEAN_METRICS_DATA.map((item, idx) => {
          const isGnn = item.model !== "RF (Morgan FP)";
          return (
            <div
              key={item.model}
              className={`flex items-center justify-between p-2 rounded-[6px] border text-xs ${
                isGnn
                  ? "bg-[#F2F4F7] border-[#0E1116]"
                  : "bg-[#FFFFFF] border-[#0E1116]/30 text-[#0E1116]/80"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full border border-[#0E1116] ${
                    isGnn ? "bg-[#2147FF]" : "bg-[#0E1116]"
                  }`}
                />
                <span className="font-bold">{item.model}</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-24 h-2 bg-[#FFFFFF] border border-[#0E1116]/30 rounded-sm overflow-hidden hidden sm:block">
                  <motion.div
                    initial={shouldReduceMotion ? { width: `${item.meanRocAuc * 100}%` } : { width: "0%" }}
                    animate={{ width: `${item.meanRocAuc * 100}%` }}
                    transition={{
                      duration: 0.7,
                      delay: idx * 0.08,
                      ease: [0.16, 1, 0.3, 1],
                    }}
                    className={`h-full ${isGnn ? "bg-[#2147FF]" : "bg-[#0E1116]/60"}`}
                  />
                </div>
                <span className="font-mono font-bold text-xs">
                  {item.meanRocAuc.toFixed(3)}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Outcome Note */}
      <div className="p-2.5 bg-[#D2FF3F] border border-[#0E1116] rounded-[6px] text-[11px] leading-tight font-medium text-[#0E1116]">
        <strong>Scaffold Split:</strong> GNN architectures outperform the 1024-bit Morgan fingerprint baseline on 9 of 12 endpoints.
      </div>
    </div>
  );
};
