#!/usr/bin/env node
/**
 * Newsletter Email Compiler
 *
 * Usage:
 *   node compile.mjs --brand geo-presence --data weekly-flash.json --out output
 *
 * Pipeline:
 *   1. Load brand config from brands/<brand>.json
 *   2. Load data JSON
 *   3. Transform data (direction → delta_color/icon, bg → bg_color, etc.)
 *   4. Render Mustache templates → MJML
 *   5. Compile MJML → HTML
 *   6. Generate text fallback
 *   7. Run QA checks
 *   8. Write output.html + output.txt
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const skillDir = join(__dirname, '..');

// ─── Args ────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const getArg = (name) => {
  const i = args.indexOf(`--${name}`);
  return i !== -1 ? args[i + 1] : null;
};

const brandName = getArg('brand') || 'geo-presence';
const dataFile = getArg('data');
const outPrefix = getArg('out') || 'output';

if (!dataFile) {
  console.error('Usage: node compile.mjs --brand <name> --data <json> [--out <prefix>]');
  process.exit(1);
}

// ─── Mustache (simple implementation — no external dependency) ───────
function renderMustache(template, data) {
  return template.replace(/\{\{#(\w+)\}\}([\s\S]*?)\{\{\/\1\}\}\}|\{\{\{\s*(\w+(?:\.\w+)*)\s*\}\}\}|\{\{\s*(\w+(?:\.\w+)*)\s*\}\}/g,
    (match, loopName, loopContent, rawKey, key) => {
      if (loopName) {
        const arr = resolvePath(data, loopName);
        if (!Array.isArray(arr)) return '';
        // For each item, merge with parent data so nested vars like {{fonts.body}} still work
        return arr.map(item => {
          const merged = { ...data, ...item };
          return renderMustache(loopContent, merged);
        }).join('');
      }
      const val = resolvePath(data, rawKey || key);
      return val !== undefined && val !== null ? String(val) : '';
    }
  );
}

function resolvePath(obj, path) {
  return path.split('.').reduce((o, k) => o?.[k], obj);
}

// ─── Data Transformation ─────────────────────────────────────────────
function transformData(data, brand) {
  const c = brand.colors;
  const f = brand.fonts;

  // Transform KPIs: direction → delta_color, delta_icon
  if (data.kpis) {
    data.kpis = data.kpis.map(kpi => ({
      ...kpi,
      color: c.surface,
      text_color: c.text,
      text_color_muted: c.text_muted,
      delta_color: kpi.direction === 'up' ? c.up : kpi.direction === 'down' ? c.down : c.text_muted,
      delta_icon: kpi.direction === 'up' ? '↑' : kpi.direction === 'down' ? '↓' : '→',
    }));
  }

  // Transform table rows: bg → bg_color
  if (data.table?.rows) {
    data.table.rows = data.table.rows.map(row => ({
      ...row,
      cells: (row.cells || []).map(cell => String(cell)),
      bg_color: row.bg || row.bg_color || c.bg,
      color: c.text,
    }));
  }

  // Merge brand into data for flat Mustache access
  data.colors = c;
  data.dark_mode = brand.dark_mode;
  data.fonts = f;
  data.display_name = brand.display_name;
  data.agency_tagline = brand.agency_tagline;
  data.footer_note = data.footer_note || 'Rapport généré automatiquement';
  data.logo = brand.logo;

  return data;
}

// ─── Load Files ──────────────────────────────────────────────────────
function loadJSON(path) {
  return JSON.parse(readFileSync(path, 'utf-8'));
}

function loadTemplate(name) {
  const path = join(skillDir, 'templates', name);
  if (!existsSync(path)) return null;
  return readFileSync(path, 'utf-8');
}

function loadSection(name) {
  return loadTemplate(join('sections', name));
}

// ─── Assemble MJML ───────────────────────────────────────────────────
function assembleMJML(brand, data) {
  let base = loadTemplate('base.mjml');
  if (!base) {
    console.error('ERROR: templates/base.mjml not found');
    process.exit(1);
  }

  // Render Mustache on base (which includes inline sections)
  // For sections that use loops (kpis, rows), they're already in the templates
  // Render all section templates first, then inject into base
  const kpiTemplate = loadSection('kpi-row.mjml');
  const tableTemplate = loadSection('data-table.mjml');
  const chartTemplate = loadSection('chart.mjml');
  const articleTemplate = loadSection('article-card.mjml');
  const dividerTemplate = loadSection('section-divider.mjml');

  // Render each section with data
  let sections = '';
  if (kpiTemplate && data.kpis) sections += renderMustache(kpiTemplate, data);
  if (dividerTemplate) sections += renderMustache(dividerTemplate, data);
  if (tableTemplate && data.table) {
    data.section_title = data.table.title || 'Données';
    sections += renderMustache(tableTemplate, data);
  }
  if (chartTemplate && data.charts?.trend) {
    data.chart_title = data.charts.trend.title || 'Tendance';
    data.chart_url = data.charts.trend.url;
    data.width = data.charts.trend.width || 500;
    data.height = data.charts.trend.height || 250;
    data.chart_alt = data.chart_title;
    sections += renderMustache(chartTemplate, data);
  }
  if (articleTemplate && data.articles) {
    for (const article of data.articles) {
      const rendered = renderMustache(articleTemplate, { ...data, card_title: article.title, card_body: article.body });
      sections += rendered;
    }
  }

  // Replace {{#sections}}...{{/sections}} block with rendered sections
  base = base.replace(/\{\{#sections\}\}\s*\{\{\{content\}\}\}\s*\{\{\/sections\}\}/, sections);

  // Render final MJML
  return renderMustache(base, data);
}

// ─── Compile MJML → HTML ─────────────────────────────────────────────
async function compileMJML(mjml) {
  try {
    const { default: mjml2html } = await import('mjml');
    const { html, errors } = mjml2html(mjml, { minify: true, beautify: false });
    if (errors.length > 0) {
      console.warn('MJML warnings:', errors.map(e => e.formattedMessage).join('\n'));
    }
    return html;
  } catch (e) {
    if (e.code === 'ERR_MODULE_NOT_FOUND' || e.message.includes('mjml')) {
      console.error('ERROR: mjml package not installed. Run: npm install mjml');
      process.exit(1);
    }
    throw e;
  }
}

// ─── Generate Text Fallback ──────────────────────────────────────────
function generateTextFallback(data) {
  let text = `${data.report_title}\n${data.period}\n${'='.repeat(40)}\n\n`;

  // KPIs
  if (data.kpis) {
    for (const kpi of data.kpis) {
      text += `${kpi.label}: ${kpi.value} ${kpi.delta || ''}\n`;
    }
    text += '\n';
  }

  // Table
  if (data.table) {
    text += `${data.table.title || 'Données'}\n${'-'.repeat(30)}\n`;
    text += data.table.headers.join(' | ') + '\n';
    text += data.table.headers.map(() => '-'.repeat(10)).join('-+-') + '\n';
    for (const row of data.table.rows) {
      text += (row.cells || []).join(' | ') + '\n';
    }
    text += '\n';
  }

  // Articles
  if (data.articles) {
    for (const article of data.articles) {
      text += `${article.title}\n${article.body}\n\n`;
    }
  }

  text += `\n${data.display_name} ${data.agency_tagline}\n`;
  text += data.footer_note;

  return text;
}

// ─── QA Checks ───────────────────────────────────────────────────────
function runQA(html, text, data) {
  const issues = [];

  // 1. DOCTYPE
  if (!html.startsWith('<!DOCTYPE html>') && !html.startsWith('<!doctype html>')) {
    issues.push('⚠️ HTML does not start with <!DOCTYPE html>');
  }

  // 2. No custom <style> blocks check (MJML generates its own for responsive - that's OK)

  // 3. No flexbox/grid/absolute
  if (/display:\s*(flex|grid)/i.test(html)) {
    issues.push('⚠️ Found flexbox or grid in compiled HTML');
  }
  if (/position:\s*absolute/i.test(html)) {
    issues.push('⚠️ Found position:absolute in compiled HTML');
  }

  // 4. All images have alt/width/height
  const imgTags = html.match(/<img[^>]*>/g) || [];
  for (const img of imgTags) {
    if (!img.includes('alt=')) issues.push('⚠️ Image missing alt attribute');
    if (!img.includes('width=')) issues.push('⚠️ Image missing width attribute');
    if (!img.includes('height=')) issues.push('⚠️ Image missing height attribute');
  }

  // 5. Subject line present
  if (!data.subject || data.subject.length < 10) {
    issues.push('⚠️ Subject line missing or too short');
  }

  // 6. Size check
  const sizeKB = Math.round(html.length / 1024);
  if (sizeKB > 35) {
    issues.push(`❌ HTML size ${sizeKB}KB exceeds 35KB limit`);
  } else {
    console.log(`   📏 HTML size: ${sizeKB}KB`);
  }

  return issues;
}

// ─── Main ────────────────────────────────────────────────────────────
async function main() {
  console.log(`📧 Newsletter Compiler — Brand: ${brandName}`);

  // Load brand
  const brandPath = join(skillDir, 'brands', `${brandName}.json`);
  if (!existsSync(brandPath)) {
    console.error(`ERROR: Brand config not found: ${brandPath}`);
    process.exit(1);
  }
  const brand = loadJSON(brandPath);
  console.log(`   ✅ Brand: ${brand.display_name}`);

  // Load data
  const data = loadJSON(dataFile);
  console.log(`   ✅ Data: ${dataFile}`);

  // Transform
  const transformed = transformData(data, brand);
  console.log(`   ✅ Data transformed (${transformed.kpis?.length || 0} KPIs, ${transformed.table?.rows?.length || 0} table rows)`);

  // Assemble MJML
  const mjml = assembleMJML(brand, transformed);
  console.log(`   ✅ MJML assembled (${Math.round(mjml.length / 1024)}KB)`);

  // Compile
  const html = await compileMJML(mjml);
  console.log(`   ✅ HTML compiled (${Math.round(html.length / 1024)}KB)`);

  // Text fallback
  const text = generateTextFallback(transformed);
  console.log(`   ✅ Text fallback generated (${Math.round(text.length / 1024)}KB)`);

  // QA
  console.log('\n🔍 QA Checks:');
  const issues = runQA(html, text, transformed);
  if (issues.length === 0) {
    console.log('   ✅ All checks passed');
  } else {
    for (const issue of issues) {
      console.log(`   ${issue}`);
    }
  }

  // Write output
  mkdirSync(dirname(outPrefix), { recursive: true });
  writeFileSync(`${outPrefix}.html`, html);
  writeFileSync(`${outPrefix}.txt`, text);
  console.log(`\n📁 Output: ${outPrefix}.html + ${outPrefix}.txt`);
}

main().catch(e => {
  console.error('FATAL:', e.message);
  process.exit(1);
});
