import React, { useState } from "react";
import { APP_URL } from "@/lib/links";
import { Button } from "@/components/ui/button";
import { Sheet, SheetTrigger, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { MenuIcon, ExternalLinkIcon } from "lucide-react";

interface NavProps {
  activeSection?: string;
  onNavigateToStep?: (stepId: string) => void;
}

export const Navbar: React.FC<NavProps> = ({ activeSection = "", onNavigateToStep }) => {
  const [isOpen, setIsOpen] = useState(false);

  const navLinks = [
    { label: "Screening", targetId: "module-screening", isModule: true, stepKey: "screening" },
    { label: "Interactions", targetId: "module-interactions", isModule: true, stepKey: "interactions" },
    { label: "Prescription", targetId: "module-prescription", isModule: true, stepKey: "prescription" },
    { label: "Performance", targetId: "performance", isModule: false },
    { label: "FAQ", targetId: "faq", isModule: false },
  ];

  const handleSmoothScroll = (e: React.MouseEvent<HTMLAnchorElement>, targetId: string, stepKey?: string) => {
    e.preventDefault();
    setIsOpen(false);

    if (stepKey && onNavigateToStep) {
      onNavigateToStep(stepKey);
    }

    const targetEl = document.getElementById(targetId);
    if (targetEl) {
      const navHeight = 64;
      const targetPos = targetEl.getBoundingClientRect().top + window.scrollY - navHeight;
      window.scrollTo({
        top: targetPos,
        behavior: "smooth",
      });
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-[#F2F4F7] text-[#0E1116] border-b border-[#0E1116]">
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Wordmark */}
        <a
          href="#"
          className="flex items-center gap-2.5 font-display font-extrabold text-xl tracking-tight text-[#0E1116] select-none hover:text-[#2147FF] transition-colors"
        >
          <span className="w-3.5 h-3.5 bg-[#2147FF] border border-[#0E1116] inline-block" />
          <span>C-FOOTPRINT</span>
          <span className="font-mono text-[10px] uppercase tracking-wider bg-[#D2FF3F] text-[#0E1116] border border-[#0E1116] px-1.5 py-0.5 rounded-[4px] hidden sm:inline-block">
            v1.0-research
          </span>
        </a>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-7 text-sm font-medium">
          {navLinks.map((link) => {
            const isCurrent = activeSection === link.targetId || activeSection === link.stepKey;
            return (
              <a
                key={link.label}
                href={`#${link.targetId}`}
                onClick={(e) => handleSmoothScroll(e, link.targetId, link.stepKey)}
                aria-current={isCurrent ? "page" : undefined}
                className={`transition-colors py-1 relative ${
                  isCurrent
                    ? "text-[#2147FF] font-bold"
                    : "text-[#0E1116]/80 hover:text-[#0E1116]"
                }`}
              >
                {link.label}
                {isCurrent && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2147FF]" />
                )}
              </a>
            );
          })}
        </nav>

        {/* Action Button & Mobile Menu */}
        <div className="flex items-center gap-3">
          <Button
            asChild
            variant="default"
            size="default"
            className="hidden sm:inline-flex"
          >
            <a href={APP_URL}>
              Get started
              <ExternalLinkIcon className="size-3.5 ml-1" />
            </a>
          </Button>

          {/* Mobile Sheet Trigger (<=860px / lg:hidden) */}
          <div className="lg:hidden">
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  aria-label="Open mobile menu"
                  className="size-10"
                >
                  <MenuIcon className="size-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right">
                <SheetHeader>
                  <SheetTitle className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-[#2147FF] border border-[#0E1116]" />
                    <span>C-FOOTPRINT</span>
                  </SheetTitle>
                </SheetHeader>
                <nav className="flex flex-col gap-4 p-6 text-base font-semibold">
                  {navLinks.map((link) => (
                    <a
                      key={link.label}
                      href={`#${link.targetId}`}
                      onClick={(e) => handleSmoothScroll(e, link.targetId, link.stepKey)}
                      className="py-2.5 border-b border-[#0E1116]/15 hover:text-[#2147FF] transition-colors"
                    >
                      {link.label}
                    </a>
                  ))}
                  <div className="pt-4">
                    <Button asChild variant="signal" size="lg" className="w-full">
                      <a
                        href={APP_URL}
                        onClick={() => setIsOpen(false)}
                        className="flex items-center justify-center gap-2"
                      >
                        Get started
                        <ExternalLinkIcon className="size-4" />
                      </a>
                    </Button>
                  </div>
                </nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
};
