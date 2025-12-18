# # File: backend/risk_detector.py
# """
# Enhanced Legal Clause Risk Assessment and Scoring Module.
# Fully compatible with updated clause_extractor output.
# """

# import logging
# import re
# from typing import Dict, List
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

# # --------------------------------------------------------------------
# # Load high-accuracy sentence transformer for legal/contract text
# # --------------------------------------------------------------------
# try:
#     sentence_model = SentenceTransformer('all-mpnet-base-v2')  # More accurate than MiniLM
# except Exception as e:
#     logging.error(f"Failed to load sentence transformer: {e}")
#     raise

# # --------------------------------------------------------------------
# # Weighted risk keywords (key: phrase/regex, value: weight 0–1)
# # --------------------------------------------------------------------
# RISK_KEYWORDS = {
#     r"\bindemnif(y|ication|ies)?\b": 1.0,
#     r"\bliquidated damages\b": 0.9,
#     r"\blimit(ed)? liability\b": 0.9,
#     r"\bunlimited liability\b": 1.0,
#     r"\bexclusive jurisdiction\b": 0.6,
#     r"\bwithout liability\b": 0.8,
#     r"\bautomatic renewal\b": 0.7,
#     r"\bnon[- ]refundable\b": 0.6,
#     r"\birrevocable\b": 0.6,
#     r"\bperpetual\b": 0.7,
#     r"\bwaive( right(s)?)?\b": 0.8,
#     r"\bhold harmless\b": 1.0,
#     r"\bas is\b": 0.5,
#     r"\bno warranty\b": 0.7,
#     r"\bfinal sale\b": 0.5,
#     r"\bbinding arbitration\b": 0.7,
#     r"\bclass action waiver\b": 0.9,
#     r"\battorney(’s|s)? fees?\b": 0.5,
#     r"\bconsequential damages\b": 0.8,
#     r"\bpunitive damages\b": 0.9,
#     r"\bspecific performance\b": 0.6,
#     r"\bpenalt(y|ies)\b": 0.7,
#     r"\bforfeit\b": 0.6,
#     r"\bbreach\b": 0.5,
#     r"\bdefault\b": 0.5
# }

# # --------------------------------------------------------------------
# # Example risky clauses for semantic similarity
# # --------------------------------------------------------------------
# RISKY_EXAMPLES = [
#     "The contractor shall indemnify and hold harmless the company from any claims or damages without limitation.",
#     "This agreement automatically renews for successive terms unless terminated with 90 days notice.",
#     "All fees are non-refundable and final upon payment regardless of termination.",
#     "The company may terminate this agreement without notice for any reason or no reason.",
#     "Contractor waives all rights to claim consequential or punitive damages.",
#     "All disputes must be resolved through binding arbitration with no class action rights.",
#     "Contractor assumes unlimited liability for any breach of confidentiality provisions."
# ]

# # Precompute embeddings for risky examples
# RISKY_EMBEDDINGS = sentence_model.encode(RISKY_EXAMPLES, normalize_embeddings=True)

# # Clause type weighting from clause_extractor output
# CLAUSE_TYPE_WEIGHTS = {
#     "liability": 1.0,
#     "indemnification": 1.0,
#     "termination": 0.7,
#     "renewal": 0.6,
#     "payment": 0.4,
#     "confidentiality": 0.5,
#     "dispute resolution": 0.8
# }

# # --------------------------------------------------------------------
# # Main API
# # --------------------------------------------------------------------
# def assess_risks(clauses: List[Dict]) -> Dict:
#     """
#     Assess risk levels for contract clauses and generate overall contract risk summary.
#     """
#     try:
#         clause_risks = []
#         total_risk_score = 0
#         risk_counts = {"Low": 0, "Medium": 0, "High": 0}

#         for clause in clauses:
#             risk_assessment = _assess_clause_risk(clause)
#             clause_risks.append(risk_assessment)
#             total_risk_score += risk_assessment["risk_score"]
#             risk_counts[risk_assessment["risk_level"]] += 1

#         avg_risk_score = total_risk_score / len(clauses) if clauses else 0
#         contract_risk_level = _score_to_level(avg_risk_score)

