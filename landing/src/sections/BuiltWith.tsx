import React from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight, Code2, Cpu, Database, Flame, FlaskConical, Network, Sparkles } from "lucide-react";
import { APP_URL } from "@/lib/links";

const TECH_STACK = [
  { name: "PyTorch", role: "Deep Learning Tensor Core", icon: Flame, color: "text-[#FF5C7A]" },
  { name: "PyTorch Geometric", role: "Graph Neural Networks (MPNN)", icon: Network, color: "text-cyan" },
  { name: "RDKit", role: "Cheminformatics & 2D Graphs", icon: FlaskConical, color: "text-mint" },
  { name: "Flask", role: "REST API & Python Runtime", icon: Code2, color: "text-amber" },
  { name: "NCBI PubChem", role: "Standardized SMILES Structures", icon: Database, color: "text-violet" },
  { name: "NIH / EPA Tox21", role: "10k Screening Data Challenge", icon: Sparkles, color: "text-cyan" },
  { name: "DDInter Benchmark", role: "122,378 Curated DDI Pairs", icon: Cpu, color: "text-mint" },
];

export const BuiltWith: React.FC = () => {
  return (
    <section className="relative py-20 bg-[#060A18] overflow-hidden w-full max-w-full border-t border-white/5">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 text-center mb-10">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-xs font-mono text-cyan mb-3">
          <span>[ Open Science Stack ]</span>
        </div>
        <h3 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-white">
          Built on open scientific foundations
        </h3>
        <p className="mt-2 text-sm text-muted-foreground max-w-xl mx-auto">
          Trained on public peer-reviewed toxicology assays and validated against canonical chemical knowledge bases.
        </p>
      </div>

      {/* Infinite Horizontal Marquee */}
      <div className="relative w-full overflow-hidden">
        {/* Left & Right Gradient Masks */}
        <div className="pointer-events-none absolute left-0 top-0 bottom-0 z-10 w-24 sm:w-36 bg-gradient-to-r from-[#060A18] to-transparent" />
        <div className="pointer-events-none absolute right-0 top-0 bottom-0 z-10 w-24 sm:w-36 bg-gradient-to-l from-[#060A18] to-transparent" />

        <div className="flex w-max animate-marquee">
          {/* First loop */}
          <div className="flex shrink-0 items-center gap-4 px-2">
            {TECH_STACK.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div
                  key={`first-${idx}`}
                  className="flex items-center gap-3 rounded-2xl border border-white/8 bg-[#0C1330]/80 px-5 py-3.5 backdrop-blur-md transition-all hover:border-cyan/40 hover:bg-[#0C1330]"
                >
                  <div className={`flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 border border-white/10 ${item.color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="text-left">
                    <span className="block text-xs font-semibold text-white font-mono">
                      {item.name}
                    </span>
                    <span className="block text-[10px] text-muted-foreground">
                      {item.role}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Duplicate loop for seamless infinite marquee */}
          <div className="flex shrink-0 items-center gap-4 px-2" aria-hidden="true">
            {TECH_STACK.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div
                  key={`second-${idx}`}
                  className="flex items-center gap-3 rounded-2xl border border-white/8 bg-[#0C1330]/80 px-5 py-3.5 backdrop-blur-md transition-all hover:border-cyan/40 hover:bg-[#0C1330]"
                >
                  <div className={`flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 border border-white/10 ${item.color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="text-left">
                    <span className="block text-xs font-semibold text-white font-mono">
                      {item.name}
                    </span>
                    <span className="block text-[10px] text-muted-foreground">
                      {item.role}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Inline CTA */}
      <div className="mt-10 flex justify-center">
        <Button
          asChild
          variant="outline"
          size="sm"
          className="rounded-full border border-white/15 bg-white/5 text-xs text-white hover:bg-white/10 hover:border-cyan/40"
        >
          <a href={APP_URL}>
            Explore full methodology in the app
            <ArrowRight className="ml-1.5 h-3.5 w-3.5 text-cyan" />
          </a>
        </Button>
      </div>
    </section>
  );
};
