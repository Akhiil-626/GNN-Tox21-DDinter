import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { MODULE_LINKS } from "@/lib/links";
import { Button } from "@/components/ui/button";
import { AssayPlateReplica } from "@/components/replicas/assay-plate-replica";
import { DdiSeverityReplica } from "@/components/replicas/ddi-severity-replica";
import { RelationGraphReplica } from "@/components/replicas/relation-graph-replica";
import { MiniPerformanceCard } from "@/components/replicas/mini-performance-card";
import { ExternalLinkIcon, CheckIcon } from "lucide-react";

interface StepData {
  id: string;
  stepKey: string;
  number: string;
  title: string;
  subtitle: string;
  description: string;
  bullets: string[];
  link: string;
}

const STEPS: StepData[] = [
  {
    id: "module-screening",
    stepKey: "screening",
    number: "01",
    title: "Compound screening",
    subtitle: "12-Endpoint Toxicity Profiling",
    description:
      "GCN, GIN and edge-aware MPNN plus a Random Forest fingerprint baseline evaluate compounds under a scaffold split. Input as SMILES, chemical name (resolved through PubChem), or a preset.",
    bullets: [
      "12 Tox21 nuclear receptor and stress response endpoints",
      "Scaffold split evaluation to test generalization to novel scaffolds",
      "Atom-level saliency gradients identifying active toxicophores",
    ],
    link: MODULE_LINKS.screening,
  },
  {
    id: "module-interactions",
    stepKey: "interactions",
    number: "02",
    title: "Interaction check",
    subtitle: "Pairwise Drug Interaction Severity",
    description:
      "Two drugs in, predicted severity (Minor, Moderate, Major) with probabilities, from a dual-encoder GNN trained on DDInter. GCN and GIN were trained; MPNN was not (too slow on CPU for this task).",
    bullets: [
      "3 severity classes: Minor, Moderate, Major",
      "Dual-encoder molecular graph architecture",
      "Evaluated on a cold-start split with completely unseen drugs",
    ],
    link: MODULE_LINKS.interactions,
  },
  {
    id: "module-prescription",
    stepKey: "prescription",
    number: "03",
    title: "Prescription checker",
    subtitle: "Multi-Drug Regimen Networks & Read-Across",
    description:
      "Add 2 to 5 drugs with autocomplete over DDInter names. Renders an interactive relation network, per-drug severity distribution, DDInter literature records, and similar-drug structural analogue read-across for unrecorded pairs.",
    bullets: [
      "Autocomplete over thousands of clinical drug entities",
      "Relation network visualization exportable as image",
      "Structural analogue analysis for unrecorded pairs labelled as inference",
    ],
    link: MODULE_LINKS.prescription,
  },
  {
    id: "module-performance",
    stepKey: "performance",
    number: "04",
    title: "Model performance",
    subtitle: "Empirical Benchmarking vs Baselines",
    description:
      "Mean ROC-AUC over 12 endpoints: GCN 0.762, GIN 0.761, MPNN 0.757, Random Forest 0.732. GNNs outperform the Morgan fingerprint baseline on 9 of 12 endpoints, while PR-AUC remains comparable.",
    bullets: [
      "Toxicity: scaffold split testing out-of-distribution molecules",
      "Interactions: cold-start split on unseen drug pairs",
      "All benchmarks verified from results/metrics.csv",
    ],
    link: MODULE_LINKS.performance,
  },
];

