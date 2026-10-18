# AGRIFY — Design System & Frontend Architecture (DESIGN.md)

**Status:** Current Implementation Audit & UI Verification Baseline
**Version:** 3.0-production
**Updated:** October 2026

---

## 1. Visual Design Philosophy & Aesthetic
AGRIFY uses a modern agricultural design system combining **dark-mode glassmorphism**, nature-inspired emerald/forest greens, deep obsidian slate backgrounds, and crisp typographic contrast. The UI is built specifically to accommodate both high-end desktop workstations used by agricultural researchers and outdoor, high-glare mobile screens used by farmers in the field.

### Key CSS Artifacts
- `frontend/css/style.css`: Base design tokens, resets, navigation, page layouts, forms, buttons, cards, responsive media queries. (**VERIFIED**)
- `frontend/css/premium.css`: Glassmorphic elevations, glowing badges, HUD overlays for Crop Doctor camera scanner, gradient accents, and bottom-sheet drawers. (**VERIFIED**)

---

## 2. Design Tokens & Color Palette

```css
:root {
  /* Surface & Backgrounds */
  --bg-primary: #0a0f0d;         /* Deep obsidian night */
  --bg-secondary: #121c17;       /* Dark evergreen tint */
  --bg-card: rgba(18, 28, 23, 0.75); /* Translucent glass card */
  --border-color: rgba(46, 125, 50, 0.25); /* Subtle green border */

  /* Brand Accents */
  --accent-primary: #10b981;     /* Vivid Emerald (Success / Actions) */
  --accent-glow: rgba(16, 185, 129, 0.2);
  --accent-warning: #f59e0b;     /* Amber (Caution / Estimated data) */
  --accent-danger: #ef4444;      /* Crimson (Disease / Critical Alerts) */
  --accent-info: #3b82f6;        /* Sky Blue (Weather / Precipitation) */

  /* Typography */
  --text-main: #f3f4f6;          /* High contrast light text */
  --text-muted: #9ca3af;         /* Secondary descriptive labels */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

---

## 3. Component Architecture & Implementation Status

### 3.1 Global Navigation (`frontend/js/components/navbar.js`) — **VERIFIED**
- Fixed top navigation bar featuring the AGRIFY leaf logo, real-time live clock, language selector dropdown (`en`, `te`), and theme toggle.
- *Localization Boundary:* Currently switches between English (`en`) and Telugu (`te`) via `i18n.js`. While Hindi voice copilot exists, full static UI Hindi localization across all 8 routes is **PLANNED**.
- Tab-based navigation links covering all 8 main routes with active-state indicators and accessible ARIA attributes.
- Collapsible hamburger menu on mobile viewports (< 768px).

### 3.2 Voice Copilot Modal & FAB (`frontend/js/components/voiceAssistantModal.js`) — **VERIFIED**
- Floating Action Button (FAB) anchored to bottom-right (`position: fixed; bottom: 24px; right: 24px; z-index: 1000`).
- Responsive presentation:
  - **Mobile (< 640px):** Slides up as an ergonomic **bottom-sheet drawer** with touch drag-handle.
  - **Desktop (>= 640px):** Centered modal with glassmorphic backdrop filter and subtle border glow.
- Speech wave animation pulsing during active voice input and synthesis.
- Dual action buttons: Text fallback input and live audio microphone capture. Verified by 28 automated tests in `frontend/test_voice_copilot_ui.js`.

### 3.3 Crop Doctor Camera & Upload HUD (`frontend/js/pages/cropDoctor.js`) — **IMPLEMENTED BUT HARDWARE DEPENDENT**
- Dual-mode selector: File Upload zone (drag & drop) vs. Live Camera scanner.
- Live camera viewport incorporates a **HUD corner bracket overlay** with dynamic scanning lines guiding leaf alignment in CSS/HTML.
- Camera streaming runtime relies on browser `navigator.mediaDevices.getUserMedia` hardware permission; file upload fallback is fully verified.

### 3.4 Data Visualizations (`frontend/js/charts.js`) — **VERIFIED**
- Powered by Chart.js (version 4.x via CDN).
- Responsive line and bar charts for 5-day temperature/humidity trends, soil nutrient radar profiles (N-P-K ratios), and historical mandi price distributions.

---

## 4. Responsive Viewport Strategy — **VERIFIED**

The application styles and layout adjustments are verified across standard mobile, tablet, and desktop breakpoints:

| Breakpoint | Target Devices | Design Adjustments | Status |
| :--- | :--- | :--- | :--- |
| **320px (Ultra-compact)** | Older / budget Android handsets | Single-column cards, font-size clamps, horizontal scroll for tables, hidden non-critical icons. | **VERIFIED** |
| **390px (Standard Mobile)** | iPhone 12/13/14/15, Pixel, Galaxy | Standard mobile layout, bottom-sheet voice copilot, stacked metric pills. | **VERIFIED** |
| **768px (Tablet)** | iPad, Android tablets | 2-column grid for farm analysis metrics, expanded navigation tabs. | **VERIFIED** |
| **1024px+ (Desktop)** | Laptops & monitors | Multi-column dashboard layouts, floating centered modals, side-by-side camera and diagnostic cards. | **VERIFIED** |

---

## 5. Accessibility & Performance Guardrails — **VERIFIED**
1. **Reduced Motion:** Comprehensive `@media (prefers-reduced-motion: reduce)` rules disable rotating spinners, pulsing waveforms, and modal slide transitions for sensitive users.
2. **High-Contrast Text:** Color contrast ratios for primary body text against dark backgrounds exceed WCAG 2.1 AA requirements (>= 4.5:1).
3. **No External Image Dependencies in Core Flow:** UI icons utilize SVG and Unicode emojis to avoid latency or broken asset requests under low rural bandwidth.
