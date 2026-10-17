# C-FOOTPRINT Landing Page

Marketing landing page for **C-FOOTPRINT** (Deep Graph Neural Networks for pre-clinical molecular toxicity screening, pairwise drug-drug interaction classification, and multi-drug prescription risk analysis).

---

## Tech Stack

- **Framework**: [React 19](https://react.dev/) + [Vite](https://vite.dev/) + [TypeScript](https://www.typescriptlang.org/) (Strict)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/)
- **UI Primitives**: [shadcn/ui](https://ui.shadcn.com/) (Radix UI primitives)
- **Animations & Motion**: [Motion](https://motion.dev/) (`framer-motion`) + [Lenis](https://lenis.darkroom.engineering/) (smooth scrolling)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Typography**: `@fontsource-variable/bricolage-grotesque` (display headings), `@fontsource-variable/geist` (body), `@fontsource-variable/geist-mono` (tabular metrics)

---

## Getting Started

### Prerequisites

- Node.js 18+ (tested on Node.js 22+)
- npm 9+

### Installation

```bash
cd landing
npm install
```

### Development Server

Runs the Vite development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

The landing page connects to the Flask dashboard via environment variables defined in `.env.development`:
- `VITE_APP_URL=http://127.0.0.1:5000/index.html`

### Typecheck

Verifies strict TypeScript compilation without emitting files:

```bash
npm run typecheck
```

### Production Build

Compiles and bundles the landing page directly into Flask's static assets directory (`../public/landing`):

```bash
npm run build
```

The built output is served by the Flask application at:
```
http://127.0.0.1:5000/landing/index.html
```

---

## Section Map & Architecture

The landing page is organized into 15 structured sections in `src/sections/`:

1. **`Navbar`**: Floating frosted glass pill with scroll-spy navigation, hide/show on scroll, and mobile drawer Sheet.
2. **`Hero`**: Animated morphing headline, 4 auto-advancing tabs, 3 floating glass cards, 3 demo presets, and a drifting 42-node canvas molecular graph.
3. **`Statement`**: 3-line scroll-linked statement with word illumination, rotating methodology tags, and closing punchline.
4. **`Stats`**: 4 rolling digit counters covering Tox21 endpoints, severity classes, curated pairs, and max prescription compounds.
5. **`Modules`**: Interactive showcase with vector illustrations (`AssayPlate`, `DdiBondIllustration`, `RelationGraphIllustration`, `MetricsBarIllustration`) and deep module launchers.
6. **`BuiltWith`**: Infinite horizontal marquee highlighting open-science dependencies.
7. **`Endpoints`**: 6 portrait cards with hover spotlights profiling the 12 Tox21 bioassays.
8. **`PullQuote`**: High-impact editorial block on the *"Not in DDInter means undocumented, not safe"* principle.
9. **`Walkthrough`**: Browser-frame mock simulating multi-drug regimen input, graph inference, and severe risk alerting.
10. **`Performance`**: Grouped benchmark bars evaluating GCN vs. GIN on strictly unseen cold-start compounds.
11. **`Features`**: Deep dive into atom-level gradient saliency ($\frac{\partial\text{Logit}}{\partial\text{Atom}}$) and clinical boundary integrity.
12. **`Trust`**: 3 pillars covering Data Provenance, Evaluation Protocols, and Clinical Disclaimers.
13. **`Faq`**: 6 domain questions in accessible dark glass shadcn Accordions.
14. **`ClosingCta`**: Cursor-reactive magnetic line field background with primary and documentation CTAs.
15. **`Footer`**: Brand, module links, Tox21 links, data attributions, and scientific compliance disclaimer.

---

## License & Attribution

- Built as part of the C-FOOTPRINT open-science pre-clinical research suite.
- Chemical interaction data attributed to the **DDInter Database** under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
- Molecular structures validated via **NCBI PubChem**.
