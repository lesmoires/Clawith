import puppeteer from "puppeteer";
import { PDFDocument } from "pdf-lib";
import { writeFileSync, mkdirSync } from "fs";

const DEFAULT_BRAND_COLORS = {
  background: "#1A1A1A",
  text: "#F5F0E8",
  primary: "#D4A853",
  secondary: "#A0A0A0",
};

const PRINT_CSS = `
  @page { margin: __MARGIN_MM__mm; }
  html {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
  }
  body {
    background: __BACKGROUND__ !important;
    color: __TEXT__ !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }
  h1, h2, h3 { color: __PRIMARY__ !important; }
  table, .kpi-card, .chart-container, .card, .section {
    page-break-inside: avoid;
  }
  h1, h2, h3, h4 { page-break-after: avoid; }
  img { max-width: 100%; height: auto; }
`;

export async function generatePdf({ html, brand_colors = {}, format, margin_mm, landscape, filename, save_path, return_base64 = true }) {
  const colors = { ...DEFAULT_BRAND_COLORS, ...brand_colors };

  // Inject CSS with brand colors
  const css = PRINT_CSS
    .replace("__MARGIN_MM__", margin_mm)
    .replace("__BACKGROUND__", colors.background)
    .replace("__TEXT__", colors.text)
    .replace("__PRIMARY__", colors.primary);

  // Inject CSS into HTML
  const injectedHtml = html.replace(
    "</head>",
    `<style>${css}</style></head>`
  );

  const browser = await puppeteer.launch({
    executablePath: "/usr/bin/chromium",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--single-process",
      "--no-zygote",
    ],
    headless: "new",
  });

  try {
    const page = await browser.newPage();

    await page.emulateMediaType("screen");

    await page.setContent(injectedHtml, {
      waitUntil: "networkidle0",
      timeout: 30000,
    });

    const pdfBuffer = await page.pdf({
      format,
      printBackground: true,
      landscape,
      margin: {
        top: `${margin_mm}mm`,
        right: `${margin_mm}mm`,
        bottom: `${margin_mm}mm`,
        left: `${margin_mm}mm`,
      },
    });

    // Count pages from the generated PDF
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPageCount();

    let saved_path = null;
    if (save_path) {
      const dir = save_path.substring(0, save_path.lastIndexOf("/"));
      if (dir) {
        mkdirSync(dir, { recursive: true });
      }
      writeFileSync(save_path, pdfBuffer);
      saved_path = save_path;
    }

    const base64 = return_base64 !== false ? pdfBuffer.toString("base64") : null;

    return {
      success: true,
      filename,
      size_bytes: pdfBuffer.length,
      pages,
      base64,
      saved_path,
    };
  } finally {
    await browser.close();
  }
}
