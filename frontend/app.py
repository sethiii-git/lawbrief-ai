# File: frontend/app.py
"""
LawBrief AI - Main Streamlit Application
A comprehensive legal document analyzer with offline-first capabilities.
"""

import os
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st
import pandas as pd

# Backend imports

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from backend.utils import load_pdf, load_docx, clean_text, setup_logging

from backend.utils import load_pdf, load_docx, clean_text, setup_logging
from backend.clause_extractor import extract_clauses
from backend.risk_detector import assess_risks, get_risk_recommendations
from backend.summarizer import summarize_document, generate_executive_summary
from backend.report_generator import generate_pdf_report, generate_docx_report

# Frontend components
from components.clause_table import render_clause_table
from components.risk_chart import create_risk_chart
from components.summary_card import render_summary_card

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="LawBrief AI - Legal Document Analyzer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)
# st.markdown("""
# <div style="text-align:center; font-size:14px;">
#   <a href="https://www.linkedin.com/in/machint-sethi-9573b6254/" target="_blank" style="text-decoration:none; display:inline-flex; align-items:center; gap:5px;">
#     Made with ❤️ by Machint Sethi
#     <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#0A66C2" viewBox="0 0 24 24">
#       <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.028-3.039-1.852-3.039-1.854 0-2.137 1.445-2.137 2.939v5.669h-3.554V9h3.413v1.561h.049c.476-.9 1.635-1.852 3.363-1.852 3.598 0 4.263 2.368 4.263 5.451v6.292zM5.337 7.433c-1.144 0-2.069-.928-2.069-2.071 0-1.144.925-2.071 2.069-2.071 1.145 0 2.07.927 2.07 2.071 0 1.143-.925 2.071-2.07 2.071zm1.777 13.019H3.56V9h3.554v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.228.792 24 1.771 24h20.451C23.2 24 24 23.228 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/>
#     </svg>
#   </a>
# </div>
# """, unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; font-size:16px; display:flex; justify-content:center; gap:15px; align-items:center; margin-top:20px;">
  <span>Made with ❤️ by Machint Sethi</span>
  <a href="https://www.linkedin.com/in/machint-sethi-9573b6254/" target="_blank" style="text-decoration:none; display:inline-flex; align-items:center; gap:5px; color:#0A66C2;">
    LinkedIn
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#0A66C2" viewBox="0 0 24 24">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.028-3.039-1.852-3.039-1.854 0-2.137 1.445-2.137 2.939v5.669h-3.554V9h3.413v1.561h.049c.476-.9 1.635-1.852 3.363-1.852 3.598 0 4.263 2.368 4.263 5.451v6.292zM5.337 7.433c-1.144 0-2.069-.928-2.069-2.071 0-1.144.925-2.071 2.069-2.071 1.145 0 2.07.927 2.07 2.071 0 1.143-.925 2.071-2.07 2.071zm1.777 13.019H3.56V9h3.554v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.228.792 24 1.771 24h20.451C23.2 24 24 23.228 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/>
    </svg>
  </a>
  <a href="https://github.com/sethiii-git" target="_blank" style="text-decoration:none; display:inline-flex; align-items:center; gap:5px; color:#0A66C2;">
    GitHub
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
      <path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 005.47 7.59c.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2 .37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.58.82-2.14-.08-.2-.36-1.02.08-2.12 0 0 .67-.22 2.2.82a7.63 7.63 0 012 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.14 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.19 0 .21.15.46.55.38A8 8 0 0016 8c0-4.42-3.58-8-8-8z"/>
    </svg>
  </a>
