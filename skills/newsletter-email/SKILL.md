---
name: newsletter-email
description: Generate and send branded HTML email newsletters with data tables, KPI cards, and charts. Use when: (1) Creating periodic client reports (weekly flash, monthly report), (2) Sending branded HTML emails from JSON/CSV data, (3) Building newsletter templates with company branding, (4) Embedding data visualizations in emails. Outputs both HTML and text versions. Delivers via AgentMail MCP.
requires:
  env:
    - AGENTMAIL_API_KEY
---

# Newsletter Email Skill — v1

Generate branded HTML email newsletters from structured data. Supports KPI cards, data tables, charts (QuickChart.io), and section-based layout. Delivers via **AgentMail MCP** with both `html` and `text` versions.

---

## When to Use This Skill

- **Periodic client reports** — Weekly flash alerts, monthly full reports
- **Branded newsletters** — Company-branded emails with logos, colors, fonts
- **Data-driven emails** — Reports with scores, rankings, trends, comparisons
- **Multi-client white-label** — Same structure, different brand configs

**DO NOT use** for: simple text emails, transactional emails, one-off messages without branding requirements.

---

## Core Principles

1. **Never write HTML from scratch** — Always compose from templates + sections
2. **Always provide both `html` AND `text`** — text is the fallback for clients that block HTML
3. **Brand config drives everything** — Colors, fonts, logo, tone come from `brands/<client>.json`
4. **Use the compile script** — `scripts/compile.mjs` handles Mustache rendering, MJML compilation, QA, and text generation
5. **Charts via QuickChart.io** — Server-rendered PNG images, zero JS in email

---

## Quick Start

### Step 1: Identify the brand
Read the brand config: `brands/<client>.json`
If no config exists, copy `brands/_template.json` and fill in real values.

### Step 2: Prepare the data
The input should be structured JSON. For GEO reports:
```json
{
  "report_type": "weekly_flash",
  "period": "2026-04-20 to 2026-04-26",
  "report_title": "Flash Hebdomadaire GEO",
  "client_name": "Storyline Communication",
  "subject": "Flash GEO — Semaine du 20 avril 2026",
  "kpis": [
    {"label": "Score moyen", "value": "78/100", "delta": "+5", "direction": "up"},
    {"label": "Requêtes top 3", "value": "12/16", "delta": "+2", "direction": "up"},
    {"label": "Couverture SERP", "value": "84%", "delta": "-3%", "direction": "down"}
  ],
  "table": {
    "title": "Top Requêtes — Scores",
    "headers": ["Requête", "Score", "Delta", "Tendance"],
    "rows": [
      {"cells": ["meilleur avocat Montréal", "92", "+8", "↑"], "bg": "#2A2A2A"},
      {"cells": ["cabinet juridique Québec", "85", "+3", "↑"], "bg": "#1A1A1A"}
    ]
  },
  "charts": {
    "trend": {
      "title": "Évolution du score moyen",
      "url": "https://quickchart.io/chart?c={type:'line',data:{labels:['S1','S2','S3','S4'],datasets:[{data:[70,74,78,81],borderColor:'#D4A853',fill:true,tension:0.4}]}},options:{scales:{y:{min:50,max:100}}}}&w=500&h=250&bg=transparent",
      "width": 500, "height": 250
    }
  },
  "articles": [
    {"title": "Points forts", "body": "Le score moyen a augmenté de 5 points."},
    {"title": "Points d'attention", "body": "La couverture SERP a diminué de 3%."}
  ],
  "footer_note": "Rapport généré automatiquement — GEO Présence surveille votre visibilité"
}
```

### Step 3: Compile the email
**Use the compile script** — it handles everything:

```bash
cd /data/.openclaw/skills/newsletter-email/
node scripts/compile.mjs --brand geo-presence --data examples/weekly-flash.json --out /tmp/newsletter
```

The compile script:
1. Loads brand config from `brands/<client>.json`
2. Loads data JSON
3. **Transforms data** — maps `direction: "up"` → `delta_color: "#4CAF50"`, `delta_icon: "↑"`, `bg` → `bg_color`
4. Renders Mustache templates → MJML
5. Compiles MJML → HTML (minified)
6. Generates plain-text fallback
7. Runs QA checks
8. Outputs `<prefix>.html` + `<prefix>.txt`

> ⚠️ **Prerequisites:** `npm install mjml` (run once in the skill directory). The script uses a built-in Mustache renderer — no external Mustache dependency needed.

### Step 4: Review QA output
The compile script runs these checks automatically:
- ✅ HTML starts with `<!DOCTYPE html>`
- ✅ No `<style>` blocks (except dark mode `data-embed`)
- ✅ No flexbox/grid/position:absolute
- ✅ All images have `alt`, `width`, `height`
- ✅ HTML size ≤ 35KB
- ✅ Subject line ≥ 10 characters

