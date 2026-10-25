import React from "react";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

export const FaqSection: React.FC = () => {
  const faqs = [
    {
      q: "What biological targets and outcomes does C-FOOTPRINT predict?",
      a: "C-FOOTPRINT evaluates compounds across 12 Tox21 bioassay endpoints: seven nuclear receptor targets (NR-AR, NR-AR-LBD, NR-AhR, NR-Aromatase, NR-ER, NR-ER-LBD, NR-PPAR-gamma) and five stress response pathways (SR-ARE, SR-ATAD5, SR-HSE, SR-MMP, SR-p53). For multi-drug regimens, it predicts pairwise interaction severity across three discrete clinical categories: Minor, Moderate, and Major.",
    },
    {
      q: "Where does the training and validation data come from?",
      a: "Bioassay benchmarks originate from the NIH Tox21 Challenge dataset, encompassing 7,831 compounds evaluated under Bemis-Murcko scaffold splits. Pairwise drug interaction data is sourced from the curated DDInter database (122,378 labelled pairs under CC BY-NC-SA 4.0), evaluated on a cold-start split where test pairs contain completely unseen drug structures.",
    },
    {
      q: "Can this system be used for clinical prescription or diagnostic decisions?",
      a: "No. C-FOOTPRINT is strictly for research and educational purposes. In silico machine learning estimates can produce false positives and false negatives, and cannot account for patient-specific metabolic differences, comorbidities, or unmodelled pharmacokinetic dynamics. Never use these predictions as a substitute for professional clinical judgment.",
    },
    {
      q: "Why are only GCN and GIN available for pairwise interaction checks?",
      a: "While single-compound screening supports GCN, GIN, and edge-aware MPNN, pairwise DDI evaluation requires dual-encoder message passing over two molecular graphs simultaneously. In local CPU training benchmarks, the MPNN dual-encoder required approximately two hours per epoch and was excluded from pairwise training to maintain reproducible computational feasibility.",
    },
    {
      q: "What does the 'not in DDInter' status signify?",
      a: "A 'not in DDInter' status signifies that the specific pair of molecules is not catalogued in the DDInter clinical interaction database. It does not mean the combination is safe or devoid of adverse effects. To assist exploration, the system retrieves structural analogues with documented records to offer read-across inferences.",
    },
    {
      q: "Does the platform require accounts, store search queries, or make external requests?",
      a: "C-FOOTPRINT requires no accounts, passwords, or subscriptions, and records no user tracking or telemetry. The machine learning models and web dashboard run locally. The only optional network request is resolving plain chemical names (e.g., 'aspirin') to canonical SMILES via the public PubChem REST API.",
    },
  ];

  return (
    <section
      id="faq"
      className="relative bg-[#FFFFFF] text-[#0E1116] py-20 md:py-32 border-b border-[#0E1116] scroll-mt-16"
    >
      <div className="max-w-[840px] mx-auto px-4 sm:px-6">
        {/* Section Header */}
        <div className="mb-12 md:mb-16 text-left">
          <span className="font-mono text-xs uppercase tracking-wider text-[#0E1116]/60 block mb-2">
            Frequently Asked Questions
          </span>
          <h2 className="text-[#0E1116] mb-4">
            Answers grounded in code and data.
          </h2>
          <p className="text-lg text-[#0E1116]/80 leading-relaxed max-w-[62ch]">
            Straightforward technical clarification regarding models, dataset splits, and operational boundaries.
          </p>
        </div>

        {/* Accordion List */}
        <Accordion type="single" collapsible className="w-full">
          {faqs.map((faq, idx) => (
            <AccordionItem key={idx} value={`item-${idx}`}>
              <AccordionTrigger>
                {faq.q}
              </AccordionTrigger>
              <AccordionContent>
                {faq.a}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
};
