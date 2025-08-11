# File: frontend/components/summary_card.py
"""
Summary card component for displaying contract summaries and key insights.
"""

import streamlit as st
from typing import Dict, List, Optional

def render_summary_card(summaries: Dict, risk_summary: Dict) -> None:
    """
    Render summary cards with contract analysis results.
    
    Args:
        summaries: Dictionary containing short_summary, long_summary, etc.
        risk_summary: Risk assessment summary dictionary
    """
    # Executive Summary Card
    with st.container():
        st.markdown("#### 📋 Executive Summary")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Short summary
            st.markdown("**Quick Overview:**")
            summary_text = summaries.get("short_summary", "No summary available")
            st.info(summary_text)
            
            # Show/hide detailed summary
            with st.expander("📖 **View Detailed Summary**"):
                detailed_summary = summaries.get("long_summary", "No detailed summary available")
                st.write(detailed_summary)
        
        with col2:
            # Key metrics
            st.markdown("**Key Metrics**")
            
            risk_level = risk_summary.get("contract_risk_level", "Unknown")
            risk_color = {
                "Low": "🟢",
                "Medium": "🟡", 
                "High": "🔴"
            }.get(risk_level, "⚪")
            
            st.metric(
                "Risk Level",
                f"{risk_color} {risk_level}",
                delta=f"Score: {risk_summary.get('contract_risk_score', 0):.3f}"
            )
            
            st.metric(
                "Total Clauses",
                risk_summary.get('total_clauses', 0)
            )
            
            st.metric(
                "High Risk Items",
                risk_summary.get('high_risk_count', 0),
                delta="Critical" if risk_summary.get('high_risk_count', 0) > 0 else "Good"
            )

def render_risk_insights_card(risk_summary: Dict, top_entities: List[Dict] = None) -> None:
    """
    Render a card with risk insights and recommendations.
    
    Args:
        risk_summary: Risk assessment summary
        top_entities: Optional list of top entities found in contract
    """
    st.markdown("#### ⚠️ Risk Insights")
    
    # Risk distribution
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🔴 High Risk",
            risk_summary.get('high_risk_count', 0),
            delta=f"{risk_summary.get('high_risk_count', 0)/risk_summary.get('total_clauses', 1)*100:.1f}%"
        )
    
    with col2:
        st.metric(
            "🟡 Medium Risk", 
            risk_summary.get('medium_risk_count', 0),
            delta=f"{risk_summary.get('medium_risk_count', 0)/risk_summary.get('total_clauses', 1)*100:.1f}%"
        )
    
    with col3:
        st.metric(
            "🟢 Low Risk",
            risk_summary.get('low_risk_count', 0),
            delta=f"{risk_summary.get('low_risk_count', 0)/risk_summary.get('total_clauses', 1)*100:.1f}%"
        )
    
    # Top risk factors
    top_risky_clauses = risk_summary.get('top_risky_clauses', [])
    if top_risky_clauses:
        st.markdown("**⚡ Top Risk Factors:**")
        
        for i, clause_risk in enumerate(top_risky_clauses[:3], 1):
            matched_terms = clause_risk.get('matched_terms', [])
            if matched_terms:
                terms_text = ", ".join(matched_terms[:3])
                if len(matched_terms) > 3:
                    terms_text += f" +{len(matched_terms)-3} more"
                
                st.markdown(
                    f"**{i}.** Clause {clause_risk['clause_id']}: "
                    f"*{terms_text}* (Score: {clause_risk['risk_score']:.3f})"
                )
    
    # Key entities (if provided)
    if top_entities:
        st.markdown("**🏢 Key Parties & Entities:**")
        for entity in top_entities[:5]:
            st.markdown(f"- **{entity['text']}** ({entity['label']})")

def render_clause_summary_cards(per_clause_summaries: List[Dict]) -> None:
    """
    Render individual summary cards for each clause.
    
    Args:
        per_clause_summaries: List of per-clause summary dictionaries
    """
    if not per_clause_summaries:
        st.info("No per-clause summaries available")
        return
    
    st.markdown("#### 📝 Clause Summaries")
    
    # Group by clause type
    type_groups = {}
    for clause_summary in per_clause_summaries:
        clause_type = clause_summary.get("clause_type", "Unknown")
        if clause_type not in type_groups:
            type_groups[clause_type] = []
        type_groups[clause_type].append(clause_summary)
    
    # Display by type
    for clause_type, clauses in type_groups.items():
        with st.expander(f"📄 **{clause_type} Clauses** ({len(clauses)})"):
            for clause_summary in clauses:
                st.markdown(f"**Clause {clause_summary.get('clause_id')}:**")
                st.write(clause_summary.get('summary', 'No summary available'))
                st.markdown("---")

def render_explain_like_im_20_toggle(summaries: Dict) -> None:
    """
    Render a toggle for simplified explanations.
    
    Args:
        summaries: Summary dictionary
    """
    st.markdown("#### 🎓 Simplified Explanation")
    
    if st.toggle("Explain Like I'm 20", key="eli20_toggle"):
        # Generate simplified explanation
        simplified_summary = _simplify_summary(summaries.get("short_summary", ""))
        
        st.markdown("**Here's what this contract means in simple terms:**")
        st.info(simplified_summary)
        
        # Key takeaways
        st.markdown("**Key Takeaways:**")
        takeaways = _generate_key_takeaways(summaries)
        for i, takeaway in enumerate(takeaways, 1):
            st.markdown(f"{i}. {takeaway}")
    else:
        st.markdown("*Toggle above to see a simplified explanation of the contract*")

