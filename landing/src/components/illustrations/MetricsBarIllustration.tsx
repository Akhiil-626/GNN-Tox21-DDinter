import React from "react";
import { motion } from "motion/react";

interface Metric {
  name: string;
  gcn: number;
  gin: number;
  max: number;
  format: (v: number) => string;
}

const METRICS: Metric[] = [
  { name: "Test Accuracy", gcn: 0.600, gin: 0.609, max: 1.0, format: (v) => `${(v * 100).toFixed(1)}%` },
  { name: "Macro-F1", gcn: 0.491, gin: 0.490, max: 1.0, format: (v) => v.toFixed(3) },
  { name: "Major-Class Recall", gcn: 0.705, gin: 0.609, max: 1.0, format: (v) => `${(v * 100).toFixed(1)}%` },
];

export const MetricsBarIllustration: React.FC = () => {
  return (
    <div className="relative rounded-2xl border border-white/10 bg-[#0C1330]/80 p-5 backdrop-blur-xl shadow-2xl">
      <div className="mb-4 flex items-center justify-between border-b border-white/8 pb-3">
        <div>
          <span className="text-[11px] font-mono font-medium tracking-wider text-cyan uppercase">
            Cold-Start Evaluation
          </span>
          <h4 className="text-sm font-semibold text-white">GCN vs GIN Benchmark Comparison</h4>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[11px] font-mono text-muted-foreground">
          Illustrative example
        </span>
      </div>

      <div className="mb-4 flex items-center gap-6 font-mono text-xs">
        <span className="flex items-center gap-2 text-white font-medium">
          <span className="h-3 w-3 rounded-xs bg-cyan shadow-[0_0_8px_rgba(25,211,255,0.6)]" /> GCN Architecture
        </span>
        <span className="flex items-center gap-2 text-muted-foreground font-medium">
          <span className="h-3 w-3 rounded-xs bg-violet shadow-[0_0_8px_rgba(122,92,255,0.6)]" /> GIN Architecture
        </span>
      </div>

      <div className="space-y-4">
        {METRICS.map((m, idx) => (
          <div key={m.name} className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-medium">
              <span className="text-white">{m.name}</span>
              <div className="flex gap-4 font-mono text-[11px]">
                <span className="text-cyan font-bold">GCN {m.format(m.gcn)}</span>
                <span className="text-violet font-bold">GIN {m.format(m.gin)}</span>
              </div>
            </div>

            {/* GCN Bar */}
            <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(m.gcn / m.max) * 100}%` }}
                transition={{ duration: 0.9, delay: idx * 0.12, ease: "easeOut" }}
                className="h-full rounded-full bg-cyan shadow-[0_0_10px_rgba(25,211,255,0.5)]"
              />
            </div>

            {/* GIN Bar */}
            <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(m.gin / m.max) * 100}%` }}
                transition={{ duration: 0.9, delay: idx * 0.12 + 0.05, ease: "easeOut" }}
                className="h-full rounded-full bg-violet shadow-[0_0_10px_rgba(122,92,255,0.5)]"
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 border-t border-white/8 pt-3 text-[11px] text-muted-foreground flex justify-between">
        <span>Strict cold-start drug split (unseen during training)</span>
        <span className="font-mono text-cyan">Major recall 70.5%</span>
      </div>
    </div>
  );
};