#         top_risky = sorted(clause_risks, key=lambda x: x["risk_score"], reverse=True)[:5]

#         return {
#             "clause_risks": clause_risks,
#             "contract_risk_score": avg_risk_score,
#             "contract_risk_level": contract_risk_level,
#             "risk_distribution": risk_counts,
#             "top_risky_clauses": top_risky,
#             "total_clauses": len(clauses),
#             "high_risk_count": risk_counts["High"],
#             "medium_risk_count": risk_counts["Medium"],
#             "low_risk_count": risk_counts["Low"]
#         }

#     except Exception as e:
#         logging.error(f"Error in risk assessment: {e}")
#         return {
#             "clause_risks": [],
#             "contract_risk_score": 0.0,
#             "contract_risk_level": "Unknown",
#             "risk_distribution": {"Low": 0, "Medium": 0, "High": 0},
#             "top_risky_clauses": [],
#             "total_clauses": 0,
#             "high_risk_count": 0,
#             "medium_risk_count": 0,
#             "low_risk_count": 0
#         }

# # --------------------------------------------------------------------
# # Internal helpers
# # --------------------------------------------------------------------
# def _assess_clause_risk(clause: Dict) -> Dict:
#     """
#     Assess risk for a single clause.
#     """
#     text = clause["text"]
#     text_lower = text.lower()

#     # 1. Keyword-based risk scoring (weighted)
#     keyword_score, matched_terms = _keyword_risk_score(text_lower)

#     # 2. Semantic similarity to risky examples
#     try:
#         clause_embedding = sentence_model.encode([text], normalize_embeddings=True)
#         similarities = cosine_similarity(clause_embedding, RISKY_EMBEDDINGS)[0]
#         max_similarity = float(np.max(similarities))
#     except Exception as e:
#         logging.warning(f"Similarity computation error: {e}")
#         max_similarity = 0.0

#     # 3. Length/complexity factor
#     length_factor = min(len(text) / 300.0, 2.0) / 2.0

#     # 4. Clause type boost
#     clause_type = clause.get("type", "").lower()
#     type_boost = CLAUSE_TYPE_WEIGHTS.get(clause_type, 0.0)

#     # Weighted combined risk score
#     raw_score = (
#         0.5 * keyword_score +
#         0.3 * max_similarity +
#         0.1 * length_factor +
#         0.1 * type_boost
#     )

#     risk_level = _score_to_level(raw_score)

#     return {
#         "clause_id": clause.get("id"),
#         "risk_score": raw_score,
#         "risk_level": risk_level,
#         "matched_terms": matched_terms,
#         "keyword_score": keyword_score,
#         "similarity_score": max_similarity,
#         "length_factor": length_factor,
#         "type_boost": type_boost
#     }


# def _keyword_risk_score(text: str):
#     """
#     Compute keyword risk score using weighted regex matching.
#     """
#     matched_terms = []
#     total_weight = 0

#     for pattern, weight in RISK_KEYWORDS.items():
#         if re.search(pattern, text, re.IGNORECASE):
#             matched_terms.append(pattern.strip(r"\b"))
#             total_weight += weight

#     # Normalize to 0–1
#     keyword_score = min(total_weight / 5.0, 1.0)
#     return keyword_score, matched_terms


# def _score_to_level(score: float) -> str:
#     """
#     Convert numerical score to categorical level.
#     """
#     if score < 0.3:
#         return "Low"
#     elif score < 0.6:
#         return "Medium"
#     else:
#         return "High"

# # --------------------------------------------------------------------
# # Recommendations generator
# # --------------------------------------------------------------------
# def get_risk_recommendations(risk_summary: Dict) -> List[str]:
#     """
#     Generate actionable recommendations.
#     """
#     recommendations = []

#     if risk_summary["contract_risk_level"] == "High":
#         recommendations.append("⚠️ HIGH overall contract risk – seek legal review before signing.")

#     if risk_summary["high_risk_count"] > 0:
#         recommendations.append(f"{risk_summary['high_risk_count']} high-risk clauses detected that need urgent attention.")

