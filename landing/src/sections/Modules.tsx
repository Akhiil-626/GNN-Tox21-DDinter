import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Button } from "@/components/ui/button";
import { ArrowUpRight, CheckCircle2, ShieldAlert, Cpu, Network, Layers, Sparkles, Activity } from "lucide-react";
import { AssayPlate } from "@/components/illustrations/AssayPlate";
import { DdiBondIllustration } from "@/components/illustrations/DdiBondIllustration";
import { RelationGraphIllustration } from "@/components/illustrations/RelationGraphIllustration";
import { MetricsBarIllustration } from "@/components/illustrations/MetricsBarIllustration";
import { MODULE_LINKS, APP_URL } from "@/lib/links";

interface FeatureCard {
  title: string;
  description: string;
  icon: React.ElementType;
}

interface ModuleItem {
  id: "screening" | "interactions" | "prescription" | "performance";
  title: string;
  tagline: string;
  oneLineDesc: string;
  dashboardLink: string;
  illustration: React.ReactNode;
  featureCards: FeatureCard[];
}

const MODULES_DATA: ModuleItem[] = [
  {
    id: "screening",
    title: "Compound screening",
    tagline: "Tox21 Bioassay Array & Saliency",
    oneLineDesc: "Predict 12 Tox21 toxicity endpoints and atom saliency from SMILES or IUPAC name.",
    dashboardLink: MODULE_LINKS.screening,
    illustration: <AssayPlate />,
    featureCards: [
      {
        title: "12 Tox21 Endpoints",
        description:
          "Screening across nuclear receptor (NR-AR, NR-AhR, NR-ER, NR-PPAR) and stress response (SR-ARE, SR-p53) bioassays.",
        icon: CheckCircle2,
      },
      {
        title: "Multi-Model Architecture",
        description:
          "Ensemble of GCN, GIN (1-WL expressive), and edge-aware MPNN alongside a Random Forest fingerprint baseline.",
        icon: Cpu,
      },
      {
        title: "Atom Saliency Heatmap",
        description:
          "Backpropagated gradient saliency (∂Logit / ∂Atom) maps toxicophore regions directly onto the 2D molecular graph.",
        icon: Sparkles,
      },
    ],
  },
  {
    id: "interactions",
    title: "Interaction check",
    tagline: "Pairwise Severity Classifier",
    oneLineDesc: "Classify pairwise drug-drug interaction severity into Minor, Moderate, or Major.",
    dashboardLink: MODULE_LINKS.interactions,
    illustration: <DdiBondIllustration />,
    featureCards: [
      {
        title: "3 Severity Classes",
        description:
          "Calibrated probabilistic classification for Minor (low impact), Moderate (monitor closely), and Major (avoid combination).",
        icon: ShieldAlert,
      },
      {
        title: "Dual GNN Molecular Encoder",
        description:
          "Both chemical structures are encoded as graph topologies with cross-attention bond-level feature aggregation.",
        icon: Cpu,
      },
      {
        title: "DDInter Benchmark",
        description:
          "Trained on 122,378 curated drug-drug interaction pairs with strict cold-start split protocols.",
        icon: Activity,
      },
    ],
  },
  {
    id: "prescription",
    title: "Prescription checker",
    tagline: "Multi-Drug Network Analysis",
    oneLineDesc: "Analyze regimens of up to 5 concurrent compounds with graph topology and similarity inference.",
    dashboardLink: MODULE_LINKS.prescription,
    illustration: <RelationGraphIllustration />,
    featureCards: [
      {
        title: "Polypharmacy Regimen Graph",
        description:
          "Simultaneously screens all pairwise combinations across up to 5 concurrent drugs with full topological visualization.",
        icon: Network,
      },
      {
        title: "Similarity Inference Fallback",
        description:
          "When a pair is undocumented in DDInter, falls back to Morgan fingerprint similarity against known analogues.",
        icon: Sparkles,
      },
      {
        title: "Worst-Case Severity Alert",
        description:
          "Summarizes overall regimen risk by highlighting the single highest-severity edge and warning clinicians.",
        icon: ShieldAlert,
      },
    ],
  },
  {
    id: "performance",
    title: "Model performance",
    tagline: "Cold-Start Benchmark Auditing",
    oneLineDesc: "Evaluate GCN & GIN architectures on cold-start splits with honest reporting of limits.",
    dashboardLink: MODULE_LINKS.performance,
    illustration: <MetricsBarIllustration />,
    featureCards: [
      {
        title: "Strict Cold-Start Split",
        description:
          "Test compounds were strictly unseen during training, preventing memorization and reflecting real drug discovery.",
        icon: CheckCircle2,
      },
      {
        title: "High Major-Class Recall",
        description:
          "GCN achieves 70.5% recall on Major severity interactions, prioritizing the detection of high-risk adverse events.",
        icon: ShieldAlert,
      },
      {
        title: "Honest Boundary Disclosures",
        description:
          "Minor severity remains the hardest to classify; absence in DDInter indicates an undocumented pair, not proof of safety.",
        icon: Layers,
      },
    ],
  },
];

