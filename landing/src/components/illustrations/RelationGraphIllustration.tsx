import React from "react";
import { motion } from "motion/react";

export const RelationGraphIllustration: React.FC = () => {
  return (
    <div className="relative rounded-2xl border border-white/10 bg-[#0C1330]/80 p-5 backdrop-blur-xl shadow-2xl">
      <div className="mb-4 flex items-center justify-between border-b border-white/8 pb-3">
        <div>
          <span className="text-[11px] font-mono font-medium tracking-wider text-cyan uppercase">
            Prescription Network Topology
          </span>
          <h4 className="text-sm font-semibold text-white">Multi-Drug Interaction Graph</h4>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[11px] font-mono text-muted-foreground">
          Illustrative example
        </span>
      </div>

      <div className="relative flex h-60 w-full items-center justify-center">
        <svg
          viewBox="0 0 400 240"
          className="h-full w-full max-w-md overflow-visible"
          role="img"
          aria-label="Drug interaction relation graph illustrating 4 prescription drugs and similar drug inference"
        >
          {/* Edge 1: Warfarin (80, 60) to Aspirin (320, 60) - Major coral */}
          <motion.line
            x1="80"
            y1="60"
            x2="320"
            y2="60"
            stroke="#FF5C7A"
            strokeWidth="2.5"
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.9, delay: 0.1, ease: "easeInOut" }}
            style={{ filter: "drop-shadow(0 0 6px rgba(255, 92, 122, 0.5))" }}
          />
          {/* Edge 2: Warfarin (80, 60) to Metformin (140, 185) - Moderate amber */}
          <motion.line
            x1="80"
            y1="60"
            x2="140"
            y2="185"
            stroke="#FFB84D"
            strokeWidth="2"
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.9, delay: 0.2, ease: "easeInOut" }}
            style={{ filter: "drop-shadow(0 0 4px rgba(255, 184, 77, 0.4))" }}
          />
          {/* Edge 3: Aspirin (320, 60) to Atorvastatin (270, 185) - Minor mint */}
          <motion.line
            x1="320"
            y1="60"
            x2="270"
            y2="185"
            stroke="#35E0A1"
            strokeWidth="2"
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.9, delay: 0.3, ease: "easeInOut" }}
            style={{ filter: "drop-shadow(0 0 4px rgba(53, 224, 161, 0.4))" }}
          />
          {/* Edge 4: Metformin (140, 185) to Atorvastatin (270, 185) - Minor mint */}
          <motion.line
            x1="140"
            y1="185"
            x2="270"
            y2="185"
            stroke="#35E0A1"
            strokeWidth="1.8"
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.9, delay: 0.4, ease: "easeInOut" }}
          />

          {/* Dashed Edge: Atorvastatin (270, 185) to Simvastatin (350, 160) - Cyan inference */}
          <motion.line
            x1="270"
            y1="185"
            x2="350"
            y2="160"
            stroke="#19D3FF"
            strokeWidth="1.8"
            strokeDasharray="4 4"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.9 }}
            transition={{ duration: 0.8, delay: 0.6, ease: "easeOut" }}
            style={{ filter: "drop-shadow(0 0 4px rgba(25, 211, 255, 0.5))" }}
          />

          {/* Major Edge Badge */}
          <rect x="180" y="48" width="40" height="18" rx="4" fill="#060A18" stroke="#FF5C7A" strokeWidth="1" />
          <text x="200" y="61" textAnchor="middle" fontSize="9" fontWeight="bold" fill="#FF5C7A" fontFamily="Geist Mono Variable, monospace">
            Major
          </text>

          {/* Node 1: Warfarin */}
          <g>
            <circle cx="80" cy="60" r="23" fill="#060A18" stroke="#FF5C7A" strokeWidth="2" />
            <text x="80" y="57" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#EAF0FF" fontFamily="Geist Variable, sans-serif">
              Warfarin
            </text>
            <text x="80" y="69" textAnchor="middle" fontSize="8" fill="#93A1C8" fontFamily="Geist Mono Variable, monospace">
              Rx #1
            </text>
          </g>

          {/* Node 2: Aspirin */}
          <g>
            <circle cx="320" cy="60" r="23" fill="#060A18" stroke="#FF5C7A" strokeWidth="2" />
            <text x="320" y="57" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#EAF0FF" fontFamily="Geist Variable, sans-serif">
              Aspirin
            </text>
            <text x="320" y="69" textAnchor="middle" fontSize="8" fill="#93A1C8" fontFamily="Geist Mono Variable, monospace">
              Rx #2
            </text>
          </g>

          {/* Node 3: Metformin */}
          <g>
            <circle cx="140" cy="185" r="21" fill="#060A18" stroke="#FFB84D" strokeWidth="1.8" />
            <text x="140" y="182" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#EAF0FF" fontFamily="Geist Variable, sans-serif">
              Metformin
            </text>
            <text x="140" y="194" textAnchor="middle" fontSize="8" fill="#93A1C8" fontFamily="Geist Mono Variable, monospace">
              Rx #3
            </text>
          </g>

          {/* Node 4: Atorvastatin */}
          <g>
            <circle cx="270" cy="185" r="21" fill="#060A18" stroke="#35E0A1" strokeWidth="1.8" />
            <text x="270" y="182" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#EAF0FF" fontFamily="Geist Variable, sans-serif">
              Atorvastatin
            </text>
            <text x="270" y="194" textAnchor="middle" fontSize="8" fill="#93A1C8" fontFamily="Geist Mono Variable, monospace">
              Rx #4
            </text>
          </g>

          {/* Node 5: Similar Drug (Analogue) */}
          <g>
            <circle cx="350" cy="160" r="17" fill="#060A18" stroke="#19D3FF" strokeWidth="1.4" strokeDasharray="3 3" />
            <text x="350" y="158" textAnchor="middle" fontSize="8" fontWeight="bold" fill="#19D3FF" fontFamily="Geist Variable, sans-serif">
              Simvastatin
            </text>
            <text x="350" y="169" textAnchor="middle" fontSize="7" fill="#93A1C8" fontFamily="Geist Mono Variable, monospace">
              Analogue
            </text>
          </g>
        </svg>
      </div>

      <div className="flex items-center justify-between border-t border-white/8 pt-3 text-[11px] text-muted-foreground">
        <span className="font-mono text-xs text-white">Regimen: 4 active drugs</span>
        <span className="font-mono text-[10px] text-cyan">Dashed line: similarity inference fallback</span>
      </div>
    </div>
  );
};
