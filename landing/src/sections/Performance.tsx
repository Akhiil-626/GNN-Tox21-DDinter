import React from "react";
import { motion } from "motion/react";
import { Info, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { APP_URL } from "@/lib/links";

interface BenchmarkMetric {
  name: string;
  description: string;
  gcn: number;
  gin: number;
  format: (v: number) => string;
}

const BENCHMARKS: BenchmarkMetric[] = [
  {
    name: "Test Accuracy",
    description: "Overall 3-class severity accuracy on strictly unseen test drugs (cold-start).",
    gcn: 0.600,
    gin: 0.609,
    format: (v) => `${(v * 100).toFixed(1)}%`,
  },
  {
    name: "Macro-F1 Score",
    description: "Unweighted harmonic mean across Minor, Moderate, and Major severity classes.",
    gcn: 0.491,
    gin: 0.490,
    format: (v) => v.toFixed(3),
  },
  {
    name: "Major-Class Recall",
    description: "Sensitivity in detecting severe, high-risk interactions where missed calls carry clinical hazard.",
    gcn: 0.705,
    gin: 0.609,
    format: (v) => `${(v * 100).toFixed(1)}%`,
  },
];

export const Performance: React.FC = () => {
  return (
    <section id="performance" className="relative py-24 sm:py-32 bg-[#060A18] border-t border-white/5 scroll-mt-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-xs font-mono text-cyan mb-3">
            <span>[ Benchmark Evaluation ]</span>
          </div>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white">
            GCN vs. GIN on Unseen Compounds
          </h2>
          <p className="mt-3 text-base text-muted-foreground">
            Strict cold-start split evaluation where test compounds were completely excluded from the training dataset, verifying true generalization to novel chemical scaffolds.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-center gap-8 font-mono text-xs mb-10">
          <div className="flex items-center gap-2.5">
            <span className="h-3 w-3 rounded-full bg-cyan shadow-[0_0_8px_rgba(25,211,255,0.8)]" />
            <span className="font-bold text-white">GCN (Graph Convolutional Network)</span>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="h-3 w-3 rounded-full bg-violet shadow-[0_0_8px_rgba(122,92,255,0.8)]" />
            <span className="font-bold text-white">GIN (Graph Isomorphism Network)</span>
          </div>
        </div>

        {/* Grouped Horizontal Comparison Bars */}
        <div className="mx-auto max-w-4xl space-y-6">
          {BENCHMARKS.map((m, idx) => (
            <motion.div
              key={m.name}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{
                duration: 0.5,
                delay: idx * 0.1,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="glass-card rounded-2xl p-6"
            >
              <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1">
                <h3 className="font-display text-base font-bold text-white">
                  {m.name}
                </h3>
                <div className="flex items-center gap-5 font-mono text-xs">
                  <span className="font-bold text-cyan">
                    GCN: {m.format(m.gcn)}
                  </span>
                  <span className="font-bold text-violet">
                    GIN: {m.format(m.gin)}
                  </span>
                </div>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {m.description}
              </p>

              {/* Bars Comparison */}
              <div className="mt-4 space-y-3">
                {/* GCN Bar */}
                <div className="flex items-center gap-3">
                  <span className="w-10 font-mono text-[11px] font-bold text-cyan">
                    GCN
                  </span>
                  <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-white/5">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${m.gcn * 100}%` }}
                      viewport={{ once: true }}
                      transition={{
                        duration: 0.8,
                        delay: idx * 0.1,
                        ease: "easeOut",
                      }}
                      className="h-full rounded-full bg-cyan shadow-[0_0_10px_rgba(25,211,255,0.5)]"
                    />
                  </div>
                  <span className="w-12 text-right font-mono text-xs font-bold text-cyan">
                    {m.format(m.gcn)}
                  </span>
                </div>

                {/* GIN Bar */}
                <div className="flex items-center gap-3">
                  <span className="w-10 font-mono text-[11px] font-bold text-violet">
                    GIN
                  </span>
                  <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-white/5">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${m.gin * 100}%` }}
                      viewport={{ once: true }}
                      transition={{
                        duration: 0.8,
                        delay: idx * 0.1 + 0.05,
                        ease: "easeOut",
                      }}
                      className="h-full rounded-full bg-violet shadow-[0_0_10px_rgba(122,92,255,0.5)]"
                    />
                  </div>
                  <span className="w-12 text-right font-mono text-xs font-bold text-violet">
                    {m.format(m.gin)}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Nuance Note on Minor Weakness & Cold-Start */}
        <div className="mx-auto mt-8 max-w-4xl rounded-xl border border-white/10 bg-[#0C1330]/60 p-4 backdrop-blur-md">
          <div className="flex items-start gap-3">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-cyan" aria-hidden="true" />
            <div className="text-xs text-muted-foreground leading-relaxed">
              <span className="font-semibold text-white">
                Critical Nuance on Class Distribution:{" "}
              </span>
              The Minor severity class is the weakest in the dataset, reflecting documented reporting bias in pre-clinical pharmacology where mild interactions are frequently under-reported. Crucially, GCN achieves <strong>70.5% Major-Class Recall</strong>, successfully prioritizing the highest-risk drug interactions.
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-10 flex justify-center">
          <Button
            asChild
            className="rounded-full bg-cyan px-6 py-2.5 text-xs font-semibold text-[#060A18] shadow-[0_0_20px_rgba(25,211,255,0.35)] hover:bg-cyan/90 hover:scale-[1.02]"
          >
            <a href={APP_URL}>
              Inspect benchmark in app
              <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
            </a>
          </Button>
        </div>
      </div>
    </section>
  );
};