#     for clause_risk in risk_summary["top_risky_clauses"][:3]:
#         terms = clause_risk.get("matched_terms", [])
#         if any("indemnif" in t for t in terms):
#             recommendations.append("Review indemnification clauses – they may impose significant liability.")
#         if any("automatic renewal" in t for t in terms):
#             recommendations.append("Check automatic renewal terms to ensure easy exit if needed.")
#         if any("non-refundable" in t for t in terms):
#             recommendations.append("Non-refundable provisions may limit recourse on termination.")

#     if not recommendations:
#         recommendations.append("Overall risk appears manageable – still review all clauses carefully.")

#     return recommendations

# # --------------------------------------------------------------------
# # Local testing
# # --------------------------------------------------------------------
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)

#     sample_clauses = [
#         {
#             "id": 1,
#             "text": "The contractor shall indemnify and hold harmless the company from any claims without limitation.",
#             "type": "Liability"
#         },
#         {
#             "id": 2,
#             "text": "Payment shall be made within 30 days of invoice receipt.",
#             "type": "Payment"
#         },
#         {
#             "id": 3,
#             "text": "This agreement automatically renews for successive one-year terms unless terminated with 90 days notice.",
#             "type": "Renewal"
#         }
#     ]

#     print("Assessing risks for sample clauses...")
#     risk_assessment = assess_risks(sample_clauses)

#     print(f"\nContract Risk Level: {risk_assessment['contract_risk_level']}")
#     print(f"Contract Risk Score: {risk_assessment['contract_risk_score']:.3f}")
#     print(f"Risk Distribution: {risk_assessment['risk_distribution']}")

#     for clause_risk in risk_assessment["clause_risks"]:
#         print(f"\nClause {clause_risk['clause_id']}:")
#         print(f"  Risk Level: {clause_risk['risk_level']}")
#         print(f"  Risk Score: {clause_risk['risk_score']:.3f}")
#         print(f"  Matched Terms: {clause_risk['matched_terms']}")

#     recs = get_risk_recommendations(risk_assessment)
#     print("\nRecommendations:")
#     for r in recs:
#         print(f"  • {r}")


## File: backend/risk_detector.py
"""
Enhanced Legal Clause Risk Assessment and Scoring Module.
Fully compatible with updated clause_extractor output.
"""
import streamlit as st
import logging
import re
from typing import Dict, List
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# --------------------------------------------------------------------
# Load high-accuracy sentence transformer for legal/contract text
# --------------------------------------------------------------------
# try:
#     sentence_model = SentenceTransformer('all-mpnet-base-v2')
# except Exception as e:
#     logging.error(f"Failed to load sentence transformer: {e}")
#     raise
@st.cache_resource(show_spinner=False)
def _load_sentence_model():
    return SentenceTransformer('all-mpnet-base-v2')

try:
    sentence_model = _load_sentence_model()
except Exception as e:
    logging.error(f"Failed to load sentence transformer: {e}")
    raise


# --------------------------------------------------------------------
# Weighted risk keywords (key: phrase/regex, value: weight 0–1)
# --------------------------------------------------------------------
RISK_KEYWORDS = {
    r"\bindemnif(y|ication|ies)?\b": 1.0,
    r"\bliquidated damages\b": 0.9,
    r"\blimit(ed)? liability\b": 0.9,
    r"\bunlimited liability\b": 1.0,
    r"\bexclusive jurisdiction\b": 0.6,
    r"\bwithout liability\b": 0.8,
    r"\bautomatic renewal\b": 0.7,
    r"\bnon[- ]refundable\b": 0.6,
    r"\birrevocable\b": 0.6,
    r"\bperpetual\b": 0.7,
    r"\bwaive( right(s)?)?\b": 0.8,
    r"\bhold harmless\b": 1.0,
    r"\bas is\b": 0.5,
    r"\bno warranty\b": 0.7,
    r"\bfinal sale\b": 0.5,
    r"\bbinding arbitration\b": 0.7,
    r"\bclass action waiver\b": 0.9,
    r"\battorney(’s|s)? fees?\b": 0.5,
    r"\bconsequential damages\b": 0.8,
    r"\bpunitive damages\b": 0.9,
    r"\bspecific performance\b": 0.6,
    r"\bpenalt(y|ies)\b": 0.7,
    r"\bforfeit\b": 0.6,
    r"\bbreach\b": 0.5,
    r"\bdefault\b": 0.5
}