Manual review:
- [ ] Brand colors match config (no conflicting hardcoded colors)
- [ ] Text version contains same key info (KPI labels, values, table headers)
- [ ] Recipient email is valid (matches `/\S+@\S+\.\S+/`)

### Step 5: Send via AgentMail
```
mcporter call agentmail.send_message \
  inboxId:<brand_inbox> \
  to:[<client_email>] \
  subject:"<subject>" \
  html:"<full_html>" \
  text:"<plain_text>" \
  cc:[<your_email>]
```

**IMPORTANT:** Use `html:` for the HTML body, `text:` for the plain-text fallback. Never put HTML in `text:` — it will render as raw code.

---

## Template Structure

```
newsletter-email/
├── SKILL.md                          # This file
├── templates/
│   ├── base.mjml                     # Master layout (header, footer, dark mode)
│   └── sections/
│       ├── header.mjml               # Logo + brand bar (also inline in base.mjml)
│       ├── kpi-row.mjml              # 3-column KPI cards with delta indicators
│       ├── data-table.mjml           # Styled table with alternating rows
│       ├── chart.mjml                # QuickChart image embed
│       ├── article-card.mjml         # Narrative content block
│       ├── section-divider.mjml      # Gold bar separator
│       └── footer.mjml               # Unsubscribe, branding, legal (also inline in base.mjml)
├── brands/
│   ├── geo-presence.json             # Dark/gold palette for GEO reports
│   └── _template.json                # Blank config for new clients
├── scripts/
│   └── compile.mjs                   # Node.js: Mustache → MJML → HTML + QA + text
├── references/
│   ├── quickchart-patterns.md        # URL patterns for common chart types
│   └── email-client-compat.md        # Compatibility notes for 2026
└── examples/
    ├── weekly-flash.json             # Sample weekly flash data
    └── weekly-flash.html             # Expected compiled output
```

---

## Data Transformation Reference

The compile script automatically transforms these fields:

| Input JSON field | Transformed to | Value mapping |
|-----------------|---------------|---------------|
| `kpis[].direction: "up"` | `delta_color` | `#4CAF50` (green) |
| `kpis[].direction: "down"` | `delta_color` | `#E53935` (red) |
| `kpis[].direction: "up"` | `delta_icon` | `↑` |
| `kpis[].direction: "down"` | `delta_icon` | `↓` |
| `kpis[].direction` (other) | `delta_color` | `#A89F8F` (muted) |
| `kpis[].direction` (other) | `delta_icon` | `→` |
| `table.rows[].bg` | `bg_color` | Same value (alias for template compat) |
| `table.rows[].cells` | `cells[]` | Each cell rendered as `<td>` |

Brand config is merged into data for flat Mustache access:
- `{{colors.primary}}` → brand config primary color
- `{{logo.url}}` → brand config logo URL
- `{{fonts.heading}}` → brand config heading font

---

## QuickChart URL Patterns

