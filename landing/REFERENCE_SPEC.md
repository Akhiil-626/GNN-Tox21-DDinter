# REFERENCE SPECIFICATION: PayPath.ai Deconstruction & C-FOOTPRINT Mapping

Based on in-depth DOM, computed styles, and visual deconstruction of `https://paypath.ai/?ref=land-book.com` at 1440px (desktop) and 390px (mobile).

---

## 0. Design System & Global Tokens

### A. Palette
- **Base Backgrounds**: Deep midnight ink `#060A18` (primary surface) and `#0C1330` (elevated cards/subsurfaces).
- **Primary Text**: Crisp ice-white `#EAF0FF` (headings and high-emphasis body).
- **Muted Text**: Slate-periwinkle `#93A1C8` (labels, subtitles, secondary captions).
- **Light Contrast Inverted Band**: Crisp pale slate `#F6F7FB` with dark text `#0B1030`.
- **Vibrant Mesh & Accent Hues**:
  - Cyan: `#19D3FF`
  - Violet: `#7A5CFF`
  - Mint: `#35E0A1` (also severity: **Minor** interaction)
  - Amber: `#FFB84D` (also severity: **Moderate** interaction)
  - Coral: `#FF5C7A` (also severity: **Major** interaction)
- **Borders**: Sub-surface hairline borders with semi-transparent tinted edges (`rgba(255, 255, 255, 0.08)` to `rgba(25, 211, 255, 0.2)` on dark; `rgba(11, 16, 48, 0.1)` on light).

### B. Typography
- **Display Headings**: `Bricolage Grotesque` (variable geometric grotesque with modern character and tight letter-spacing; no serifs).
- **Body & Interface**: `Geist` (`Geist Sans` - modern sans-serif with exceptional legibility at small sizes).
- **Data & Code**: `Geist Mono` (tabular numerals, code chips, metrics).

### C. Motion & Curves
- **Standard Entrance**: `translateY(24px)` -> `0px`, `opacity: 0` -> `1`, `duration: 0.6s`, easing `cubic-bezier(0.22, 1, 0.36, 1)`, stagger `80ms`.
- **Card Hover**: `translateY(-4px)` with subtle spotlight radial glow transition (`0.2s ease-out`).
- **Scroll-Linked Statement**: Opacity transform tied to scroll progression (`[0.15, 1.0]`).
- **Smooth Scrolling**: Lenis smooth-scroll orchestration for fluid acceleration and deceleration.

---

## 1. Navbar
- **PayPath Reference**:
  - Floating pill fixed navbar, top: 16px, max-w-7xl.
  - Backdrop blur: `16px`, background: `rgba(6, 10, 24, 0.75)`, border: `1px solid rgba(255, 255, 255, 0.1)`.
  - Left: Logo icon + Wordmark (`font-weight: 700`, `18px`).
  - Center: Nav link items (`13px`, font-medium, color `#93A1C8`, hover `#EAF0FF`).
  - Right: Primary CTA button with subtle glow (`13px`, px-4 py-2, rounded-full or rounded-xl).
  - Mobile ($\le 860$px): Collapses to Sheet drawer.
  - Behavior: Hide on downward scroll past 80px, reveal on upward scroll.
- **C-FOOTPRINT Element**:
  - `Navbar.tsx` with logo, links ("Screening", "Interactions", "Prescription", "Performance", "FAQ"), and "Get started" button linking to `APP_URL`.
  - Desktop: Floating frosted pill with scroll-spy indicator.
  - Mobile ($\le 860$px): shadcn Sheet with branded dark drawer.
  - No Login or Sign-up links.

---

## 2. Hero Section
- **PayPath Reference**:
  - Height: min 92vh. Centered layout with layered background: deep ink base, radial multi-color mesh, drifting background particles/lines, subtle film grain.
  - Eyebrow: Bracket badge `[ Autonomous AI Agents ]` (font-mono, 12px, border rounded-full, px-3.5 py-1).
  - Headline: H1, 56px–64px desktop / 32px–36px mobile, letter-spacing `-0.03em`, weight 700. Features dynamic morphing word with subtle highlight gradient.
  - Subtext: 18px / 15px mobile, text `#93A1C8`, max-w-2xl.
  - CTAs: Primary "Get started" (filled cyan/violet accent) + Secondary "Explore modules" (glass outline with icon).
  - 4 Hero Tabs: `Origination`, `Servicing`, `Collections`, `Recovery`. Auto-advance every 4s with animated progress indicator.
  - Floating Status Cards: Trio of glass cards floating in 3D perspective with status pill badges (`Synced`, `At risk`, `Live`, `Measured`). Offset oscillation $\pm 6$px (5s–7s loops).
  - Persona Chips: Row of 3 interactive persona/case chips beneath the hero cards (`Dana · Regional Bank`, etc.).
