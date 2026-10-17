import React, { useEffect, useRef, useState } from "react";
import { motion, useInView } from "motion/react";
import { Layers, ShieldCheck, Database, Pill } from "lucide-react";

interface StatItem {
  id: string;
  target: number;
  suffix?: string;
  label: string;
  category: string;
  desc: string;
  icon: any;
  accent: string;
  format: (n: number) => string;
}

const STATS_DATA: StatItem[] = [
  {
    id: "endpoints",
    target: 12,
    label: "Tox21 Endpoints",
    category: "Bioassay Coverage",
    desc: "Nuclear receptors & cellular stress pathways screened across canonical SMILES.",
    icon: Layers,
    accent: "text-cyan border-cyan/30 bg-cyan/10",
    format: (n) => `${Math.round(n)}`,
  },
  {
    id: "classes",
    target: 3,
    label: "Severity Classes",
    category: "Risk Tiers",
    desc: "Minor, Moderate, and Major severity classification for pairwise clinical interactions.",
    icon: ShieldCheck,
    accent: "text-mint border-mint/30 bg-mint/10",
    format: (n) => `${Math.round(n)}`,
  },
  {
    id: "pairs",
    target: 122378,
    label: "Labelled Drug Pairs",
    category: "Dataset Scale",
    desc: "Expert-curated DDI pairs from the DDInter database prepared for GNN training.",
    icon: Database,
    accent: "text-violet border-violet/30 bg-violet/10",
    format: (n) => Math.round(n).toLocaleString(),
  },
  {
    id: "max-drugs",
    target: 5,
    label: "Max Drugs Per Check",
    category: "Polypharmacy Regimen",
    desc: "Simultaneous multi-drug prescription network analysis with similarity inference.",
    icon: Pill,
    accent: "text-amber border-amber/30 bg-amber/10",
    format: (n) => `${Math.round(n)}`,
  },
];

export const Stats: React.FC = () => {
  return (
    <section className="relative py-20 sm:py-24 bg-[#060A18] border-t border-white/5 w-full max-w-full overflow-hidden">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {STATS_DATA.map((stat, idx) => (
            <StatCard key={stat.id} stat={stat} index={idx} />
          ))}
        </div>
      </div>
    </section>
  );
};

const StatCard: React.FC<{ stat: StatItem; index: number }> = ({ stat, index }) => {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: "some" });
  const [count, setCount] = useState(stat.target);
  const Icon = stat.icon;

  useEffect(() => {
    if (!isInView) return;

    let startTime: number | null = null;
    const duration = 1200;

    const step = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      setCount(ease * stat.target);

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        setCount(stat.target);
      }
    };

    requestAnimationFrame(step);
  }, [isInView, stat.target]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.1 }}
      transition={{ duration: 0.5, delay: index * 0.08, ease: [0.22, 1, 0.36, 1] }}
      className="glass-card glass-card-hover rounded-2xl p-6 flex flex-col justify-between"
    >
      <div>
        <div className="flex items-center justify-between mb-4">
          <span className="font-mono text-[10px] tracking-wider text-muted-foreground uppercase">
            {stat.category}
          </span>
          <div className={`flex h-7 w-7 items-center justify-center rounded-lg border ${stat.accent}`}>
            <Icon className="h-3.5 w-3.5" />
          </div>
        </div>

        {/* Big Tabular Counter */}
        <div className="font-display text-4xl sm:text-5xl font-extrabold tracking-tight text-white font-mono">
          <span aria-label={`${stat.target} ${stat.label}`}>
            {stat.format(count)}
          </span>
        </div>

        <h4 className="mt-2 text-sm font-semibold text-foreground">{stat.label}</h4>
      </div>

      <p className="mt-4 text-xs text-muted-foreground leading-relaxed border-t border-white/6 pt-3">
        {stat.desc}
      </p>
    </motion.div>
  );
};
