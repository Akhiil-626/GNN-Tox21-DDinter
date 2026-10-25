import React from "react";
import { APP_URL } from "@/lib/links";
import { Button } from "@/components/ui/button";
import { MorphingText } from "@/components/ui/morphing-text";
import { Plane } from "@/components/signature/planes";
import { ArcSet } from "@/components/signature/arcs";
import { AssayPlateReplica } from "@/components/replicas/assay-plate-replica";
import { ArrowDownIcon, ExternalLinkIcon } from "lucide-react";

export const HeroSection: React.FC = () => {
  const handleScrollToModules = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const el = document.getElementById("modules-stage");
    if (el) {
      const navOffset = 64;
      const targetPos = el.getBoundingClientRect().top + window.scrollY - navOffset;
      window.scrollTo({ top: targetPos, behavior: "smooth" });
    }
  };

  return (
    <section className="relative overflow-hidden bg-[#F2F4F7] pt-12 pb-20 md:pt-20 md:pb-32 border-b border-[#0E1116]">
      {/* Signature Graphic Elements */}
      <Plane
        color="blue"
        rotate={-3}
        parallaxSpeed={0.2}
        className="w-[320px] h-[340px] md:w-[480px] md:h-[440px] right-[-40px] top-[10%] opacity-90 hidden sm:block"
      />
      <ArcSet
        color="lime"
        baseRadius={320}
        gap={40}
        rotationDuration={34}
        className="right-[-80px] top-[15%] hidden md:block"
      />

      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column (Cols 1-7): Strictly Left-Aligned Asymmetric Content */}
          <div className="lg:col-span-7 flex flex-col items-start text-left">
            {/* Exactly one subtle category eyebrow allowed on the entire page */}
            <div className="inline-flex items-center gap-2 mb-6">
              <span className="w-2 h-2 bg-[#2147FF] inline-block" />
              <span className="font-mono text-xs font-semibold tracking-wider uppercase text-[#0E1116]/80">
                Molecular Graph Inference Platform
              </span>
            </div>

            {/* H1 Headline with text morphing */}
            <h1 className="text-[#0E1116] mb-6 leading-[0.95] tracking-[-0.03em]">
              <span className="sr-only">
                Toxicity and interactions, read from chemical structure and experimental evidence.
              </span>
              <span aria-hidden="true">
                Toxicity and interactions, read from{" "}
                <MorphingText
                  words={["structure", "atoms", "evidence"]}
                  className="font-extrabold"
                />
              </span>
            </h1>

            {/* Subtext */}
            <p className="text-lg md:text-[20px] text-[#0E1116]/85 max-w-[58ch] leading-relaxed mb-8">
              C-FOOTPRINT turns a chemical name into a 12-endpoint toxicity profile and a
              pairwise interaction severity, with the atoms and the evidence behind them.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-4">
              <Button asChild variant="default" size="lg">
                <a
                  href={APP_URL}
                  className="flex items-center gap-2"
                >
                  Get started
                  <ExternalLinkIcon className="size-4" />
                </a>
              </Button>

              <Button asChild variant="outline" size="lg">
                <a
                  href="#modules-stage"
                  onClick={handleScrollToModules}
                  className="flex items-center gap-2"
                >
                  See the modules
                  <ArrowDownIcon className="size-4" />
                </a>
              </Button>
            </div>
          </div>

          {/* Right Column (Cols 8-12): Authentic Floating Product Card */}
          <div className="lg:col-span-5 relative flex justify-center lg:justify-end">
            <div className="w-full max-w-[460px] relative z-20">
              <AssayPlateReplica isFloating={true} className="shadow-none" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
