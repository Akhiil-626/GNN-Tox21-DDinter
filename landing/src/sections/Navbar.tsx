import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Menu, ArrowRight, Activity } from "lucide-react";
import { APP_URL } from "@/lib/links";

interface NavbarProps {
  onSelectModuleTab?: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onSelectModuleTab }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [activeSection, setActiveSection] = useState<string>("");
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    let lastScrollY = window.scrollY;

    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      // Transparent at top, blurred and bordered after 20px
      setIsScrolled(currentScrollY > 20);

      // Hide on scroll down past 80px, show on scroll up
      if (currentScrollY > 80 && currentScrollY > lastScrollY) {
        setIsVisible(false);
      } else {
        setIsVisible(true);
      }

      lastScrollY = currentScrollY;

      // Scroll-spy
      const sections = ["modules", "endpoints", "performance", "faq"];
      let current = "";
      for (const sectionId of sections) {
        const el = document.getElementById(sectionId);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 200 && rect.bottom >= 200) {
            current = sectionId;
            break;
          }
        }
      }
      setActiveSection(current);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleNavClick = (
    e: React.MouseEvent<HTMLAnchorElement>,
    targetId: string,
    moduleTab?: string
  ) => {
    e.preventDefault();
    setMobileOpen(false);

    if (moduleTab && onSelectModuleTab) {
      onSelectModuleTab(moduleTab);
    }

    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      const navOffset = 90;
      const elementPosition = targetElement.getBoundingClientRect().top + window.scrollY;
      const offsetPosition = elementPosition - navOffset;

      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth",
      });

      if (moduleTab) {
        window.history.pushState(null, "", `#${moduleTab}`);
      } else {
        window.history.pushState(null, "", `#${targetId}`);
      }
    }
  };

  return (
    <header
      className={`fixed top-3 sm:top-4 left-1/2 -translate-x-1/2 z-50 w-[calc(100%-1.5rem)] sm:w-[calc(100%-3rem)] max-w-6xl transition-all duration-300 ${
        isVisible ? "translate-y-0 opacity-100" : "-translate-y-20 opacity-0"
      }`}
    >
      <div
        className={`flex h-14 items-center justify-between rounded-full px-4 sm:px-6 transition-all duration-300 ${
          isScrolled
            ? "border border-white/12 bg-[#060A18]/85 shadow-[0_12px_36px_rgba(0,0,0,0.65)] backdrop-blur-xl"
            : "border border-white/8 bg-[#060A18]/60 backdrop-blur-md"
        }`}
      >
        {/* Brand / Logo */}
        <a
          href="#"
          className="group flex items-center gap-2.5 transition-opacity hover:opacity-90"
          aria-label="C-FOOTPRINT Home"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-cyan to-violet text-[#060A18] shadow-[0_0_15px_rgba(25,211,255,0.4)] transition-transform group-hover:scale-105">
            <Activity className="h-4.5 w-4.5 stroke-[2.4]" aria-hidden="true" />
          </div>
          <div className="flex flex-col">
            <span className="font-display text-base font-bold tracking-tight text-white">
              C-FOOTPRINT
            </span>
          </div>
        </a>

        {/* Desktop Navigation (Visible for viewport > 860px) */}
        <nav className="hidden min-[861px]:flex items-center gap-1 text-xs" aria-label="Desktop Navigation">
          <a
            href="#modules"
            onClick={(e) => handleNavClick(e, "modules", "screening")}
            className={`rounded-full px-3.5 py-1.5 font-medium transition-all ${
              activeSection === "modules"
                ? "bg-white/10 text-cyan shadow-inner"
                : "text-muted-foreground hover:bg-white/5 hover:text-white"
            }`}
          >
            Screening
          </a>
          <a
            href="#modules"
            onClick={(e) => handleNavClick(e, "modules", "interactions")}
            className="rounded-full px-3.5 py-1.5 font-medium text-muted-foreground transition-all hover:bg-white/5 hover:text-white"
          >
            Interactions
          </a>
          <a
            href="#modules"
            onClick={(e) => handleNavClick(e, "modules", "prescription")}
            className="rounded-full px-3.5 py-1.5 font-medium text-muted-foreground transition-all hover:bg-white/5 hover:text-white"
          >
            Prescription
          </a>
          <a
            href="#endpoints"
            onClick={(e) => handleNavClick(e, "endpoints")}
            className={`rounded-full px-3.5 py-1.5 font-medium transition-all ${
              activeSection === "endpoints"
                ? "bg-white/10 text-cyan shadow-inner"
                : "text-muted-foreground hover:bg-white/5 hover:text-white"
            }`}
          >
            Endpoints
          </a>
          <a
            href="#performance"
            onClick={(e) => handleNavClick(e, "performance")}
            className={`rounded-full px-3.5 py-1.5 font-medium transition-all ${
              activeSection === "performance"
                ? "bg-white/10 text-cyan shadow-inner"
                : "text-muted-foreground hover:bg-white/5 hover:text-white"
            }`}
          >
            Performance
          </a>
          <a
            href="#faq"
            onClick={(e) => handleNavClick(e, "faq")}
            className={`rounded-full px-3.5 py-1.5 font-medium transition-all ${
              activeSection === "faq"
                ? "bg-white/10 text-cyan shadow-inner"
                : "text-muted-foreground hover:bg-white/5 hover:text-white"
            }`}
          >
            FAQ
          </a>
        </nav>

        {/* Desktop CTA (Visible > 860px) */}
        <div className="hidden min-[861px]:flex items-center gap-3">
          <Button
            asChild
            size="sm"
            className="rounded-full bg-cyan px-4 py-1.5 text-xs font-semibold text-[#060A18] shadow-[0_0_20px_rgba(25,211,255,0.35)] transition-all hover:bg-cyan/90 hover:shadow-[0_0_25px_rgba(25,211,255,0.5)] hover:scale-[1.02]"
          >
            <a href={APP_URL}>
              Get started
              <ArrowRight className="ml-1 h-3.5 w-3.5" aria-hidden="true" />
            </a>
          </Button>
        </div>

        {/* Mobile Menu via Sheet (Visible <= 860px) */}
        <div className="flex min-[861px]:hidden">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-full text-white hover:bg-white/10"
                aria-label="Open navigation menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent
              side="right"
              className="w-[300px] border-l border-white/10 bg-[#060A18]/95 p-6 backdrop-blur-2xl"
            >
              <SheetHeader className="border-b border-white/10 pb-4 text-left">
                <SheetTitle className="flex items-center gap-2.5 font-display text-lg font-bold text-white">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-tr from-cyan to-violet text-[#060A18]">
                    <Activity className="h-4 w-4 stroke-[2.4]" aria-hidden="true" />
                  </div>
                  C-FOOTPRINT
                </SheetTitle>
              </SheetHeader>
              <nav className="mt-6 flex flex-col gap-2 font-medium" aria-label="Mobile Navigation">
                <a
                  href="#modules"
                  onClick={(e) => handleNavClick(e, "modules", "screening")}
                  className="rounded-xl px-4 py-2.5 text-sm text-foreground transition-all hover:bg-white/5 hover:text-cyan"
                >
                  Compound screening
                </a>
                <a
                  href="#modules"
                  onClick={(e) => handleNavClick(e, "modules", "interactions")}
                  className="rounded-xl px-4 py-2.5 text-sm text-foreground transition-all hover:bg-white/5 hover:text-cyan"
                >
                  Interaction check
                </a>
                <a
                  href="#modules"
                  onClick={(e) => handleNavClick(e, "modules", "prescription")}
                  className="rounded-xl px-4 py-2.5 text-sm text-foreground transition-all hover:bg-white/5 hover:text-cyan"
                >
                  Prescription checker
                </a>
                <a
                  href="#endpoints"
                  onClick={(e) => handleNavClick(e, "endpoints")}
                  className="rounded-xl px-4 py-2.5 text-sm text-foreground transition-all hover:bg-white/5 hover:text-cyan"
                >
                  Tox21 Endpoints
                </a>
                <a
                  href="#performance"
                  onClick={(e) => handleNavClick(e, "performance")}
                  className="rounded-xl px-4 py-2.5 text-sm text-foreground transition-all hover:bg-white/5 hover:text-cyan"
                >
                  Model performance
                </a>
                <a
                  href="#faq"
                  onClick={(e) => handleNavClick(e, "faq")}
                  className="rounded-xl px-4 py-2.5 text-sm text-foreground transition-all hover:bg-white/5 hover:text-cyan"
                >
                  FAQ
                </a>
                <div className="mt-6 pt-4 border-t border-white/10">
                  <Button asChild className="w-full rounded-full bg-cyan text-[#060A18] font-semibold shadow-[0_0_20px_rgba(25,211,255,0.4)]">
                    <a href={APP_URL}>
                      Get started
                      <ArrowRight className="ml-1.5 h-4 w-4" aria-hidden="true" />
                    </a>
                  </Button>
                </div>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
};
