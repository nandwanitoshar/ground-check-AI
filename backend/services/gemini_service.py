import os
import json
import re
import logging
from typing import List, Dict, Any, Optional
from backend.models.audit import Claim, GeographicCoordinates

logger = logging.getLogger("gemini_service")

CLAIM_EXTRACTION_PROMPT = """
You are GroundCheck AI's Document Claims Extractor.
Your sole job is to extract factual, falsifiable claims from the provided Environmental Impact Assessment (EIA) or Environmental Report.

CRITICAL RULES:
1. ONLY extract claims actually asserted by the document text.
2. NEVER invent claims, numbers, distances, or coordinates.
3. Categorize each claim into one of: ["Water", "Land", "Biodiversity", "Air", "Waste", "Distance", "Infrastructure", "Environmental impact", "Compliance", "Other"]
4. Set importance to "high", "medium", or "low" based on environmental significance.
5. Set verification_type:
   - "geographic_distance" (if the claim mentions a distance, buffer, radius, or proximity to a feature)
   - "presence_absence" (if the claim asserts absence or presence of a feature or species)
   - "regulatory_buffer" (if the claim asserts meeting a setback/regulatory distance)
   - "baseline_air_quality" (if the claim specifies particulate or emission levels)
   - "factual_statement" (for general procedural or regulatory assertions)
6. If a specific distance is claimed, extract `claimed_distance_km` as a float (convert meters to km if necessary, e.g. 500m = 0.5km).
7. If a specific feature is referenced, extract `claimed_feature`.
8. Cite the exact page number where the claim was found.

Output strictly a JSON list of objects matching this schema:
[
  {
    "id": "claim-1",
    "text": "Exact or synthesized claim statement",
    "page": 14,
    "category": "Water",
    "importance": "high",
    "verification_type": "geographic_distance",
    "raw_quote": "Direct quote from the page",
    "claimed_distance_km": 2.0,
    "claimed_feature": "water body"
  }
]
"""

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Gemini Client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize google.genai: {e}")

    def extract_claims(self, pages: List[Dict[str, Any]]) -> List[Claim]:
        """
        Extract claims from pages using Gemini if available, or fall back to intelligent heuristic parser.
        """
        if self.client:
            try:
                return self._extract_with_gemini(pages)
            except Exception as e:
                logger.error(f"Gemini API extraction failed: {e}. Falling back to rule-based parser.")
        
        return self._extract_with_heuristics(pages)

    def _extract_with_gemini(self, pages: List[Dict[str, Any]]) -> List[Claim]:
        context_chunks = []
        for p in pages:
            text = p.get("text", "")
            if len(text.strip()) > 50:
                context_chunks.append(f"--- PAGE {p['page_number']} ---\n{text[:2000]}")

        full_prompt = (
            f"{CLAIM_EXTRACTION_PROMPT}\n\n"
            f"DOCUMENT CONTENT:\n" + "\n\n".join(context_chunks[:15])
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config={
                "response_mime_type": "application/json"
            }
        )

        raw_json = response.text.strip()
        data = json.loads(raw_json)
        claims = []
        for idx, item in enumerate(data):
            claims.append(Claim(
                id=item.get("id") or f"claim-{idx+1}",
                text=item["text"],
                page=int(item.get("page", 1)),
                category=item.get("category", "Other"),
                importance=item.get("importance", "medium"),
                verification_type=item.get("verification_type", "factual_statement"),
                raw_quote=item.get("raw_quote"),
                section=item.get("section"),
                claimed_distance_km=item.get("claimed_distance_km"),
                claimed_feature=item.get("claimed_feature")
            ))
        return claims

    def _extract_with_heuristics(self, pages: List[Dict[str, Any]]) -> List[Claim]:
        """
        Intelligent rule-based claim extraction parser.
        Detects environmental claims, distances, buffers, and regulatory limits.
        """
        extracted_claims: List[Claim] = []
        claim_counter = 1

        for p in pages:
            page_num = p["page_number"]
            raw_text = p.get("text", "")
            
            # Normalize text by repairing wrapped words and combining lines
            normalized = re.sub(r'(\b\w+)-\n(\w+\b)', r'\1\2', raw_text)
            normalized = normalized.replace("sea\nsonal", "seasonal").replace("peren\nnial", "perennial")
            # Replace multiple newlines with period space or space
            normalized_single_line = re.sub(r'\s*\n\s*', ' ', normalized)

            # 1. Check for explicit EIA callouts (e.g. KEY FINDING:, KEY CLAIM:, STATEMENT:, CLAIM:)
            prefixes = [
                ("KEY FINDING:", "high"),
                ("KEY CLAIM:", "high"),
                ("STATEMENT:", "medium"),
                ("CLAIM:", "medium"),
                ("BASELINE STATEMENT:", "medium"),
                ("FINDING:", "medium")
            ]

            for prefix, importance in prefixes:
                if prefix in normalized_single_line:
                    parts = normalized_single_line.split(prefix)
                    for pt in parts[1:]:
                        # Take until end of sentence or double space
                        match = re.split(r'\. (?=[A-Z])|\.\s*$', pt.strip())
                        if match and match[0].strip():
                            claim_sentence = match[0].strip()
                            if len(claim_sentence) > 25:
                                # Determine category and distance
                                cat = "Other"
                                v_type = "factual_statement"
                                dist_val = None

                                lower = claim_sentence.lower()
                                if "water" in lower or "stream" in lower or "river" in lower or "drainage" in lower or "drawdown" in lower:
                                    cat = "Water"
                                elif "park" in lower or "buffer" in lower or "reserve" in lower or "open space" in lower:
                                    cat = "Land"
                                elif "residential" in lower or "dwelling" in lower or "meters" in lower or "distance" in lower:
                                    cat = "Distance"
                                elif "pm10" in lower or "naaqs" in lower or "air" in lower:
                                    cat = "Air"
                                    v_type = "baseline_air_quality"
                                elif "habitat" in lower or "species" in lower or "endangered" in lower:
                                    cat = "Biodiversity"
                                    v_type = "presence_absence"
                                elif "stakeholder" in lower or "hearing" in lower:
                                    cat = "Compliance"

                                # Check distance
                                dist_match = re.search(r'([\d\.,]+)\s*(?:-| )?(km|kilometer|m|meter)s?', claim_sentence, re.IGNORECASE)
                                if dist_match:
                                    v_type = "geographic_distance"
                                    val_str = dist_match.group(1).replace(",", "")
                                    try:
                                        val = float(val_str)
                                        unit = dist_match.group(2).lower()
                                        dist_val = val if "km" in unit else val / 1000.0
                                    except:
                                        pass

                                extracted_claims.append(Claim(
                                    id=f"claim-{claim_counter}",
                                    text=claim_sentence,
                                    page=page_num,
                                    category=cat,
                                    importance=importance,
                                    verification_type=v_type,
                                    raw_quote=f"{prefix} {claim_sentence}",
                                    claimed_distance_km=dist_val,
                                    claimed_feature=cat.lower()
                                ))
                                claim_counter += 1

            # 2. General regex patterns across sentences
            sentences = re.split(r'\.\s+(?=[A-Z])', normalized_single_line)
            for s in sentences:
                s_clean = s.strip()
                s_lower = s_clean.lower()

                # Skip headers/footers
                if "groundcheck test eia" in s_lower or "confidential" in s_lower:
                    continue

                if any(c.text in s_clean for c in extracted_claims):
                    continue

                # Water distance
                if "water body" in s_lower and ("within" in s_lower or "nearest" in s_lower or "no " in s_lower):
                    dist_match = re.search(r'([\d\.]+)\s*(km|kilometer|m|meter)', s_clean, re.IGNORECASE)
                    dist_val = float(dist_match.group(1)) if dist_match else None
                    if dist_match and "m" in dist_match.group(2).lower() and "km" not in dist_match.group(2).lower():
                        dist_val = dist_val / 1000.0 if dist_val else None

                    extracted_claims.append(Claim(
                        id=f"claim-{claim_counter}",
                        text=s_clean,
                        page=page_num,
                        category="Water",
                        importance="high",
                        verification_type="geographic_distance",
                        raw_quote=s_clean,
                        claimed_distance_km=dist_val,
                        claimed_feature="water body"
                    ))
                    claim_counter += 1

                # Buffer / park
                elif ("buffer" in s_lower or "setback" in s_lower) and ("park" in s_lower or "protected" in s_lower or "open space" in s_lower):
                    dist_match = re.search(r'([\d\.,]+)\s*(?:-| )?(km|kilometer|m|meter)', s_clean, re.IGNORECASE)
                    dist_val = None
                    if dist_match:
                        val = float(dist_match.group(1).replace(",", ""))
                        dist_val = val if "km" in dist_match.group(2).lower() else val / 1000.0

                    extracted_claims.append(Claim(
                        id=f"claim-{claim_counter}",
                        text=s_clean,
                        page=page_num,
                        category="Land",
                        importance="high",
                        verification_type="regulatory_buffer",
                        raw_quote=s_clean,
                        claimed_distance_km=dist_val,
                        claimed_feature="protected open space"
                    ))
                    claim_counter += 1

                # Residential
                elif "residential" in s_lower and ("dwelling" in s_lower or "home" in s_lower or "meters" in s_lower or "km" in s_lower):
                    dist_match = re.search(r'([\d\.,]+)\s*(?:-| )?(km|kilometer|m|meter)', s_clean, re.IGNORECASE)
                    dist_val = None
                    if dist_match:
                        val = float(dist_match.group(1).replace(",", ""))
                        dist_val = val if "km" in dist_match.group(2).lower() else val / 1000.0

                    extracted_claims.append(Claim(
                        id=f"claim-{claim_counter}",
                        text=s_clean,
                        page=page_num,
                        category="Distance",
                        importance="medium",
                        verification_type="geographic_distance",
                        raw_quote=s_clean,
                        claimed_distance_km=dist_val,
                        claimed_feature="residential dwelling"
                    ))
                    claim_counter += 1

                # Air Quality
                elif "pm10" in s_lower or ("naaqs" in s_lower and "µg/m³" in s_clean):
                    extracted_claims.append(Claim(
                        id=f"claim-{claim_counter}",
                        text=s_clean,
                        page=page_num,
                        category="Air",
                        importance="medium",
                        verification_type="baseline_air_quality",
                        raw_quote=s_clean,
                        claimed_feature="particulate matter"
                    ))
                    claim_counter += 1

                # Biodiversity
                elif "critical habitat" in s_lower or "endangered species" in s_lower:
                    extracted_claims.append(Claim(
                        id=f"claim-{claim_counter}",
                        text=s_clean,
                        page=page_num,
                        category="Biodiversity",
                        importance="high",
                        verification_type="presence_absence",
                        raw_quote=s_clean,
                        claimed_feature="endangered species habitat"
                    ))
                    claim_counter += 1

                # Groundwater
                elif "groundwater" in s_lower and ("drawdown" in s_lower or "dewatering" in s_lower):
                    extracted_claims.append(Claim(
                        id=f"claim-{claim_counter}",
                        text=s_clean,
                        page=page_num,
                        category="Water",
                        importance="medium",
                        verification_type="factual_statement",
                        raw_quote=s_clean,
                        claimed_feature="groundwater drawdown"
                    ))
                    claim_counter += 1

                # Stakeholder
                elif "stakeholder" in s_lower or "public hearing" in s_lower:
                    extracted_claims.append(Claim(
                        id=f"claim-{claim_counter}",
                        text=s_clean,
                        page=page_num,
                        category="Compliance",
                        importance="low",
                        verification_type="factual_statement",
                        raw_quote=s_clean,
                        claimed_feature="stakeholder engagement"
                    ))
                    claim_counter += 1

        # Deduplicate claims with same page, category, or similar text
        unique_claims: List[Claim] = []
        seen = set()
        for idx, c in enumerate(extracted_claims):
            clean_snippet = c.text[:35].lower()
            key = (c.page, c.category, clean_snippet)
            if key not in seen:
                seen.add(key)
                c.id = f"claim-{len(unique_claims) + 1}"
                unique_claims.append(c)

        return unique_claims
