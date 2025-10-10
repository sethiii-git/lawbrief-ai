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

---


## 💡 How It Works

The application is structured into a **backend processing engine** and a **frontend user interface**.

### Backend
- **utils.py**: Handles document loading (PDF/DOCX) and text cleaning.  
- **clause_extractor.py**: Uses spaCy and sentence transformers to split the document into clauses, classify their type (e.g., "Termination", "Payment"), and extract named entities (like dates, organizations, monetary values).  
- **risk_detector.py**: Analyzes each clause for risky keywords and semantic meaning, assigning a risk score and level (Low, Medium, High).  
- **summarizer.py**: Employs abstractive and extractive summarization models to generate short, long, and executive-level summaries.  
- **report_generator.py**: Creates professional, downloadable reports of the analysis in PDF and DOCX formats.  

### Frontend
- **app.py**: The main Streamlit application that provides the user interface for uploading documents and viewing the analysis.  
- **components/**: Reusable Streamlit components for displaying the clause table, risk charts, and summary cards in a clean and interactive way.  

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve LawBrief AI, please follow these steps:

1. Fork the repository.  
2. Create a new branch (`git checkout -b feature/your-feature-name`).  
3. Make your changes.  
4. Commit your changes (`git commit -m 'Add some amazing feature'`).  
5. Push to the branch (`git push origin feature/your-feature-name`).  
6. Open a Pull Request.  

---

## 📜 License

This project is licensed under the MIT License. See the LICENSE file for details.

> **Disclaimer:** This tool provides informational analysis only and does not constitute legal advice. Always consult a qualified legal professional for assistance with legal matters.



