# File: backend/utils.py
"""
Utility functions for document processing, clause-aware cleaning,
and file operations for LawBrief AI.
"""

import json
import logging
import os
import re
from typing import Any, List, Dict, Optional

import pdfplumber
from docx import Document


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("lawbrief.log", encoding="utf-8")
        ]
    )


# ----------------------------
# FILE LOADING
# ----------------------------

def load_pdf(path: str) -> Dict[str, Any]:
    """
    Extract plain text and page-level mapping from a PDF file.

    Returns:
        {
            "full_text": str,
            "pages": [{"page_num": int, "text": str}]
        }
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        pages_data = []
        all_text = []

        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                cleaned = _remove_repetitive_headers_footers(page_text)
                if cleaned.strip():
                    pages_data.append({"page_num": i, "text": cleaned})
                    all_text.append(cleaned)

        return {
            "full_text": "\n\n".join(all_text),
            "pages": pages_data
        }
    except Exception as e:
        logging.error(f"Error loading PDF {path}: {str(e)}")
        raise Exception(f"Failed to parse PDF: {str(e)}")


def load_docx(path: str) -> Dict[str, Any]:
    """
    Extract text from a DOCX file with paragraph-level mapping.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"DOCX file not found: {path}")

    try:
        doc = Document(path)
        paragraphs = []
        numbered_paragraphs = []

        for idx, paragraph in enumerate(doc.paragraphs, start=1):
            if paragraph.text.strip():
                cleaned = paragraph.text.strip()
                paragraphs.append(cleaned)
                numbered_paragraphs.append({"para_num": idx, "text": cleaned})

        return {
            "full_text": "\n\n".join(paragraphs),
            "paragraphs": numbered_paragraphs
        }
    except Exception as e:
        logging.error(f"Error loading DOCX {path}: {str(e)}")
        raise Exception(f"Failed to parse DOCX: {str(e)}")


# ----------------------------
# TEXT CLEANING
# ----------------------------

def _remove_repetitive_headers_footers(text: str) -> str:
    """
    Remove likely headers/footers without killing legit repeated section titles.
    """
    lines = text.split("\n")
    counts = {}
    for line in lines:
        stripped = line.strip()
        if 6 <= len(stripped) <= 80:  # Skip very short/very long lines
            counts[stripped] = counts.get(stripped, 0) + 1

    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if counts.get(stripped, 0) <= 5:  # Less aggressive threshold
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# def clean_text(text: str) -> str:
#     """
#     Normalize whitespace & bullets, but preserve double newlines between clauses.
#     """
#     text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", text)  # printable chars only

#     # Keep paragraph breaks intact
#     text = text.replace("\r\n", "\n")
#     text = re.sub(r"\n{3,}", "\n\n", text)

#     # Normalize bullets & numbering
#     text = re.sub(r"[•·▪▫◦‣⁃]\s*", "• ", text)
#     text = re.sub(r"^\s*((?:\d+\.){1,3}|\d+\)|[A-Za-z]\))\s+",
#                   r"\1 ", text, flags=re.MULTILINE)

#     # Collapse excessive spaces within lines
#     text = re.sub(r"[ \t]+", " ", text)

#     return text.strip()
def clean_text(text: str) -> str:
    """
    Normalize whitespace & bullets, but preserve double newlines between clauses.
    """
    if text is None:
        return ""

    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", text)  # printable chars only

    # Keep paragraph breaks intact
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Normalize bullets & numbering
    text = re.sub(r"[•·▪▫◦‣⁃]\s*", "• ", text)
    text = re.sub(r"^\s*((?:\d+\.){1,3}|\d+\)|[A-Za-z]\))\s+",
                  r"\1 ", text, flags=re.MULTILINE)

    # Collapse excessive spaces within lines
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


# ----------------------------
# CLAUSE EXTRACTION
# ----------------------------

def extract_clauses(text: str) -> List[Dict[str, Any]]:
    """
    Split text into clauses based on legal numbering and headings.
    Returns list of {"id": int, "numbering": str, "text": str}.
    """
    clauses = []
    clause_pattern = re.compile(
        r"(?P<numbering>(?:\d+\.){1,3}|\d+\)|[A-Z]\)|Section\s+\d+)[ \t]+",
        re.IGNORECASE
    )

    parts = clause_pattern.split(text)
    temp_text = ""
    clause_id = 1
    numbering = None

    for part in parts:
        if clause_pattern.match(part):
            if temp_text.strip():
                clauses.append({
                    "id": clause_id,
                    "numbering": numbering,
                    "text": temp_text.strip()
                })
                clause_id += 1
                temp_text = ""
            numbering = part.strip()
        else:
            temp_text += part

    if temp_text.strip():
        clauses.append({
            "id": clause_id,
            "numbering": numbering,
            "text": temp_text.strip()
        })

    return clauses


# ----------------------------
# CHUNKING
# ----------------------------

def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    """
    Chunk text while preserving clause boundaries.
    """
    clauses = extract_clauses(text)
    chunks = []
    current_chunk = ""

    for clause in clauses:
        clause_text = clause["text"]
        if len(current_chunk) + len(clause_text) + 2 > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = clause_text
            else:
                chunks.append(clause_text[:max_chars])
                clause_text = clause_text[max_chars:]
        else:
            current_chunk += ("\n\n" + clause_text) if current_chunk else clause_text

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


# ----------------------------
# JSON HELPERS
# ----------------------------

def save_json(path: str, obj: Any) -> None:
    """Save an object to a JSON file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving JSON to {path}: {str(e)}")
        raise


def load_json(path: str) -> Any:
    """Load an object from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON from {path}: {str(e)}")
        raise


if __name__ == "__main__":
    setup_logging()
    logging.info("Testing utils.py improvements...")

    sample = """Section 1. Definitions
This Agreement...

Section 2. Obligations
The Parties agree to...
"""
    print(extract_clauses(sample))
