import { PDFDocument } from "pdf-lib";

export async function mergePdfs({ pdfs, filename }) {
  if (!pdfs || pdfs.length === 0) {
    throw new Error("No PDFs provided");
  }

  const mergedPdf = await PDFDocument.create();

  for (const base64 of pdfs) {
    const pdfBytes = Uint8Array.from(Buffer.from(base64, "base64"));
    const pdf = await PDFDocument.load(pdfBytes);
    const copiedPages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
    copiedPages.forEach((page) => mergedPdf.addPage(page));
  }

  const mergedBytes = await mergedPdf.save();
  const base64 = Buffer.from(mergedBytes).toString("base64");

  return {
    success: true,
    filename,
    size_bytes: mergedBytes.length,
    pages: mergedPdf.getPageCount(),
    base64,
  };
}