# --------------------------------------------------------------------
# Example risky clauses for semantic similarity
# --------------------------------------------------------------------
RISKY_EXAMPLES = [
    "The contractor shall indemnify and hold harmless the company from any claims or damages without limitation.",
    "This agreement automatically renews for successive terms unless terminated with 90 days notice.",
    "All fees are non-refundable and final upon payment regardless of termination.",
    "The company may terminate this agreement without notice for any reason or no reason.",
    "Contractor waives all rights to claim consequential or punitive damages.",
    "All disputes must be resolved through binding arbitration with no class action rights.",
    "Contractor assumes unlimited liability for any breach of confidentiality provisions."
]

# Precompute embeddings
RISKY_EMBEDDINGS = sentence_model.encode(
    RISKY_EXAMPLES, normalize_embeddings=True
)

# Clause type weighting
CLAUSE_TYPE_WEIGHTS = {
    "liability": 1.0,
    "indemnification": 1.0,
    "termination": 0.7,
    "renewal": 0.6,
    "payment": 0.4,
    "confidentiality": 0.5,
    "dispute resolution": 0.8
}

# --------------------------------------------------------------------
# Main API
# --------------------------------------------------------------------
def assess_risks(clauses: List[Dict]) -> Dict:
    """
    Assess risk levels for contract clauses and generate overall contract risk summary.
    """
    try:
        clause_risks = []
        total_risk_score = 0
        risk_counts = {"Low": 0, "Medium": 0, "High": 0}

        for clause in clauses:
            risk_assessment = _assess_clause_risk(clause)
            clause_risks.append(risk_assessment)
            total_risk_score += risk_assessment["risk_score"]
            risk_counts[risk_assessment["risk_level"]] += 1

        avg_risk_score = total_risk_score / len(clauses) if clauses else 0

        # 🔹 Subtle elevation if any high-risk clause exists
        if risk_counts["High"] > 0:
            avg_risk_score = min(avg_risk_score + 0.1, 1.0)

        contract_risk_level = _score_to_level(avg_risk_score)

        top_risky = sorted(
            clause_risks, key=lambda x: x["risk_score"], reverse=True
        )[:5]

        return {
            "clause_risks": clause_risks,
            "contract_risk_score": avg_risk_score,
            "contract_risk_level": contract_risk_level,
            "risk_distribution": risk_counts,
            "top_risky_clauses": top_risky,
            "total_clauses": len(clauses),
            "high_risk_count": risk_counts["High"],
            "medium_risk_count": risk_counts["Medium"],
            "low_risk_count": risk_counts["Low"]
        }

    except Exception as e:
        logging.error(f"Error in risk assessment: {e}")
        return {
            "clause_risks": [],
            "contract_risk_score": 0.0,
            "contract_risk_level": "Unknown",
            "risk_distribution": {"Low": 0, "Medium": 0, "High": 0},
            "top_risky_clauses": [],
            "total_clauses": 0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "low_risk_count": 0
        }

# --------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------
def _assess_clause_risk(clause: Dict) -> Dict:
    """
    Assess risk for a single clause.
    """
    text = clause["text"]
    text_lower = text.lower()

    # 1. Keyword-based risk scoring
    keyword_score, matched_terms = _keyword_risk_score(text_lower)

    # 2. Semantic similarity
    try:
        clause_embedding = sentence_model.encode(
            [text], normalize_embeddings=True
        )
        similarities = cosine_similarity(
            clause_embedding, RISKY_EMBEDDINGS
        )[0]
        max_similarity = float(np.max(similarities))

        # 🔹 Boost very strong semantic matches
        if max_similarity > 0.75:
            max_similarity = min(max_similarity + 0.05, 1.0)

    except Exception as e:
        logging.warning(f"Similarity computation error: {e}")
        max_similarity = 0.0

    # 3. Length/complexity factor
    length_factor = min(len(text) / 300.0, 2.0) / 2.0

    # 4. Clause type boost
    clause_type = clause.get("type", "").lower()
    type_boost = CLAUSE_TYPE_WEIGHTS.get(clause_type, 0.0)

    # 🔹 Extra realism for liability-heavy clauses
    if clause_type in {"liability", "indemnification"}:
        type_boost = min(type_boost + 0.1, 1.0)

    # Combined weighted score
    raw_score = (
        0.5 * keyword_score +
        0.3 * max_similarity +
        0.1 * length_factor +
        0.1 * type_boost
    )

    risk_level = _score_to_level(raw_score)

    return {
        "clause_id": clause.get("id"),
        "risk_score": raw_score,
        "risk_level": risk_level,
        "matched_terms": matched_terms,
        "keyword_score": keyword_score,
        "similarity_score": max_similarity,
        "length_factor": length_factor,
        "type_boost": type_boost
    }

