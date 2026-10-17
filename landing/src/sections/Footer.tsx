import React from "react";
import { Activity, ExternalLink } from "lucide-react";
import { MODULE_LINKS, GITHUB_URL } from "@/lib/links";

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-white/8 bg-[#060A18] py-16 text-muted-foreground">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-4">
          {/* Col 1: Brand & Tagline */}
          <div className="space-y-4">
            <div className="flex items-center gap-2.5 text-white">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-cyan to-violet text-[#060A18] shadow-[0_0_15px_rgba(25,211,255,0.4)]">
                <Activity className="h-4 w-4 stroke-[2.4]" aria-hidden="true" />
              </div>
              <span className="font-display text-lg font-bold tracking-tight">
                C-FOOTPRINT
              </span>
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Deep Graph Neural Networks for pre-clinical molecular toxicity screening, atom-level saliency attribution, and multi-drug interaction risk assessment.
            </p>
            <div className="pt-1 text-[11px] font-mono text-cyan">
              CC BY-NC-SA 4.0 Non-Commercial Benchmarks
            </div>
          </div>

          {/* Col 2: Modules */}
          <div className="space-y-3">
            <h4 className="font-display text-xs font-bold tracking-wider text-white uppercase">
              Modules
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a
                  href={MODULE_LINKS.screening}
                  className="transition-colors hover:text-cyan"
                >
                  Compound screening
                </a>
              </li>
              <li>
                <a
                  href={MODULE_LINKS.interactions}
                  className="transition-colors hover:text-cyan"
                >
                  Interaction check
                </a>
              </li>
              <li>
                <a
                  href={MODULE_LINKS.prescription}
                  className="transition-colors hover:text-cyan"
                >
                  Prescription checker
                </a>
              </li>
              <li>
                <a
                  href={MODULE_LINKS.performance}
                  className="transition-colors hover:text-cyan"
                >
                  Model performance
                </a>
              </li>
            </ul>
          </div>

          {/* Col 3: Tox21 Endpoints */}
          <div className="space-y-3">
            <h4 className="font-display text-xs font-bold tracking-wider text-white uppercase">
              Tox21 Bioassays
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#endpoints" className="transition-colors hover:text-cyan">
                  Nuclear Receptors (NR)
                </a>
              </li>
              <li>
                <a href="#endpoints" className="transition-colors hover:text-cyan">
                  Stress Pathways (SR)
                </a>
              </li>
              <li>
                <a href="#performance" className="transition-colors hover:text-cyan">
                  Bemis-Murcko Scaffold Split
                </a>
              </li>
              <li>
                <a href="#modules" className="transition-colors hover:text-cyan">
                  Atom Gradient Saliency
                </a>
              </li>
            </ul>
          </div>

          {/* Col 4: Data Attributions */}
          <div className="space-y-3">
            <h4 className="font-display text-xs font-bold tracking-wider text-white uppercase">
              Data Attributions
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a
                  href="https://ddinter.scbdd.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 transition-colors hover:text-cyan"
                >
                  DDInter Database
                  <ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              </li>
              <li>
                <span className="text-muted-foreground">
                  NIH / EPA Tox21 Challenge
                </span>
              </li>
              <li>
                <span className="text-muted-foreground">
                  NCBI PubChem Standardized SMILES
                </span>
              </li>
              {GITHUB_URL ? (
                <li>
                  <a
                    href={GITHUB_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 transition-colors hover:text-cyan"
                  >
                    GitHub Repository
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </a>
                </li>
              ) : null}
            </ul>
          </div>
        </div>

        {/* Bottom Bar: Mandatory Disclaimer & Copyright */}
        <div className="mt-12 border-t border-white/8 pt-8 text-[11px] leading-relaxed text-muted-foreground">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="max-w-3xl">
              <strong className="text-white">Disclaimer: </strong>
              For pre-clinical scientific research and educational purposes only. C-FOOTPRINT is an in silico computational exploration tool and is not validated or intended for clinical diagnosis, therapeutic recommendations, or medical prescription decision-making.
            </p>
            <p className="shrink-0 font-mono text-[10px]">
              &copy; {new Date().getFullYear()} C-FOOTPRINT Research.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};
