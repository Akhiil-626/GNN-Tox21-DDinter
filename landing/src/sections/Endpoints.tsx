import React from "react";
import { motion } from "motion/react";
import { ShieldCheck, Flame, Dna, Activity, HeartPulse, Zap } from "lucide-react";

interface EndpointCard {
  id: string;
  name: string;
  category: "Nuclear Receptor" | "Stress Response";
  chips: string[];
  description: string;
  biomarker: string;
  icon: any;
  color: string;
  gradient: string;
}

const ENDPOINTS_CARDS: EndpointCard[] = [
  {
    id: "nr-ar",
    name: "Androgen Receptor",
    category: "Nuclear Receptor",
    chips: ["NR-AR", "NR-AR-LBD"],
    description: "Mediates biological effects of androgens. Critical for evaluating endocrine disruption in male reproductive biology.",
    biomarker: "Transactivation & Ligand-Binding Domain assays",
    icon: ShieldCheck,
    color: "text-cyan",
    gradient: "from-cyan/20 via-cyan/5 to-transparent",
  },
  {
    id: "nr-er",
    name: "Estrogen Receptor",
    category: "Nuclear Receptor",
    chips: ["NR-ER", "NR-ER-LBD"],
    description: "Transcription factor governing cellular growth and reproductive homeostasis. Sensitive to xenoestrogens.",
    biomarker: "Full Receptor & Alpha Ligand-Binding assays",
    icon: Activity,
    color: "text-violet",
    gradient: "from-violet/20 via-violet/5 to-transparent",
  },
  {
    id: "nr-ahr",
    name: "Aryl Hydrocarbon",
    category: "Nuclear Receptor",
    chips: ["NR-AhR"],
    description: "Key regulator of xenobiotic metabolism enzymes (CYP1A1). Mediates cellular responses to planar aromatic hydrocarbons.",
    biomarker: "Dioxin response element reporter gene",
    icon: Flame,
    color: "text-amber",
    gradient: "from-amber/20 via-amber/5 to-transparent",
  },
  {
    id: "nr-aromatase",
    name: "Aromatase Enzyme",
    category: "Nuclear Receptor",
    chips: ["NR-Aromatase"],
    description: "Cytochrome P450 enzyme converting C19 androgens to estrogens. Essential for screening hormone synthesis disruptors.",
    biomarker: "CYP19A1 catalytic inhibition assay",
    icon: HeartPulse,
    color: "text-coral",
    gradient: "from-coral/20 via-coral/5 to-transparent",
  },
  {
    id: "nr-pparg",
    name: "PPAR-gamma",
    category: "Nuclear Receptor",
    chips: ["NR-PPAR-gamma"],
    description: "Peroxisome proliferator-activated receptor gamma controlling lipid metabolism, insulin sensitivity, and adipogenesis.",
    biomarker: "Nuclear receptor transactivation assay",
    icon: Zap,
    color: "text-mint",
    gradient: "from-mint/20 via-mint/5 to-transparent",
  },
  {
    id: "sr-stress",
    name: "Stress Response Pathways",
    category: "Stress Response",
    chips: ["SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"],
    description: "Comprehensive 5-endpoint cascade profiling oxidative stress (ARE), genotoxicity (ATAD5), heat shock (HSE), mitochondrial collapse (MMP), and p53 tumor suppression.",
    biomarker: "Multiplexed cellular viability and DNA damage reporters",
    icon: Dna,
    color: "text-cyan",
    gradient: "from-cyan/20 via-violet/10 to-transparent",
  },
];

export const Endpoints: React.FC = () => {
  return (
    <section id="endpoints" className="relative py-24 sm:py-32 bg-[#060A18] border-t border-white/5 scroll-mt-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-xs font-mono text-cyan mb-3">
            <span>[ Tox21 Bioassays ]</span>
          </div>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white">
            12 Targeted Nuclear Receptors & Stress Pathways
          </h2>
          <p className="mt-3 text-base text-muted-foreground">
            C-FOOTPRINT predicts compound activity across the NIH/EPA Tox21 high-throughput screening panel, enabling early identification of potential endocrine disruption and cellular toxicity.
          </p>
        </div>

        {/* 6 Portrait Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {ENDPOINTS_CARDS.map((card, idx) => {
            const Icon = card.icon;
            return (
              <motion.div
                key={card.id}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: idx * 0.08, ease: [0.22, 1, 0.36, 1] }}
                className="group relative rounded-2xl border border-white/8 bg-[#0C1330]/70 p-6 backdrop-blur-xl flex flex-col justify-between overflow-hidden transition-all duration-300 hover:border-cyan/40 hover:-translate-y-1 hover:shadow-[0_15px_35px_-10px_rgba(25,211,255,0.2)]"
              >
                {/* Gradient subtle spotlight header */}
                <div
                  className={`pointer-events-none absolute -top-12 -right-12 h-36 w-36 rounded-full bg-gradient-to-br ${card.gradient} blur-2xl opacity-60 transition-opacity group-hover:opacity-100`}
                />

                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                      {card.category}
                    </span>
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 border border-white/10 ${card.color}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                  </div>

                  <h3 className="font-display text-lg font-bold text-white group-hover:text-cyan transition-colors">
                    {card.name}
                  </h3>

                  {/* Chips */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {card.chips.map((chip) => (
                      <span
                        key={chip}
                        className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 font-mono text-[11px] font-semibold text-white/90"
                      >
                        {chip}
                      </span>
                    ))}
                  </div>

                  <p className="mt-4 text-xs text-muted-foreground leading-relaxed">
                    {card.description}
                  </p>
                </div>

                <div className="mt-6 pt-3 border-t border-white/6 flex items-center justify-between text-[11px] font-mono text-muted-foreground">
                  <span className="truncate pr-2">{card.biomarker}</span>
                  <span className="text-cyan font-semibold">Tox21</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