interface ModulesProps {
  currentTab?: string;
  onTabChange?: (tab: string) => void;
}

export const Modules: React.FC<ModulesProps> = ({ currentTab, onTabChange }) => {
  const [internalTab, setInternalTab] = useState<ModuleItem["id"]>("screening");

  useEffect(() => {
    if (
      currentTab &&
      ["screening", "interactions", "prescription", "performance"].includes(currentTab)
    ) {
      setInternalTab(currentTab as ModuleItem["id"]);
    }
  }, [currentTab]);

  const handleTabClick = (tabId: ModuleItem["id"]) => {
    setInternalTab(tabId);
    if (onTabChange) {
      onTabChange(tabId);
    }
  };

  const activeModule =
    MODULES_DATA.find((m) => m.id === internalTab) ?? MODULES_DATA[0];

  return (
    <section id="modules" className="relative py-24 sm:py-32 bg-[#060A18] border-t border-white/5 scroll-mt-20 overflow-hidden w-full max-w-full">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 min-w-0">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 pb-12 border-b border-white/8">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-mono text-cyan mb-3">
              <span>[ Modules ]</span>
            </div>
            <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white">
              Explore screening & analysis modules
            </h2>
            <p className="mt-3 text-base text-muted-foreground max-w-2xl">
              Inspect candidate molecules, evaluate pairwise combinations, and check full prescription regimens with deep graph neural models.
            </p>
          </div>

          <Button
            asChild
            className="rounded-full bg-cyan text-[#060A18] font-semibold text-xs px-5 py-2.5 shadow-[0_0_20px_rgba(25,211,255,0.3)] hover:bg-cyan/90 hover:scale-[1.02]"
          >
            <a href={APP_URL}>
              Open the app
              <ArrowUpRight className="ml-1.5 h-4 w-4" />
            </a>
          </Button>
        </div>

        {/* 2-Column Layout */}
        <div className="mt-12 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start min-w-0 max-w-full">
          {/* Left Column: Vertical Tabs on Desktop, Horizontal on Mobile */}
          <div className="lg:col-span-4 flex lg:flex-col gap-2.5 overflow-x-auto pb-4 lg:pb-0 scrollbar-none min-w-0 max-w-full">
            {MODULES_DATA.map((module) => {
              const isActive = module.id === internalTab;
              return (
                <button
                  key={module.id}
                  onClick={() => handleTabClick(module.id)}
                  className={`relative flex flex-col text-left rounded-2xl p-4 transition-all whitespace-normal min-w-[240px] lg:min-w-0 ${
                    isActive
                      ? "border border-cyan/40 bg-[#0C1330] shadow-[0_8px_30px_rgba(0,0,0,0.5)]"
                      : "border border-white/6 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/12"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-cyan uppercase tracking-wider">
                      {module.tagline}
                    </span>
                    {isActive && (
                      <span className="h-2 w-2 rounded-full bg-cyan shadow-[0_0_8px_rgba(25,211,255,0.8)]" />
                    )}
                  </div>
                  <h4 className={`mt-1.5 font-display text-base font-bold transition-colors ${
                    isActive ? "text-white" : "text-foreground"
                  }`}>
                    {module.title}
                  </h4>
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                    {module.oneLineDesc}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Right Column: Showcase Panel */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeModule.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.35, ease: "easeOut" }}
                className="space-y-6"
              >
                {/* Active Illustration */}
                <div className="rounded-2xl overflow-hidden">
                  {activeModule.illustration}
                </div>

                {/* Sub-Feature Carousel / Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {activeModule.featureCards.map((feat, i) => {
                    const Icon = feat.icon;
                    return (
                      <div
                        key={i}
                        className="glass-card rounded-xl p-4 flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/5 border border-white/10 text-cyan mb-2.5">
                            <Icon className="h-3.5 w-3.5" />
                          </div>
                          <h5 className="text-xs font-semibold text-white">{feat.title}</h5>
                        </div>
                        <p className="mt-2 text-[11px] text-muted-foreground leading-relaxed">
                          {feat.description}
                        </p>
                      </div>
                    );
                  })}
                </div>

                {/* Open this module Button */}
                <div className="flex items-center justify-end pt-2">
                  <Button
                    asChild
                    variant="outline"
                    className="rounded-full border border-cyan/40 bg-cyan/10 text-cyan hover:bg-cyan/20 hover:border-cyan hover:text-white px-5 text-xs font-semibold"
                  >
                    <a href={activeModule.dashboardLink}>
                      Launch {activeModule.title}
                      <ArrowUpRight className="ml-1.5 h-3.5 w-3.5" />
                    </a>
                  </Button>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
};
