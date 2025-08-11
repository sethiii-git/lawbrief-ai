# File: frontend/components/clause_table.py
"""
Interactive clause table component for displaying contract clauses.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List

def render_clause_table(clauses: List[Dict], clause_risks: List[Dict]) -> None:
    """
    Render an interactive table of contract clauses.
    
    Args:
        clauses: List of extracted clause dictionaries
        clause_risks: List of risk assessment dictionaries
    """
    if not clauses:
        st.warning("No clauses found to display")
        return
    
    # Create risk lookup dictionary
    risk_lookup = {risk["clause_id"]: risk for risk in clause_risks}
    
    # Prepare table data
    table_data = []
    for clause in clauses:
        risk_info = risk_lookup.get(clause["id"], {})
        
        # Format entities
        entities_text = ""
        if clause.get("entities"):
            entity_strs = [f"{ent['text']} ({ent['label']})" for ent in clause["entities"]]
            entities_text = ", ".join(entity_strs[:3])
            if len(clause["entities"]) > 3:
                entities_text += f" +{len(clause['entities']) - 3} more"
        
        # Preview text (first 100 characters)
        preview = clause["text"][:100] + "..." if len(clause["text"]) > 100 else clause["text"]
        
        table_data.append({
            "ID": clause["id"],
            "Type": clause["type"],
            "Risk Level": risk_info.get("risk_level", "Unknown"),
            "Risk Score": f"{risk_info.get('risk_score', 0):.3f}",
            "Entities": entities_text,
            "Preview": preview,
            "Full Text": clause["text"]  # Hidden column for expandable view
        })
    
    # Create DataFrame
    df = pd.DataFrame(table_data)
    
    # Display table with selection
    st.markdown("**Select clauses to view details:**")
    
    # Color code risk levels
    def highlight_risk(row):
        if row['Risk Level'] == 'High':
            return ['background-color: #ffebee'] * len(row)
        elif row['Risk Level'] == 'Medium':
            return ['background-color: #fff3e0'] * len(row)
        elif row['Risk Level'] == 'Low':
            return ['background-color: #e8f5e8'] * len(row)
        else:
            return [''] * len(row)
    
    # Display styled dataframe (excluding Full Text column)
    display_df = df.drop('Full Text', axis=1)
    styled_df = display_df.style.apply(highlight_risk, axis=1)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Expandable clause details
    st.markdown("---")
    st.markdown("**📖 Clause Details**")
    
    # Risk level filter
    risk_levels = ["All"] + sorted(df["Risk Level"].unique().tolist())
    selected_risk = st.selectbox("Filter by Risk Level:", risk_levels)
    
    # Filter clauses based on selection
    filtered_clauses = clauses
    if selected_risk != "All":
        filtered_clause_ids = df[df["Risk Level"] == selected_risk]["ID"].tolist()
        filtered_clauses = [c for c in clauses if c["id"] in filtered_clause_ids]
    
    # Display detailed clause information
    for clause in filtered_clauses:
        risk_info = risk_lookup.get(clause["id"], {})
        
        # Risk level emoji
        risk_emoji = {
            "High": "🔴",
            "Medium": "🟡", 
            "Low": "🟢"
        }.get(risk_info.get("risk_level", "Unknown"), "⚪")
        
        with st.expander(
            f"{risk_emoji} **Clause {clause['id']}: {clause['type']}** "
            f"(Risk: {risk_info.get('risk_level', 'Unknown')})"
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**Clause Text:**")
                st.write(clause["text"])
                
                # Copy button for clause text
                if st.button(f"📋 Copy Text", key=f"copy_{clause['id']}"):
                    st.code(clause["text"], language=None)
                    st.success("Text ready to copy from code block above!")
            
            with col2:
                st.markdown("**Details:**")
                
                # Risk information
                if risk_info:
                    st.metric(
                        "Risk Score",
                        f"{risk_info.get('risk_score', 0):.3f}",
                        delta=risk_info.get('risk_level', 'Unknown')
                    )
                    
                    if risk_info.get("matched_terms"):
                        st.markdown("**Concerning Terms:**")
                        for term in risk_info["matched_terms"]:
                            st.markdown(f"- `{term}`")
                
                # Entities
                if clause.get("entities"):
                    st.markdown("**Entities Found:**")
                    for entity in clause["entities"]:
                        st.markdown(f"- **{entity['text']}** ({entity['label']})")
                
                # Clause metadata
                st.markdown("**Metadata:**")
                st.json({
                    "Clause ID": clause["id"],
                    "Type": clause["type"],
                    "Character Count": len(clause["text"]),
                    "Word Count": len(clause["text"].split())
                })

def render_clause_search(clauses: List[Dict]) -> List[Dict]:
    """
    Render a search interface for clauses.
    
    Args:
        clauses: List of clause dictionaries
        
    Returns:
        Filtered list of clauses
    """
    st.markdown("### 🔍 Search Clauses")
    
    # Search input
    search_term = st.text_input(
        "Search in clause text:",
        placeholder="Enter keywords to search..."
    )
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        clause_types = ["All Types"] + sorted(set(clause["type"] for clause in clauses))
        selected_type = st.selectbox("Filter by Type:", clause_types)
    
    with col2:
        # Entity filter
        all_entities = set()
        for clause in clauses:
            for entity in clause.get("entities", []):
                all_entities.add(entity["label"])
        
        entity_labels = ["All Entities"] + sorted(all_entities)
        selected_entity = st.selectbox("Filter by Entity Type:", entity_labels)
    
    # Apply filters
    filtered_clauses = clauses
    
    # Text search
    if search_term:
        filtered_clauses = [
            clause for clause in filtered_clauses
            if search_term.lower() in clause["text"].lower()
        ]
    
    # Type filter
    if selected_type != "All Types":
        filtered_clauses = [
            clause for clause in filtered_clauses
            if clause["type"] == selected_type
        ]
    
    # Entity filter
    if selected_entity != "All Entities":
        filtered_clauses = [
            clause for clause in filtered_clauses
            if any(entity["label"] == selected_entity for entity in clause.get("entities", []))
        ]
    
    # Display results count
    if len(filtered_clauses) != len(clauses):
        st.info(f"Found {len(filtered_clauses)} clauses matching your criteria")
    
    return filtered_clauses

if __name__ == "__main__":
    # Demo functionality
    st.title("Clause Table Component Demo")
    
    # Sample data
    sample_clauses = [
        {
            "id": 1,
            "type": "Termination",
            "text": "This agreement may be terminated by either party with thirty (30) days written notice.",
            "entities": [{"text": "thirty (30) days", "label": "DATE", "start": 55, "end": 71}]
        },
        {
            "id": 2,
            "type": "Payment",
            "text": "Company ABC shall pay Contractor XYZ the sum of $10,000 within 30 days of invoice receipt.",
            "entities": [
                {"text": "Company ABC", "label": "ORG", "start": 0, "end": 11},
                {"text": "Contractor XYZ", "label": "ORG", "start": 22, "end": 36},
                {"text": "$10,000", "label": "MONEY", "start": 49, "end": 56}
            ]
        }
    ]
    
    sample_risks = [
        {"clause_id": 1, "risk_level": "Low", "risk_score": 0.2, "matched_terms": []},
        {"clause_id": 2, "risk_level": "Medium", "risk_score": 0.4, "matched_terms": ["payment"]}
    ]
    
    # Render components
    render_clause_table(sample_clauses, sample_risks)
    
    st.markdown("---")
    
    filtered_clauses = render_clause_search(sample_clauses)
    st.write(f"Search returned {len(filtered_clauses)} clauses")