export const ModulesStageSection: React.FC<{ activeStep?: string }> = ({ activeStep }) => {
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const shouldReduceMotion = useReducedMotion();
  const stepRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    if (activeStep) {
      const idx = STEPS.findIndex(
        (s) => s.stepKey === activeStep || s.id === activeStep
      );
      if (idx !== -1) setCurrentStepIdx(idx);
    }
  }, [activeStep]);

  // Track active step on scroll for desktop pinned view
  useEffect(() => {
    const handleScroll = () => {
      if (window.innerWidth < 1024) return;

      const viewportCenter = window.innerHeight / 2;
      let closestIdx = 0;
      let closestDist = Infinity;

      stepRefs.current.forEach((el, idx) => {
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const dist = Math.abs(rect.top + rect.height / 2 - viewportCenter);
        if (dist < closestDist) {
          closestDist = dist;
          closestIdx = idx;
        }
      });

      setCurrentStepIdx(closestIdx);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const renderVisual = (index: number) => {
    switch (index) {
      case 0:
        return <AssayPlateReplica key="plate" />;
      case 1:
        return <DdiSeverityReplica key="ddi" />;
      case 2:
        return <RelationGraphReplica key="graph" />;
      case 3:
        return <MiniPerformanceCard key="perf" />;
      default:
        return <AssayPlateReplica key="default" />;
    }
  };

  return (
    <section
      id="modules-stage"
      className="relative bg-[#F2F4F7] text-[#0E1116] py-20 md:py-32 border-b border-[#0E1116]"
    >
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6">
        {/* Section Header */}
        <div className="mb-8 lg:mb-12 max-w-[62ch]">
          <h2 className="text-[#0E1116] mb-4">
            Predictive modules, built on validated chemistry.
          </h2>
          <p className="text-lg md:text-[19px] text-[#0E1116]/80 leading-relaxed">
            From single-molecule bioassays to multi-drug regimens, each module pairs deep
            graph neural predictions with verifiable clinical or experimental evidence.
          </p>
        </div>

        {/* DESKTOP (>=1024px): Pinned Scroll-Driven Stage */}
        <div className="hidden lg:grid lg:grid-cols-12 gap-12 items-start relative">
          {/* Left Column (Cols 1-5): Scrolling Text Steps */}
          <div className="lg:col-span-5 space-y-16 pt-0 pb-8">
            {STEPS.map((step, idx) => {
              const isActive = currentStepIdx === idx;
              return (
                <div
                  key={step.id}
                  id={step.id}
                  ref={(el) => {
                    stepRefs.current[idx] = el;
                  }}
                  className={`scroll-mt-32 p-8 rounded-[12px] border transition-all duration-300 ${
                    isActive
                      ? "bg-[#FFFFFF] border-[#0E1116] shadow-none"
                      : "bg-[#FFFFFF]/40 border-[#0E1116]/30 opacity-70"
                  }`}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <span
                      className={`font-mono text-xs font-bold px-2 py-0.5 rounded-[4px] border ${
                        isActive
                          ? "bg-[#2147FF] text-[#F2F4F7] border-[#0E1116]"
                          : "bg-[#0E1116]/10 text-[#0E1116] border-[#0E1116]/30"
                      }`}
                    >
                      Step {step.number}
                    </span>
                    <span className="text-xs font-mono font-medium text-[#0E1116]/60">
                      {step.subtitle}
                    </span>
                  </div>

                  <h3 className="text-2xl font-bold text-[#0E1116] mb-3">
                    {step.title}
                  </h3>

                  <p className="text-[16px] text-[#0E1116]/85 leading-relaxed mb-6">
                    {step.description}
                  </p>

                  <ul className="space-y-2 mb-8">
                    {step.bullets.map((b, bIdx) => (
                      <li key={bIdx} className="flex items-start gap-2 text-sm text-[#0E1116]/80">
                        <CheckIcon className="size-4 text-[#2147FF] shrink-0 mt-0.5" />
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>

                  <Button asChild variant={isActive ? "signal" : "outline"} size="default">
                    <a href={step.link} target="_blank" rel="noopener noreferrer">
                      Open this module
                      <ExternalLinkIcon className="size-3.5 ml-1" />
                    </a>
                  </Button>
                </div>
              );
            })}
          </div>

          {/* Right Column (Cols 6-12): Pinned Visual Stage */}
          <div className="lg:col-span-7 sticky top-28 pt-0 pb-8">
            <div className="w-full max-w-[580px] mx-auto min-h-[420px] flex items-center justify-center">
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentStepIdx}
                  initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -15 }}
                  transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                  className="w-full"
                >
                  {renderVisual(currentStepIdx)}
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* MOBILE & TABLET (<1024px) / REDUCED MOTION: Stacked Layout */}
        <div className="lg:hidden space-y-10">
          {STEPS.map((step, idx) => (
            <div
              key={step.id}
              id={step.id}
              className="scroll-mt-24 p-6 sm:p-8 bg-[#FFFFFF] border border-[#0E1116] rounded-[12px] space-y-6"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-[4px] bg-[#2147FF] text-[#F2F4F7] border border-[#0E1116]">
                  Step {step.number}
                </span>
                <span className="text-xs font-mono font-medium text-[#0E1116]/60">
                  {step.subtitle}
                </span>
              </div>

              <h3 className="text-2xl font-bold text-[#0E1116]">
                {step.title}
              </h3>

              <p className="text-[16px] text-[#0E1116]/85 leading-relaxed">
                {step.description}
              </p>

              {/* Inlined Visual */}
              <div className="py-2">
                {renderVisual(idx)}
              </div>

              <ul className="space-y-2">
                {step.bullets.map((b, bIdx) => (
                  <li key={bIdx} className="flex items-start gap-2 text-sm text-[#0E1116]/80">
                    <CheckIcon className="size-4 text-[#2147FF] shrink-0 mt-0.5" />
                    <span>{b}</span>
                  </li>
                ))}
              </ul>

              <Button asChild variant="signal" size="default" className="w-full sm:w-auto">
                <a href={step.link} target="_blank" rel="noopener noreferrer">
                  Open this module
                  <ExternalLinkIcon className="size-3.5 ml-1" />
                </a>
              </Button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
