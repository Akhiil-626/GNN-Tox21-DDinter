import React from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface FaqItem {
  question: string;
  answer: string;
}

const FAQ_ITEMS: FaqItem[] = [
  {
    question: "What makes Graph Neural Networks well-suited for molecular screening?",
    answer:
      "Molecules are inherently topological graphs where atoms form nodes and covalent bonds form edges. Traditional fixed-length fingerprints (like ECFP) compress structural motifs into bit vectors, losing spatial connectivity. Graph Neural Networks (GCN, GIN, MPNN) iteratively propagate neural messages directly along chemical bonds, preserving permutation invariance, 3D neighborhood context, and stereochemical geometry without lossy compression.",
  },
  {
    question: "How are molecular structures represented as graph inputs?",
    answer:
      "C-FOOTPRINT uses RDKit to featurize canonical SMILES into PyTorch Geometric Data objects. Each atom receives a high-dimensional feature vector encoding atomic number, degree, formal charge, hybridization (sp, sp2, sp3), aromaticity, and hydrogen count. Bonds are encoded as typed undirected edges with single, double, triple, or aromatic descriptors.",
  },
  {
    question: "Why does C-FOOTPRINT evaluate on a cold-start scaffold split?",
    answer:
      "Random data splits cause severe data leakage in cheminformatics because molecules sharing identical Bemis-Murcko core scaffolds end up in both training and test sets. A cold-start split guarantees that test molecules and pairwise test drugs possess distinct scaffolds that never appeared in the training set. This strictly reflects realistic pre-clinical drug discovery on novel chemical space.",
  },
  {
    question: "What does \"Not in DDInter means undocumented, not safe\" mean in practice?",
    answer:
      "When a candidate drug pair yields no record in DDInter, it signifies that the interaction is undocumented in curated biomedical literature — NOT that it has been tested and confirmed safe. Drug interaction databases suffer from strong positive publication bias. Unreported pairs remain unknown hazards, which is why C-FOOTPRINT triggers similarity fallback inference rather than reporting a clean bill of health.",
  },
  {
    question: "How does the multi-drug prescription checker infer interactions when pairs are missing?",
    answer:
      "When an input drug combination lacks a direct DDInter entry, C-FOOTPRINT computes Morgan fingerprint Tanimoto similarities across the database to identify structural analogues. It then predicts potential interactions by transferring calibrated severity distributions from the most chemically similar documented analogues.",
  },
  {
    question: "Can C-FOOTPRINT be used for clinical decision support or prescribing?",
    answer:
      "No. C-FOOTPRINT is strictly engineered for pre-clinical academic research, chemical hypothesis prioritization, and pharmacology education. It is not an FDA-cleared or CE-marked medical device. All outputs require wet-lab experimental confirmation and licensed clinical pharmacist review before any therapeutic consideration.",
  },
];

export const Faq: React.FC = () => {
  return (
    <section id="faq" className="relative py-24 sm:py-32 bg-[#060A18] border-t border-white/5 scroll-mt-20">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-xs font-mono text-cyan mb-3">
            <span>[ Frequently Asked Questions ]</span>
          </div>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white">
            Scientific & architectural details
          </h2>
          <p className="mt-3 text-base text-muted-foreground">
            Core questions on graph neural representations, benchmark validation, and clinical scope.
          </p>
        </div>

        <div>
          <Accordion type="single" collapsible className="w-full space-y-3.5">
            {FAQ_ITEMS.map((item, idx) => (
              <AccordionItem
                key={idx}
                value={`item-${idx}`}
                className="glass-card rounded-2xl px-6 border-white/8 transition-colors hover:border-cyan/40"
              >
                <AccordionTrigger className="text-left font-display text-base font-semibold text-white hover:text-cyan hover:no-underline py-5">
                  {item.question}
                </AccordionTrigger>
                <AccordionContent className="text-xs sm:text-sm text-muted-foreground leading-relaxed pb-5 pt-1 border-t border-white/6">
                  {item.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>
    </section>
  );
};