Charts are server-rendered PNG images via [QuickChart.io](https://quickchart.io). Pass Chart.js config as URL parameter.

### Bar Chart — Query Scores
```
https://quickchart.io/chart?c={type:'bar',data:{labels:['Q1','Q2','Q3'],datasets:[{data:[92,85,67],backgroundColor:['#D4A853','#B8943F','#8B7330']}]},options:{plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,max:100}}}}&w=400&h=200&bg=transparent
```

### Line Chart — Trend Over Time
```
https://quickchart.io/chart?c={type:'line',data:{labels:['S1','S2','S3','S4'],datasets:[{label:'Score',data:[70,74,78,81],borderColor:'#D4A853',backgroundColor:'rgba(212,168,83,0.1)',fill:true,tension:0.4}]},options:{scales:{y:{beginAtZero:false,min:50,max:100}}}}&w=500&h=250&bg=transparent
```

### Gauge/Doughnut — Score 0-100
```
https://quickchart.io/chart?c={type:'doughnut',data:{labels:['Score','Reste'],datasets:[{data:[78,22],backgroundColor:['#D4A853','#2A2A2A'],borderWidth:0}]},options:{cutout:'75%',plugins:{legend:{display:false}}}}&w=150&h=150&bg=transparent
```

### Sparkline — Mini Inline Trend
```
https://quickchart.io/chart?c={type:'line',data:{labels:['','','','',''],datasets:[{data:[65,70,68,74,78],borderColor:'#D4A853',borderWidth:2,pointRadius:0,fill:false}]},options:{plugins:{legend:{display:false}},scales:{x:{display:false},y:{display:false}}}}&w=80&h=30&bg=transparent
```

**Key parameters:**
- `bg=transparent` — Critical for dark mode compatibility
- `w`/`h` — Width/height in pixels (match your email layout)
- `f=png` — Format (default). Use `f=svg` for vector (limited email support)

---

## Brand Config Structure

```json
{
  "name": "geo-presence",
  "display_name": "GEO Présence",
  "agency_tagline": "by {agency_name}",
  "colors": {
    "primary": "#D4A853",
    "secondary": "#8B7330",
    "bg": "#1A1A1A",
    "surface": "#2A2A2A",
    "text": "#F5F0E8",
    "text_muted": "#A89F8F",
    "border": "#3A3A3A",
    "up": "#4CAF50",
    "down": "#E53935"
  },
  "dark_mode": {
    "bg": "#121212",
    "surface": "#1E1E1E",
    "text": "#E8E0D0",
    "text_muted": "#999080"
  },
  "fonts": {
    "heading": "Georgia, 'Times New Roman', serif",
    "body": "'Segoe UI', Tahoma, sans-serif"
  },
  "logo": {
    "url": "https://storage.example.com/logo-dark.png",
    "width": 160,
    "height": 40,
    "alt": "GEO Présence"
  },
  "quickchart_theme": {
    "primary": "#D4A853",
    "bg": "transparent",
    "grid": "rgba(255,255,255,0.1)"
  },
  "delivery": {
    "inbox_id": "geo.presence@agentmail.to",
    "from_name": "GEO Présence",
    "cc": ["guillaume@moiria.com"]
  }
}
```

---

## Email Constraints (2026 Reality)

| Constraint | Rule |
|------------|------|
| **CSS** | Inline only (`style="..."`). `<style>` blocks stripped by Gmail. Use `<mj-style data-embed="only">` for dark mode media queries. |
| **Layout** | Table-based (`<table><tr><td>`). No flexbox, no grid, no `position:absolute`. Outlook desktop uses Word rendering engine. |
| **JavaScript** | Zero. No `<script>`, no `onclick`, no event handlers. |
| **Max width** | 600px body width. Email clients don't scale well beyond this. |
| **Images** | Always `alt`, `width`, `height`. External images may be blocked by default. |
| **Web fonts** | Many clients fall back to system fonts. Use Georgia + Segoe UI as safe defaults. |
| **Dark mode** | Use `@media (prefers-color-scheme: dark)` with `data-embed` block. Test in Gmail, Apple Mail, Outlook. |
| **Max size** | ~35KB for AgentMail. Keep HTML lean — minify MJML output. |
| **Charts** | PNG images via URL. No JS charts. QuickChart.io is free and self-hostable. |
| **Attachments** | Via `url` (public link) or `content` (base64). Inline images use `contentId` + `<img src="cid:...">`. |

**Reference:** [CanIEmail.com](https://www.caniemail.com/) — CSS/HTML feature support matrix.

---

## Workflow — Weekly Flash Report

1. **Read brand config** → `brands/geo-presence.json`
2. **Prepare data JSON** → KPIs, table data, chart data
3. **Run compile script** → `node scripts/compile.mjs --brand geo-presence --data data.json --out output`
4. **Review QA output** → Fix any warnings
5. **Send** → `mcporter call agentmail.send_message html:"..." text:"..."`
6. **Log** → Record in `memory/comm_tracker.md` with thread_id

---

## Workflow — Monthly Full Report

Same as weekly, but with additional sections:
- Executive summary (article-card with narrative)
- Full matrix table (all 16 queries × 4 models)
- Competitor radar (radar chart via QuickChart)
- Recommendations (2-3 article cards)
- CTA button (section-divider + CTA)

**Structure order:**
1. Header
2. Executive summary
3. KPI row (4 cards)
4. Trend chart
5. Top queries table (top 5)
6. Full matrix (link to online version)
7. Competitor radar chart
8. Recommendations
9. CTA → "Voir le rapport complet en ligne"
10. Footer

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| "mjml package not installed" | `npm install mjml` not run | Run `npm install mjml` in skill directory |
| "Brand config not found" | Wrong brand name or missing file | Check `brands/` directory, use `_template.json` as base |
| HTML renders as raw code in email | Used `text:` instead of `html:` | Move HTML to `html:` parameter, plain text to `text:` |
| Dark mode breaks chart visibility | Chart has white bg | Use `bg=transparent` in QuickChart URL |
| Table rows don't alternate | Missing `bg` field on row objects | Add `"bg": "#2A2A2A"` to each row in data JSON |
| Email exceeds 35KB | Too many charts or verbose HTML | Minify HTML output, reduce chart sizes, use sparklines |
| QuickChart returns 404 | URL malformed or service down | URL-encode chart config, or use POST to QuickChart API |
| "Unknown tool" on agentmail.send_message | MCP server not registered | Check `mcporter list` — agentmail must be active |

---

## References

- [MJML Documentation](https://documentation.mjml.io/)
- [QuickChart.io](https://quickchart.io/)
- [CanIEmail.com](https://www.caniemail.com/)
- [AgentMail API Reference](https://docs.agentmail.to/api-reference)
- `references/quickchart-patterns.md` — More chart URL patterns
- `references/email-client-compat.md` — 2026 compatibility matrix
- `examples/weekly-flash.json` — Sample input data
- `examples/weekly-flash.html` — Expected compiled output
