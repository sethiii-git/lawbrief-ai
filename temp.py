import pdfplumber

path = r"C:\Users\smach\OneDrive\Desktop\sample_contract.pdf"

with pdfplumber.open(path) as pdf:
    full_text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        print(f"Page text: {repr(page_text)}")  # Check if None or empty
        if page_text:
            full_text += page_text + "\n\n"

print("Full text length:", len(full_text))
print(full_text[:1000])  # Print first 1000 chars
