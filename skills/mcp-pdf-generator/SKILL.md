---
name: mcp-pdf-generator
description: Generate PDFs from HTML via Puppeteer (headless Chromium) — A4, dark mode, brand-aware, merge support
category: pdf
icon: 📄
requires:
  env: []
---

# MCP PDF Generator

Generate PDFs from HTML using Puppeteer (headless Chromium). Available to all agents via the Clawith MCP tool system.

## Overview

This skill provides two tools for PDF generation and manipulation:

| Tool | Description |
|------|-------------|
| `generate_pdf` | Convert HTML content to a branded A4 PDF (supports direct save) |
| `merge_pdfs` | Combine multiple PDFs into a single document |

The PDF engine runs in a dedicated Docker container on moiria-claw with full Chromium rendering — identical to what you see in a browser.

## When to use this skill

- Convert an HTML report to a PDF attachment
- Generate a branded monthly report in PDF format
- Merge multiple PDF documents
- Create a PDF snapshot of a dashboard or data visualization
- Convert Markdown (rendered to HTML first) into a polished PDF

## Tools

### generate_pdf

Convert HTML content to a formatted PDF document.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `html` | string | ✅ | — | Full HTML content to convert |
| `brand_colors` | object | ❌ | See below | Brand color overrides |
| `format` | string | ❌ | `"A4"` | Page format: `"A4"`, `"Letter"`, `"Legal"` |
| `margin_mm` | number | ❌ | `15` | Margin size in millimeters |
| `landscape` | boolean | ❌ | `false` | Landscape orientation |
| `filename` | string | ❌ | `"document.pdf"` | Output filename |
| `save_path` | string | ❌ | — | **Direct filesystem save.** Bypasses base64 truncation. Use: `/agents/<agent_id>/workspace/output/<filename>.pdf` |
| `return_base64` | boolean | ❌ | `true` | Set `false` when using `save_path` to avoid large responses. |

**Default brand colors:**
```json
{
  "background": "#1A1A1A",
  "text": "#F5F0E8",
  "primary": "#D4A853"
}
```

**Returns:**
```json
{
  "success": true,
  "filename": "rapport-geo-2026-04.pdf",
  "size_bytes": 245000,
  "pages": 4,
  "base64": "JVBERi0xLjQKJcfs..."
}
```

**Example usage:**
```
Tool: generate_pdf
Arguments: {
  "html": "<html><body><h1>Rapport</h1><p>Contenu...</p></body></html>",
  "brand_colors": {
    "background": "#1A1A1A",
    "text": "#F5F0E8",
    "primary": "#D4A853"
  },
  "format": "A4",
  "margin_mm": 15,
  "filename": "rapport-geo-2026-04.pdf"
}
```

### merge_pdfs

