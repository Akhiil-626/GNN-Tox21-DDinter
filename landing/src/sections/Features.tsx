import React from "react";
import { motion } from "motion/react";
import { Eye, AlertOctagon, Sparkles, Network, ShieldAlert, BookOpen } from "lucide-react";

export const Features: React.FC = () => {
  return (
    <section className="relative py-24 sm:py-32 bg-[#060A18] border-t border-white/5">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-xs font-mono text-cyan mb-3">
            <span>[ Methodological Rigor ]</span>
          </div>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white">
            Interpretability and scientific transparency
          </h2>
          <p className="mt-3 text-base text-muted-foreground">
            Black-box predictions are inadequate for pharmacology. C-FOOTPRINT provides transparent mechanistic attribution alongside clear clinical boundaries.
          </p>
        </div>

        {/* Two Wide Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Card 1: Explainable by design */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="glass-card glass-card-hover rounded-2xl p-8 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan/15 border border-cyan/30 text-cyan">
                  <Eye className="h-6 w-6" aria-hidden="true" />
                </div>
                <span className="font-mono text-xs text-cyan border border-cyan/30 rounded-full px-3 py-1 bg-cyan/10">
                  Feature 01
                </span>
              </div>

              <h3 className="font-display text-2xl font-bold text-white">
                Explainable by design
              </h3>
              <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
                Rather than delivering opaque scalar risk scores, C-FOOTPRINT pinpoints the exact chemical substructures and toxicophores driving predictions.
              </p>

              <div className="mt-6 space-y-4 border-t border-white/8 pt-5">
                <div className="flex items-start gap-3">
                  <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-cyan" aria-hidden="true" />
                  <div className="text-xs text-muted-foreground">
                    <span className="font-semibold text-white">Atom-Level Saliency: </span>
                    Gradient backpropagation calculates <code className="font-mono text-[11px] text-cyan bg-cyan/10 px-1 py-0.5 rounded">∂Logit / ∂Atom</code> to identify functional toxicophores directly on the 2D molecular graph.
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Network className="mt-0.5 h-4 w-4 shrink-0 text-cyan" aria-hidden="true" />
                  <div className="text-xs text-muted-foreground">
                    <span className="font-semibold text-white">Topological Network Mapping: </span>
                    Polypharmacy regimens map pairwise severity into an interactive graph with per-drug risk distributions and one-click image export.
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 rounded-xl bg-[#060A18]/80 border border-white/8 p-3 text-center font-mono text-[11px] text-cyan">
              Mechanistic Attribution Verified via RDKit
            </div>
          </motion.div>

          {/* Card 2: Honest about limits */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.5, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="glass-card glass-card-hover rounded-2xl p-8 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-coral/15 border border-coral/30 text-coral">
                  <AlertOctagon className="h-6 w-6" aria-hidden="true" />
                </div>
                <span className="font-mono text-xs text-coral border border-coral/30 rounded-full px-3 py-1 bg-coral/10">
                  Feature 02
                </span>
              </div>

              <h3 className="font-display text-2xl font-bold text-white">
                Honest about limits
              </h3>
              <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
                Computational models must state their statistical boundaries clearly. C-FOOTPRINT differentiates empirical documentation from negative findings.
              </p>

              <div className="mt-6 space-y-4 border-t border-white/8 pt-5">
                <div className="flex items-start gap-3">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber" aria-hidden="true" />
                  <div className="text-xs text-muted-foreground">
                    <span className="font-semibold text-white">&ldquo;Not in DDInter&rdquo; != Safe: </span>
                    Absence of an interaction in DDInter indicates an undocumented pair in published literature, never proof of clinical compatibility.
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <BookOpen className="mt-0.5 h-4 w-4 shrink-0 text-coral" aria-hidden="true" />
                  <div className="text-xs text-muted-foreground">
                    <span className="font-semibold text-white">Research & Education Scope: </span>
                    Designed strictly for in silico hypothesis generation and academic research. It is never a substitute for clinical pharmacist review or medical advice.
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 rounded-xl bg-[#060A18]/80 border border-white/8 p-3 text-center font-mono text-[11px] text-muted-foreground">
              Non-Commercial CC BY-NC-SA 4.0 Attributed
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
