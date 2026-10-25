import React from "react";

export const HonestySection: React.FC = () => {
  const honestyPoints = [
    {
      title: "Atom-level saliency gradients",
      detail:
        "Every toxicity prediction includes integrated gradient attributions across the 2D molecular graph. You inspect exactly which substructures and functional groups drive the toxicophore classification.",
    },
    {
      title: "Recorded clinical evidence beside model estimates",
      detail:
        "When an interaction is evaluated, documented DDInter clinical literature records and severity tiers are displayed directly beside the GNN probability distribution for immediate verification.",
    },
    {
      title: "Similar-drug read-across labelled as inference",
      detail:
        "For novel or undocumented drug pairs, structural analogues are surfaced via molecular similarity. These are explicitly demarcated as computational inferences, never masquerading as confirmed clinical interactions.",
    },
    {
      title: "Research and educational use only",
      detail:
        "C-FOOTPRINT is engineered for in silico screening, bioassay exploration, and chemical triage. It is not medical software and must never replace clinical judgement or laboratory assays.",
    },
  ];

  return (
    <section className="relative bg-[#F2F4F7] text-[#0E1116] py-20 md:py-32 border-b border-[#0E1116]">
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">
          {/* Left Column (Cols 1-5): Large Pull Statement */}
          <div className="lg:col-span-5 flex flex-col justify-between">
            <div>
              <span className="font-mono text-xs uppercase tracking-wider text-[#0E1116]/60 block mb-3">
                Methodological Integrity
              </span>
              <h2 className="text-[#0E1116] mb-8">
                Built to be checked.
              </h2>
            </div>

            {/* Large Prominent Pull Statement */}
            <div className="p-6 md:p-8 bg-[#0E1116] text-[#F2F4F7] border border-[#0E1116] rounded-[12px] relative">
              <span className="w-3 h-3 bg-[#D2FF3F] inline-block mb-4" />
              <blockquote className="font-display font-extrabold text-2xl sm:text-3xl lg:text-3xl leading-snug tracking-tight text-[#D2FF3F]">
                “Not in DDInter means undocumented, not safe.”
              </blockquote>
              <p className="font-mono text-xs text-[#F2F4F7]/80 mt-4 leading-relaxed">
                Absence of documentation is not proof of biocompatibility. Unrecorded molecular
                pairs require active empirical testing before clinical consideration.
              </p>
            </div>
          </div>

          {/* Right Column (Cols 6-12): Plain Typographic List (Not Cards) */}
          <div className="lg:col-span-7 flex flex-col divide-y divide-[#0E1116]">
            {honestyPoints.map((item, idx) => (
              <div key={idx} className="py-6 first:pt-0 last:pb-0">
                <div className="flex items-baseline gap-3 mb-2">
                  <span className="font-mono text-xs font-bold text-[#2147FF]">
                    0{idx + 1}
                  </span>
                  <h3 className="text-xl font-bold text-[#0E1116]">
                    {item.title}
                  </h3>
                </div>
                <p className="text-[16px] text-[#0E1116]/85 leading-relaxed pl-7 max-w-[62ch]">
                  {item.detail}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
