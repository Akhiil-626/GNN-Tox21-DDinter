import { useState, useEffect } from "react";
import Lenis from "lenis";
import { Navbar } from "./sections/Navbar";
import { Hero } from "./sections/Hero";
import { Statement } from "./sections/Statement";
import { Stats } from "./sections/Stats";
import { Modules } from "./sections/Modules";
import { BuiltWith } from "./sections/BuiltWith";
import { Endpoints } from "./sections/Endpoints";
import { PullQuote } from "./sections/PullQuote";
import { Walkthrough } from "./sections/Walkthrough";
import { Performance } from "./sections/Performance";
import { Features } from "./sections/Features";
import { Trust } from "./sections/Trust";
import { Faq } from "./sections/Faq";
import { ClosingCta } from "./sections/ClosingCta";
import { Footer } from "./sections/Footer";

export default function App() {
  const [selectedModuleTab, setSelectedModuleTab] = useState<string>("screening");

  // Lenis smooth scrolling orchestration
  useEffect(() => {
    const isReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (isReduced) return;

    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });

    let rafId: number;
    function raf(time: number) {
      lenis.raf(time);
      rafId = requestAnimationFrame(raf);
    }
    rafId = requestAnimationFrame(raf);

    return () => {
      cancelAnimationFrame(rafId);
      lenis.destroy();
    };
  }, []);

  // Hash anchor navigation handling
  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.replace("#", "");
      if (!hash) return;

      if (["screening", "interactions", "prescription", "performance"].includes(hash)) {
        setSelectedModuleTab(hash);
      }

      const targetId =
        hash === "screening" || hash === "interactions" || hash === "prescription"
          ? "modules"
          : hash;

      const el = document.getElementById(targetId);
      if (el) {
        const navOffset = 90;
        const pos = el.getBoundingClientRect().top + window.scrollY - navOffset;
        window.scrollTo({ top: pos, behavior: "smooth" });
      }
    };

    const timer = setTimeout(handleHash, 150);
    window.addEventListener("hashchange", handleHash);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("hashchange", handleHash);
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#060A18] text-[#EAF0FF] antialiased selection:bg-cyan/20 selection:text-white">
      {/* 1. Navbar */}
      <Navbar onSelectModuleTab={setSelectedModuleTab} />

      <main>
        {/* 2. Hero */}
        <Hero />

        {/* 3. Statement */}
        <Statement />

        {/* 4. Stats */}
        <Stats />

        {/* 5. Modules (#modules) */}
        <Modules
          currentTab={selectedModuleTab}
          onTabChange={setSelectedModuleTab}
        />

        {/* 6. Built With (Marquee "Built on open science") */}
        <BuiltWith />

        {/* 7. Endpoints (#endpoints) */}
        <Endpoints />

        {/* 8. Pull Quote */}
        <PullQuote />

        {/* 9. Walkthrough */}
        <Walkthrough />

        {/* 10. Performance (#performance) */}
        <Performance />

        {/* 11. Features */}
        <Features />

        {/* 12. Trust */}
        <Trust />

        {/* 13. FAQ (#faq) */}
        <Faq />

        {/* 14. Closing CTA */}
        <ClosingCta />
      </main>

      {/* 15. Footer */}
      <Footer />
    </div>
  );
}
