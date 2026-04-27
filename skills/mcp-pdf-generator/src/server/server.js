import express from "express";
import { randomUUID } from "crypto";
import { generatePdf } from "../tools/generate_pdf.js";
import { mergePdfs } from "../tools/merge_pdfs.js";

const app = express();
app.use(express.json({ limit: "10mb" }));

let sessionId = null;

function headers() {
  return sessionId ? { "Mcp-Session-Id": sessionId } : {};
}

function jsonResponse(res, body) {
  res.set(headers());
  res.json(body);
}

app.post("/mcp", async (req, res) => {
  if (!sessionId) sessionId = randomUUID();

  const raw = req.body;
  const method = raw.method;
  const params = raw.params || {};
  const rid = raw.id;

  if (rid === undefined || rid === null) {
    res.set(headers());
    res.status(200).end();
    return;
  }

  if (method === "initialize") {
    return jsonResponse(res, {
      jsonrpc: "2.0",
      id: rid,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: "mcp-pdf-generator", version: "1.0.0" },
      },
    });
  }

  if (method === "tools/list") {
    return jsonResponse(res, {
      jsonrpc: "2.0",
      id: rid,
      result: {
        tools: [
          {
            name: "generate_pdf",
            description: "Convert HTML content to a formatted PDF document with optional brand colors",
            inputSchema: {
              type: "object",
              properties: {
                html: { type: "string", description: "Full HTML content to convert" },
                brand_colors: {
                  type: "object",
                  description: "Brand color overrides",
                  properties: {
                    background: { type: "string" },
                    text: { type: "string" },
                    primary: { type: "string" },
                    secondary: { type: "string" },
                  },
                },
                format: { type: "string", enum: ["A4", "Letter", "Legal"], default: "A4" },
                margin_mm: { type: "number", default: 15 },
                landscape: { type: "boolean", default: false },
                filename: { type: "string", default: "document.pdf" },
                save_path: { type: "string", description: "Filesystem path to save the PDF directly (bypasses base64 truncation). E.g., /data/shared/test-geo.pdf" },
                return_base64: { type: "boolean", default: true, description: "Include base64 in response. Set false when using save_path to avoid large responses." },
              },
              required: ["html"],
            },
          },
          {
            name: "merge_pdfs",
            description: "Combine multiple base64-encoded PDFs into a single document",
            inputSchema: {
              type: "object",
              properties: {
                pdfs: { type: "array", items: { type: "string" }, description: "Array of base64-encoded PDF strings" },
                filename: { type: "string", default: "merged.pdf" },
              },
              required: ["pdfs"],
            },
          },
        ],
      },
    });
  }

  if (method === "tools/call") {
    const name = params.name;
    const args = params.arguments || {};
    try {
      let result;
      if (name === "generate_pdf") {
        result = await generatePdf({
          html: args.html,
          brand_colors: args.brand_colors,
          format: args.format || "A4",
          margin_mm: args.margin_mm || 15,
          landscape: args.landscape || false,
          filename: args.filename || "document.pdf",
          save_path: args.save_path,
          return_base64: args.return_base64,
        });
      } else if (name === "merge_pdfs") {
        result = await mergePdfs({
          pdfs: args.pdfs,
          filename: args.filename || "merged.pdf",
        });
      } else {
        result = { success: false, error: `Unknown tool: ${name}` };
      }
      return jsonResponse(res, {
        jsonrpc: "2.0",
        id: rid,
        result: { content: [{ type: "text", text: JSON.stringify(result) }] },
      });
    } catch (err) {
      return jsonResponse(res, {
        jsonrpc: "2.0",
        id: rid,
        result: { content: [{ type: "text", text: JSON.stringify({ success: false, error: err.message }) }], isError: true },
      });
    }
  }

  return jsonResponse(res, {
    jsonrpc: "2.0",
    id: rid,
    error: { code: -32601, message: `Method not found: ${method}` },
  });
});

app.get("/mcp", (req, res) => {
  res.status(405).json({ error: "Method not allowed" });
});

app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "mcp-pdf-generator" });
});

const PORT = process.env.PORT || 3100;
app.listen(PORT, () => {
  console.log(`MCP PDF Generator running on http://0.0.0.0:${PORT}/mcp`);
});
