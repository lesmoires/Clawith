# 👁️ Vision Capabilities in Clawith

**Version:** 1.0  
**Date:** 2026-03-31  
**Status:** ✅ Production Ready

---

## 🎯 Overview

Clawith supports vision-capable LLMs that can analyze images and PDFs visually.

**Key Features:**
- ✅ Image analysis (PNG, JPEG, WebP)
- ✅ PDF visual analysis (auto-converts to images)
- ✅ Multi-page PDF support
- ✅ Base64 image embedding
- ✅ Automatic PDF→image conversion for vision models

---

## 📋 Supported Models

| Model | Provider | Vision Support | Status |
|-------|----------|----------------|--------|
| qwen3.5-plus | Alibaba/Qwen | ✅ YES | Active |
| qwen-vl-max | Alibaba/Qwen | ✅ YES | Available |
| gpt-4-vision | OpenAI | ✅ YES | Available |
| glm-5-turbo | Zhipu | ❌ NO | Active |

**Check in DB:**
```sql
SELECT name, model, supports_vision 
FROM llm_models 
WHERE enabled = true;
```

---

## 🛠️ Architecture

### PDF Auto-Conversion Flow

```
User uploads PDF
       ↓
WebSocket receives file
       ↓
Check: supports_vision = true?
       ↓ YES
Convert PDF page 0 → PNG (2x zoom)
       ↓
Inject as [image_data:data:image/png;base64,...]
       ↓
Send to LLM with vision support
       ↓
LLM analyzes image visually
```

### Code Locations

| Component | File | Purpose |
|-----------|------|---------|
| PDF Renderer | `app/services/pdf_renderer.py` | PDF→image conversion |
| Vision Tools | `app/tools/vision_tools.py` | analyze_image, analyze_pdf |
| WebSocket | `app/api/websocket.py` | Auto PDF detection |
| DB Schema | `llm_models.supports_vision` | Model capability flag |

---

## 🧪 Usage

### For End Users

**Upload an image or PDF in Clawith UI:**

1. Select agent with vision-capable model (e.g., qwen3.5-plus)
2. Upload file (PNG, JPEG, WebP, or PDF)
3. Ask: "Describe what you see" or "Analyze this document"

**Example:**
```
[Uploads resume.pdf]

User: "Describe the layout and formatting of this resume"

Agent: "This resume has a clean two-column layout. The left column 
contains contact information and skills in a dark blue sidebar. The 
right column has work experience with company logos. The header has 
the candidate's name in large bold text..."
```

### For Developers

**Using vision tools:**

```python
# Tool call
{
  "tool": "analyze_pdf",
  "arguments": {
    "file_path": "/path/to/document.pdf",
    "page": 0,
    "focus": "layout and signatures"
  }
}
```

**Checking if model supports vision:**

```python
from app.models.llm import LLMModel

model = await get_model(agent_id)
if getattr(model, 'supports_vision', False):
    # Can send images
    content += f"\n[image_data:{base64_image}]"
```

---

## 🔧 Configuration

### Enable Vision for a Model

```sql
UPDATE llm_models 
SET supports_vision = true 
WHERE model = 'qwen3.5-plus';
```

### PDF Rendering Settings

**File:** `app/services/pdf_renderer.py`

```python
# Default zoom: 2.0 (144 DPI)
zoom = 2.0

# Higher = better quality, more tokens
# Lower = faster, less tokens
```

---

## 📊 Performance

| Operation | Time | Token Usage |
|-----------|------|-------------|
| PDF→image (1 page) | ~100ms | ~2000 tokens (base64) |
| Image analysis | ~2-5s | ~500 tokens (response) |
| Multi-page PDF | ~100ms × pages | ~2000 tokens × pages |

**Recommendation:** For multi-page PDFs, analyze first page only unless user specifies.

---

## ⚠️ Limitations

1. **PDF Size:** Large PDFs (>10MB) may timeout
2. **Token Limit:** Base64 images consume ~2000 tokens per page
3. **Model Support:** Only vision-capable models can analyze images
4. **Text Quality:** OCR not included — use `read_pdf` for text extraction

---

## 🎯 Best Practices

### ✅ DO:
- Use vision for scanned documents, forms, handwritten notes
- Convert PDFs to images when visual layout matters
- Specify focus: "Analyze the signatures" or "Describe the layout"
- Use first page only for multi-page documents

### ❌ AVOID:
- Uploading 50-page PDFs for visual analysis (use text extraction)
- Expecting OCR from vision models (use `read_pdf` for text)
- Using vision models for text-only PDFs (wastes tokens)

---

## 🧪 Testing

### Test 1: Image Upload
```bash
# Upload candidate_photo.png to Moneva Daily
# Ask: "Describe this person's appearance"
# Expected: Detailed visual description ✅
```

### Test 2: PDF Visual Analysis
```bash
# Upload resume.pdf to Moneva Daily
# Ask: "What does this resume look like visually?"
# Expected: Description of layout, formatting, design ✅
```

### Test 3: Vision Model Detection
```sql
SELECT name, supports_vision 
FROM llm_models 
WHERE name ILIKE '%qwen%';
-- Expected: qwen3.5-plus = true ✅
```

---

## 📚 Related Documentation

- `docs/MCP_GUIDE.md` — MCP server configuration
- `docs/AGENT_TOOLS.md` — Tool system overview
- `docs/LLM_MODELS.md` — Model configuration

---

## 🚀 Future Enhancements

- [ ] OCR integration for text extraction from images
- [ ] Multi-page PDF summary (analyze all pages, summarize)
- [ ] Image comparison tool (compare two images)
- [ ] Chart/graph analysis (extract data from visualizations)

---

**Last Updated:** 2026-03-31  
**Author:** Clawith Repair + Clawith Maintainer
