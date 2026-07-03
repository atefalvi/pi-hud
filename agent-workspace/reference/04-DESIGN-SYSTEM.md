# 04 — Design System: "Observatory"

The v4 design language. Codename **Observatory**: a precision instrument with an
editorial soul. Everything here is implementation-ready; token values are final unless
the handoff records a change.

---

## 1. Art direction

### 1.1 Concept
A quiet, dark, high-craft reading environment — the feeling of a well-lit instrument
panel in a calm room. Three ingredients, deliberately balanced:

1. **Editorial**: serif display headlines, generous whitespace, strong typographic
   hierarchy, restrained color. The site reads like a beautifully typeset journal.
2. **Technical**: mono-set metadata, hairline rules, data-as-texture (dates, counts,
   reading time), one signal color used like an annotation marker.
3. **Alive but still**: one ambient canvas moment (the homepage hero), micro-motion
   everywhere else measured in pixels, not theatrics.

### 1.2 What makes it premium (operationally, not adjectives)
- **One display serif used rarely and large** — H1/H2 only. Scarcity reads as intent.
- **A 4px-grid spacing system actually obeyed** — no ad-hoc 13px paddings.
- **Hairline borders (1px, low-contrast) instead of boxes and shadows** as the default
  separator; elevation reserved for genuinely floating UI (menus, dialogs).
- **Max two typefaces visible per viewport** (serif display + sans body; mono appears
  only as metadata/code).
- **Asymmetric editorial layouts**: content blocks sit on a 12-col grid with intentional
  offsets (e.g. article header spans cols 1–8, meta rail 10–12) instead of centered
  symmetric stacks.
- **Color discipline**: neutrals do 95% of the work; ember accent < 5% of any viewport.
- **Real states**: every interactive element has designed hover, focus-visible, active,
  and disabled states — specified in §10, no defaults left to the browser.

### 1.3 Explicit anti-patterns (reject in review)
Gradient-mesh hero blobs; glassmorphism cards everywhere; 3+ accent colors; scroll-jacked
sections; text over busy imagery; uppercase body text; skeleton shimmer on static pages;
emoji as icons; drop shadows on text; carousels for primary content.

### 1.4 Brand motifs — pixel · data · connection (owner requirement, binding)
The existing DataDreamer logo (a bold geometric "D" built from nested squares, with a
small red circular dot at the lower-left) **is retained, not redesigned** (§9). Its
three ideas are the visual DNA the whole site must echo:

| Motif | Source in the logo | Where it recurs in v4 |
|---|---|---|
| **Pixel** | the nested-square, grid-built construction | hero field's neutral points are small *squares*, not circles (07 §2); square stat tiles; sharp square crops inside otherwise-rounded media frames are allowed as accents; favicon |
| **Data** | the detached red dot (the datum) | ember-accent dots: active nav indicator, list markers, the pulsing nodes in the hero, specialty anchors in the team graph, "live" indicators |
| **Connection** | the dot's relationship to the frame | hairline link lines: hero node connections, Dream Team edges, timeline rules, breadcrumb separators |

Rule of use: motifs appear as *details*, never as wallpaper — one motif moment per
section maximum. They are how the elite, editorial v4 still unmistakably reads as
DataDreamer.

## 2. Theme decision

