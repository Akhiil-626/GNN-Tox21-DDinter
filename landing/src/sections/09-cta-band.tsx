import React from "react";
import { APP_URL } from "@/lib/links";
import { Button } from "@/components/ui/button";
import { MagnetLines } from "@/components/ui/magnet-lines";
import { ExternalLinkIcon } from "lucide-react";

export const CtaBandSection: React.FC = () => {
  return (
    <section className="relative bg-[#D2FF3F] text-[#0E1116] py-20 md:py-32 border-b border-[#0E1116] overflow-hidden">
      {/* Componentry Magnet Lines: Cursor-reactive interactive lines in ink */}
      <MagnetLines
        rows={8}
        columns={22}
        lineColor="#0E1116"
        lineWidth={1.5}
        lineLength={22}
        className="opacity-20"
      />

      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 relative z-10">
        <div className="max-w-[62ch]">
          <h2 className="text-[#0E1116] mb-6 tracking-tight">
            Run your first screen.
          </h2>
          <p className="text-lg md:text-[20px] text-[#0E1116] font-medium leading-relaxed mb-8 max-w-[56ch]">
            Evaluate single molecular structures across 12 bioassay targets or check multi-drug
            interaction networks in your local environment.
          </p>

          <div className="flex flex-wrap items-center gap-4">
            <Button asChild variant="default" size="lg" className="bg-[#0E1116] text-[#F2F4F7] hover:bg-[#2147FF]">
              <a
                href={APP_URL}
                className="flex items-center gap-2"
              >
                Get started
                <ExternalLinkIcon className="size-4" />
              </a>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
};
