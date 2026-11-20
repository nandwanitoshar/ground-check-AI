import os
import json
import re
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

from backend.app.models.audit import AuditDocument, PageContent
from backend.app.models.claim import (
    Claim,
    ClaimCategory,
    ClaimImportance,
    VerificationType,
    Extractability
)

# Load environment variables
load_dotenv()
backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
if os.path.exists(backend_env):
    load_dotenv(backend_env)

logger = logging.getLogger("gemini_service")

class GeminiConfigurationError(Exception):
    """Raised when the Gemini API key is missing or misconfigured."""
    pass

class GeminiExtractionError(Exception):
    """Raised when extraction from the Gemini API fails."""
    pass

class RawClaimItem(BaseModel):
    text: str
    page: int
    sourceText: str
    category: str
    importance: str
    verificationType: str
    extractability: str

class RawExtractionOutput(BaseModel):
    claims: List[RawClaimItem] = Field(default_factory=list)

class DocumentChunk(BaseModel):
    chunk_index: int
    start_page: int
    end_page: int
    pages_included: List[int]
    formatted_text: str

SYSTEM_EXTRACTION_PROMPT = """
You are GroundCheck AI's Environmental Document Claim Extraction Engine.

Your sole task is to analyze the provided pages from an Environmental Impact Assessment (EIA) / Environmental Report and extract ONLY specific, factual, independently checkable claims.

CRITICAL EXTRACTION CRITERIA:
Extract claims that assert verifiable facts, including:
1. Geographic locations, coordinates, parcels, and project boundaries.
2. Exact distances and separation buffers from water bodies, wetlands, protected areas, parks, forests, and residences.
3. Quantified land use and project footprint areas (e.g., hectares, acres).
4. Hydrological and water assertions (surface water, groundwater drawdown, aquifers, discharge rates).
5. Baseline ambient measurements (air quality metrics, PM10/PM2.5, noise decibels, emissions).
6. Biodiversity assertions (presence or absence of protected habitats, endangered flora/fauna species).
7. Infrastructure, waste treatment, and hazardous material management specifications.
8. Concrete regulatory compliance limits and statutory setback distances.

WHAT NOT TO EXTRACT (MANDATORY):
- Do NOT extract opinions, intentions, or interpretations (e.g., "The project is environmentally beneficial").
- Do NOT extract vague general statements (e.g., "The report discusses water resources").
- Do NOT extract section headings, tables of contents, or general background narratives.
- Do NOT invent facts or modify quoted numbers.

ATOMIC CLAIMS RULE:
Split compound sentences containing multiple distinct factual assertions into separate claims.
Example: "The project is 2 km from River X and 500 m from Village Y" MUST be split into:
- Claim 1: "The project is 2 km from River X."
- Claim 2: "The project is 500 m from Village Y."

PAGE & SOURCE TEXT ACCURACY:
- Each claim MUST cite the exact page number where it appears.
- The `sourceText` field MUST contain the exact or near-exact verbatim quotation from that page.
- Do not assign arbitrary page numbers.

CATEGORIES (Choose exactly one):
"water", "land", "air", "biodiversity", "waste", "infrastructure", "distance", "compliance", "environmental-impact", "other"

IMPORTANCE (Choose exactly one based on environmental/permitting significance):
"high" (major distance buffer, water body proximity, protected zone, air baseline violation, key setback)
"medium" (moderate significance numeric or infrastructure characteristic)
"low" (procedural or secondary factual observation)

VERIFICATION TYPE (Choose exactly one):
"geographic", "numeric", "documentary", "regulatory", "external-evidence", "mixed", "unknown"

EXTRACTABILITY (Choose exactly one):
"high" (clear quantitative or spatial fact with obvious verification pathway)
"medium" (potentially verifiable but requires composite records)
"low" (difficult to audit from open records)

OUTPUT FORMAT:
Return valid JSON ONLY matching this schema:
{
  "claims": [
    {
      "text": "Specific atomic claim text",
      "page": 17,
      "sourceText": "Exact quote from page text",
      "category": "distance",
      "importance": "high",
      "verificationType": "geographic",
      "extractability": "high"
    }
  ]
}
"""