Combine multiple base64-encoded PDFs into a single document.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pdfs` | string[] | ✅ | — | Array of base64-encoded PDF strings |
| `filename` | string | ❌ | `"merged.pdf"` | Output filename |

**Returns:**
```json
{
  "success": true,
  "filename": "merged.pdf",
  "size_bytes": 502000,
  "pages": 8,
  "base64": "JVBERi0xLjQKJcfs..."
}
```

## HTML requirements

For best results, your HTML should:

1. **Be complete** — include `<html>`, `<head>`, `<body>` tags
2. **Have inline or embedded CSS** — no external stylesheets (the PDF engine can't fetch them)
3. **Use `page-break-inside: avoid`** on tables, cards, and charts to prevent them from being split across pages
4. **Use `page-break-after: avoid`** on headings to keep them with their content
5. **Use `max-width: 100%`** on images to prevent overflow
6. **Include `@page` rules** if you need custom margins or page size

### Recommended CSS for dark mode PDFs:
```css
@page {
  size: A4;
  margin: 15mm;
}
html {
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
body {
  background: #1A1A1A;
  color: #F5F0E8;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
h1, h2, h3 {
  font-family: Georgia, 'Times New Roman', serif;
  color: #D4A853;
}
table, .kpi-card, .chart-container {
  page-break-inside: avoid;
}
```

## Common patterns

### Pattern 1: Newsletter with PDF attachment

The `newsletter-email` skill compiles MJML templates into HTML emails. When the compiled HTML exceeds 10KB, this skill generates a PDF attachment.

**Workflow:**
```
1. newsletter-email skill: compile.mjs processes data.json
   → outputs: newsletter.html, newsletter.txt, newsletter.meta.json

2. Agent reads .meta.json:
   → if meta.needs_pdf == true:
     a. Read the compiled HTML file
     b. Read brand config from brands/<brand>.json
     c. Call generate_pdf with HTML + brand_colors
     d. Receive PDF in base64

3. Agent sends via AgentMail:
   → Email body: summary HTML (≤10KB, excerpt from newsletter)
   → Attachment: PDF (complete report)
```

**MJML-to-PDF compatibility:**
- MJML compiles to **table-based HTML** — renders correctly in Puppeteer
- Dark mode uses `<mj-raw><style>` blocks — preserved via `print-color-adjust: exact`
- QuickChart images are external PNG URLs — load during `networkidle0` wait
- KPI cards (`mj-group`) → table cells → respect `page-break-inside: avoid`
- Tables may be wide — use `landscape: true` for benchmark tables (4 LLM × 16 queries)

### Pattern 2: Markdown report → PDF

```
1. Render Markdown to HTML (using a simple Markdown → HTML converter)
2. Call generate_pdf with the HTML
3. Save or send the PDF
```

### Pattern 3: Dashboard screenshot as PDF

```
1. Fetch the dashboard HTML or screenshot
2. Call generate_pdf with format="A4" and landscape=true for wide dashboards
3. Save the PDF
```

### Pattern 3.5: Direct save (recommended for agents)

When generating large PDFs, use `save_path` to write directly to the agent workspace:

```
Tool: generate_pdf
Arguments: {
  "html": "<html>...complete HTML...</html>",
  "brand_colors": { "background": "#1A1A1A", "text": "#F5F0E8", "primary": "#D4A853" },
  "filename": "rapport-geo-001.pdf",
  "save_path": "/agents/4be725d9-2673-4f5f-89ae-aa2d442c6322/workspace/output/rapport-geo-001.pdf",
  "return_base64": false
}
```

This returns a tiny response `{"success": true, "saved_path": "...", "pages": N, "size_bytes": N}` instead of a 50KB+ base64 string that gets truncated.

After saving, use `list_files` or `read_file` to verify the PDF is in the workspace.

### Pattern 4: Merge multiple reports

```
1. Generate individual PDFs via generate_pdf
2. Call merge_pdfs with the base64 PDFs array
3. Send the merged document
```

## Limitations

| Limitation | Value |
|---|---|
| Max HTML size | ~500KB |
| Max PDF output | ~10MB |
| Timeout | 30 seconds |
| Concurrent generations | 1 at a time per container |
| JavaScript in HTML | Not executed (static HTML only) |
| External resources | Not fetched (CSS/fonts must be embedded) |
| Fonts | System fonts only (Georgia, Segoe UI, Arial, etc.) |

## Troubleshooting

### PDF is blank or missing content
- Ensure your HTML is complete and valid
- Check that all CSS is embedded (no external stylesheets)
- Verify the HTML doesn't rely on JavaScript

### Colors are wrong
- Add `-webkit-print-color-adjust: exact !important;` to your CSS
- The PDF engine uses `screen` media type for dark mode
- Brand colors are injected automatically — check your `brand_colors` parameter

### Tables are split across pages
- Add `page-break-inside: avoid;` to your table CSS
- Add `page-break-after: avoid;` to headings

### PDF is too large
- Compress images before embedding (use base64 or external URLs)
- Reduce the number of pages
- Consider splitting into multiple PDFs

## References

- **Setup guide:** `references/setup-guide.md`
- **Puppeteer docs:** https://pptr.dev/
- **pdf-lib docs:** https://pdf-lib.js.org/