- **C-FOOTPRINT Element**:
  - `Hero.tsx`:
    - Bracket label: `[ Pre-clinical Molecular Intelligence ]`.
    - Morphing headline: "Graph intelligence for **[toxicity | interactions | prescriptions]**." (Magic UI / Motion text morph; full sentence in `sr-only` span).
    - Subtext: "Deep Graph Neural Networks for pre-clinical molecular toxicity screening, pairwise drug-drug interaction classification, and multi-drug prescription risk analysis."
    - Dual CTAs: "Get started" (`APP_URL`) and "Explore modules" (`#modules`).
    - Multi-hue animated mesh background (cyan `#19D3FF`, violet `#7A5CFF`, mint `#35E0A1`, coral `#FF5C7A`) + 40-node canvas molecular graph + film grain.
    - 4 Auto-advancing Tabs: `Screening`, `Interactions`, `Prescription`, `Performance` (4s timer).
    - 3 Floating Status Cards with pill badges (`12 Endpoints`, `Scaffold split`, `Major recall 70.5%`).
    - 3 Example Chips: `"Aspirin"`, `"Ethanol + Abacavir"`, `"Four drugs at once"` (clicking sets demo preset).

---

## 3. Scroll-Revealed Statement
- **PayPath Reference**:
  - High impact scroll-triggered statement: 3 lines of 40px–48px text where words transition from `opacity: 0.15` to `opacity: 1.0` based on scroll progress.
  - Followed by a row of rotating/interactive pill badges and a punchy closing tagline.
- **C-FOOTPRINT Element**:
  - `Statement.tsx`:
    - 3-line statement: *"Compounds come in thousands of forms. Combinations multiply the risk. When it could all be screened and explained."*
    - Motion `useScroll` + `useTransform` word-by-word opacity transition.
    - Rotating tag pills: `"Assay plate / screening"`, `"Relation chart / prescription"`, `"Saliency / explainable"`.
    - Closing punchline: *"C-FOOTPRINT makes it visible."*

---

## 4. Stats Counter
- **PayPath Reference**:
  - Grid: 4 columns on desktop, 2 on tablet, 1 on mobile.
  - Metrics: Large digits (48px–56px font-serif or grotesque), rolling digit counter that activates at 40% scroll into view, ease-out 1.2s.
  - Card style: Dark glass cards with border glow, category badge, and concise description.
- **C-FOOTPRINT Element**:
  - `Stats.tsx`:
    - 4 real metrics from Section 6:
      1. `12` Tox21 endpoints
      2. `3` severity classes
      3. `122,378` labelled drug pairs prepared
      4. `5` max drugs per prescription check
    - Split flap / rolling digit animation, tabular numerals, `aria-label` with final value.

---

## 5. Modules Showcase (#modules)
- **PayPath Reference**:
  - Section header with bracket label `[ Solutions ]`, heading, and top-right CTA button.
  - Left column (desktop): Vertical list of 4 tabs with active indicator, title, and one-line description.
  - Right column: Interactive panel containing a hero showcase card (illustration) + carousel of feature cards + "Open this module" action.
  - Mobile: Tabs become a swipeable horizontal tab list.
- **C-FOOTPRINT Element**:
  - `Modules.tsx` (id `#modules`):
    - Bracket label: `[ Modules ]`.
    - Heading: "Explore screening & analysis modules" + "Open the app" button.
    - 4 Tabs: Compound screening, Interaction check, Prescription checker, Model performance.
    - Active panel: Original interactive artwork card (Assay plate wells filling with severity tints; Pairwise bond line with probability bars; SVG relation chart with dashed similar-drug edge; GCN vs GIN metric bars) + feature cards carousel + "Open this module" button linking via `MODULE_LINKS`.

---

## 6. Stack Marquee ("Built on open science")
- **PayPath Reference**:
  - Infinite horizontal marquee with gradient fade masks on left and right edges.
  - Speed: 30s–40s linear loop, pauses on hover, duplicate track `aria-hidden`.
  - Includes a CTA button inline or above.
- **C-FOOTPRINT Element**:
  - `BuiltWith.tsx`:
    - Text chips for: `PyTorch`, `PyTorch Geometric`, `RDKit`, `Flask`, `PubChem`, `Tox21`, `DDInter`.
    - "Get started" button. No third-party brand logos.

---

## 7. Endpoints Grid (#endpoints)
- **PayPath Reference**:
  - "Industries" section: 6 portrait cards with abstract gradients, category badge, sub-chips, and hover spotlight effect.