class GeminiService:
    @staticmethod
    def _canonicalize_model_name(name: str) -> str:
        clean = (name or "").strip()
        if clean in ("3.8", "gemini-3.8"):
            return "gemini-3.8-flash"
        if clean in ("3.7", "gemini-3.7"):
            return "gemini-3.7-flash"
        if clean in ("3.6", "gemini-3.6"):
            return "gemini-3.6-flash"
        if clean in ("3.5", "gemini-3.5"):
            return "gemini-3.5-flash"
        if clean in ("3.1", "gemini-3.1"):
            return "gemini-3.1-flash-lite"
        return clean

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self._explicit_api_key = api_key
        raw_model = model_name or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.model_name = self._canonicalize_model_name(raw_model)
        self._client = None

    def _get_model_candidates(self) -> List[str]:
        primary = self._canonicalize_model_name(self.model_name)
        defaults = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"]
        candidates = [primary] if primary else []
        for d in defaults:
            if d not in candidates:
                candidates.append(d)
        return candidates

    @property
    def api_key(self) -> Optional[str]:
        if self._explicit_api_key is not None:
            return self._explicit_api_key
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    @api_key.setter
    def api_key(self, value: Optional[str]):
        self._explicit_api_key = value
        self._client = None

    def is_configured(self) -> bool:
        """Returns True if a non-empty Gemini API key is configured."""
        key = self.api_key
        return bool(key and key.strip())

    def test_connection(self) -> tuple[bool, str]:
        """
        Safely tests Gemini API connectivity without leaking secrets.
        Returns (success: bool, sanitized_reason: str).
        """
        if not self.is_configured():
            return False, "GEMINI_API_KEY is not configured."
        client = self._get_client()
        last_err = ""
        for model in self._get_model_candidates():
            try:
                res = client.models.generate_content(
                    model=model,
                    contents="ping"
                )
                self.model_name = model
                return True, f"Successfully authenticated with Gemini API (active model: {model})."
            except Exception as e:
                last_err = f"{type(e).__name__} - {str(e)[:120]}"
                logger.warning(f"Model {model} unavailable during connection test ({last_err}), attempting fallback...")
        return False, f"Gemini API request failed across candidates: {last_err}"

    def _get_client(self):
        """Initializes and returns the Google GenAI client."""
        if not self.is_configured():
            raise GeminiConfigurationError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file or environment variables."
            )
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                raise GeminiConfigurationError(f"Failed to initialize Google GenAI SDK: {str(e)}")
        return self._client

    def chunk_document(self, pages: List[PageContent], max_words_per_chunk: int = 1800) -> List[DocumentChunk]:
        """
        Group pages intelligently with explicit page boundary headers.
        Preserves page tracking for every page in the chunk.
        """
        chunks: List[DocumentChunk] = []
        current_chunk_pages: List[int] = []
        current_chunk_text_parts: List[str] = []
        current_word_count = 0
        chunk_idx = 1

        for p in pages:
            page_text = p.text.strip()
            word_count = p.word_count

            # If adding this page exceeds chunk size and we already have pages, flush chunk
            if current_word_count + word_count > max_words_per_chunk and current_chunk_pages:
                chunks.append(DocumentChunk(
                    chunk_index=chunk_idx,
                    start_page=current_chunk_pages[0],
                    end_page=current_chunk_pages[-1],
                    pages_included=list(current_chunk_pages),
                    formatted_text="\n\n".join(current_chunk_text_parts)
                ))
                chunk_idx += 1
                current_chunk_pages = []
                current_chunk_text_parts = []
                current_word_count = 0

            # Add page with explicit boundary
            page_header = f"--- PAGE {p.page_number} ---"
            current_chunk_pages.append(p.page_number)
            current_chunk_text_parts.append(f"{page_header}\n{page_text if page_text else '[Empty page]'}")
            current_word_count += word_count

        # Flush remaining pages
        if current_chunk_pages:
            chunks.append(DocumentChunk(
                chunk_index=chunk_idx,
                start_page=current_chunk_pages[0],
                end_page=current_chunk_pages[-1],
                pages_included=list(current_chunk_pages),
                formatted_text="\n\n".join(current_chunk_text_parts)
            ))

        return chunks

    def _normalize_string(self, s: str) -> str:
        """Helper to normalize whitespace and lowercase for reliable quote matching."""
        return re.sub(r'\s+', ' ', s or "").strip().lower()

    def _to_alphanumeric(self, s: str) -> str:
        """Helper to strip all non-alphanumeric characters for robust quotation verification."""
        return re.sub(r'[^a-zA-Z0-9]', '', s or "").lower()

    def _verify_source_text(
        self,
        source_text: str,
        reported_page: int,
        pages_dict: Dict[int, str]
    ) -> Tuple[bool, int]:
        """
        Verifies that sourceText actually occurs on the reported page.
        If not found on reported page, checks adjacent pages and then the entire document.
        Returns (is_verified, actual_page).
        """
        norm_source = self._normalize_string(source_text)
        alpha_source = self._to_alphanumeric(source_text)
        if not norm_source or len(alpha_source) < 8:
            return False, reported_page

        def is_match(src_norm: str, src_alpha: str, p_text: str) -> bool:
            p_norm = self._normalize_string(p_text)
            if src_norm in p_norm:
                return True
            p_alpha = self._to_alphanumeric(p_text)
            if src_alpha in p_alpha:
                return True
            # Substring match for longer quotes
            if len(src_alpha) > 30:
                if src_alpha[:25] in p_alpha or src_alpha[-25:] in p_alpha:
                    return True
            return False

        # 1. Check reported page
        page_text = pages_dict.get(reported_page, "")
        if is_match(norm_source, alpha_source, page_text):
            return True, reported_page

        # 2. Check adjacent pages (reported_page - 1, reported_page + 1, etc.)
        for offset in [-1, 1, -2, 2]:
            adj_page = reported_page + offset
            if adj_page in pages_dict:
                if is_match(norm_source, alpha_source, pages_dict[adj_page]):
                    return True, adj_page

        # 3. Check all other pages in document as fallback
        for page_num, text in pages_dict.items():
            if page_num != reported_page and is_match(norm_source, alpha_source, text):
                return True, page_num

        return False, reported_page

    def _clean_json_response(self, raw_text: str) -> str:
        """Strips markdown code fences and extracts JSON payload."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _call_gemini_with_retry(self, prompt: str) -> Dict[str, Any]:
        """Calls Gemini API and parses JSON with automatic candidate fallback on high-demand spikes."""
        client = self._get_client()
        candidates = self._get_model_candidates()
        last_error = "Extraction failed"

        for model in candidates:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config={
                            "response_mime_type": "application/json",
                            "temperature": 0.1,  # Low temperature for deterministic, factual extraction
                        }
                    )

                    if not response or not response.text:
                        raise GeminiExtractionError(f"Model {model} returned an empty response.")

                    raw_json = self._clean_json_response(response.text)
                    self.model_name = model
                    return json.loads(raw_json)

                except json.JSONDecodeError as je:
                    logger.warning(f"Model {model} returned invalid JSON (attempt {attempt + 1}/2): {je}")
                    last_error = f"Malformed JSON: {str(je)}"
                    if attempt == 1:
                        break
                except Exception as e:
                    if isinstance(e, GeminiConfigurationError):
                        raise
                    last_error = str(e)
                    logger.warning(f"Model {model} call error (attempt {attempt + 1}/2): {e}")
                    if attempt == 1:
                        break

        raise GeminiExtractionError(f"Gemini API communication failed across candidates: {last_error}")

    def extract_claims_from_chunk(
        self,
        chunk: DocumentChunk,
        audit_id: str,
        pages_dict: Dict[int, str]
    ) -> List[Claim]:
        """
        Sends a single chunk to Gemini, validates schema, verifies quotes, and standardizes claims.
        """
        prompt = (
            f"{SYSTEM_EXTRACTION_PROMPT}\n\n"
            f"=== DOCUMENT PAGES {chunk.start_page} TO {chunk.end_page} ===\n\n"
            f"{chunk.formatted_text}\n\n"
            f"Extract all factual claims from the above text. Return strictly valid JSON."
        )

        output_json = self._call_gemini_with_retry(prompt)

        # Validate with Pydantic
        try:
            parsed = RawExtractionOutput(**output_json)
        except ValidationError as ve:
            logger.warning(f"Schema validation warning on chunk {chunk.chunk_index}: {ve}")
            # Try to recover valid items
            claims_raw = output_json.get("claims", [])
            valid_items = []
            for item in claims_raw:
                try:
                    valid_items.append(RawClaimItem(**item))
                except:
                    continue
            parsed = RawExtractionOutput(claims=valid_items)

        extracted_claims: List[Claim] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        valid_categories = {
            "water", "land", "air", "biodiversity", "waste",
            "infrastructure", "distance", "compliance", "environmental-impact", "other"
        }
        valid_importances = {"high", "medium", "low"}
        valid_types = {
            "geographic", "numeric", "documentary", "regulatory",
            "external-evidence", "mixed", "unknown"
        }
        valid_extractabilities = {"high", "medium", "low"}

        for item in parsed.claims:
            claim_text = item.text.strip()
            source_text = item.sourceText.strip()

            if not claim_text or not source_text:
                continue

            # Ensure page is within chunk range
            reported_page = item.page
            if reported_page not in chunk.pages_included:
                # If page is outside chunk, snap to chunk start or try to locate quote
                reported_page = chunk.start_page

            # Verify quote in page text
            is_verified, actual_page = self._verify_source_text(
                source_text, reported_page, pages_dict
            )

            # Normalize enums
            category = item.category.lower().replace(" ", "-")
            if category not in valid_categories:
                category = "other"

            importance = item.importance.lower()
            if importance not in valid_importances:
                importance = "medium"

            v_type = item.verificationType.lower()
            if v_type not in valid_types:
                v_type = "documentary"

            extractability = item.extractability.lower()
            if extractability not in valid_extractabilities:
                extractability = "medium"

            claim_id = f"claim_{uuid.uuid4().hex[:10]}"

            extracted_claims.append(Claim(
                id=claim_id,
                audit_id=audit_id,
                text=claim_text,
                page=actual_page,
                pages=[actual_page],
                source_text=source_text,
                category=category,  # type: ignore
                importance=importance,  # type: ignore
                verification_type=v_type,  # type: ignore
                extractability=extractability,  # type: ignore
                status="pending",
                created_at=now_iso,
                source_verified=is_verified
            ))

        return extracted_claims

    def deduplicate_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Deduplicates repeated claims while preserving all referenced page numbers.
        Section 11: If a claim asserts the exact same fact on Page 17 and Page 42,
        consolidate into a single claim with pages: [17, 42].
        """
        deduped: List[Claim] = []
        seen_map: Dict[str, Claim] = {}

        for claim in claims:
            # Normalize claim text for comparison
            normalized_key = self._normalize_string(claim.text)
            # Remove punctuation for comparison
            clean_key = re.sub(r'[^\w\s]', '', normalized_key)

            if clean_key in seen_map:
                existing = seen_map[clean_key]
                # Merge page references
                if claim.page not in existing.pages:
                    existing.pages.append(claim.page)
                    existing.pages.sort()
                # If the new reference is marked high importance, upgrade existing
                if claim.importance == "high" and existing.importance != "high":
                    existing.importance = "high"
            else:
                seen_map[clean_key] = claim
                deduped.append(claim)

        return deduped

    def extract_claims(self, audit: AuditDocument) -> List[Claim]:
        """
        Full end-to-end extraction pipeline:
        1. Validate document has pages and text.
        2. Chunk document intelligently.
        3. Extract claims sequentially via Gemini.
        4. Validate schema and verify source quotations against actual page text.
        5. Deduplicate claims across chunks.
        6. Return clean, normalized, auditable claims.
        """
        if not audit.pages:
            raise GeminiExtractionError("Document contains no extracted pages.")

        pages_dict = {p.page_number: p.text for p in audit.pages}
        chunks = self.chunk_document(audit.pages)

        logger.info(f"Chunked audit {audit.id} ({len(audit.pages)} pages) into {len(chunks)} chunks.")

        raw_claims: List[Claim] = []
        for chunk in chunks:
            chunk_claims = self.extract_claims_from_chunk(chunk, audit.id, pages_dict)
            raw_claims.extend(chunk_claims)

        # Deduplicate across entire document
        final_claims = self.deduplicate_claims(raw_claims)

        # Priority sorting: High first, then medium, then low; then by page number
        importance_rank = {"high": 0, "medium": 1, "low": 2}
        final_claims.sort(key=lambda c: (importance_rank.get(c.importance, 3), c.page))

        # Re-number IDs cleanly for human review: claim_1, claim_2...
        for idx, c in enumerate(final_claims, 1):
            c.id = f"claim_{audit.id[:8]}_{idx:02d}"

        return final_claims

# Global singleton service
gemini_service = GeminiService()

