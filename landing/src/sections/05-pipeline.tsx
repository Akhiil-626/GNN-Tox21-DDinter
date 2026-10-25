import React, { useRef } from "react";
import { motion, useScroll, useTransform, useReducedMotion } from "motion/react";

export const PipelineSection: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });

  const pathLength = useTransform(scrollYProgress, [0.15, 0.75], [0, 1]);

  const steps = [
    {
      num: "1",
      title: "Input Resolution",
      role: "PubChem API",
      rotate: -2,
      planeBg: "bg-[#FFFFFF]",
      content:
        "Accepts canonical SMILES strings or chemical trade/generic names, resolving them to validated molecular structures via PubChem REST endpoints.",
      tech: "SMILES / Chemical Name",
    },
    {
      num: "2",
      title: "Graph Featurization",
      role: "RDKit Featurizer",
      rotate: 2.5,
      planeBg: "bg-[#FFFFFF]",
      content:
        "Extracts atom features (atomic number, hybridization, formal charge, aromaticity) and bond orders into PyTorch Geometric graph tensors.",
      tech: "Node & Edge Tensors",
    },
    {
      num: "3",
      title: "Graph Neural Network",
      role: "Message Passing",
      rotate: -1.5,
      planeBg: "bg-[#FFFFFF]",
      content:
        "Spatial convolutions propagate structural information through 3-layer GCN or 1-WL expressive GIN architectures with batch normalization.",
      tech: "GCN / GIN / MPNN",
    },
    {
      num: "4",
      title: "Explainable Output",
      role: "Gradient Saliency",
      rotate: 3,
      planeBg: "bg-[#FFFFFF]",
      content:
        "Outputs calibrated probabilities across 12 Tox21 bioassays or 3 interaction classes, coupled with atom-level saliency attribution heatmaps.",
      tech: "Logits + Atom Saliency",
    },
  ];

  return (
    <section
      ref={containerRef}
      className="relative bg-[#F2F4F7] text-[#0E1116] py-20 md:py-32 border-b border-[#0E1116] overflow-hidden"
    >
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 relative z-10">
        {/* Header */}
        <div className="max-w-[62ch] mb-16 md:mb-24">
          <h2 className="text-[#0E1116] mb-4">
            How a molecule becomes a prediction.
          </h2>
          <p className="text-lg md:text-[19px] text-[#0E1116]/80 leading-relaxed">
            Every inference step is deterministic, auditable, and grounded in molecular graph topology.
          </p>
        </div>

        {/* Large SVG Connecting Arc (visible on lg screens) */}
        <div className="relative">
          <svg
            className="absolute top-[80px] left-0 w-full h-[220px] pointer-events-none hidden lg:block overflow-visible"
            viewBox="0 0 1100 220"
            fill="none"
            aria-hidden="true"
          >
            {/* Background static dashed arc */}
            <path
              d="M 60 110 C 300 20, 800 200, 1040 110"
              stroke="#0E1116"
              strokeWidth="2"
              strokeDasharray="6 6"
              strokeOpacity="0.2"
            />
            {/* Animated drawing arc */}
            <motion.path
              d="M 60 110 C 300 20, 800 200, 1040 110"
              stroke="#2147FF"
              strokeWidth="2.5"
              style={{
                pathLength: shouldReduceMotion ? 1 : pathLength,
              }}
            />
          </svg>

          {/* 4 Steps Grid: each step on its own angled plane */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 relative z-10">
            {steps.map((step) => (
              <div
                key={step.num}
                className="relative flex flex-col h-full"
              >
                {/* Background Hard-Edged Plane */}
                <div
                  className="absolute inset-0 bg-[#2147FF] translate-x-1.5 translate-y-1.5 border border-[#0E1116] rounded-[12px] -z-10"
                  style={{
                    transform: `rotate(${step.rotate}deg)`,
                  }}
                  aria-hidden="true"
                />

                {/* Card Surface */}
                <div
                  className={`${step.planeBg} border border-[#0E1116] rounded-[12px] p-6 flex flex-col justify-between h-full relative z-10`}
                >
                  <div>
                    {/* Step Number & Tech Tag */}
                    <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#0E1116]/20">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-[4px] bg-[#D2FF3F] text-[#0E1116] border border-[#0E1116]">
                        Step {step.num}
                      </span>
                      <span className="font-mono text-[11px] text-[#0E1116]/70">
                        {step.role}
                      </span>
                    </div>

                    <h3 className="text-xl font-bold text-[#0E1116] mb-3">
                      {step.title}
                    </h3>

                    <p className="text-[15px] text-[#0E1116]/85 leading-relaxed mb-6">
                      {step.content}
                    </p>
                  </div>

                  {/* Tech Chip */}
                  <div className="pt-3 border-t border-[#0E1116]/15 flex items-center justify-between font-mono text-[11px]">
                    <span className="text-[#0E1116]/60">Format:</span>
                    <span className="font-bold text-[#0E1116] bg-[#F2F4F7] px-2 py-0.5 rounded-[4px] border border-[#0E1116]/30">
                      {step.tech}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
