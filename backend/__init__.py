# File: backend/__init__.py
"""
LawBrief AI Backend Package

A comprehensive legal document analysis suite for contract parsing,
clause extraction, risk detection, and summarization.
"""

__version__ = "1.0.0"
__author__ = "LawBrief AI Team"

from .utils import load_pdf, load_docx, clean_text, chunk_text, save_json, load_json, setup_logging
from .clause_extractor import extract_clauses, classify_clause, extract_entities
from .risk_detector import assess_risks
from .summarizer import summarize_document
from .report_generator import generate_pdf_report, generate_docx_report

__all__ = [
    "load_pdf",
    "load_docx", 
    "clean_text",
    "chunk_text",
    "save_json",
    "load_json",
    "setup_logging",
    "extract_clauses",
    "classify_clause", 
    "extract_entities",
    "assess_risks",
    "summarize_document",
    "generate_pdf_report",
    "generate_docx_report"
]
