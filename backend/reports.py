import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import numpy as np
from backend.diagnostics import add_health_scores, detect_anomalies, generate_recommendations

def create_health_report(df, report_type='weekly', output_path=None):
    """
    Generate a comprehensive health report in PDF format
    
    Args:
        df: DataFrame with DAB data
        report_type: 'weekly' or 'monthly'
        output_path: Path to save the PDF (if None, returns bytes)
    
    Returns:
        PDF bytes if output_path is None
    """
    # Add health scores and detect anomalies
    df = add_health_scores(df)
    anomalies = detect_anomalies(df)
    recommendations = generate_recommendations(df, anomalies)
    
    # Filter data based on report type
    if report_type == 'weekly':
        end_date = df['timestamp'].max()
        start_date = end_date - timedelta(days=7)
    else:  # monthly
        end_date = df['timestamp'].max()
        start_date = end_date - timedelta(days=30)
    
    df_filtered = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    # Create plots
    plots = create_report_plots(df_filtered, anomalies)
    
    # Generate PDF
    if output_path:
        doc = SimpleDocTemplate(output_path, pagesize=A4)
    else:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph(f"DAB Converter {report_type.title()} Health Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report metadata
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph(f"Report period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Executive summary
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    avg_efficiency = df_filtered['efficiency_percent'].mean()
    avg_temp = df_filtered['temperature_C'].mean()
    avg_health = df_filtered['health_score'].mean()
    anomaly_count = len(anomalies)
    
    summary_data = [
        ['Metric', 'Value', 'Status'],
        ['Average Efficiency', f"{avg_efficiency:.2f}%", '🟢' if avg_efficiency > 95 else '🟡' if avg_efficiency > 90 else '🔴'],
        ['Average Temperature', f"{avg_temp:.1f}°C", '🟢' if avg_temp < 50 else '🟡' if avg_temp < 60 else '🔴'],
        ['Average Health Score', f"{avg_health:.1f}/100", '🟢' if avg_health > 80 else '🟡' if avg_health > 60 else '🔴'],
        ['Anomalies Detected', str(anomaly_count), '🟢' if anomaly_count == 0 else '🟡' if anomaly_count < 5 else '🔴']
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Add plots
    for plot_name, plot_data in plots.items():
        story.append(Paragraph(plot_name, styles['Heading3']))
        story.append(Image(plot_data, width=6*inch, height=4*inch))
        story.append(Spacer(1, 20))
    
    # Anomalies section
    if anomalies:
        story.append(Paragraph("Detected Anomalies", styles['Heading2']))
        anomaly_data = [['Timestamp', 'Metric', 'Value', 'Threshold', 'Severity']]
        for anomaly in anomalies[:10]:  # Limit to top 10
            anomaly_data.append([
                anomaly['timestamp'].strftime('%Y-%m-%d %H:%M'),
                anomaly['metric'],
                f"{anomaly['value']:.2f}",
                f"{anomaly['threshold']:.2f}",
                anomaly['severity']
            ])
        
        anomaly_table = Table(anomaly_data)
        anomaly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(anomaly_table)
        story.append(Spacer(1, 20))
    
    # Recommendations section
    if recommendations:
        story.append(Paragraph("Recommendations", styles['Heading2']))
        for i, rec in enumerate(recommendations[:5], 1):  # Limit to top 5
            story.append(Paragraph(f"{i}. {rec['action']}", styles['Normal']))
            story.append(Paragraph(f"   Expected Impact: {rec['impact']}", styles['Normal']))
            story.append(Paragraph(f"   Priority: {rec['priority']}", styles['Normal']))
            story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    
    if output_path:
        return output_path
    else:
        buffer.seek(0)
        return buffer.getvalue()

def create_report_plots(df, anomalies):
    """Create plots for the health report"""
    plots = {}
    
    # Set style
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('DAB Converter Performance Metrics', fontsize=16)
    
    # Efficiency trend
    axes[0, 0].plot(df['timestamp'], df['efficiency_percent'], 'b-', linewidth=2)
    axes[0, 0].set_title('Efficiency Trend')
    axes[0, 0].set_ylabel('Efficiency (%)')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # Temperature trend
    axes[0, 1].plot(df['timestamp'], df['temperature_C'], 'r-', linewidth=2)
    axes[0, 1].set_title('Temperature Trend')
    axes[0, 1].set_ylabel('Temperature (°C)')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # Health score
    axes[1, 0].plot(df['timestamp'], df['health_score'], 'g-', linewidth=2)
    axes[1, 0].set_title('Health Score Trend')
    axes[1, 0].set_ylabel('Health Score')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Power losses
    axes[1, 1].plot(df['timestamp'], df['power_loss_W'], 'orange', linewidth=2, label='Total Loss')
    axes[1, 1].plot(df['timestamp'], df['switching_loss_W'], 'purple', linewidth=2, label='Switching Loss')
    axes[1, 1].plot(df['timestamp'], df['conduction_loss_W'], 'brown', linewidth=2, label='Conduction Loss')
    axes[1, 1].set_title('Power Losses')
    axes[1, 1].set_ylabel('Power Loss (W)')
    axes[1, 1].legend()
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Save plot to bytes
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    plots['Performance Metrics Overview'] = buffer
    
    # Anomaly plot if any
    if anomalies:
        plt.figure(figsize=(10, 6))
        anomaly_df = pd.DataFrame(anomalies)
        anomaly_df['timestamp'] = pd.to_datetime(anomaly_df['timestamp'])
        
        for metric in anomaly_df['metric'].unique():
            metric_data = anomaly_df[anomaly_df['metric'] == metric]
            plt.scatter(metric_data['timestamp'], metric_data['value'], 
                       label=metric, s=100, alpha=0.7)
        
        plt.title('Detected Anomalies')
        plt.xlabel('Timestamp')
        plt.ylabel('Value')
        plt.legend()
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plots['Anomaly Detection'] = buffer
    
    plt.close('all')
    return plots
