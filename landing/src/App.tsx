import { useState, useEffect } from "react";
import { AtomCursor } from "./components/AtomCursor";
import { Navbar } from "./sections/01-nav";
import { HeroSection } from "./sections/02-hero";
import { ProofBandSection } from "./sections/03-proof-band";
import { ModulesStageSection } from "./sections/04-modules-stage";
import { PipelineSection } from "./sections/05-pipeline";
import { PerformanceSection } from "./sections/06-performance";
import { HonestySection } from "./sections/07-honesty";
import { FaqSection } from "./sections/08-faq";
import { CtaBandSection } from "./sections/09-cta-band";
import { FooterSection } from "./sections/10-footer";

export default function App() {
  const [activeSection, setActiveSection] = useState<string>("");
  const [activeStep, setActiveStep] = useState<string>("screening");

  // Hash anchor navigation handling
  useEffect(() => {
    const handleHash = () => {
      const rawHash = window.location.hash.replace("#", "");
      if (!rawHash) return;

      if (["screening", "interactions", "prescription"].includes(rawHash)) {
        setActiveStep(rawHash);
        setActiveSection(rawHash);
        const el = document.getElementById(`module-${rawHash}`);
        if (el) {
          const navOffset = 64;
          const pos = el.getBoundingClientRect().top + window.scrollY - navOffset;
          window.scrollTo({ top: pos, behavior: "smooth" });
        }
      } else if (rawHash === "performance" || rawHash === "faq") {
        setActiveSection(rawHash);
        const el = document.getElementById(rawHash);
        if (el) {
          const navOffset = 64;
          const pos = el.getBoundingClientRect().top + window.scrollY - navOffset;
          window.scrollTo({ top: pos, behavior: "smooth" });
        }
      }
    };

    const timer = setTimeout(handleHash, 100);
    window.addEventListener("hashchange", handleHash);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("hashchange", handleHash);
    };
  }, []);

  // IntersectionObserver scroll-spy to update nav aria-current
  useEffect(() => {
    const sectionIds = [
      "module-screening",
      "module-interactions",
      "module-prescription",
      "performance",
      "faq",
    ];

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            if (id.startsWith("module-")) {
              const stepKey = id.replace("module-", "");
              setActiveSection(stepKey);
              setActiveStep(stepKey);
            } else {
              setActiveSection(id);
            }
          }
        });
      },
      {
        rootMargin: "-20% 0px -60% 0px",
        threshold: 0,
      }
    );

    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div className="min-h-screen bg-[#F2F4F7] text-[#0E1116] antialiased selection:bg-[#D2FF3F] selection:text-[#0E1116]">
      {/* Creative Atom Cursor */}
      <AtomCursor />

      {/* 1. Nav */}
      <Navbar
        activeSection={activeSection}
        onNavigateToStep={(stepKey) => {
          setActiveStep(stepKey);
          setActiveSection(stepKey);
        }}
      />

      <main>
        {/* 2. Hero */}
        <HeroSection />

        {/* 3. Proof Band */}
        <ProofBandSection />

        {/* 4. Modules as Scroll-Driven Stage */}
        <ModulesStageSection activeStep={activeStep} />

        {/* 5. Pipeline */}
        <PipelineSection />

        {/* 6. Performance */}
        <PerformanceSection />

        {/* 7. Honesty Section */}
        <HonestySection />

        {/* 8. FAQ */}
        <FaqSection />

        {/* 9. CTA Band */}
        <CtaBandSection />
      </main>

      {/* 10. Footer */}
      <FooterSection />
    </div>
  );
}
