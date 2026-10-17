import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Button } from "@/components/ui/button";
import { MolecularGraphCanvas } from "@/components/canvas/MolecularGraphCanvas";
import { ArrowRight, ChevronDown, Sparkles, Activity, ShieldAlert, Cpu } from "lucide-react";
import { APP_URL } from "@/lib/links";

const MORPH_WORDS = [
  { text: "toxicity", color: "text-coral" },
  { text: "interactions", color: "text-cyan" },
  { text: "prescriptions", color: "text-violet" },
];

const HERO_TABS = [
  { id: "screening", label: "Screening" },
  { id: "interactions", label: "Interactions" },
  { id: "prescription", label: "Prescription" },
  { id: "performance", label: "Performance" },
];

const TAB_CARDS = {
  screening: [
    {
      title: "12 Tox21 Bioassays",
      subtitle: "Nuclear receptors & stress pathways",
      badge: "Scaffold split",
      badgeColor: "bg-cyan/15 text-cyan border-cyan/30",
      metric: "0.84 AUC",
      icon: Activity,
    },
    {
      title: "Active Toxicophore",
      subtitle: "SR-ARE Antioxidant response",
      badge: "Major Alert",
      badgeColor: "bg-coral/15 text-coral border-coral/30",
      metric: "Score 0.89",
      icon: ShieldAlert,
    },
    {
      title: "Molecular Featurizer",
      subtitle: "RDKit canonical SMILES graph",
      badge: "Zero leakage",
      badgeColor: "bg-mint/15 text-mint border-mint/30",
      metric: "42 Atoms",
      icon: Cpu,
    },
  ],
  interactions: [
    {
      title: "122,378 Curated Pairs",
      subtitle: "DDInter database benchmark",
      badge: "Dual GNN",
      badgeColor: "bg-cyan/15 text-cyan border-cyan/30",
      metric: "Validated",
      icon: Activity,
    },
    {
      title: "Ethanol + Abacavir",
      subtitle: "Enzyme inhibition pathway",
      badge: "Moderate Risk",
      badgeColor: "bg-amber/15 text-amber border-amber/30",
      metric: "Prob 0.64",
      icon: ShieldAlert,
    },
    {
      title: "Cold-Start Evaluation",
      subtitle: "Test compounds unseen in train",
      badge: "Major 70.5%",
      badgeColor: "bg-mint/15 text-mint border-mint/30",
      metric: "Cold split",
      icon: Cpu,
    },
  ],
  prescription: [
    {
      title: "Multi-Drug Polypharmacy",
      subtitle: "Up to 5 concurrent compounds",
      badge: "Graph Topology",
      badgeColor: "bg-violet/15 text-violet border-violet/30",
      metric: "5 Drugs",
      icon: Activity,
    },
    {
      title: "Warfarin + Aspirin",
      subtitle: "Additive bleeding hemorrhage",
      badge: "Major Risk",
      badgeColor: "bg-coral/15 text-coral border-coral/30",
      metric: "Severity 3",
      icon: ShieldAlert,
    },
    {
      title: "Analogue Similarity",
      subtitle: "Simvastatin fallback inference",
      badge: "Similarity 0.84",
      badgeColor: "bg-cyan/15 text-cyan border-cyan/30",
      metric: "Inferred",
      icon: Cpu,
    },
  ],
  performance: [
    {
      title: "GCN Architecture",
      subtitle: "Graph Convolutional Network",
      badge: "Acc 60.0%",
      badgeColor: "bg-cyan/15 text-cyan border-cyan/30",
      metric: "F1: 0.491",
      icon: Cpu,
    },
    {
      title: "GIN Architecture",
      subtitle: "Graph Isomorphism Network",
      badge: "Acc 60.9%",
      badgeColor: "bg-violet/15 text-violet border-violet/30",
      metric: "F1: 0.490",
      icon: Cpu,
    },
    {
      title: "Major Severity Recall",
      subtitle: "Prioritizing high-risk detection",
      badge: "Recall 70.5%",
      badgeColor: "bg-mint/15 text-mint border-mint/30",
      metric: "Priority",
      icon: ShieldAlert,
    },
  ],
};