- **C-FOOTPRINT Element**:
  - `Endpoints.tsx` (id `#endpoints`):
    - 6 portrait cards for the 12 Tox21 assays:
      1. Androgen receptor (`NR-AR`, `NR-AR-LBD`)
      2. Estrogen receptor (`NR-ER`, `NR-ER-LBD`)
      3. Aryl hydrocarbon receptor (`NR-AhR`)
      4. Aromatase (`NR-Aromatase`)
      5. PPAR-gamma (`NR-PPAR-gamma`)
      6. Stress response (`SR-ARE`, `SR-ATAD5`, `SR-HSE`, `SR-MMP`, `SR-p53`)
    - Abstract original vector artwork per card with active assay code pills and biological pathway descriptions.

---

## 8. Pull-Quote (Editorial Principle)
- **PayPath Reference**:
  - High-impact editorial pull-quote block (replaces testimonial): large typography (28px–36px), quotation mark ornament, attribution to institutional authority.
- **C-FOOTPRINT Element**:
  - `PullQuote.tsx`:
    - Large typography: *"Not in DDInter means undocumented, not safe."*
    - Attribution: *"C-FOOTPRINT design principle — computational screening establishes hypothesis, not clinical clearance."*

---

## 9. Interactive Walkthrough Mock
- **PayPath Reference**:
  - Framed video/interface walkthrough demonstrating platform workflow in action.
- **C-FOOTPRINT Element**:
  - `Walkthrough.tsx`:
    - Browser-frame mock with tab header, URL bar (`c-footprint.local/prescription`), and a scripted looping SVG/CSS interaction:
      - 3 drug chips (`Warfarin`, `Aspirin`, `Metformin`) enter the prescription tray.
      - Dynamic network edges draw in between nodes with severity color-coding.
      - Assessment card slides in with DDInter record and similarity inference fallback.
      - Labelled "Illustrative example".

---

## 10. Model Performance Benchmark (#performance)
- **PayPath Reference**:
  - Grouped comparison bars with benchmark metrics and side-by-side performance tiers.
- **C-FOOTPRINT Element**:
  - `Performance.tsx` (id `#performance`):
    - Grouped horizontal bars GCN vs GIN using real values:
      - Test Accuracy: GCN `0.600` vs GIN `0.609`
      - Macro-F1: GCN `0.491` vs GIN `0.490`
      - Major-Class Recall: GCN `0.705` vs GIN `0.609`
    - Highlighting note: Minor class is the weakest; all test drugs were strictly unseen during training (cold-start split). Includes "Get started" button.

---

## 11. Two Feature Cards
- **PayPath Reference**:
  - Two wide technical cards: high-contrast layout, icon, deep dive on methodology and data integrity.
- **C-FOOTPRINT Element**:
  - `Features.tsx`:
    - Card 1: **"Explainable by design"** (atom-level backpropagated gradient saliency `dLogit / dAtom`, topological relation network).
    - Card 2: **"Honest about limits"** (absence in DDInter is undocumented, not safe; in silico hypothesis generation; strictly research & education use).

---

## 12. Trust Section (Data, Evaluation, Limits)
- **PayPath Reference**:
  - Institutional governance/security section with 3 pillars and protocol bullet points.
- **C-FOOTPRINT Element**:
  - `Trust.tsx`:
    - Pillar 1: **Data Provenance** (NIH/EPA Tox21 Data Challenge, DDInter CC BY-NC-SA 4.0, NCBI PubChem).
    - Pillar 2: **Evaluation Protocol** (Bemis-Murcko scaffold split for toxicity, cold-start drug split for pairwise DDI).
    - Pillar 3: **Clinical Boundaries** (Strictly research and education; not medical advice or diagnostic software).

---

## 13. FAQ Accordion (#faq)
- **PayPath Reference**:
  - Accordion list with expandable items, smooth height animation, plus/minus indicator.
- **C-FOOTPRINT Element**:
  - `Faq.tsx` (id `#faq`):
    - shadcn Accordion covering the 6 exact domain questions from Section 6.

---

## 14. Closing CTA Band (Cursor-Reactive Background)
- **PayPath Reference**:
  - High contrast closing section with bold headline, subtitle, primary CTA, and cursor-reactive line mesh / interactive particles.
- **C-FOOTPRINT Element**:
  - `ClosingCta.tsx`:
    - Headline: *"From structure to insight."*
    - Interactive cursor-reactive magnetic lines / particle field canvas.
    - "Get started" Button to `APP_URL`.

---

## 15. Footer
- **PayPath Reference**:
  - Multi-column link layout: Product modules, categories, data attributions, copyright, and compliance disclaimer.
- **C-FOOTPRINT Element**:
  - `Footer.tsx`:
    - Columns: Modules, Tox21 Endpoints, Data Attributions (`https://ddinter.scbdd.com` link).
    - Disclaimer: Research and education only; not for clinical use.
    - Conditional GitHub link (hidden when `GITHUB_URL` is empty).
