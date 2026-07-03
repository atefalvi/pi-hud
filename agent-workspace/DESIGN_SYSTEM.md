# pi-hud Design System

## Design source

`pi-hud` must visually align with DataDreamer Observatory.

Use the uploaded DataDreamer logo asset:

```text
agent-workspace/assets/data-dreamer-logo-pop-dark.svg
```

Do not redraw the DataDreamer logo. Use the asset as-is if branding is needed.

## Art direction

The interface should feel like:

```text
a calm technical instrument panel
not a generic homelab dashboard
not a neon cyberpunk dashboard
not a SaaS admin template
```

## Brand translation

DataDreamer Observatory principles applied to `pi-hud`:

| DataDreamer principle | pi-hud translation |
|---|---|
| Dark-first | Default UI uses dark surfaces |
| Hairline rules | Use 1px borders, not heavy shadows |
| Ember accent | Use ember for selected/active/brand states |
| Pixel motif | Use square/pixel details subtly |
| Data motif | Use the ember dot as live/status marker |
| Connection motif | Use thin timeline lines and status rails |
| Restrained color | Semantic colors only when state requires them |

## Color tokens

```css
--bg-0: #0A0C10;
--bg-1: #0F1318;
--bg-2: #161B22;
--bg-3: #1D242E;
--border-1: #1F262F;
--border-2: #2E3744;
--text-1: #EDEFF3;
--text-2: #A8B1BD;
--text-3: #858E99;
--accent: #FF5C38;
--success: #3ECF8E;
--warning: #F5B83D;
--danger: #F0564A;
--info: #5CA7FF;
```

## UI rules

- Do not write `OK` repeatedly.
- Use colored values, dots, badge piles, rails, and severity chips.
- Do not put `sticky` in the UI. Use `Pinned`, `PIN`, or `Pinned on display`.
- Do not put service badges on screens where they compete with alert content.
- Pending queue screen must only show grouped queue rows and counts.
- Use Inter/system UI for body.
- Use Fraunces-like serif for H1/H2 in the web UI if available.
- Use mono labels for metadata.
- Use hairlines over shadows.

## Anti-patterns

Reject:

- gradient mesh backgrounds
- glass cards everywhere
- 3+ accent colors in one section
- text over busy imagery
- emoji as icons
- heavy drop shadows
- long status labels
- uppercase body text
- React-style component dashboards