</div>
""", unsafe_allow_html=True)

# Load custom CSS
def load_css():
    """Load custom CSS styling."""
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@st.cache_resource
def load_models():
    """Load NLP models with caching."""
    try:
        # Import here to trigger model loading
        from backend.clause_extractor import nlp, sentence_model
        from backend.risk_detector import sentence_model as risk_model  
        from backend.summarizer import abstractive_summarizer
        return True
    except Exception as e:
        st.error(f"Error loading models: {e}")
        logger.error(f"Model loading error: {e}")
        return False
# @st.cache_data
# def process_document(file_content: bytes, filename: str) -> Dict:
    # """
    # Process uploaded document with caching.
    
    # Args:
    #     file_content: Binary content of uploaded file
    #     filename: Name of the uploaded file
        
    # Returns:
    #     Dictionary with processing results
    # """
    # tmp_path = None  # Initialize to ensure scope in finally block
    # try:
    #     # Save uploaded file temporarily
    #     with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
    #         tmp_file.write(file_content)
    #         tmp_path = tmp_file.name
        
    #     # Extract text based on file type
    #     if filename.lower().endswith('.pdf'):
    #         pdf_data = load_pdf(tmp_path)
    #         raw_text = pdf_data.get("full_text")
    #     elif filename.lower().endswith('.docx'):
    #         docx_data = load_docx(tmp_path)
    #         raw_text = docx_data.get("full_text")
    #     else:
    #         raise ValueError("Unsupported file format")

    #     # Validate extracted text
    #     # if raw_text is None or not isinstance(raw_text, str) or not raw_text.strip():
    #     #     raise ValueError("Failed to extract any text from the document")
    #     if raw_text is None:
    #         raise ValueError("Extracted raw_text is None")
    #     if not isinstance(raw_text, str):
    #         raise ValueError(f"Extracted raw_text is not a string, but {type(raw_text)}")
    #     if not raw_text.strip():
    #         raise ValueError("Extracted raw_text is empty or whitespace only")

    #     # Clean text
    #     clean_text_content = clean_text(raw_text)

    #     # Extract clauses
    #     clauses = extract_clauses(clean_text_content)
        
    #     # Assess risks
    #     risk_summary = assess_risks(clauses)
        
    #     # Generate summaries
    #     summaries = summarize_document(clean_text_content, mode="hybrid", clauses=clauses)
        
    #     # Create metadata
    #     metadata = {
    #         "filename": filename,
    #         "file_size": f"{len(file_content) / 1024:.1f} KB",
    #         "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #         "total_clauses": len(clauses),
    #         "total_characters": len(clean_text_content)
    #     }

    #     # Cleanup temp file
    #     if tmp_path and os.path.exists(tmp_path):
    #         os.unlink(tmp_path)
        
    #     return {
    #         "success": True,
    #         "metadata": metadata,
    #         "raw_text": raw_text,
    #         "clean_text": clean_text_content,
    #         "clauses": clauses,
    #         "risk_summary": risk_summary,
    #         "summaries": summaries
    #     }
        
    # except Exception as e:
    #     logger.error(f"Document processing error: {e}")
    #     if tmp_path and os.path.exists(tmp_path):
    #         os.unlink(tmp_path)
    #     return {"success": False, "error": str(e)}

# @st.cache_data
# def process_document(file_content: bytes, filename: str) -> Dict:
#     """
#     Process uploaded document with caching.
    
#     Args:
#         file_content: Binary content of uploaded file
#         filename: Name of the uploaded file
        
#     Returns:
#         Dictionary with processing results
#     """
#     try:
#         # Save uploaded file temporarily
#         with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
#             tmp_file.write(file_content)
#             tmp_path = tmp_file.name
        
#         # # Extract text based on file type
#         # if filename.lower().endswith('.pdf'):
#         #     raw_text = load_pdf(tmp_path)
#         # elif filename.lower().endswith('.docx'):
#         #     raw_text = load_docx(tmp_path)
#         # else:
#         #     raise ValueError("Unsupported file format")
        
#         # # Clean text
#         # clean_text_content = clean_text(raw_text)

#         if filename.lower().endswith('.pdf'):
#             pdf_data = load_pdf(tmp_path)
#             raw_text = pdf_data.get("full_text", "")
#         elif filename.lower().endswith('.docx'):
#             docx_data = load_docx(tmp_path)
#             raw_text = docx_data.get("full_text", "")
#         else:
#             raise ValueError("Unsupported file format")

#         if not isinstance(raw_text, str) or not raw_text.strip():
#             raise ValueError("Failed to extract any text from the document")

#         clean_text_content = clean_text(raw_text)

        
#         # Extract clauses
#         clauses = extract_clauses(clean_text_content)
        
#         # Assess risks
#         risk_summary = assess_risks(clauses)
        
#         # Generate summaries
#         summaries = summarize_document(clean_text_content, mode="hybrid", clauses=clauses)
        
#         # Create metadata
#         metadata = {
#             "filename": filename,
#             "file_size": f"{len(file_content) / 1024:.1f} KB",
#             "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "total_clauses": len(clauses),
#             "total_characters": len(clean_text_content)
#         }
        
#         # Cleanup
#         os.unlink(tmp_path)
        
#         return {
#             "success": True,
#             "metadata": metadata,
#             "raw_text": raw_text,
#             "clean_text": clean_text_content,
#             "clauses": clauses,
#             "risk_summary": risk_summary,
#             "summaries": summaries
#         }
        
#     except Exception as e:
#         logger.error(f"Document processing error: {e}")
#         if 'tmp_path' in locals() and os.path.exists(tmp_path):
#             os.unlink(tmp_path)
#         return {"success": False, "error": str(e)}

