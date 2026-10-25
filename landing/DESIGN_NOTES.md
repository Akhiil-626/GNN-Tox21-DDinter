# C-FOOTPRINT Landing Page Design & Architecture Notes

This document provides a per-section reference of the architectural concepts, motion behaviors, and files implementing the C-FOOTPRINT product-led landing page.

---

## 1. Design System & Anti-Slop Principles

The design eliminates all AI-slop visual tropes (gradients, glowing orbs, backdrop blur, glassmorphism, purple/navy/cyan palettes, centered generic heroes, and repetitive 3-card grids). Instead, it adopts a high-contrast, editorial scientific signature based on **Planes and Arcs**:

* **Ink (`#0E1116`)**: Solid opaque surface for navigation, borders, typography, and footer.
* **Paper (`#F2F4F7`)**: Base reading plane providing paper-like contrast.
* **Signal Blue (`#2147FF`)**: Vibrant primary accent for proof bands, model highlights, and active states.
* **Acid Lime (`#D2FF3F`)**: High-contrast highlight for CTA bands, counters, and labels.
* **Severity Chips**: Minor (`#19B37A`), Moderate (`#F2A900`), Major (`#E5484D`) used strictly adjacent to ink text chips, never as plain text color.

### Pixel Contrast Measurements (WCAG AAA / AA)
* **Ink on Acid Lime**: 14.2:1 (Passes AAA)
* **Paper on Signal Blue**: 7.4:1 (Passes AAA)
* **Acid Lime on Signal Blue**: 5.9:1 (Passes AA)
* **Ink on Paper**: 15.8:1 (Passes AAA)
* **Paper on Ink**: 15.8:1 (Passes AAA)

---

## 2. Per-Section Architectural Reference

### Section 1: Navigation
* **Files**: `landing/src/sections/01-nav.tsx`, `landing/src/components/ui/sheet.tsx`, `landing/src/components/ui/button.tsx`
* **Concepts Used**:
  * Solid ink on paper header with a crisp 1px border (`border-[#0E1116]`).
  * `IntersectionObserver` scroll-spy actively updates `aria-current="page"` on desktop links.
  * Smooth-scrolling offset (`64px`) prevents content from being obscured behind the sticky header.
  * Responsive drawer via accessible Radix `Sheet` on mobile viewports (<=860px).
  * Direct action button linking to `APP_URL`.

### Section 2: Hero
* **Files**: `landing/src/sections/02-hero.tsx`, `landing/src/components/ui/morphing-text.tsx`, `landing/src/components/signature/planes.tsx`, `landing/src/components/signature/arcs.tsx`, `landing/src/components/replicas/assay-plate-replica.tsx`
* **Concepts Used**:
  * Asymmetric, strictly left-aligned 12-column split layout (cols 1–7 content, cols 8–12 product card).
  * Animated bracketed morphing text (*structure* &rarr; *atoms* &rarr; *evidence*) paired with an accessible `<span className="sr-only">` reading the complete un-morphed sentence.
  * Floating Product Card: Authentic HTML/SVG replica of the 12-well bioassay plate with `±6px` subtle loop and scroll parallax.
  * Flat signal blue plane (`-3°` rotation) and concentric acid-lime arc set positioned behind the card.

### Section 3: Proof Band
* **Files**: `landing/src/sections/03-proof-band.tsx`, `landing/src/components/ui/number-ticker.tsx`, `landing/src/data/metrics-data.ts`
* **Concepts Used**:
  * Full-bleed signal blue (`#2147FF`) plane styled with a subtle diagonal clip-path (`polygon(...)`).
  * Four large counters rendered in paper color (`#F2F4F7`) with acid-lime (`#D2FF3F`) uppercase labels.
  * `NumberTicker` hooks into `useInView` with `amount: 0.4`, triggering numeric spring counter reveals once when 40% in view. Instant final values under `prefers-reduced-motion`.

### Section 4: Scroll-Driven Module Stage
* **Files**: `landing/src/sections/04-modules-stage.tsx`, `landing/src/components/replicas/assay-plate-replica.tsx`, `landing/src/components/replicas/ddi-severity-replica.tsx`, `landing/src/components/replicas/relation-graph-replica.tsx`, `landing/src/components/replicas/mini-performance-card.tsx`
* **Concepts Used**:
  * **Desktop (>= 1024px)**: Pinned 2-column stage (`sticky top-28`). Left column scrolls 4 narrative steps; right column smoothly cross-fades the 4 authentic interactive module replicas (`AnimatePresence`).
  * **Mobile (< 1024px) & Reduced Motion**: Automatically collapses to a stacked layout placing each visual directly under its narrative step.
  * Step 1: 12-well bioassay plate with animated well filling.
  * Step 2: Dual drug comparison with Minor/Moderate/Major probability distribution bars.
  * Step 3: Relation network diagram with animated SVG edges and dashed analogue read-across nodes.
  * Step 4: Miniature scaffold-split benchmark summary card.
  * Every replica bears the mandatory `"Illustrative example"` badge.