**Dark-first, dual theme.** Dark is the brand-defining default (data/AI audience,
continuity with v3); light theme is a first-class equal, not an inversion afterthought —
it uses warm paper neutrals, not pure white. Toggle in nav; preference stored in
`localStorage.theme`; pre-paint inline script (keep v3's mechanism, audit §6). Both
themes must pass AA contrast; both get designed screenshots in QA.

## 3. Color system

Defined once in `src/styles/tokens.css` as CSS custom properties. No raw hex anywhere
else (lint rule: grep for `#[0-9a-fA-F]{3,8}` outside tokens.css fails review; SVG
assets exempt).

### 3.1 Dark theme (default)

| Token | Value | Role |
|---|---|---|
| `--bg-0` | `#0A0C10` | Page background |
| `--bg-1` | `#0F1318` | Card / surface |
| `--bg-2` | `#161B22` | Raised surface (hover, code blocks, inputs) |
| `--bg-3` | `#1D242E` | Highest surface (menus, dialogs) |
| `--border-1` | `#1F262F` | Hairlines, default borders |
| `--border-2` | `#2E3744` | Hover borders, emphasized rules |
| `--text-1` | `#EDEFF3` | Headings, primary text |
| `--text-2` | `#A8B1BD` | Body secondary, descriptions |
| `--text-3` | `#858E99` | Metadata, placeholders |
| `--text-on-accent` | `#05070A` | Text/icons on solid accent controls |
| `--accent` | `#FF5C38` | Ember — links, active states, markers |
| `--accent-hover` | `#FF7657` | Hover on accent elements |
| `--accent-press` | `#E04A2A` | Active/pressed |
| `--accent-subtle` | `rgba(255,92,56,0.12)` | Tints, selected backgrounds |
| `--success` | `#3ECF8E` | Completion, positive |
| `--warning` | `#F5B83D` | Warning callouts |
| `--danger` | `#F0564A` | Errors, destructive |
| `--info` | `#5CA7FF` | Info callouts |
| `--focus-ring` | `#7AB8FF` | Focus outline (distinct from accent on purpose) |

### 3.2 Light theme ("gallery paper")

| Token | Value |
|---|---|
| `--bg-0` `#FAF9F7` · `--bg-1` `#FFFFFF` · `--bg-2` `#F2F0EB` · `--bg-3` `#FFFFFF` |
| `--border-1` `#E5E2DA` · `--border-2` `#CFCABF` |
| `--text-1` `#1B1E23` · `--text-2` `#4D545E` · `--text-3` `#646D77` · `--text-on-accent` `#05070A` |
| `--accent` `#D9431F` (darkened ember for 4.5:1 on paper) · `--accent-hover` `#B83817` · `--accent-press` `#9C2F12` · `--accent-subtle` `rgba(217,67,31,0.08)` |
| `--success` `#1E9E68` · `--warning` `#B07A12` · `--danger` `#C92F23` · `--info` `#1F6FD6` · `--focus-ring` `#2D6FD0` |

### 3.3 Data-viz / specialty ramp (Dream Team graph, charts)
`--viz-1: var(--accent)`, `--viz-2: #5CA7FF`, `--viz-3: #3ECF8E`, `--viz-4: #C792EA`,
`--viz-5: #F5B83D`, `--viz-6: #64D8CB`. Never used for UI semantics; specialty color
assignments live in the `specialties.color_key` field (values `viz-1`…`viz-6`).

### 3.4 Brand continuity note
Ember `#FF5C38` is a deliberate descendant of v3's `#FF2E00` — same family, lower
aggression, AA-checked. **The logo's red dot keeps its original brand red `#FD2E00`
in the lockup itself** (logos are identity, not UI); everywhere the dot motif is
*echoed* in UI (§1.4) it uses `--accent` so it harmonizes with each theme.

> Deviation (V4-DS-001): `--text-3` was adjusted from the planning values
> (`#6E7783` dark, `#7A828D` light) to `#858E99` and `#646D77` so the metadata token
> meets WCAG AA contrast across every documented v4 surface in both themes.

## 4. Typography

### 4.1 Faces (all self-hosted woff2 via `@fontsource-variable/*`; no Google CDN)

| Role | Face | Usage |
|---|---|---|
| Display | **Fraunces** (variable; opsz, wght 500–650, SOFT 0, WONK 0) | H1, H2, pull quotes, big numerals. Never below 24px. |
| Text/UI | **Inter** (variable) | Body, H3–H6, nav, buttons, forms |
| Mono | **JetBrains Mono** (400, 600) | Code, kickers/eyebrows, metadata, dates, tags |
| Brand wordmark | **Vector pixel wordmark** (§9.2) | The "DATA DREAMER" wordmark in the logo lockup, footer brand block, and OG images. **Never loaded as a webfont in v4** and never used for headings or UI text |

Per owner direction on 2026-06-12, the lockup wordmark uses a custom pixel-outline
treatment instead of Anton. The wordmark ships as SVG paths only, keeping zero
font-loading cost and preserving the pixel/data brand motif.

Loading: preload the two variable woff2 files used above the fold (Fraunces + Inter),
`font-display: swap`, metric-compatible fallback stacks
(`Georgia, serif` / `system-ui, sans-serif` / `ui-monospace, monospace`) with
`size-adjust` overrides to keep CLS ≈ 0.

### 4.2 Fluid type scale (clamp between 360px and 1440px viewports)

| Token | Min → Max | Line-height | Use |
|---|---|---|---|
| `--fs-xs` | 12 → 12.5px | 1.5 | fine print, tag chips |
| `--fs-sm` | 13.5 → 14px | 1.55 | metadata, captions, nav |
| `--fs-base` | 16 → 17.5px | 1.65 | body (blog body uses max) |
| `--fs-lg` | 18 → 20px | 1.55 | lede paragraphs, card titles |
| `--fs-xl` | 21 → 24px | 1.4 | H4 / section intros |
| `--fs-2xl` | 25 → 30px | 1.3 | H3 |
| `--fs-3xl` | 30 → 40px | 1.15 | H2 (Fraunces) |
| `--fs-4xl` | 38 → 56px | 1.08 | H1 standard pages (Fraunces) |
| `--fs-display` | 44 → 84px | 1.02 | Home hero / landing H1 (Fraunces) |
| `--fs-mono-label` | 12 → 13px | 1.4, tracking +0.08em, uppercase | kickers ("eyebrows") |

Heading behavior: Fraunces headings use `letter-spacing: -0.015em`, `font-weight: 560`,
`text-wrap: balance`. Sentence case **always** (no `text-transform: uppercase` except
`--fs-mono-label` kickers). Headings never truncate; cards clamp descriptions
(2 lines), never titles (3-line max via `-webkit-line-clamp: 3`).

### 4.3 Reading measure
- Prose (article body): `max-width: 70ch` (~720px at `--fs-base` max).
- Ledes/intros: `max-width: 56ch`.
- Card descriptions: `max-width: 44ch`.
Never let body text exceed 75 characters per line — enforced by container widths.

## 5. Layout grid & spacing

### 5.1 Containers
| Token | Width | Use |
|---|---|---|
| `--container-prose` | 720px | Article bodies |
| `--container-content` | 1120px | Default page content |
| `--container-wide` | 1320px | Hero, full-bleed grids, graph |
| Page gutter | `clamp(20px, 4vw, 48px)` | `--gutter` |

### 5.2 Grid
12-column CSS grid (`display:grid; grid-template-columns: repeat(12, 1fr); gap: var(--space-6)`)
inside containers, used for asymmetric editorial layouts. Collapse map per breakpoint is
specified in each blueprint; default collapse: 12 → 6 (tablet) → 4 (mobile) conceptual
columns (in practice: explicit `grid-template-columns` overrides at breakpoints).

### 5.3 Spacing scale (4px base)
`--space-1: 4px` `-2: 8` `-3: 12` `-4: 16` `-5: 24` `-6: 32` `-7: 48` `-8: 64`
`-9: 96` `-10: 128`. Section vertical rhythm: `--section-y: clamp(72px, 9vw, 136px)`.
Component internal padding ratio: cards `--space-5/--space-6`; never mix scales.

### 5.4 Breakpoints (decision rationale in 11 §1)
`--bp-sm 480px` (large phones) · `--bp-md 768px` (tablet portrait / nav switch) ·
`--bp-lg 1024px` (tablet landscape / sidebars appear) · `--bp-xl 1280px` (full grid) ·
`--bp-2xl 1536px` (wide clamp). Mobile-first media queries only (`min-width`).

## 6. Surfaces, elevation, geometry

- Radius: `--radius-sm: 6px` (chips, inputs) · `--radius-md: 10px` (cards, buttons) ·
  `--radius-lg: 16px` (media, dialogs) · `--radius-full` (avatars, pills).
  This is the headline geometric break from v3's 0px world.
- Borders 1px `--border-1` everywhere; 2px reserved for selected states.
- Elevation: `--shadow-1: 0 1px 2px rgba(0,0,0,.3)` (dark) — cards at rest have **no**
  shadow, only border; `--shadow-2: 0 8px 24px rgba(0,0,0,.35)` menus/dialogs;
  `--shadow-3: 0 16px 48px rgba(0,0,0,.45)` modals/lightbox. Light theme: same
  structure at .08/.12/.18 alpha.
- Glass: **one permitted use** — the sticky nav (`backdrop-filter: blur(14px)` +
  `background: color-mix(in srgb, var(--bg-0) 78%, transparent)`). Nowhere else.
- Texture: no grain overlay. Optional ultra-subtle radial vignette on hero only.

## 7. Imagery & media

- Cover/case-study images: rendered at natural color (retire grayscale-hover),
  `--radius-lg`, 1px inset hairline (`outline: 1px solid color-mix(...border-1 50%…)`),
  hover: `transform: scale(1.02)` on the img inside an `overflow:hidden` wrapper.
- Aspect ratios fixed per slot (cards 16/10, article inline images natural, avatars 1/1)
  with `aspect-ratio` CSS → zero CLS.
- All Directus images delivered via transform params (see `09-…` §7): widths
  {480, 800, 1200, 1600}, `format=webp`, `quality=80`, `srcset` + `sizes` mandatory.
- Portrait/avatar treatment: circular, 2px `--bg-0` ring + 1px `--border-2`;
  duotone optional treatment for the team graph (CSS `filter: saturate(.85)`).
- Decorative figures (hero field, dividers) are SVG/canvas, never raster.

## 8. Iconography

- **Library: Lucide** (`lucide-static` — import raw SVGs at build, no JS runtime).
  Single library; adding any other icon set requires a documented decision in handoff.
- Stroke 1.75 at 16px, 1.5 at 20/24px. Sizes: 16 (inline/meta), 20 (buttons, nav), 24
  (feature/callouts). Icons inherit `currentColor`.
- Decorative icons: `aria-hidden="true"`. Meaningful stand-alone icons: wrap with
  visually-hidden text or `aria-label` on the interactive parent.
- Custom SVGs allowed only for: logo system, callout glyph set (§ Callouts in 05),
  specialty marks (graph), empty-state illustrations. Stored in `src/assets/icons/`
  (custom) — naming `icon-[name].svg`, lowercase-hyphenated.

## 9. Logo system — **the existing mark is retained** (owner decision, 2026-06-12)

### 9.1 The mark (not a redesign)
The DataDreamer logo stays exactly what it is: a bold, geometric **"D" monogram built
from nested square shapes** — an outer square frame, an inner square counter, pixel-grid
construction — with a **small red circular dot at the lower-left corner** where the
frame breaks open. It already embodies the brand motifs (§1.4): pixel (nested squares),
data (the dot), connection (the dot completing the frame). The v4 job is to
*productionize* it, not replace it.

**Source of truth**: the path data currently in
`frontend/src/components/Logo.astro` (`viewBox 0 0 1024 1024`; main path on
`--logo-main`, accent path `#fd2e00`). Task V4-DS-004 extracts this into standalone
SVG assets with only these permitted changes:
- path cleanup/optimization (svgo; merge stray subpaths; no visible geometry change —
  before/after overlay diff at 1024px must show no deviation);
- accent dot color stays brand red `#FD2E00` in the lockup (§3.4); the mono variant
  may flatten it to `currentColor`;
- ink fill driven by `--logo-ink` (defaults to `currentColor`) so the mark sits on
  both themes without per-theme files.

### 9.2 Wordmark & lockup
The wordmark reads **"DATA DREAMER" in uppercase vector pixel outlines**, optically
aligned to the mark's cap height. In v4 it ships as SVG paths only — no brand
webfont is loaded (§4.1), and the lockup must not contain live `<text>`. The primary
lockup is a composed horizontal system: retained mark, fine vertical divider, then a
stacked two-line wordmark (`DATA` above `DREAMER`) built from separated modular
pixels. This stacked composition is the preferred premium lockup because it gives the
long name a controlled block shape instead of an overextended single line. This is
the only place uppercase display type appears in v4, making the brand moment a
single intentional signature instead of a reusable UI type style.

### 9.3 Variants & usage

| Variant | Composition | Used at |
|---|---|---|
| Primary lockup | Mark + fine divider + stacked pixel-outline wordmark "DATA" / "DREAMER", red dot in brand red | Nav (≥480px), footer brand block, OG images |
| Compact mark | Mark alone (with red dot) | Nav <480px, favicons, avatars, watermark |
| Mono (ink) | Everything `currentColor`, dot included | Print, single-color contexts, 404 watermark |
| Light-bg / dark-bg | Ink = `--text-1` of active theme via `--logo-ink`; dot always `#FD2E00` (verify dot contrast on `--bg-0` light: passes — it sits on paper `#FAF9F7`) | everywhere |
| Favicon | Mark alone; at 16px the dot may be enlarged ~1.4× for legibility (only permitted geometry deviation, favicon files only) | `/favicon.svg`, 32px `.ico` |

Rules: min height 20px (mark), 64px (stacked lockup). Use the compact mark instead
of the stacked lockup below 64px; the two-line pixel wordmark is a premium brand
composition, not a tiny nav label. Clear space = dot diameter on all sides. Never
recolor the dot (except mono variant); never skew, outline, or shadow the mark;
never set the wordmark in a live font. `aria-label="DataDreamer"` when the logo is
the home link's only content; `aria-hidden="true"` when accompanied by visible text.
Files: `src/assets/brand/logo-mark.svg`, `logo-lockup.svg`, `logo-mono.svg`,
`public/favicon.svg`, `public/favicon.ico`. `Logo.astro` and `public/logo.svg` are
superseded by these assets (swap in SHELL-002; old files removed in CLEAN-001).

## 10. Interaction states (universal contract)

| State | Treatment |
|---|---|
| Hover (links) | `color: var(--accent)`; underline `text-underline-offset: 3px` appears (body links are underlined at rest; nav/card links are not) |
| Hover (cards) | `border-color: var(--border-2)`; `translateY(-2px)`; 200ms ease-out; img scale 1.02 |
| Hover (buttons) | bg shifts one step (`--accent-hover` / `--bg-2`→`--bg-3`) |
| Focus-visible | `outline: 2px solid var(--focus-ring); outline-offset: 2px` — global rule, never removed, never replaced by box-shadow |
| Active/pressed | translateY(0) + `--accent-press`/`--bg-2`; 80ms |
| Disabled | `opacity: .45; cursor: not-allowed`; no hover effects |
| Selected (chips/filters) | `background: var(--accent-subtle); border-color: var(--accent); color: var(--text-1)` + a leading check icon (never color alone) |

## 11. Button hierarchy (exactly three)

| Variant | Look | Use |
|---|---|---|
| `primary` | Solid `--accent`, `--text-on-accent`, radius-md, 40px (md) / 48px (lg) height, Inter 500 | One per view max: hero CTA, Start/Resume guide, Submit |
| `secondary` | 1px `--border-2` border, `--text-1`, transparent bg; hover `--bg-2` | Paired actions, "View all" |
| `ghost` | Text + 16px icon, no border; hover `--bg-2` pill | Tertiary, toolbars, "← Back" |

Sizes: sm 32px (dense UI), md 40px (default), lg 48px (hero/forms). Icon gap 8px.
Loading state: label → spinner + label ("Saving…"), `aria-busy="true"`, width locked.

## 12. Motion language

- Durations: `--dur-1: 120ms` (state), `--dur-2: 200ms` (hover/UI), `--dur-3: 360ms`
  (entrances, menus), `--dur-4: 700ms` (hero reveals only).
- Easings: `--ease-out: cubic-bezier(0.16, 1, 0.3, 1)` (entrances),
  `--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1)` (movement), linear for opacity-only.
- Scroll reveals: opacity 0→1 + translateY 12px→0, `--dur-3`, once per element,
  IntersectionObserver threshold 0.2, stagger 60ms within a group, max 5 staggered
  items (rest appear together). Implemented by one utility (`lib/motion/reveal.ts`)
  via `data-reveal` attributes — no per-component observers.
- Page transitions: **none in v4.0** (SSR full loads; fast > fancy). Astro View
  Transitions evaluated post-launch; recorded as future work, not planned scope.
- `prefers-reduced-motion: reduce` → global: all `data-reveal` elements render final
  state; hero shows static composition; durations forced to 1ms via media query.
- Nothing animates `width/height/top/left`; transforms + opacity only.

## 13. Editorial rhythm & density

- Page = vertical sequence of sections separated by `--section-y`; alternate full-width
  hairline rules (`<hr class="rule">`) between major sections instead of background
  color bands (max one tinted band per page, e.g. the guides teaser).
- Each section opens with the **kicker pattern**: mono label (`--fs-mono-label`,
  `--text-3`) + Fraunces heading + optional 56ch intro — the v4 descendant of v3's
  `// LABEL` habit, now sentence case without slashes.
- Density rule: listing pages show 6–9 items before any "view all"; article pages have
  zero sidebars except TOC ≥ 1024px; dashboards may be denser (40px row heights).

## 14. Component consistency principles

1. Every shared component lives in `src/components/ui/` or a domain folder and defines
   a typed `Props` interface — no `any`.
2. Tokens only — a component using a raw px value > 4px-grid or raw hex fails review.
3. Variants via props, not copy-paste (`<Button variant="secondary">`).
4. Cards across domains (post, project, guide, author) share the `Card` primitive's
   geometry/hover and differ only in slot content.
5. Empty/loading/error visual patterns come from `ui/EmptyState.astro` and
   `ui/ErrorState.astro` — never bespoke.
6. New tokens require editing `tokens.css` + this doc in the same PR.

## 15. Token file skeleton (authoritative starting point for V4-DS-001)

```css
/* src/styles/tokens.css */
:root {
  /* color: dark default (§3.1) … */
  /* type (§4) --font-display, --font-text, --font-mono, --fs-* … */
  /* space (§5.3), radius (§6), shadow (§6), motion (§12) … */
}
[data-theme="light"] { /* §3.2 overrides */ }
@media (prefers-reduced-motion: reduce) {
  :root { --dur-1: 1ms; --dur-2: 1ms; --dur-3: 1ms; --dur-4: 1ms; }
}
```
`base.css` (v4) = thin reset + base element styles importing tokens; the 953-line v3
`global.css` is deleted in V4-CLEAN-001, with blog-content styles moving to
`styles/prose.css` (rewritten to the v4 look but selector-compatible with the markdown
pipeline output classes).
