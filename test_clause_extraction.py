from backend.utils import load_pdf
from backend.clause_extractor import extract_clauses

def test_pdf_clause_extraction(pdf_path):
    data = load_pdf(pdf_path)
    full_text = data["full_text"]
    clauses = extract_clauses(full_text)

    for c in clauses:
        print(f"ID: {c['id']}")
        print(f"Title: {c['title']}")
        print(f"Type: {c['type']} (Confidence: {c['confidence']})")
        print(f"Text: {c['text'][:300]}")  # first 300 chars
        print(f"Entities: {c['entities']}")
        print("="*60)

if __name__ == "__main__":
    path = "C:/Users/smach/OneDrive/Desktop/sample_contract.pdf"  # change to your PDF path
    test_pdf_clause_extraction(path)
