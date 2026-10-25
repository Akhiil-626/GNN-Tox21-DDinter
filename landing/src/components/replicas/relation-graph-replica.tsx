import React from "react";
import { motion, useReducedMotion } from "motion/react";

interface RelationGraphReplicaProps {
  className?: string;
}

export const RelationGraphReplica: React.FC<RelationGraphReplicaProps> = ({
  className = "",
}) => {
  const shouldReduceMotion = useReducedMotion();

  // Nodes configuration
  const nodes = [
    { id: "warfarin", label: "Warfarin", x: 100, y: 70, type: "rx", color: "#0E1116", bg: "#FFFFFF" },
    { id: "aspirin", label: "Aspirin", x: 260, y: 70, type: "rx", color: "#0E1116", bg: "#FFFFFF" },
    { id: "clopidogrel", label: "Clopidogrel", x: 180, y: 175, type: "rx", color: "#0E1116", bg: "#FFFFFF" },
    { id: "analogue1", label: "Phenprocoumon", x: 30, y: 160, type: "analogue", color: "#0E1116", bg: "#D2FF3F" },
    { id: "analogue2", label: "Ticlopidine", x: 320, y: 160, type: "analogue", color: "#0E1116", bg: "#D2FF3F" },
  ];

  // Edges
  const edges = [
    // Direct regimen pairs
    { from: [100, 70], to: [260, 70], color: "#E5484D", dashed: false, label: "Major" },
    { from: [100, 70], to: [180, 175], color: "#E5484D", dashed: false, label: "Major" },
    { from: [260, 70], to: [180, 175], color: "#F2A900", dashed: false, label: "Moderate" },
    // Structural analogue read-across inferences (dashed)
    { from: [100, 70], to: [30, 160], color: "#2147FF", dashed: true, label: "Analogue" },
    { from: [180, 175], to: [320, 160], color: "#2147FF", dashed: true, label: "Analogue" },
  ];

  return (
    <div
      className={`bg-[#FFFFFF] text-[#0E1116] border border-[#0E1116] rounded-[12px] p-5 shadow-none select-none font-mono ${className}`}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between pb-3.5 mb-3 border-b border-[#0E1116]">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#2147FF] border border-[#0E1116]" />
          <span className="text-xs font-bold tracking-tight text-[#0E1116]">
            Prescription Network & Analogue Graph
          </span>
        </div>
        <span className="text-[10px] font-mono font-semibold tracking-wider uppercase bg-[#D2FF3F] text-[#0E1116] px-2 py-0.5 rounded-[4px] border border-[#0E1116]">
          Illustrative example
        </span>
      </div>

      {/* SVG Network diagram */}
      <div className="relative w-full h-[210px] bg-[#F2F4F7] border border-[#0E1116]/30 rounded-[6px] overflow-hidden">
        <svg
          viewBox="0 0 360 210"
          className="w-full h-full"
          aria-label="Prescription relation network showing Warfarin, Aspirin, Clopidogrel and structural analogues"
        >
          {/* Edges */}
          {edges.map((edge, idx) => {
            const [x1, y1] = edge.from;
            const [x2, y2] = edge.to;

            return (
              <g key={idx}>
                <motion.line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={edge.color}
                  strokeWidth={edge.dashed ? 1.5 : 2}
                  strokeDasharray={edge.dashed ? "4 4" : undefined}
                  initial={
                    shouldReduceMotion
                      ? { pathLength: 1 }
                      : { pathLength: 0 }
                  }
                  animate={{ pathLength: 1 }}
                  transition={{
                    duration: 0.8,
                    delay: idx * 0.1,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                />
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node, idx) => (
            <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
              <motion.circle
                r={node.type === "analogue" ? 14 : 17}
                fill={node.bg}
                stroke="#0E1116"
                strokeWidth={1.5}
                initial={shouldReduceMotion ? { scale: 1 } : { scale: 0 }}
                animate={{ scale: 1 }}
                transition={{
                  duration: 0.4,
                  delay: 0.4 + idx * 0.08,
                  ease: "easeOut",
                }}
              />
              <text
                y={node.type === "analogue" ? 24 : 27}
                textAnchor="middle"
                className="text-[9px] font-mono font-bold fill-[#0E1116]"
              >
                {node.label}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* Legend & Analogue notice */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[10px] text-[#0E1116]/80 pt-2 border-t border-[#0E1116]/20">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-0.5 bg-[#E5484D] inline-block" /> Major pair
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-0.5 bg-[#F2A900] inline-block" /> Moderate pair
          </span>
        </div>
        <div className="flex items-center gap-1 text-[10px] bg-[#D2FF3F] text-[#0E1116] px-1.5 py-0.5 rounded-[3px] border border-[#0E1116]">
          <span className="w-2.5 border-t border-dashed border-[#0E1116] inline-block" />
          <span>Analogue read-across (inference only)</span>
        </div>
      </div>
    </div>
  );
};
