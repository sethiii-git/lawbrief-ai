# File: frontend/components/risk_chart.py
"""
Risk visualization component for creating charts and graphs.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, List, Optional
import numpy as np

def create_risk_chart(risk_summary: Dict) -> Optional[plt.Figure]:
    """
    Create a risk distribution visualization.
    
    Args:
        risk_summary: Risk assessment summary dictionary
        
    Returns:
        Matplotlib figure object or None if no data
    """
    try:
        risk_dist = risk_summary.get("risk_distribution", {})
        
        # Filter out zero values
        filtered_dist = {k: v for k, v in risk_dist.items() if v > 0}
        
        if not filtered_dist:
            return None
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Pie chart
        labels = list(filtered_dist.keys())
        sizes = list(filtered_dist.values())
        colors = {'Low': '#4CAF50', 'Medium': '#FF9800', 'High': '#F44336'}
        chart_colors = [colors.get(label, '#9E9E9E') for label in labels]
        
        wedges, texts, autotexts = ax1.pie(
            sizes, 
            labels=labels, 
            colors=chart_colors,
            autopct='%1.1f%%',
            startangle=90,
            explode=[0.05 if label == 'High' else 0 for label in labels]
        )
        
        ax1.set_title('Risk Distribution', fontsize=14, fontweight='bold', pad=20)
        
        # Style the percentage text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        # Bar chart
        y_pos = np.arange(len(labels))
        bars = ax2.barh(y_pos, sizes, color=chart_colors)
        
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(labels)
        ax2.invert_yaxis()
        ax2.set_xlabel('Number of Clauses')
        ax2.set_title('Risk Levels by Count', fontsize=14, fontweight='bold', pad=20)
        
        # Add value labels on bars
        for i, (bar, size) in enumerate(zip(bars, sizes)):
            width = bar.get_width()
            ax2.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                    str(size), ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        print(f"Error creating risk chart: {e}")
        return None

def create_risk_score_heatmap(clauses: List[Dict], clause_risks: List[Dict]) -> Optional[plt.Figure]:
    """
    Create a heatmap showing risk scores across clause types.
    
    Args:
        clauses: List of clause dictionaries
        clause_risks: List of risk assessment dictionaries
        
    Returns:
        Matplotlib figure object or None if insufficient data
    """
    try:
        # Create risk lookup
        risk_lookup = {risk["clause_id"]: risk for risk in clause_risks}
        
        # Group by clause type
        type_risks = {}
        for clause in clauses:
            clause_type = clause["type"]
            risk_info = risk_lookup.get(clause["id"], {})
            risk_score = risk_info.get("risk_score", 0)
            
            if clause_type not in type_risks:
                type_risks[clause_type] = []
            type_risks[clause_type].append(risk_score)
        
        # Calculate average risk per type
        avg_risks = {
            clause_type: np.mean(scores) 
            for clause_type, scores in type_risks.items()
        }
        
        if not avg_risks:
            return None
        
        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(10, max(6, len(avg_risks) * 0.8)))
        
        types = list(avg_risks.keys())
        scores = list(avg_risks.values())
        
        # Color based on risk level
        colors = []
        for score in scores:
            if score < 0.25:
                colors.append('#4CAF50')  # Green for low risk
            elif score < 0.55:
                colors.append('#FF9800')  # Orange for medium risk
            else:
                colors.append('#F44336')  # Red for high risk
        
        bars = ax.barh(types, scores, color=colors)
        
        ax.set_xlabel('Average Risk Score')
        ax.set_title('Average Risk Score by Clause Type', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 1.0)
        
        # Add score labels
        for bar, score in zip(bars, scores):
            width = bar.get_width()
            ax.text(width + 0.02, bar.get_y() + bar.get_height()/2,
                   f'{score:.3f}', ha='left', va='center', fontweight='bold')
        
        # Add risk level guidelines
        ax.axvline(x=0.25, color='gray', linestyle='--', alpha=0.7, label='Low-Medium Threshold')
        ax.axvline(x=0.55, color='gray', linestyle='--', alpha=0.7, label='Medium-High Threshold')
        ax.legend()
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        print(f"Error creating risk heatmap: {e}")
        return None

def create_risk_radar_chart(risk_summary: Dict) -> Optional[plt.Figure]:
    """
    Create a radar chart showing different risk dimensions.
    
    Args:
        risk_summary: Risk assessment summary
        
    Returns:
        Matplotlib figure object or None if insufficient data
    """
    try:
        # Define risk dimensions based on available data
        dimensions = [
            'Overall Risk',
            'High Risk Ratio',
            'Contract Complexity',
            'Risk Distribution'
        ]
        
        # Calculate scores for each dimension (0-1 scale)
        total_clauses = risk_summary.get('total_clauses', 1)
        high_risk_count = risk_summary.get('high_risk_count', 0)
        medium_risk_count = risk_summary.get('medium_risk_count', 0)
        
        scores = [
            risk_summary.get('contract_risk_score', 0),  # Overall risk
            high_risk_count / max(total_clauses, 1),     # High risk ratio
            min(total_clauses / 20, 1.0),               # Complexity based on clause count
            (high_risk_count + medium_risk_count * 0.5) / max(total_clauses, 1)  # Risk distribution
        ]
        
        # Create radar chart
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        # Calculate angle for each dimension
        angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
        scores += [scores[0]]  # Complete the circle
        angles += [angles]  # Complete the circle
        
        # Plot
        ax.plot(angles, scores, 'o-', linewidth=2, label='Risk Profile', color='#FF5722')
        ax.fill(angles, scores, alpha=0.25, color='#FF5722')
        
        # Add labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dimensions)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'])
        ax.grid(True)
        
        ax.set_title('Contract Risk Profile', size=16, fontweight='bold', pad=30)
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        print(f"Error creating radar chart: {e}")
        return None

def create_clause_risk_timeline(clauses: List[Dict], clause_risks: List[Dict]) -> Optional[plt.Figure]:
    """
    Create a timeline showing risk scores across clauses.
    
    Args:
        clauses: List of clause dictionaries  
        clause_risks: List of risk assessment dictionaries
        
    Returns:
        Matplotlib figure object or None if insufficient data
    """
    try:
        if not clauses or not clause_risks:
            return None
            
        # Create risk lookup
        risk_lookup = {risk["clause_id"]: risk for risk in clause_risks}
        
        # Prepare data
        clause_ids = [clause["id"] for clause in clauses]
        risk_scores = [risk_lookup.get(clause["id"], {}).get("risk_score", 0) for clause in clauses]
        risk_levels = [risk_lookup.get(clause["id"], {}).get("risk_level", "Unknown") for clause in clauses]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Color map for risk levels
        color_map = {'Low': '#4CAF50', 'Medium': '#FF9800', 'High': '#F44336', 'Unknown': '#9E9E9E'}
        colors = [color_map.get(level, '#9E9E9E') for level in risk_levels]
        
        # Plot timeline
        ax.scatter(clause_ids, risk_scores, c=colors, s=100, alpha=0.7)
        ax.plot(clause_ids, risk_scores, color='gray', alpha=0.5, linestyle='--')
        
        # Add risk level thresholds
        ax.axhline(y=0.25, color='green', linestyle='-', alpha=0.3, label='Low Risk Threshold')
        ax.axhline(y=0.55, color='orange', linestyle='-', alpha=0.3, label='High Risk Threshold')
        
        ax.set_xlabel('Clause ID')
        ax.set_ylabel('Risk Score')
        ax.set_title('Risk Score Timeline Across Clauses', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Annotate high-risk clauses
        for i, (clause_id, score, level) in enumerate(zip(clause_ids, risk_scores, risk_levels)):
            if level == 'High':
                ax.annotate(f'Clause {clause_id}', 
                           (clause_id, score), 
                           xytext=(5, 5), 
                           textcoords='offset points',
                           fontsize=8, 
                           fontweight='bold')
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        print(f"Error creating timeline chart: {e}")
        return None

if __name__ == "__main__":
    # Demo functionality
    import matplotlib.pyplot as plt
    
    # Sample data
    sample_risk_summary = {
        "risk_distribution": {"Low": 5, "Medium": 3, "High": 2},
        "contract_risk_score": 0.45,
        "total_clauses": 10,
        "high_risk_count": 2,
        "medium_risk_count": 3,
        "low_risk_count": 5
    }
    
    sample_clauses = [
        {"id": 1, "type": "Termination"},
        {"id": 2, "type": "Payment"},
        {"id": 3, "type": "Liability"}
    ]
    
    sample_risks = [
        {"clause_id": 1, "risk_score": 0.2, "risk_level": "Low"},
        {"clause_id": 2, "risk_score": 0.6, "risk_level": "High"},
        {"clause_id": 3, "risk_score": 0.4, "risk_level": "Medium"}
    ]
    
    print("Creating demo charts...")
    
    # Test risk distribution chart
    fig1 = create_risk_chart(sample_risk_summary)
    if fig1:
        plt.show()
        print("✓ Risk distribution chart created")
    
    # Test risk heatmap
    fig2 = create_risk_score_heatmap(sample_clauses, sample_risks)
    if fig2:
        plt.show()
        print("✓ Risk heatmap created")
    
    # Test radar chart
    fig3 = create_risk_radar_chart(sample_risk_summary)
    if fig3:
        plt.show()
        print("✓ Risk radar chart created")
    
    print("Demo completed!")
