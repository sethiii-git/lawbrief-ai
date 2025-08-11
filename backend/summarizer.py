# File: backend/summarizer.py
"""
Improved Contract Summarization Module
--------------------------------------
Supports extractive, abstractive, and hybrid summarization modes with
robust chunking, semantic ranking, and clause-level summarization.
"""

import logging
import re
from typing import Dict, List, Literal, Optional
import numpy as np
from transformers import pipeline, AutoTokenizer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

from .utils import chunk_text, clean_text

# -------------------------
# Model Initialization
# -------------------------
try:
    # Abstractive model (BART)
    abstractive_summarizer = pipeline(
        "summarization",
        model="facebook/bart-large-cnn",
        device=-1  # CPU
    )
    bart_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")

    # Embedding model for extractive
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")

except Exception as e:
    logging.error(f"[Summarizer] Model loading failed: {e}")
    raise


# -------------------------
# Public API
# -------------------------
def summarize_document(
    text: str,
    mode: Literal["abstractive", "extractive", "hybrid"] = "hybrid",
    clauses: Optional[List[Dict]] = None
) -> Dict:
    """
    Summarize a full contract in different modes, optionally with per-clause summaries.

    Args:
        text: Contract text
        mode: Summarization mode
        clauses: Optional clause extraction results

    Returns:
        Dict with short_summary, long_summary, and per_clause_summaries
    """
    try:
        text = clean_text(text)
        result = {
            "short_summary": "",
            "long_summary": "",
            "per_clause_summaries": []
        }

        if mode == "abstractive":
            result["short_summary"] = safe_abstractive_summarize(text, max_length=128)
            result["long_summary"] = safe_abstractive_summarize(text, max_length=256)

        elif mode == "extractive":
            result["short_summary"] = " ".join(_extract_key_sentences(text, 3))
            result["long_summary"] = " ".join(_extract_key_sentences(text, 6))

        elif mode == "hybrid":
            try:
                # Abstractive for main summaries
                result["short_summary"] = safe_abstractive_summarize(text, max_length=128)
                result["long_summary"] = safe_abstractive_summarize(text, max_length=256)
            except Exception as e:
                logging.warning(f"[Hybrid] Abstractive failed, falling back to extractive: {e}")
                result["short_summary"] = " ".join(_extract_key_sentences(text, 3))
                result["long_summary"] = " ".join(_extract_key_sentences(text, 6))

        # Per-clause summaries
        if clauses:
            for clause in clauses:
                clause_text = clean_text(clause.get("text", ""))
                try:
                    clause_summary = safe_abstractive_summarize(clause_text, max_length=64)
                except Exception:
                    clause_summary = _first_sentence_fallback(clause_text)
                result["per_clause_summaries"].append({
                    "clause_id": clause.get("id"),
                    "clause_type": clause.get("type"),
                    "summary": clause_summary
                })

        return result

    except Exception as e:
        logging.error(f"[Summarizer] Document summarization error: {e}")
        return {
            "short_summary": "Error generating summary",
            "long_summary": "Error generating summary",
            "per_clause_summaries": []
        }


def generate_executive_summary(clauses: List[Dict], risk_summary: Dict) -> str:
    """
    Generate a high-level summary combining clause overview and risk analysis.
    """
    try:
        summary_parts = []

        # Clause overview
        clause_types = sorted({c["type"] for c in clauses})
        summary_parts.append(
            f"The contract contains {len(clauses)} clauses across {len(clause_types)} main categories: {', '.join(clause_types)}."
        )

        # Risk overview
        risk_level = risk_summary.get("contract_risk_level", "Unknown")
        dist = risk_summary.get("risk_distribution", {})
        summary_parts.append(
            f"Overall risk level: {risk_level}. Distribution: {dist.get('High', 0)} high-risk, {dist.get('Medium', 0)} medium-risk, {dist.get('Low', 0)} low-risk clauses."
        )

        # Top risky clause
        top_risky = risk_summary.get("top_risky_clauses", [])
        if top_risky:
            c = top_risky[0]
            terms = ", ".join(c.get("matched_terms", [])[:3])
            summary_parts.append(
                f"Highest-risk clause (ID {c['clause_id']}) scored {c['risk_score']:.2f} and includes: {terms}."
            )

        return " ".join(summary_parts)

    except Exception as e:
        logging.error(f"[Summarizer] Executive summary error: {e}")
        return "Unable to generate executive summary."


