import React from "react";
import { APP_URL, MODULE_LINKS } from "@/lib/links";

export const FooterSection: React.FC = () => {
  const builtOnChips = [
    "PyTorch",
    "PyTorch Geometric",
    "RDKit",
    "Flask",
    "PubChem",
    "Tox21",
    "DDInter",
  ];

  const moduleNav = [
    { label: "Screening Module", url: MODULE_LINKS.screening },
    { label: "Interaction Checker", url: MODULE_LINKS.interactions },
    { label: "Prescription Network", url: MODULE_LINKS.prescription },
    { label: "Benchmark Performance", url: MODULE_LINKS.performance },
  ];

  return (
    <footer className="bg-[#0E1116] text-[#F2F4F7] py-16 border-t border-[#0E1116]">
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 pb-12 border-b border-[#F2F4F7]/15">
          {/* Col 1: Wordmark & Core Identity */}
          <div className="md:col-span-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-3.5 h-3.5 bg-[#D2FF3F] inline-block" />
                <span className="font-display font-extrabold text-xl tracking-tight text-[#F2F4F7]">
                  C-FOOTPRINT
                </span>
                <span className="font-mono text-[10px] uppercase bg-[#2147FF] text-[#F2F4F7] px-2 py-0.5 rounded-[4px]">
                  Research Edition
                </span>
              </div>
              <p className="text-sm text-[#F2F4F7]/75 max-w-[42ch] leading-relaxed">
                Graph neural network molecular toxicity screening and multi-drug interaction
                assessment platform.
              </p>
            </div>

            <div className="mt-6 text-xs font-mono text-[#F2F4F7]/60">
              Contract preserved: local server deployment.
            </div>
          </div>

          {/* Col 2: Module Links */}
          <div className="md:col-span-3">
            <h4 className="font-mono text-xs uppercase tracking-wider text-[#D2FF3F] mb-4">
              Dashboard Modules
            </h4>
            <ul className="space-y-2 text-sm">
              {moduleNav.map((item) => (
                <li key={item.label}>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[#F2F4F7]/80 hover:text-[#D2FF3F] transition-colors"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
              <li>
                <a
                  href={APP_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#2147FF] hover:underline font-medium"
                >
                  Launch Full Dashboard &rarr;
                </a>
              </li>
            </ul>
          </div>

          {/* Col 3: Built On Stack Chips */}
          <div className="md:col-span-4">
            <h4 className="font-mono text-xs uppercase tracking-wider text-[#D2FF3F] mb-4">
              Built On Open Science
            </h4>
            <div className="flex flex-wrap gap-2">
              {builtOnChips.map((tech) => (
                <span
                  key={tech}
                  className="font-mono text-xs bg-[#F2F4F7]/10 text-[#F2F4F7] px-2.5 py-1 rounded-[4px] border border-[#F2F4F7]/20"
                >
                  {tech}
                </span>
              ))}
            </div>
            <div className="mt-5 text-xs text-[#F2F4F7]/70 leading-relaxed">
              Interaction dataset source:{" "}
              <a
                href="https://ddinter.scbdd.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#D2FF3F] underline underline-offset-2 hover:text-white"
              >
                DDInter Database
              </a>{" "}
              (licensed under CC BY-NC-SA 4.0, non-commercial).
            </div>
          </div>
        </div>

        {/* Disclaimer & Bottom Strip */}
        <div className="pt-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs text-[#F2F4F7]/60 font-mono">
          <p className="max-w-[70ch]">
            <strong>Disclaimer:</strong> Strictly for academic research and educational evaluation. Not intended
            for clinical triage, medical diagnosis, or pharmacological treatment directives.
          </p>
          <p className="shrink-0">
            © {new Date().getFullYear()} C-FOOTPRINT.
          </p>
        </div>
      </div>
    </footer>
  );
};
