import os
import pymupdf  # PyMuPDF
from typing import Dict, Any, List, Optional
from backend.app.models.audit import PageContent

class PDFProcessingError(Exception):
    """Custom exception raised when PDF parsing fails."""
    pass

class PDFService:
    @staticmethod
    def extract_text(pdf_path: str) -> Dict[str, Any]:
        """
        Extract page-level text and metadata from PDF using PyMuPDF.
        Preserves page boundaries and extracts word counts per page.
        """
        if not os.path.exists(pdf_path):
            raise PDFProcessingError(f"PDF file does not exist: {pdf_path}")

        file_size = os.path.getsize(pdf_path)
        if file_size == 0:
            raise PDFProcessingError("Uploaded file is empty (0 bytes).")

        doc = None
        try:
            doc = pymupdf.open(pdf_path)
        except Exception as e:
            raise PDFProcessingError(f"Invalid or corrupted PDF file: {str(e)}")

        try:
            page_count = len(doc)
            if page_count == 0:
                raise PDFProcessingError("PDF contains 0 pages.")

            # Document metadata
            metadata = doc.metadata or {}
            title = metadata.get("title") or None
            if title and not title.strip():
                title = None

            pages: List[PageContent] = []

            for page_index in range(page_count):
                page = doc[page_index]
                page_num = page_index + 1
                text = page.get_text("text").strip()
                word_count = len(text.split()) if text else 0

                pages.append(PageContent(
                    page_number=page_num,
                    text=text,
                    word_count=word_count
                ))

            return {
                "page_count": page_count,
                "title": title,
                "pages": pages,
                "metadata": metadata
            }

        except PDFProcessingError:
            raise
        except Exception as e:
            raise PDFProcessingError(f"Failed to extract text from PDF: {str(e)}")
        finally:
            if doc:
                doc.close()