# -------------------------
# Internal Helpers
# -------------------------
def safe_abstractive_summarize(text: str, max_length: int = 256) -> str:
    """
    Abstractive summarization with chunking, fallback, and secondary compression.
    """
    if len(text.split()) < 20:
        return text.strip()

    try:
        tokens = bart_tokenizer.encode(text, truncation=False)
        if len(tokens) <= 1024:
            return _abstractive_single_pass(text, max_length)

        # Chunk & summarize
        chunks = chunk_text(text, max_chars=3000)
        chunk_summaries = [_abstractive_chunk(c) for c in chunks]

        combined = " ".join(chunk_summaries)

        if len(combined.split()) > max_length // 2:
            try:
                return _abstractive_single_pass(combined, max_length)
            except Exception:
                return " ".join(_extract_key_sentences(combined, 3))
        return combined.strip()

    except Exception as e:
        logging.error(f"[Summarizer] Abstractive failed: {e}")
        return " ".join(_extract_key_sentences(text, 3))


def _abstractive_single_pass(text: str, max_length: int) -> str:
    """Run abstractive summarization on a single chunk of text."""
    return abstractive_summarizer(
        text,
        max_length=max_length,
        min_length=max_length // 4,
        do_sample=False
    )[0]["summary_text"].strip()


def _abstractive_chunk(text: str) -> str:
    """Summarize one chunk, fallback to first sentences if fail."""
    try:
        return abstractive_summarizer(
            text,
            max_length=128,
            min_length=32,
            do_sample=False
        )[0]["summary_text"].strip()
    except Exception:
        return _first_sentence_fallback(text)


def _extract_key_sentences(text: str, num_sentences: int) -> List[str]:
    """
    Extract key sentences via TextRank using sentence-transformer embeddings.
    """
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
    if len(sentences) <= num_sentences:
        return sentences

    try:
        embeddings = sentence_model.encode(sentences, convert_to_numpy=True)
        sim_matrix = cosine_similarity(embeddings)
        np.fill_diagonal(sim_matrix, 0.0)  # Avoid self-loops
        graph = nx.from_numpy_array(sim_matrix)
        scores = nx.pagerank(graph)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_idx = sorted([i for i, _ in ranked[:num_sentences]])
        return [sentences[i] for i in top_idx]
    except Exception as e:
        logging.warning(f"[Summarizer] Extractive fallback: {e}")
        return sentences[:num_sentences]


def _first_sentence_fallback(text: str) -> str:
    """Get the first sentence or first 100 chars as fallback."""
    sentences = re.split(r'[.!?]+', text)
    return sentences[0].strip() if sentences else text[:100]


# -------------------------
# Debug run
# -------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sample_contract = """
    This Software License Agreement is entered into between Company ABC and Contractor XYZ.
    The contractor agrees to provide software development services for 12 months.
    Payment terms require invoices to be paid within 30 days of receipt.
    The contractor shall indemnify the company against claims from the software.
    This agreement may be terminated by either party with 30 days written notice.
    Intellectual property developed remains with the company.
    Confidential information must be kept for 5 years.
    """

    for mode in ["extractive", "abstractive", "hybrid"]:
        logging.info(f"=== {mode.upper()} MODE ===")
        summary = summarize_document(sample_contract, mode=mode)
        logging.info(f"Short: {summary['short_summary']}")
        logging.info(f"Long: {summary['long_summary']}")
