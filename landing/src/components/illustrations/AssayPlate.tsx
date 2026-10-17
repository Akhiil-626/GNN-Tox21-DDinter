import React from "react";
import { motion } from "motion/react";

interface WellData {
  id: string;
  name: string;
  type: "NR" | "SR";
  status: "minor" | "moderate" | "major";
  score: string;
}

const ENDPOINTS: WellData[] = [
  { id: "NR-AR", name: "Androgen Receptor", type: "NR", status: "minor", score: "0.08" },
  { id: "NR-AR-LBD", name: "AR Ligand-Binding", type: "NR", status: "minor", score: "0.05" },
  { id: "NR-AhR", name: "Aryl Hydrocarbon", type: "NR", status: "moderate", score: "0.42" },
  { id: "NR-Aromatase", name: "Aromatase Enzyme", type: "NR", status: "minor", score: "0.12" },
  { id: "NR-ER", name: "Estrogen Receptor", type: "NR", status: "minor", score: "0.09" },
  { id: "NR-ER-LBD", name: "ER Ligand-Binding", type: "NR", status: "minor", score: "0.04" },
  { id: "NR-PPAR-gamma", name: "PPAR-gamma", type: "NR", status: "minor", score: "0.15" },
  { id: "SR-ARE", name: "Antioxidant Resp.", type: "SR", status: "major", score: "0.89" },
  { id: "SR-ATAD5", name: "Genotoxicity ATAD5", type: "SR", status: "minor", score: "0.07" },
  { id: "SR-HSE", name: "Heat Shock Resp.", type: "SR", status: "moderate", score: "0.51" },
  { id: "SR-MMP", name: "Mitochondrial Mem.", type: "SR", status: "minor", score: "0.11" },
  { id: "SR-p53", name: "p53 Tumor Suppressor", type: "SR", status: "minor", score: "0.06" },
];

export const AssayPlate: React.FC = () => {
  return (
    <div className="relative rounded-2xl border border-white/10 bg-[#0C1330]/80 p-5 backdrop-blur-xl shadow-2xl">
      <div className="mb-4 flex items-center justify-between border-b border-white/8 pb-3">
        <div>
          <span className="text-[11px] font-mono font-medium tracking-wider text-cyan uppercase">
            Tox21 High-Throughput Array
          </span>
          <h4 className="text-sm font-semibold text-white">12 Bioassay Endpoint Wells</h4>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[11px] font-mono text-muted-foreground">
          Illustrative example
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2.5 sm:grid-cols-4 sm:gap-3">
        {ENDPOINTS.map((ep, idx) => {
          const bgTint =
            ep.status === "minor"
              ? "rgba(53, 224, 161, 0.12)"
              : ep.status === "moderate"
              ? "rgba(255, 184, 77, 0.15)"
              : "rgba(255, 92, 122, 0.18)";

          const strokeColor =
            ep.status === "minor"
              ? "#35E0A1"
              : ep.status === "moderate"
              ? "#FFB84D"
              : "#FF5C7A";

          return (
            <motion.div
              key={ep.id}
              initial={{ scale: 0.85, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{
                duration: 0.4,
                delay: idx * 0.05,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="group relative flex flex-col items-center justify-center rounded-xl border border-white/6 bg-[#060A18]/60 p-2.5 text-center transition-all hover:border-cyan/40 hover:bg-[#060A18]/90"
            >
              <div
                className="relative flex h-10 w-10 items-center justify-center rounded-full border transition-transform duration-300 group-hover:scale-105 shadow-inner"
                style={{
                  backgroundColor: bgTint,
                  borderColor: strokeColor,
                  boxShadow: `0 0 12px ${bgTint}`,
                }}
              >
                <span
                  className="font-mono text-[10px] font-bold"
                  style={{ color: strokeColor }}
                >
                  {ep.score}
                </span>
              </div>
              <span className="mt-2 block font-mono text-[11px] font-semibold text-foreground">
                {ep.id}
              </span>
              <span className="truncate text-[10px] text-muted-foreground">
                {ep.status === "minor" ? "INACTIVE" : ep.status === "moderate" ? "MODERATE" : "ACTIVE TOX"}
              </span>
            </motion.div>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-white/8 pt-3 text-[11px] text-muted-foreground">
        <div className="flex items-center gap-3 font-mono">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[#35E0A1]" /> 9 Minor / Inactive
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[#FFB84D]" /> 2 Moderate
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[#FF5C7A]" /> 1 Major Tox
          </span>
        </div>
        <span className="font-mono text-[10px] text-cyan">Bemis-Murcko Scaffold Split</span>
      </div>
    </div>
  );
};