@st.cache_data
def process_document(file_content: bytes, filename: str) -> Dict:
    import logging
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        
        if filename.lower().endswith('.pdf'):
            pdf_data = load_pdf(tmp_path)
            raw_text = pdf_data.get("full_text")
        elif filename.lower().endswith('.docx'):
            docx_data = load_docx(tmp_path)
            raw_text = docx_data.get("full_text")
        else:
            raise ValueError("Unsupported file format")

        logging.debug(f"Raw text type: {type(raw_text)}; length: {len(raw_text) if raw_text else 'None'}")

        # Defensive: convert None to empty string before stripping
        if raw_text is None:
            raise ValueError("Extracted raw_text is None")
        if not isinstance(raw_text, str):
            raise ValueError(f"Extracted raw_text is not a string, but {type(raw_text)}")
        if not raw_text.strip():
            raise ValueError("Extracted raw_text is empty or whitespace only")

        clean_text_content = clean_text(raw_text)

        clauses = extract_clauses(clean_text_content)
        risk_summary = assess_risks(clauses)
        summaries = summarize_document(clean_text_content, mode="hybrid", clauses=clauses)

        metadata = {
            "filename": filename,
            "file_size": f"{len(file_content) / 1024:.1f} KB",
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_clauses": len(clauses),
            "total_characters": len(clean_text_content)
        }

        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

        return {
            "success": True,
            "metadata": metadata,
            "raw_text": raw_text,
            "clean_text": clean_text_content,
            "clauses": clauses,
            "risk_summary": risk_summary,
            "summaries": summaries
        }

    except Exception as e:
        logging.error(f"Document processing error: {e}", exc_info=True)
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return {"success": False, "error": str(e)}