def _keyword_risk_score(text: str):
    """
    Compute keyword risk score using weighted regex matching.
    """
    matched_terms = []
    total_weight = 0
    high_weight_hits = 0

    for pattern, weight in RISK_KEYWORDS.items():
        if re.search(pattern, text, re.IGNORECASE):
            matched_terms.append(pattern.strip(r"\b"))
            total_weight += weight
            if weight >= 0.8:
                high_weight_hits += 1

    keyword_score = min(total_weight / 5.0, 1.0)

    # 🔹 Boost when multiple strong legal signals appear together
    if high_weight_hits >= 2:
        keyword_score = min(keyword_score + 0.1, 1.0)

    return keyword_score, matched_terms

def _score_to_level(score: float) -> str:
    """
    Convert numerical score to categorical level.
    """
    if score < 0.3:
        return "Low"
    elif score < 0.6:
        return "Medium"
    else:
        return "High"

# --------------------------------------------------------------------
# Recommendations generator
# --------------------------------------------------------------------
def get_risk_recommendations(risk_summary: Dict) -> List[str]:
    """
    Generate actionable recommendations.
    """
    recommendations = []

    if risk_summary["contract_risk_level"] == "High":
        recommendations.append(
            "⚠️ HIGH overall contract risk – seek legal review before signing."
        )

    if risk_summary["high_risk_count"] > 0:
        recommendations.append(
            f"{risk_summary['high_risk_count']} high-risk clauses detected that need urgent attention."
        )

    for clause_risk in risk_summary["top_risky_clauses"][:3]:
        terms = clause_risk.get("matched_terms", [])
        if any("indemnif" in t for t in terms):
            recommendations.append(
                "Review indemnification clauses – they may impose significant liability."
            )
        if any("automatic renewal" in t for t in terms):
            recommendations.append(
                "Check automatic renewal terms to ensure easy exit if needed."
            )
        if any("non-refundable" in t for t in terms):
            recommendations.append(
                "Non-refundable provisions may limit recourse on termination."
            )

    if not recommendations:
        recommendations.append(
            "Overall risk appears manageable – still review all clauses carefully."
        )

    return recommendations

# --------------------------------------------------------------------
# Local testing
# --------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sample_clauses = [
        {
            "id": 1,
            "text": "The contractor shall indemnify and hold harmless the company from any claims without limitation.",
            "type": "Liability"
        },
        {
            "id": 2,
            "text": "Payment shall be made within 30 days of invoice receipt.",
            "type": "Payment"
        },
        {
            "id": 3,
            "text": "This agreement automatically renews for successive one-year terms unless terminated with 90 days notice.",
            "type": "Renewal"
        }
    ]

    print("Assessing risks for sample clauses...")
    risk_assessment = assess_risks(sample_clauses)

    print(f"\nContract Risk Level: {risk_assessment['contract_risk_level']}")
    print(f"Contract Risk Score: {risk_assessment['contract_risk_score']:.3f}")
    print(f"Risk Distribution: {risk_assessment['risk_distribution']}")

    for clause_risk in risk_assessment["clause_risks"]:
        print(f"\nClause {clause_risk['clause_id']}:")
        print(f"  Risk Level: {clause_risk['risk_level']}")
        print(f"  Risk Score: {clause_risk['risk_score']:.3f}")
        print(f"  Matched Terms: {clause_risk['matched_terms']}")

    recs = get_risk_recommendations(risk_assessment)
    print("\nRecommendations:")
    for r in recs:
        print(f"  • {r}")

