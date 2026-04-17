"""PDF to Image Renderer for Vision Models.

This module provides PDF→image conversion for vision-capable LLMs.
Used when users upload PDFs that should be analyzed visually (not just text extraction).
"""

import base64
from io import BytesIO
from typing import Optional

import fitz  # PyMuPDF
from loguru import logger


async def pdf_to_base64_image(
    pdf_bytes: bytes,
    page: int = 0,
    zoom: float = 2.0
) -> Optional[str]:
    """Convert PDF page to base64 PNG image.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        page: Page number (0-indexed)
        zoom: Zoom factor (1.0 = 72 DPI, 2.0 = 144 DPI, etc.)
    
    Returns:
        Base64 data URL: "data:image/png;base64,..."
        None if conversion fails
    """
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Check if page exists
        if page >= len(doc):
            logger.warning(f"PDF page {page} not found (total: {len(doc)})")
            return None
        
        # Render page to pixmap
        page_obj = doc[page]
        matrix = fitz.Matrix(zoom, zoom)  # Zoom for better quality
        pix = page_obj.get_pixmap(matrix=matrix)
        
        # Convert to PNG bytes
        img_bytes = pix.tobytes("png")
        
        # Encode to base64
        base64_img = base64.b64encode(img_bytes).decode('ascii')
        
        # Clean up
        pix = None
        doc.close()
        
        # Return data URL
        return f"data:image/png;base64,{base64_img}"
        
    except Exception as e:
        logger.error(f"PDF→image conversion failed: {e}")
        return None


async def pdf_to_base64_images(
    pdf_bytes: bytes,
    pages: Optional[list[int]] = None,
    zoom: float = 2.0
) -> list[str]:
    """Convert multiple PDF pages to base64 PNG images.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        pages: List of page numbers (0-indexed). None = all pages.
        zoom: Zoom factor
    
    Returns:
        List of base64 data URLs
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        
        if pages is None:
            pages = list(range(total_pages))
        
        results = []
        for page_num in pages:
            if page_num >= total_pages:
                logger.warning(f"Skipping page {page_num} (total: {total_pages})")
                continue
            
            result = await pdf_to_base64_image(pdf_bytes, page_num, zoom)
            if result:
                results.append(result)
        
        doc.close()
        return results
        
    except Exception as e:
        logger.error(f"PDF→images conversion failed: {e}")
        return []


async def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """Get number of pages in PDF."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        count = len(doc)
        doc.close()
        return count
    except Exception as e:
        logger.error(f"Failed to get PDF page count: {e}")
        return 0


async def pdf_has_images(pdf_bytes: bytes) -> bool:
    """Check if PDF contains images (vs text-only)."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for page_num in range(min(len(doc), 3)):  # Check first 3 pages
            page = doc[page_num]
            images = page.get_images()
            if images:
                doc.close()
                return True
        
        doc.close()
        return False
        
    except Exception as e:
        logger.error(f"Failed to check PDF for images: {e}")
        return False