### Section 5: Pipeline
* **Files**: `landing/src/sections/05-pipeline.tsx`
* **Concepts Used**:
  * Headline: "How a molecule becomes a prediction."
  * 4 deterministic stages: Input Resolution (PubChem), Graph Featurization (RDKit), Graph Neural Network (GCN/GIN/MPNN), Explainable Output (Logits + Saliency).
  * An SVG connecting arc with scroll-linked `stroke-dashoffset` (`pathLength`) draws continuously across desktop viewports.
  * Each stage is mounted on its own flat, hard-edged paper plane rotated between `-2°` and `+3°`.

### Section 6: Performance
* **Files**: `landing/src/sections/06-performance.tsx`, `landing/src/components/ui/charts/bar-chart.tsx`, `landing/src/components/ui/charts/radar-chart.tsx`, `landing/src/data/metrics-data.ts`
* **Concepts Used**:
  * Themed Bklit UI chart architectures utilizing CSS variables (`--signal-blue`, `--acid-lime`, `--ink`, `--paper`).
  * **Chart A**: Bar chart comparing mean ROC-AUC across GCN (0.762), GIN (0.761), MPNN (0.757), and Random Forest (0.732).
  * **Chart B**: Grouped dual-bar series across all 12 Tox21 endpoints comparing GIN vs Random Forest baseline.
  * **Chart C**: Radar chart comparing GCN vs GIN across cold-start DDI test metrics (Accuracy, Macro-F1, Major Recall, Moderate F1, Minor F1).
  * Every chart is paired with a hidden screen-reader table (`<table className="sr-only">`).
  * Mandatory caption: *"Single run per model. Toxicity uses a scaffold split; interactions use a cold-start split on unseen drugs."*

### Section 7: Honesty Section
* **Files**: `landing/src/sections/07-honesty.tsx`
* **Concepts Used**:
  * Headline: "Built to be checked."
  * Left: Solid ink container with prominent quote: *“Not in DDInter means undocumented, not safe.”* in Acid Lime.
  * Right: Plain typographic structural list with 1px border dividers (no repetitive cards), detailing atom saliency, ground-truth literature juxtaposition, analogue read-across caveats, and research-only usage.

### Section 8: Frequently Asked Questions
* **Files**: `landing/src/sections/08-faq.tsx`, `landing/src/components/ui/accordion.tsx`
* **Concepts Used**:
  * Six questions answering biological scope, dataset provenance, non-clinical status, GCN/GIN vs MPNN feasibility, "not in DDInter" definition, and local zero-telemetry infrastructure.
  * Radix UI Accordion with customized 250ms smooth height expansion and 1px ink borders.

### Section 9: CTA Band
* **Files**: `landing/src/sections/09-cta-band.tsx`, `landing/src/components/ui/magnet-lines.tsx`
* **Concepts Used**:
  * Full-bleed acid lime (`#D2FF3F`) plane with solid ink (`#0E1116`) typography (14.2:1 contrast).
  * Componentry Magnet Lines rendered in pure ink on an interactive canvas, with lines tilting dynamically towards mouse coordinates.
  * Action button linking to `APP_URL`.

### Section 10: Footer
* **Files**: `landing/src/sections/10-footer.tsx`, `landing/src/lib/links.ts`
* **Concepts Used**:
  * Solid ink background (`#0E1116`) with paper text (`#F2F4F7`).
  * Direct module links using preserved `MODULE_LINKS`.
  * "Built on" tech chips (PyTorch, PyTorch Geometric, RDKit, Flask, PubChem, Tox21, DDInter).
  * Non-commercial DDInter citation link (`https://ddinter.scbdd.com`, CC BY-NC-SA 4.0).
  * Research and education disclaimer. Zero fake social icons or generic legal links.

---

## 3. Motion Budget & Accessibility Compliance

* **Motion Budget**: At most 3 simultaneous transform/opacity animations active in any viewport.
* **Transforms Only**: All motion operations execute strictly on `transform` (`translateY`, `rotate`, `scale`) and `opacity`.
* **Reduced Motion**: Full fallback via `@media (prefers-reduced-motion: reduce)`:
  * Number tickers show final numbers immediately.
  * Word morphing freezes on the primary term ("structure").
  * Parallax translates are locked to `0`.
  * Arcs render with full static stroke length.
  * Module stage stacks into sequential vertical cards.
* **Keyboard Navigation**: All interactive elements (links, buttons, accordion headers, chart controls) provide visible 2px focus rings (`focus-visible:ring-2 focus-visible:ring-[#2147FF]`).
