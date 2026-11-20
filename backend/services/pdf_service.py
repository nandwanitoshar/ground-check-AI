import os
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF

class PDFService:
    @staticmethod
    def extract_text_and_metadata(pdf_path: str) -> Dict[str, Any]:
        """
        Extract text page-by-page and document metadata using PyMuPDF.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found at {pdf_path}")

        doc = fitz.open(pdf_path)
        pages = []
        full_text_list = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            text = page.get_text("text").strip()
            
            # Extract basic text blocks
            blocks = page.get_text("blocks")
            clean_blocks = []
            for b in blocks:
                # b = (x0, y0, x1, y1, text, block_no, block_type)
                if len(b) >= 5 and b[4].strip():
                    clean_blocks.append({
                        "bbox": [round(coord, 2) for coord in b[:4]],
                        "text": b[4].strip()
                    })

            pages.append({
                "page_number": page_num,
                "text": text,
                "block_count": len(clean_blocks),
                "blocks": clean_blocks
            })
            if text:
                full_text_list.append(f"--- PAGE {page_num} ---\n{text}")

        metadata = doc.metadata or {}
        page_count = len(doc)
        doc.close()

        return {
            "page_count": page_count,
            "metadata": metadata,
            "pages": pages,
            "full_text": "\n\n".join(full_text_list)
        }

