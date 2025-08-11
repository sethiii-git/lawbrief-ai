# File: backend/clause_extractor.py
"""
Improved Contract Clause Extraction & Classification
"""

import logging
import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from itertools import groupby

logging.basicConfig(level=logging.INFO)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_trf")  # better accuracy than sm
except OSError:
    logging.error("spaCy model not found. Install: python -m spacy download en_core_web_trf")
    raise

# Load better transformer
try:
    sentence_model = SentenceTransformer("all-mpnet-base-v2")
except Exception as e:
    logging.error(f"Failed to load transformer: {e}")
    raise

# Keywords & templates
CLAUSE_KEYWORDS = {
    "termination": ["terminate", "termination", "end agreement", "expire", "dissolution", "cancel"],
    "payment": ["payment", "fee", "cost", "invoice", "billing", "remuneration", "compensation"],
    "liability": ["liability", "liable", "damages", "indemnify", "indemnification", "harm"],
    "confidentiality": ["confidential", "non-disclosure", "proprietary", "trade secret", "nda"],
    "intellectual_property": ["intellectual property", "ip", "patent", "trademark", "copyright", "license"],
    "force_majeure": ["force majeure", "act of god", "unforeseeable", "beyond control"],
    "governing_law": ["governing law", "jurisdiction", "applicable law", "courts", "venue"],
    "warranty": ["warranty", "guarantee", "warrants", "represents", "assurance"],
    "dispute_resolution": ["dispute", "arbitration", "mediation", "litigation", "resolution"],
    "renewal": ["renewal", "renew", "extend", "automatic", "term"]
}

TEMPLATE_CLAUSES = {
    "termination": "This agreement may be terminated by either party with thirty days written notice.",
    "payment": "Payment shall be due within thirty days of invoice receipt.",
    "liability": "Neither party shall be liable for indirect or consequential damages.",
    "confidentiality": "All confidential information shall be kept strictly confidential.",
    "intellectual_property": "All intellectual property rights remain with the original owner.",
    "force_majeure": "Neither party shall be liable for delays caused by force majeure events.",
    "governing_law": "This agreement shall be governed by the laws of the specified jurisdiction.",
    "warranty": "The services are provided with no warranties express or implied.",
    "dispute_resolution": "Any disputes shall be resolved through binding arbitration.",
    "renewal": "This agreement shall automatically renew for successive one-year terms."
}

@lru_cache(maxsize=1)
def _get_template_embeddings() -> Dict[str, np.ndarray]:
    return {k: sentence_model.encode([v])[0] for k, v in TEMPLATE_CLAUSES.items()}

def _split_into_clauses(text: str) -> List[str]:
    """
    Improved clause splitting:
    - Headings
    - Blank lines
    - Semantic chunking
    """
    # First, try heading-based
    # heading_pattern = r"(?m)^(?:\d+(\.\d+)*\.|[A-Z][A-Z\s]+):?\s"

    heading_pattern = r"(?m)^(?:\d+(?:\.\d+)*\.|[A-Z][A-Z\s]+):?\s"
    parts = re.split(heading_pattern, text)
    clauses = []

    for part in parts:
        chunk = part.strip()
        if len(chunk) > 40:  # min length filter
            clauses.append(chunk)

    if not clauses:
        # Fallback: sentence grouping
        doc = nlp(text)
        buffer = []
        for sent in doc.sents:
            buffer.append(sent.text)
            if sum(len(s) for s in buffer) > 250:
                clauses.append(" ".join(buffer).strip())
                buffer = []
        if buffer:
            clauses.append(" ".join(buffer).strip())

    return clauses

def classify_clause(text: str) -> Tuple[str, float]:
    """
    Classify clause using weighted keyword + semantic similarity.
    Returns (clause_type, confidence_score)
    """
    text_lower = text.lower()

    # Keyword score
    keyword_scores = {}
    for clause_type, keywords in CLAUSE_KEYWORDS.items():
        score = sum(text_lower.count(k) for k in keywords) / len(keywords)
        keyword_scores[clause_type] = score

    best_kw = max(keyword_scores, key=keyword_scores.get)
    kw_score = keyword_scores[best_kw]

    # Semantic score
    clause_embedding = sentence_model.encode([text])
    template_embeddings = _get_template_embeddings()
    similarities = {ct: cosine_similarity(clause_embedding, [emb])[0][0]
                    for ct, emb in template_embeddings.items()}
    best_sem = max(similarities, key=similarities.get)
    sem_score = similarities[best_sem]

    # Combine scores (weighted)
    if kw_score > 0.3 and sem_score > 0.65:
        final_type = best_kw if kw_score >= sem_score else best_sem
    elif sem_score > 0.7:
        final_type = best_sem
    else:
        final_type = best_kw

    confidence = max(kw_score, sem_score)
    return final_type.replace("_", " ").title(), round(float(confidence), 3)

def extract_entities(text: str) -> List[Dict]:
    """
    Extract named entities with extended legal coverage.
    """
    doc = nlp(text)
    entities = []
    allowed_labels = {"ORG", "PERSON", "DATE", "MONEY", "GPE", "TIME", "PERCENT", "QUANTITY", "LAW"}

    for ent in doc.ents:
        if ent.label_ in allowed_labels:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
    return entities

def extract_clauses(text: str) -> List[Dict]:
    raw_clauses = _split_into_clauses(text)
    results = []
    for i, clause_text in enumerate(raw_clauses, start=1):
        ctype, confidence = classify_clause(clause_text)
        entities = extract_entities(clause_text)
        results.append({
            "id": i,
            "title": _extract_title_from_text(clause_text),
            "text": clause_text,
            "type": ctype,
            "confidence": confidence,
            "entities": entities
        })
    return results

def _extract_title_from_text(text: str) -> Optional[str]:
    # Headings first
    lines = text.split("\n")
    for line in lines[:2]:
        if len(line) > 5 and (line.isupper() or ":" in line):
            return line.replace(":", "").strip()
    # Else first sentence
    sentences = re.split(r"[.!?]+", text)
    return sentences[0].strip() if sentences else None

if __name__ == "__main__":
    sample = """
    1. TERMINATION
    This Agreement may be terminated by either party upon thirty (30) days written notice.

    2. PAYMENT TERMS
    Company ABC shall pay Contractor $10,000 within 30 days of invoice receipt.

    3. CONFIDENTIALITY
    All confidential information disclosed shall remain strictly confidential.
    """
    clauses = extract_clauses(sample)
    for c in clauses:
        print(f"\nID {c['id']} | {c['type']} ({c['confidence']})")
        print(f"Title: {c['title']}")
        print(f"Text: {c['text']}")
        print(f"Entities: {c['entities']}")