def _simplify_summary(summary: str) -> str:
    """
    Convert technical summary to simplified language.
    
    Args:
        summary: Original summary text
        
    Returns:
        Simplified summary text
    """
    if not summary:
        return "This contract sets up a business agreement between different parties."
    
    # Simple replacements for legal jargon
    simplifications = {
        "hereby": "by this document",
        "whereas": "since",
        "shall": "will",
        "pursuant to": "according to",
        "notwithstanding": "despite",
        "indemnify": "protect from legal costs",
        "liquidated damages": "agreed penalty amount",
        "force majeure": "uncontrollable events",
        "termination": "ending the contract",
        "confidential": "private/secret",
        "intellectual property": "creative works and ideas",
        "liability": "legal responsibility"
    }
    
    simplified = summary.lower()
    for complex_term, simple_term in simplifications.items():
        simplified = simplified.replace(complex_term.lower(), simple_term)
    
    # Capitalize first letter
    simplified = simplified[0].upper() + simplified[1:] if simplified else ""
    
    return simplified

def _generate_key_takeaways(summaries: Dict) -> List[str]:
    """
    Generate key takeaways from summaries.
    
    Args:
        summaries: Summary dictionary
        
    Returns:
        List of key takeaway strings
    """
    takeaways = [
        "Read all terms carefully before signing",
        "Pay special attention to payment and termination clauses",
        "Consider having a lawyer review high-risk sections",
        "Make sure you understand your obligations and rights",
        "Keep a copy of the signed contract for your records"
    ]
    
    # Could be enhanced to extract specific takeaways from the actual summary
    # For now, return generic but useful advice
    
    return takeaways[:3]  # Return top 3 takeaways

def render_action_items_card(risk_summary: Dict) -> None:
    """
    Render a card with recommended action items based on risk analysis.
    
    Args:
        risk_summary: Risk assessment summary
    """
    st.markdown("#### ✅ Recommended Actions")
    
    actions = []
    
    # Generate actions based on risk level
    risk_level = risk_summary.get('contract_risk_level', 'Unknown')
    high_risk_count = risk_summary.get('high_risk_count', 0)
    
    if risk_level == "High" or high_risk_count > 2:
        actions.append("🔴 **URGENT**: Have this contract reviewed by a qualified attorney")
        actions.append("📋 Negotiate terms for high-risk clauses before signing")
    
    if high_risk_count > 0:
        actions.append("⚠️ Carefully review all high-risk clauses highlighted above")
        actions.append("💬 Discuss concerning terms with the other party")
    
    # Always include general recommendations
    actions.extend([
        "📖 Read the entire contract thoroughly",
        "🤝 Ensure all verbal agreements are included in writing",
        "📅 Note all important dates and deadlines",
        "💾 Keep digital and physical copies of the signed contract"
    ])
    
    for action in actions[:6]:  # Show top 6 actions
        st.markdown(action)

if __name__ == "__main__":
    # Demo functionality
    st.title("Summary Card Component Demo")
    
    # Sample data
    sample_summaries = {
        "short_summary": "This Software License Agreement establishes terms between Company ABC and Contractor XYZ for software development services over 12 months with standard payment and termination provisions.",
        "long_summary": "This comprehensive Software License Agreement defines a business relationship between Company ABC and Contractor XYZ. The contract includes provisions for software development services, intellectual property rights, payment terms requiring 30-day invoice processing, and standard termination clauses allowing either party to exit with proper notice.",
        "per_clause_summaries": [
            {"clause_id": 1, "clause_type": "Termination", "summary": "Either party can end the agreement with 30 days notice"},
            {"clause_id": 2, "clause_type": "Payment", "summary": "Invoices must be paid within 30 days of receipt"}
        ]
    }
    
    sample_risk_summary = {
        "contract_risk_level": "Medium",
        "contract_risk_score": 0.45,
        "total_clauses": 8,
        "high_risk_count": 1,
        "medium_risk_count": 2,
        "low_risk_count": 5,
        "top_risky_clauses": [
            {"clause_id": 3, "risk_score": 0.75, "matched_terms": ["indemnify", "hold harmless"]}
        ]
    }
    
    sample_entities = [
        {"text": "Company ABC", "label": "ORG"},
        {"text": "Contractor XYZ", "label": "ORG"},
        {"text": "$10,000", "label": "MONEY"}
    ]
    
    # Render components
    render_summary_card(sample_summaries, sample_risk_summary)
    
    st.markdown("---")
    
    render_risk_insights_card(sample_risk_summary, sample_entities)
    
    st.markdown("---")
    
    render_clause_summary_cards(sample_summaries["per_clause_summaries"])
    
    st.markdown("---")
    
    render_explain_like_im_20_toggle(sample_summaries)
    
    st.markdown("---")
    
    render_action_items_card(sample_risk_summary)
