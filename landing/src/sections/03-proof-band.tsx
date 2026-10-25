import React from "react";
import { NumberTicker } from "@/components/ui/number-ticker";
import { PROOF_STATS } from "@/data/metrics-data";

export const ProofBandSection: React.FC = () => {
  return (
    <section
      className="relative bg-[#2147FF] text-[#F2F4F7] py-16 md:py-24 border-b border-[#0E1116] overflow-hidden"
      style={{
        clipPath: "polygon(0 0, 100% 1.8vw, 100% 100%, 0 calc(100% - 1.8vw))",
        marginTop: "-1vw",
        marginBottom: "-1vw",
      }}
    >
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 relative z-10 py-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 md:gap-12">
          {PROOF_STATS.map((stat, idx) => (
            <div
              key={stat.label}
              className="flex flex-col border-l-2 border-[#D2FF3F] pl-4 sm:pl-6"
            >
              {/* Large Counter in Paper Colour */}
              <div className="font-mono font-bold text-4xl sm:text-5xl lg:text-6xl text-[#F2F4F7] tracking-tight leading-none mb-2">
                <NumberTicker value={stat.value} delay={idx * 0.1} />
                {stat.suffix}
              </div>

              {/* Label in Acid Lime */}
              <div className="font-display font-semibold text-sm sm:text-base text-[#D2FF3F] uppercase tracking-wider">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
