import React from "react";
import { motion } from "motion/react";
import { Database, ShieldCheck, Scale, Check } from "lucide-react";

const TRUST_PILLARS = [
  {
    id: "data-provenance",
    title: "Data Provenance",
    subtitle: "Standardized Open Repositories",
    icon: Database,
    color: "text-cyan",
    badge: "Public Science",
    points: [
      "NIH & EPA Tox21 10k chemical library covering 12 high-throughput bioassays.",
      "DDInter curated database under Creative Commons CC BY-NC-SA 4.0.",
      "Canonical SMILES standardization & structure validation via NCBI PubChem.",
    ],
  },
  {
    id: "evaluation-protocol",
    title: "Evaluation Protocol",
    subtitle: "Zero-Leakage Benchmark Splits",
    icon: ShieldCheck,
    color: "text-mint",
    badge: "Cold-Start",
    points: [
      "Bemis-Murcko scaffold split prevents memorization of common core rings.",
      "Cold-start graph partition tests pairs where candidate drugs never appeared in train.",
      "Full macro-F1 and class-stratified recall auditing reported openly.",
    ],
  },
  {
    id: "clinical-boundaries",
    title: "Clinical Boundaries",
    subtitle: "Pre-Clinical Discovery Scope",
    icon: Scale,
    color: "text-amber",
    badge: "Compliance",
    points: [
      "Strictly intended for pre-clinical research and university education.",
      "In silico hypothesis generation to prioritize in vitro lab assays.",
      "Not diagnostic software, clinical decision support, or medical prescription advice.",
    ],
  },
];

export const Trust: React.FC = () => {
  return (
    <section className="relative py-24 sm:py-32 bg-[#060A18] border-t border-white/5">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-xs font-mono text-cyan mb-3">
            <span>[ Governance & Trust ]</span>
          </div>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white">
            Architected for scientific integrity
          </h2>
          <p className="mt-3 text-base text-muted-foreground">
            Built from the ground up on verifiable public datasets, leak-free evaluation protocols, and clear clinical boundary disclosures.
          </p>
        </div>

        {/* 3 Pillars Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TRUST_PILLARS.map((pillar, idx) => {
            const Icon = pillar.icon;
            return (
              <motion.div
                key={pillar.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ duration: 0.5, delay: idx * 0.1, ease: [0.22, 1, 0.36, 1] }}
                className="glass-card glass-card-hover rounded-2xl p-6 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-5">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 border border-white/10 ${pillar.color}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="font-mono text-[10px] text-muted-foreground border border-white/10 bg-white/5 rounded-full px-2.5 py-0.5">
                      {pillar.badge}
                    </span>
                  </div>

                  <h3 className="font-display text-lg font-bold text-white">
                    {pillar.title}
                  </h3>
                  <p className="font-mono text-xs text-muted-foreground mb-5">
                    {pillar.subtitle}
                  </p>

                  <ul className="space-y-3 border-t border-white/8 pt-4">
                    {pillar.points.map((pt, pIdx) => (
                      <li key={pIdx} className="flex items-start gap-2.5 text-xs text-muted-foreground leading-relaxed">
                        <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan" />
                        <span>{pt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
