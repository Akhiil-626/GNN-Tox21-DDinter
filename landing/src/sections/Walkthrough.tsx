import React, { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Lock, ShieldAlert, Activity } from "lucide-react";

export const Walkthrough: React.FC = () => {
  const [step, setStep] = useState(0);

  // 3-step looping cycle every 3.5s
  useEffect(() => {
    const timer = setInterval(() => {
      setStep((prev) => (prev + 1) % 3);
    }, 3500);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="relative py-24 sm:py-32 bg-[#060A18] overflow-hidden border-t border-white/5">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-xs font-mono text-cyan mb-3">
            <span>[ Workflow Walkthrough ]</span>
          </div>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white">
            Simulate multi-drug regimens in seconds
          </h2>
          <p className="mt-3 text-base text-muted-foreground">
            Watch how C-FOOTPRINT resolves pairwise polypharmacy graphs, checks DDInter database records, and executes similarity fallback inference.
          </p>
        </div>

        {/* Browser Mockup Window */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="relative mx-auto max-w-4xl rounded-2xl border border-white/12 bg-[#0C1330]/90 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8)] backdrop-blur-2xl overflow-hidden"
        >
          {/* Browser Chrome Header */}
          <div className="flex items-center justify-between border-b border-white/8 bg-[#060A18]/80 px-4 py-3">
            {/* Window controls */}
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-[#FF5C7A]/80 inline-block" />
              <span className="h-3 w-3 rounded-full bg-[#FFB84D]/80 inline-block" />
              <span className="h-3 w-3 rounded-full bg-[#35E0A1]/80 inline-block" />
            </div>

            {/* URL bar */}
            <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 sm:px-4 py-1 text-[11px] sm:text-xs font-mono text-muted-foreground max-w-[190px] sm:max-w-none sm:w-96 justify-center truncate">
              <Lock className="h-3 w-3 text-cyan shrink-0" />
              <span className="truncate">c-footprint.local/prescription</span>
            </div>

            {/* Status / Badge */}
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-cyan/15 border border-cyan/30 px-2 py-0.5 text-[10px] font-mono text-cyan font-medium hidden sm:inline-block">
                GNN Live
              </span>
            </div>
          </div>

          {/* Browser Body */}
          <div className="p-6 sm:p-8 space-y-6">
            {/* Drug Tray (Step 1) */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                  Prescription Regimen (3 compounds)
                </span>
                <span className="text-[11px] font-mono text-cyan">
                  Phase {step + 1} of 3: {step === 0 ? "Regimen Input" : step === 1 ? "Graph Inference" : "Risk Report"}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="flex items-center gap-3 rounded-xl border border-coral/40 bg-coral/10 p-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-coral/20 text-coral font-mono text-xs font-bold">
                    Rx 1
                  </div>
                  <div>
                    <h5 className="text-xs font-bold text-white">Warfarin</h5>
                    <span className="text-[10px] text-coral font-mono">Anticoagulant</span>
                  </div>
                </div>

                <div className="flex items-center gap-3 rounded-xl border border-coral/40 bg-coral/10 p-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-coral/20 text-coral font-mono text-xs font-bold">
                    Rx 2
                  </div>
                  <div>
                    <h5 className="text-xs font-bold text-white">Aspirin</h5>
                    <span className="text-[10px] text-coral font-mono">Antiplatelet NSAID</span>
                  </div>
                </div>

                <div className="flex items-center gap-3 rounded-xl border border-amber/40 bg-amber/10 p-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber/20 text-amber font-mono text-xs font-bold">
                    Rx 3
                  </div>
                  <div>
                    <h5 className="text-xs font-bold text-white">Metformin</h5>
                    <span className="text-[10px] text-amber font-mono">Biguanide</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Interactive Graph Simulation (Step 2) */}
            <div className="rounded-xl border border-white/8 bg-[#060A18]/80 p-5">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold text-white flex items-center gap-2">
                  <Activity className="h-4 w-4 text-cyan" />
                  Topological Severity Mapping
                </span>
                <span className="font-mono text-[10px] text-muted-foreground">
                  Dual-Encoder MPNN
                </span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                {/* Pair 1 */}
                <div className="flex items-center justify-between rounded-lg border border-coral/30 bg-coral/5 p-3">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-coral animate-ping" />
                    <span className="text-white font-semibold">Warfarin ↔ Aspirin</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-muted-foreground text-[11px] hidden sm:inline">DDInter #1248</span>
                    <span className="rounded-md bg-coral/20 px-2 py-0.5 font-bold text-coral text-[11px]">
                      Major Risk (Bleeding)
                    </span>
                  </div>
                </div>

                {/* Pair 2 */}
                <div className="flex items-center justify-between rounded-lg border border-amber/30 bg-amber/5 p-3">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-amber" />
                    <span className="text-white font-semibold">Warfarin ↔ Metformin</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-muted-foreground text-[11px] hidden sm:inline">Inferred via Phenformin</span>
                    <span className="rounded-md bg-amber/20 px-2 py-0.5 font-bold text-amber text-[11px]">
                      Moderate Risk (Glucose flux)
                    </span>
                  </div>
                </div>

                {/* Pair 3 */}
                <div className="flex items-center justify-between rounded-lg border border-mint/30 bg-mint/5 p-3">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-mint" />
                    <span className="text-white font-semibold">Aspirin ↔ Metformin</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-muted-foreground text-[11px] hidden sm:inline">No known adverse edge</span>
                    <span className="rounded-md bg-mint/20 px-2 py-0.5 font-bold text-mint text-[11px]">
                      Minor / Tolerated
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Assessment Verdict (Step 3) */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 rounded-xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-3 text-left">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-coral/20 text-coral border border-coral/40">
                  <ShieldAlert className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Regimen Alert: Severe Interaction Detected</h4>
                  <p className="text-[11px] text-muted-foreground">
                    Combination of Warfarin and Aspirin increases gastrointestinal bleeding hazard. Clinical review advised.
                  </p>
                </div>
              </div>

              <div className="shrink-0 flex items-center gap-2 font-mono text-xs">
                <span className="rounded-full bg-white/10 px-3 py-1 text-white text-[11px]">
                  Illustrative simulation
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
