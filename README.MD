# LawBrief AI ⚖️
**"Law, Simplified"**

LawBrief AI is a powerful, offline-first legal document analyzer designed to demystify complex contracts. It leverages advanced NLP models to extract clauses, assess risks, and generate insightful summaries, all while ensuring your data remains private and secure on your local machine.

---

## ✨ Features

- 📄 **PDF & DOCX Support**: Upload and analyze standard legal document formats.  
- 🔍 **Smart Clause Extraction**: Automatically identifies and categorizes clauses (e.g., Termination, Payment, Liability).  
- ⚠️ **In-Depth Risk Assessment**: Scores clauses for potential risk and highlights concerning terms.  
- 📊 **Visual Analytics**: Interactive charts and graphs to visualize risk distribution and scores.  
- 📝 **Executive Summaries**: Generates concise, executive-level summaries of the entire document.  
- 📑 **Professional Reports**: Creates and downloads comprehensive analysis reports in both PDF and DOCX formats.  
- 🔒 **Offline & Secure**: All processing happens on your local machine. Your documents are never uploaded to the cloud.  

---

## 🛠️ Tech Stack

**Backend:** Python, spaCy, Sentence-Transformers, Transformers (Hugging Face), NLTK, scikit-learn  
**Frontend:** Streamlit  
**File Processing:** pdfplumber, python-docx  
**Report Generation:** reportlab, python-docx  
**Visualization:** Matplotlib  

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Pip

### Installation
1. Clone the repository:

```bash
git clone https://github.com/sethiii-git/lawbrief-ai.git
cd lawbrief-ai
```

2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Run the appication:

```bash
streamlit run frontend/app.py
```

4.Open your web browser and navigate to the local URL provided by Streamlit (usually http://localhost:8501).