const PERSONA_CHIPS = [
  { label: "Aspirin", desc: "Single compound toxicity", tab: "screening" },
  { label: "Ethanol + Abacavir", desc: "Pairwise interaction check", tab: "interactions" },
  { label: "Four drugs at once", desc: "Multi-drug prescription network", tab: "prescription" },
];

export const Hero: React.FC = () => {
  const [morphIndex, setMorphIndex] = useState(0);
  const [activeTab, setActiveTab] = useState<keyof typeof TAB_CARDS>("screening");
  const [progress, setProgress] = useState(0);

  // Morphing headline word interval (3.2s)
  useEffect(() => {
    const timer = setInterval(() => {
      setMorphIndex((prev) => (prev + 1) % MORPH_WORDS.length);
    }, 3200);
    return () => clearInterval(timer);
  }, []);

  // 4s auto-advancing hero tabs with progress
  useEffect(() => {
    const tabKeys: (keyof typeof TAB_CARDS)[] = ["screening", "interactions", "prescription", "performance"];
    const intervalMs = 40;
    const totalMs = 4000;
    const step = (intervalMs / totalMs) * 100;

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          setActiveTab((currTab) => {
            const nextIdx = (tabKeys.indexOf(currTab) + 1) % tabKeys.length;
            return tabKeys[nextIdx];
          });
          return 0;
        }
        return prev + step;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [activeTab]);

  const handleSelectTab = (tabId: keyof typeof TAB_CARDS) => {
    setActiveTab(tabId);
    setProgress(0);
  };

  const cards = TAB_CARDS[activeTab];

  return (
    <section className="relative min-h-[92vh] pt-24 sm:pt-28 pb-16 flex flex-col justify-center overflow-hidden w-full max-w-full bg-[#060A18]">
      {/* Background Mesh Gradients */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[350px] sm:h-[500px] w-[350px] sm:w-[700px] rounded-full bg-gradient-to-tr from-cyan/15 via-violet/15 to-mint/10 blur-[90px] sm:blur-[130px] opacity-70" />
        <div className="absolute top-1/3 left-1/4 h-[250px] sm:h-[350px] w-[250px] sm:w-[350px] rounded-full bg-violet/15 blur-[80px] sm:blur-[100px] opacity-50" />
        <div className="absolute top-2/5 right-1/4 h-[250px] sm:h-[350px] w-[250px] sm:w-[350px] rounded-full bg-cyan/15 blur-[80px] sm:blur-[100px] opacity-50" />
      </div>

      {/* Interactive Molecular Canvas */}
      <MolecularGraphCanvas className="z-0" />

      {/* Content Container */}
      <div className="relative z-10 mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 text-center">
        {/* Eyebrow Bracket Badge */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-[11px] sm:text-xs font-mono text-cyan shadow-[0_0_15px_rgba(25,211,255,0.15)] backdrop-blur-md mb-6"
        >
          <Sparkles className="h-3.5 w-3.5 text-cyan" aria-hidden="true" />
          <span>[ Pre-clinical Molecular Intelligence ]</span>
        </motion.div>

        {/* Morphing Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto max-w-4xl font-display text-3xl sm:text-5xl lg:text-7xl font-bold tracking-tight text-white leading-tight"
        >
          <span className="sr-only">
            Graph intelligence for molecular toxicity, drug interactions, and multi-drug prescriptions.
          </span>
          <span aria-hidden="true">
            Graph intelligence for{" "}
            <span className="inline-block relative">
              <AnimatePresence mode="wait">
                <motion.span
                  key={morphIndex}
                  initial={{ opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -18 }}
                  transition={{ duration: 0.35, ease: "easeOut" }}
                  className={`inline-block font-extrabold ${MORPH_WORDS[morphIndex].color}`}
                >
                  {MORPH_WORDS[morphIndex].text}
                </motion.span>
              </AnimatePresence>
              <span className="text-white">.</span>
            </span>
          </span>
        </motion.h1>

        {/* Subtext */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto mt-5 sm:mt-6 max-w-2xl text-sm sm:text-base lg:text-lg text-muted-foreground font-sans leading-relaxed"
        >
          Deep Graph Neural Networks for pre-clinical molecular toxicity screening, pairwise drug-drug interaction classification, and multi-drug prescription risk analysis.
        </motion.p>

        {/* Dual CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="mt-7 sm:mt-8 flex flex-wrap items-center justify-center gap-3.5 sm:gap-4"
        >
          <Button
            asChild
            size="lg"
            className="rounded-full bg-cyan px-6 sm:px-7 py-2.5 sm:py-3 text-xs sm:text-sm font-semibold text-[#060A18] shadow-[0_0_25px_rgba(25,211,255,0.4)] transition-all hover:bg-cyan/90 hover:scale-[1.02] hover:shadow-[0_0_35px_rgba(25,211,255,0.6)]"
          >
            <a href={APP_URL}>
              Get started
              <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
            </a>
          </Button>

          <Button
            asChild
            variant="outline"
            size="lg"
            className="rounded-full border border-white/15 bg-white/5 px-6 sm:px-7 py-2.5 sm:py-3 text-xs sm:text-sm font-medium text-white backdrop-blur-md transition-all hover:bg-white/10 hover:border-white/25 hover:scale-[1.02]"
          >
            <a href="#modules">
              Explore modules
              <ChevronDown className="ml-2 h-4 w-4 text-cyan" aria-hidden="true" />
            </a>
          </Button>
        </motion.div>

        {/* Four Auto-Advancing Hero Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="mt-12 sm:mt-14 mx-auto max-w-md w-full flex items-center justify-between rounded-full border border-white/10 bg-[#0C1330]/70 p-1 sm:p-1.5 backdrop-blur-xl"
        >
          {HERO_TABS.map((tab) => {
            const isSelected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleSelectTab(tab.id as keyof typeof TAB_CARDS)}
                className={`relative flex-1 rounded-full px-2 sm:px-3 py-1.5 text-[11px] sm:text-xs font-medium transition-all ${
                  isSelected ? "text-white font-semibold" : "text-muted-foreground hover:text-white"
                }`}
              >
                {isSelected && (
                  <motion.div
                    layoutId="heroTabActive"
                    className="absolute inset-0 rounded-full bg-white/10 border border-white/15 shadow-sm"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
                  />
                )}
                <span className="relative z-10">{tab.label}</span>
                {isSelected && (
                  <div className="absolute bottom-0 left-2 right-2 sm:left-3 sm:right-3 h-[2px] overflow-hidden rounded-full bg-white/10">
                    <div
                      className="h-full bg-cyan transition-all duration-75"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                )}
              </button>
            );
          })}
        </motion.div>

        {/* Trio of Floating Status Cards with cross-fade & float loops */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
          <AnimatePresence mode="wait">
            {cards.map((card, i) => {
              const Icon = card.icon;
              const floatClasses = i === 0 ? "animate-float-1" : i === 1 ? "animate-float-2" : "animate-float-3";
              return (
                <motion.div
                  key={`${activeTab}-${i}`}
                  initial={{ opacity: 0, y: 15, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -15, scale: 0.96 }}
                  transition={{ duration: 0.4, delay: i * 0.08, ease: "easeOut" }}
                  className={`glass-card glass-card-hover rounded-2xl p-4 text-left ${floatClasses}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 border border-white/10 text-cyan">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-mono font-medium ${card.badgeColor}`}>
                      {card.badge}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-white">{card.title}</h4>
                  <p className="mt-1 text-xs text-muted-foreground">{card.subtitle}</p>
                  <div className="mt-3 pt-2.5 border-t border-white/6 flex items-center justify-between text-[11px] font-mono">
                    <span className="text-muted-foreground">Status / Value:</span>
                    <span className="text-white font-bold">{card.metric}</span>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        {/* Persona / Example Chips */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-2.5 sm:gap-4 text-xs"
        >
          <span className="text-muted-foreground font-mono text-[11px]">Demo presets:</span>
          {PERSONA_CHIPS.map((chip) => (
            <button
              key={chip.label}
              onClick={() => handleSelectTab(chip.tab as keyof typeof TAB_CARDS)}
              className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1.5 text-muted-foreground backdrop-blur-md transition-all hover:border-cyan/40 hover:bg-white/10 hover:text-white"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-cyan shadow-[0_0_6px_rgba(25,211,255,0.8)]" />
              <span className="font-semibold text-white">{chip.label}</span>
              <span className="hidden sm:inline text-muted-foreground/80 font-mono text-[10px]">· {chip.desc}</span>
            </button>
          ))}
        </motion.div>
      </div>
    </section>
  );
};