def main():
    """Main application function."""
    
    # Load CSS
    load_css()
    
    # Header
    st.title("⚖️ LawBrief AI")
    st.markdown("**Professional Legal Document Analysis - Offline & Secure**")
    
    # Sidebar
    with st.sidebar:
        st.image(os.path.join(os.path.dirname(__file__), "assets", "logo.png"), width=150)
        st.markdown("---")
        st.markdown("### About")
        st.info(
            "LawBrief AI analyzes legal contracts using advanced NLP to extract clauses, "
            "assess risks, and generate comprehensive reports. All processing happens offline "
            "to ensure your documents remain private and secure."
        )
        
        st.markdown("### Features")
        st.markdown(
            "- 📄 PDF & DOCX Support\n"
            "- 🔍 Smart Clause Extraction\n" 
            "- ⚠️ Risk Assessment\n"
            "- 📊 Visual Analytics\n"
            "- 📋 Executive Summaries\n"
            "- 📑 Professional Reports"
        )
        
        st.markdown("---")
        st.markdown("### Model Status")
        
    # Check if models are loaded
    if not load_models():
        st.error("❌ **Models not loaded**")
        st.markdown(
            "Please ensure you have downloaded the required models. "
            "See the README.md for installation instructions."
        )
        st.stop()
    else:
        with st.sidebar:
            st.success("✅ Models loaded successfully")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📤 Upload Contract")
        uploaded_file = st.file_uploader(
            "Choose a PDF or DOCX file",
            type=['pdf', 'docx'],
            help="Upload your legal contract for analysis"
        )
        
        if uploaded_file is not None:
            # Display file info
            file_size = len(uploaded_file.getvalue()) / 1024
            st.success(f"✅ **{uploaded_file.name}** uploaded ({file_size:.1f} KB)")
            
            # Analysis button
            if st.button("🔍 **Analyze Contract**", type="primary"):
                
                with st.spinner("🤖 Analyzing contract... This may take a moment."):
                    
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Update progress
                    status_text.text("📄 Extracting text from document...")
                    progress_bar.progress(20)
                    
                    # Process document
                    result = process_document(uploaded_file.getvalue(), uploaded_file.name)
                    
                    if not result["success"]:
                        st.error(f"❌ **Analysis failed:** {result['error']}")
                        st.stop()
                    
                    status_text.text("🔍 Extracting clauses...")
                    progress_bar.progress(50)
                    
                    status_text.text("⚠️ Assessing risks...")
                    progress_bar.progress(75)
                    
                    status_text.text("📝 Generating summaries...")
                    progress_bar.progress(90)
                    
                    status_text.text("✅ Analysis complete!")
                    progress_bar.progress(100)
                    
                    # Store results in session state
                    st.session_state.analysis_result = result
                    st.session_state.uploaded_filename = uploaded_file.name
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        if "analysis_result" in st.session_state:
            result = st.session_state.analysis_result
            metadata = result["metadata"]
            risk_summary = result["risk_summary"]
            
            # Quick stats metrics
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Total Clauses", metadata["total_clauses"])
                st.metric("File Size", metadata["file_size"])
            with col_b:
                st.metric("Risk Level", risk_summary["contract_risk_level"])
                st.metric("High Risk", risk_summary["high_risk_count"])
        else:
            st.info("Upload and analyze a contract to see statistics")
    
    # Results section
    if "analysis_result" in st.session_state:
        result = st.session_state.analysis_result
        
        st.markdown("---")
        st.markdown("## 📋 Analysis Results")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Summary", "⚠️ Risk Analysis", "📄 Clauses", "📊 Charts", "📑 Reports"])
        
        with tab1:
            st.markdown("### Executive Summary")
            render_summary_card(result["summaries"], result["risk_summary"])
            
            # Key findings
            st.markdown("### Key Findings")
            exec_summary = generate_executive_summary(result["clauses"], result["risk_summary"])
            st.info(exec_summary)
            
        with tab2:
            st.markdown("### Risk Assessment Overview")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Overall Risk Level",
                    result["risk_summary"]["contract_risk_level"],
                    delta=f"Score: {result['risk_summary']['contract_risk_score']:.3f}"
                )
            with col2:
                st.metric("High Risk Clauses", result["risk_summary"]["high_risk_count"])
            with col3:
                st.metric("Medium Risk Clauses", result["risk_summary"]["medium_risk_count"])
            
            # Risk recommendations
            st.markdown("### Risk Recommendations")
            recommendations = get_risk_recommendations(result["risk_summary"])
            for i, rec in enumerate(recommendations, 1):
                st.warning(f"**{i}.** {rec}")
            
            # Top risky clauses
            st.markdown("### Top Risk Clauses")
            top_risky = result["risk_summary"]["top_risky_clauses"][:5]
            
            for clause_risk in top_risky:
                clause = next(c for c in result["clauses"] if c["id"] == clause_risk["clause_id"])
                
                with st.expander(
                    f"🚨 Clause {clause['id']}: {clause['type']} - {clause_risk['risk_level']} Risk"
                ):
                    st.markdown(f"**Risk Score:** {clause_risk['risk_score']:.3f}")
                    if clause_risk["matched_terms"]:
                        st.markdown(f"**Concerning Terms:** {', '.join(clause_risk['matched_terms'])}")
                    st.markdown(f"**Text:** {clause['text']}")
        
        with tab3:
            st.markdown("### Contract Clauses")
            render_clause_table(result["clauses"], result["risk_summary"]["clause_risks"])
        
        with tab4:
            st.markdown("### Risk Visualization")
            
            # Risk distribution chart
            fig = create_risk_chart(result["risk_summary"])
            if fig:
                st.pyplot(fig)
            
            # Risk scores by clause
            st.markdown("### Risk Scores by Clause")
            clause_data = []
            for clause in result["clauses"]:
                clause_risk = next(
                    (r for r in result["risk_summary"]["clause_risks"] if r["clause_id"] == clause["id"]),
                    {"risk_score": 0, "risk_level": "Unknown"}
                )
                clause_data.append({
                    "Clause ID": clause["id"],
                    "Type": clause["type"], 
                    "Risk Score": clause_risk["risk_score"],
                    "Risk Level": clause_risk["risk_level"]
                })
            
            df = pd.DataFrame(clause_data)
            st.bar_chart(data=df.set_index("Clause ID")["Risk Score"])
        
        with tab5:
            st.markdown("### Download Reports")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📑 Generate PDF Report"):
                    with st.spinner("Generating PDF report..."):
                        try:
                            pdf_path = f"temp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            generate_pdf_report(
                                pdf_path,
                                result["metadata"],
                                result["clauses"],
                                result["risk_summary"],
                                result["summaries"]
                            )
                            
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label="📥 Download PDF Report",
                                    data=f.read(),
                                    file_name=f"lawbrief_report_{st.session_state.uploaded_filename.split('.')[0]}.pdf",
                                    mime="application/pdf"
                                )
                            
                            os.unlink(pdf_path)
                            st.success("✅ PDF report ready for download!")
                            
                        except Exception as e:
                            st.error(f"❌ PDF generation failed: {e}")
            
            with col2:
                if st.button("📄 Generate DOCX Report"):
                    with st.spinner("Generating DOCX report..."):
                        try:
                            docx_path = f"temp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                            generate_docx_report(
                                docx_path,
                                result["metadata"],
                                result["clauses"],
                                result["risk_summary"],
                                result["summaries"]
                            )
                            
                            with open(docx_path, "rb") as f:
                                st.download_button(
                                    label="📥 Download DOCX Report",
                                    data=f.read(),
                                    file_name=f"lawbrief_report_{st.session_state.uploaded_filename.split('.')[0]}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                            
                            os.unlink(docx_path)
                            st.success("✅ DOCX report ready for download!")
                            
                        except Exception as e:
                            st.error(f"❌ DOCX generation failed: {e}")
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            "<div style='text-align: center; color: #666; font-size: 0.9em;'>"
            "⚖️ LawBrief AI - Professional Legal Document Analysis<br>"
            "<b>Disclaimer:</b> This tool provides informational analysis only. "
            "Always consult qualified legal professionals for legal advice."
            "</div>",
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
