import numpy as np
import pandas as pd
from io import BytesIO
import pdfkit
from datetime import datetime
from flask import abort
from flask_login import current_user
from functools import wraps

def role_required(*roles):
    """
    Decorator untuk membatasi akses route berdasarkan role user.
    Contoh penggunaan:
    @login_required
    @role_required('admin', 'chief_strategic_officer')
    def some_route():
        ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def calculate_saw(criteria_list, alternatives):
    """
    Perform SAW (Simple Additive Weighting) method calculation
    
    Returns:
    - decision_matrix: raw values
    - normalized_matrix: normalized values
    - weighted_matrix: normalized * weights
    - final_scores: sum of weighted values for each alternative
    """
    # Create decision matrix
    n_alternatives = len(alternatives)
    n_criteria = len(criteria_list)
    
    decision_matrix = np.zeros((n_alternatives, n_criteria))
    
    # Fill decision matrix with values
    for i, alternative in enumerate(alternatives):
        for j, criteria in enumerate(criteria_list):
            value = alternative.get_criteria_value(alternative.id, criteria.id)
            decision_matrix[i, j] = value if value is not None else 0
    
    # Normalize decision matrix
    normalized_matrix = np.zeros_like(decision_matrix)
    
    for j in range(n_criteria):
        criteria = criteria_list[j]
        column = decision_matrix[:, j]
        
        if criteria.is_benefit:  # Benefit criteria (higher is better)
            max_val = np.max(column) if np.max(column) > 0 else 1  # Avoid division by zero
            normalized_matrix[:, j] = column / max_val
        else:  # Cost criteria (lower is better)
            min_val = np.min(column) if np.min(column) > 0 else 1  # Avoid division by zero
            normalized_matrix[:, j] = min_val / column
    
    # Apply weights to normalized matrix
    weighted_matrix = np.zeros_like(normalized_matrix)
    
    for j in range(n_criteria):
        criteria = criteria_list[j]
        weighted_matrix[:, j] = normalized_matrix[:, j] * criteria.weight
    
    # Calculate final scores
    final_scores = np.sum(weighted_matrix, axis=1)
    
    return decision_matrix, normalized_matrix, weighted_matrix, final_scores

def generate_pdf_report(analysis, details):
    """Generate a PDF report for the analysis results"""
    ranked_alternatives = details.get('ranked_alternatives', [])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Analysis Report - {analysis.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #334155; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .header {{ border-bottom: 2px solid #334155; padding-bottom: 10px; margin-bottom: 20px; }}
            .footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 0.8em; color: #666; }}
            .rank-1 {{ background-color: #d1fae5; }}
            .rank-2 {{ background-color: #e0f2fe; }}
            .rank-3 {{ background-color: #fef3c7; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Factory Location Decision Support Analysis</h1>
            <p><strong>Analysis Name:</strong> {analysis.name}</p>
            <p><strong>Date:</strong> {analysis.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Description:</strong> {analysis.description or 'No description provided'}</p>
        </div>
        
        <h2>Ranking Results</h2>
        <table>
            <tr>
                <th>Rank</th>
                <th>Alternative</th>
                <th>Location</th>
                <th>Score</th>
            </tr>
    """
    
    # Add rows for ranked alternatives
    for alt in ranked_alternatives:
        row_class = f"rank-{alt['rank']}" if alt['rank'] <= 3 else ""
        html_content += f"""
            <tr class="{row_class}">
                <td>{alt['rank']}</td>
                <td>{alt['name']}</td>
                <td>{alt['location']}</td>
                <td>{alt['score']:.4f}</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>Recommendation</h2>
        <p>Based on the SAW method analysis and the criteria weights provided, """
    
    if ranked_alternatives:
        top_alt = ranked_alternatives[0]
        html_content += f"""
        <strong>{top_alt['name']}</strong> (located at <strong>{top_alt['location']}</strong>) 
        is the recommended location with a score of <strong>{top_alt['score']:.4f}</strong>.
        """
    else:
        html_content += "no recommendation could be made due to insufficient data."
    
    html_content += """
        </p>
        
        <div class="footer">
            <p>This report was generated by SAW Method Decision Support System on """
    html_content += datetime.now().strftime('%Y-%m-%d %H:%M')
    html_content += """.</p>
        </div>
    </body>
    </html>
    """
    
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    # Use pdfkit to convert HTML to PDF
    pdf = pdfkit.from_string(html_content, False, configuration=config)
    return pdf

CRITERIA_OPTION_LABELS = {
    "Harga Lahan": {
        1: "< Rp5.000.000/m²",
        2: "Rp5.000.000 – Rp8.000.000/m²",
        3: "> Rp8.000.000/m²"
    },
    "Luas Lahan": {
        1: "< 3000 m²",
        2: "1000 – 3000 m²",
        3: "> 3000 m²"
    },
    "Ketersediaan Calon Pekerja": {
        1: "< 4%",
        2: "4% – 6.5%",
        3: "> 6.5%"
    },
    "Aksesbilitas": {
        1: "Buruk",
        2: "Sedang",
        3: "Baik"
    },
    "Jarak Ke Pemasok": {
        1: "< 20 km",
        2: "20 – 50 km",
        3: "> 50 km"
    },
    "Jarak Ke Pasar": {
        1: "< 20 km",
        2: "20 – 50 km",
        3: "> 50 km"
    }
}