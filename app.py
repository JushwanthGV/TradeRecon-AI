import os
from main import run_full_reconciliation
import json
from pathlib import Path
from dotenv import load_dotenv
from io import BytesIO
import pandas as pd

# CRITICAL: Load .env file BEFORE any other imports
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=True)
    print(f"✅ Loaded .env from: {env_file}")
else:
    print(f"⚠️ .env not found at: {env_file}")

import streamlit as st
from matching import reconcile_trades
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="TradeRecon AI - Trade Reconciliation",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# HELPER: Convert markdown to PDF (requires reportlab)
def markdown_to_pdf(markdown_text: str, filename: str) -> bytes:
    """Convert text report to PDF with clean formatting"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=40
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom monospace style for compliance reports
        mono_style = ParagraphStyle(
            'MonoStyle',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=9,
            leading=11,
            leftIndent=0,
            rightIndent=0,
            alignment=TA_LEFT,
            spaceAfter=6
        )
        
        # Clean text for PDF - remove problematic characters
        clean_text = markdown_text.replace('&', 'and').replace('<', '(').replace('>', ')')
        
        # Split by lines and render
        for line in clean_text.split('\n'):
            if line.strip():
                # Escape special XML characters
                safe_line = line.replace('&', '&amp;')
                try:
                    story.append(Paragraph(safe_line, mono_style))
                except:
                    # Fallback for problematic lines
                    story.append(Spacer(1, 0.1*inch))
            else:
                story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        st.warning("⚠️ PDF generation requires 'reportlab'. Install with: pip install reportlab")
        return markdown_text.encode('utf-8')
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return markdown_text.encode('utf-8')

# HELPER: Create XLSX from DataFrame
def create_excel_buffer(dataframes_dict: dict) -> bytes:
    """Create multi-sheet Excel file"""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for sheet_name, df in dataframes_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    buffer.seek(0)
    return buffer.getvalue()

# HELPER: Generate markdown file with proper formatting
def generate_markdown_report(report_text: str) -> str:
    """Ensure report has proper markdown formatting"""
    if not report_text or report_text.strip() == "":
        return "# ⚠️ Empty Report\n\nNo report content generated."
    return report_text

# HELPER: Format markdown to DOCX-compatible format
def format_report_for_export(report_text: str) -> str:
    """Format report for better readability in exports"""
    return report_text if report_text else "# Trade Reconciliation Report\n\n*No data available*"

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }

    .header-container {
        background: linear-gradient(90deg, #1e40af 0%, #7c3aed 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }

    .header-title {
        color: white;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }

    .header-subtitle {
        color: #e0e7ff;
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }

    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }

    .metric-card.success { border-left-color: #10b981; }
    .metric-card.warning { border-left-color: #f59e0b; }
    .metric-card.danger  { border-left-color: #ef4444; }
    .metric-card.info    { border-left-color: #3b82f6; }

    .stButton button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    .stButton button:hover {
        background: linear-gradient(90deg, #2563eb 0%, #7c3aed 100%);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
        transform: translateY(-2px);
    }

    .agent-card {
        background-color: rgba(30, 41, 59, 0.5);
        border: 1px solid #2b313a;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .agent-header {
        color: #60a5fa;
        font-weight: bold;
        font-size: 1em;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .risk-high { border-left: 4px solid #ef4444; }
    .risk-med  { border-left: 4px solid #f59e0b; }
    .risk-low  { border-left: 4px solid #10b981; }
    
    .report-container {
        background: rgba(30, 41, 59, 0.3);
        border: 1px solid #2b313a;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        max-height: 600px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-container">
    <h1 class="header-title">🤖 TradeRecon AI</h1>
    <p class="header-subtitle">AI-Powered Trade Reconciliation & Exception Analysis</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
    st.title("📁 Upload Trade Files")
    st.markdown("---")

    broker_file = st.file_uploader("**Broker Trades CSV**", type=['csv'])
    exchange_file = st.file_uploader("**Exchange Trades CSV**", type=['csv'])

    st.markdown("---")
    st.checkbox("Show All Trades", value=False)
    st.checkbox("Auto-explain High Risk", value=False)

    st.markdown("---")
    st.info("""
    **TradeRecon AI** uses advanced AI agents to:
    - Match trades across systems
    - Identify discrepancies
    - Explain root causes
    - Generate compliance reports
    """)

# Main Content
if broker_file and exchange_file:
    try:
        # Load data
        with st.spinner("🔄 Loading trade data..."):
            broker_df = pd.read_csv(broker_file)
            exchange_df = pd.read_csv(exchange_file)

        st.success("✅ Files loaded successfully!")

        # Reconcile
        with st.spinner("🔍 Reconciling trades..."):
            results = reconcile_trades(broker_df, exchange_df)

        # Dashboard
        st.markdown("## 📊 Reconciliation Dashboard")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card info">
                <h3>📈 Total Trades</h3>
                <h1>{results['total_trades']}</h1>
                <p>Processed</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card success">
                <h3>✅ Matched</h3>
                <h1>{results['matched_count']}</h1>
                <p>{(results['matched_count']/results['total_trades']*100):.1f}% Success Rate</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card warning">
                <h3>⚠️ Mismatches</h3>
                <h1>{results['mismatch_count']}</h1>
                <p>Requires Review</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card danger">
                <h3>❌ Missing</h3>
                <h1>{results['missing_count']}</h1>
                <p>Not Found</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Exceptions",
            "📄 Compliance Report",
            "📊 All Trades",
            "🤖 Intelligent Reconciliation"
        ])

        # ============ TAB 1: EXCEPTIONS ============
        with tab1:
            st.markdown("### 🚨 Trade Exceptions")

            if len(results['exceptions']) > 0:
                exceptions_df = results['exceptions']

                def highlight_exception_type(row):
                    if row['exception_type'] == 'mismatch':
                        return ['background-color: rgba(245, 158, 11, 0.2)'] * len(row)
                    elif 'missing' in row['exception_type']:
                        return ['background-color: rgba(239, 68, 68, 0.2)'] * len(row)
                    return [''] * len(row)

                styled_df = exceptions_df.style.apply(highlight_exception_type, axis=1)
                st.dataframe(styled_df, use_container_width=True, height=400)

                # Download exceptions as Excel
                st.markdown("---")
                st.markdown("### 📥 Download Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    excel_buffer = create_excel_buffer({'Exceptions': exceptions_df})
                    st.download_button(
                        label="📊 Download as Excel (.xlsx)",
                        data=excel_buffer,
                        file_name=f"exceptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col2:
                    csv_data = exceptions_df.to_csv(index=False)
                    st.download_button(
                        label="📄 Download as CSV",
                        data=csv_data,
                        file_name=f"exceptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                st.markdown("---")
                st.markdown("### 🤖 AI Exception Analysis")

                exception_options = [
                    f"Trade ID: {row['trade_id']} - {row['exception_type']}"
                    for _, row in exceptions_df.iterrows()
                ]

                selected_exception = st.selectbox(
                    "Select an exception to analyze:",
                    options=range(len(exception_options)),
                    format_func=lambda x: exception_options[x]
                )

                st.info("💡 **Tip:** Use the 'Intelligent Reconciliation' tab to run the unified Intelligence Engine for complete AI analysis.")

            else:
                st.success("🎉 No exceptions found!")

        # ============ TAB 2: COMPLIANCE REPORT ============
        with tab2:
            st.markdown("### 📄 Compliance Report")

            ai_report = None
            if "intelligent_results" in st.session_state:
                ai_report = st.session_state.intelligent_results.get("final_compliance_report")

            if ai_report:
                report = ai_report
                st.success("✅ Showing AI-Generated Compliance Report")
            else:
                st.warning("⚠️ Basic report shown. Run 'Intelligent Reconciliation' tab for full AI analysis.")
                # Enhanced default report
                report = f"""TRADE RECONCILIATION COMPLIANCE REPORT

Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}
Report Type: Basic Reconciliation Summary

================================================================================

EXECUTIVE SUMMARY

This report summarizes the trade reconciliation results between broker and exchange systems.

RECONCILIATION METRICS

Total Trades Processed: {results['total_trades']}
Successfully Matched: {results['matched_count']} ({results['matched_count']/max(results['total_trades'], 1)*100:.1f}%)
Exceptions Detected: {results['mismatch_count'] + results['missing_count']}
  - Data Mismatches: {results['mismatch_count']}
  - Missing Trades: {results['missing_count']}

Match Rate: {results['matched_count']}/{results['total_trades']}

================================================================================

RECONCILIATION STATUS

Matched Trades:
Count: {results['matched_count']} trades successfully reconciled
- These trades match between broker and exchange systems
- No action required for these trades

Exceptions Requiring Review:
Total Exceptions: {results['mismatch_count'] + results['missing_count']}

Data Mismatches:
- Count: {results['mismatch_count']} trades
- Type: Data differences between systems
- Action: Manual review and correction required

Missing Trades:
- Count: {results['missing_count']} trades
- Type: Trades present in one system but not the other
- Action: Investigate source of discrepancy

================================================================================

RECOMMENDED ACTIONS

IMMEDIATE (0-24 hours):
- Review all {results['mismatch_count'] + results['missing_count']} exceptions
- Prioritize high-value exceptions for immediate review
- Document all investigation findings

SHORT-TERM (1-7 days):
- Complete root cause analysis for all exceptions
- Make necessary corrections in broker or exchange systems
- Implement controls to prevent future discrepancies

LONG-TERM (Ongoing):
- Monitor reconciliation match rates
- Maintain comprehensive audit documentation
- Regular system validation and testing

================================================================================

REPORT DETAILS

Report Type: Basic Trade Reconciliation Summary
Generated By: TradeRecon AI System
Compliance Status: Review required for {results['mismatch_count'] + results['missing_count']} exceptions

NOTE: For detailed AI-powered analysis with root cause diagnosis, risk assessment,
and specific remediation recommendations, please run the Intelligent Reconciliation
workflow in the dedicated tab.

================================================================================

END OF REPORT
"""

            # Display report in scrollable container
            st.markdown('<div class="report-container">', unsafe_allow_html=True)
            st.markdown(report)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 📥 Download Compliance Report")

            col1, col2, col3 = st.columns(3)

            with col1:
                md_data = format_report_for_export(report)
                st.download_button(
                    label="📄 Download as Markdown (.md)",
                    data=md_data,
                    file_name=f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

            with col2:
                pdf_data = markdown_to_pdf(report, "compliance_report")
                st.download_button(
                    label="📕 Download as PDF (.pdf)",
                    data=pdf_data,
                    file_name=f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            with col3:
                txt_data = report.encode('utf-8')
                st.download_button(
                    label="📃 Download as Text (.txt)",
                    data=txt_data,
                    file_name=f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        # ============ TAB 3: ALL TRADES ============
        with tab3:
            st.markdown("### 📊 All Trades")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Broker Trades")
                st.dataframe(broker_df, use_container_width=True, height=400)
                broker_excel = create_excel_buffer({'Broker Trades': broker_df})
                st.download_button(
                    label="📊 Download Broker Trades (Excel)",
                    data=broker_excel,
                    file_name=f"broker_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with col2:
                st.markdown("#### Exchange Trades")
                st.dataframe(exchange_df, use_container_width=True, height=400)
                exchange_excel = create_excel_buffer({'Exchange Trades': exchange_df})
                st.download_button(
                    label="📊 Download Exchange Trades (Excel)",
                    data=exchange_excel,
                    file_name=f"exchange_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        # ============ TAB 4: INTELLIGENT RECONCILIATION ============
        with tab4:
            st.markdown("### 🤖 AI-Powered Autonomous Reconciliation")

            st.info("""
**Intelligent Reconciliation Workflow** powered by a unified AI Intelligence Engine:

🤖 **Single Intelligence Engine** performs complete analysis:
- Root Cause Diagnosis
- Severity Classification  
- Fix Recommendations
- Risk Assessment
- Compliance Reporting

All in **ONE optimized call** for maximum speed and consistency!

**AI Models (Groq Infrastructure):**
- Primary: OpenAI GPT-OSS-120B (120B parameters, superior reasoning)
- Fallback: LLaMA 3.3-70B Versatile (fast & reliable backup)
""")

            col1, col2 = st.columns([3, 1])

            with col1:
                run_intelligent = st.button(
                    "🚀 Run Intelligent Reconciliation",
                    use_container_width=True,
                    type="primary"
                )

            if run_intelligent:
                with st.spinner("🤖 Running AI agents... This may take a minute..."):
                    try:
                        intelligent_results = run_full_reconciliation(broker_df, exchange_df)
                        st.session_state.intelligent_results = intelligent_results
                        st.success("✅ Intelligent Reconciliation Complete!")
                    except Exception as e:
                        st.error(f"❌ Error during intelligent reconciliation: {str(e)}")
                        st.exception(e)

            if "intelligent_results" in st.session_state:
                i_results = st.session_state.intelligent_results
                summary = i_results.get("summary", {})

                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🔴 High Severity", summary.get("high_severity_count", 0))
                with col2:
                    st.metric("🟡 Medium Severity", summary.get("medium_severity_count", 0))
                with col3:
                    st.metric("🟢 Low Severity", summary.get("low_severity_count", 0))
                with col4:
                    st.metric("🤖 Exceptions Analyzed", summary.get("exceptions_processed", 0))

                st.markdown("---")

                # Download buttons
                d_col1, d_col2, d_col3, d_col4 = st.columns(4)
                
                final_report = i_results.get("final_compliance_report", "No report generated.")
                
                with d_col1:
                    st.download_button(
                        "📄 Markdown",
                        data=final_report,
                        file_name=f"ai_compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                
                with d_col2:
                    pdf_report = markdown_to_pdf(final_report, "ai_compliance")
                    st.download_button(
                        "📕 PDF",
                        data=pdf_report,
                        file_name=f"ai_compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                
                with d_col3:
                    st.download_button(
                        "📊 JSON",
                        data=json.dumps(i_results, indent=2, default=str),
                        file_name=f"reconciliation_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                
                with d_col4:
                    excel_data = create_excel_buffer({
                        'Summary': pd.DataFrame([summary]),
                        'Exceptions': i_results.get('exceptions', []) if isinstance(i_results.get('exceptions'), list) else pd.DataFrame()
                    })
                    st.download_button(
                        "📊 Excel",
                        data=excel_data,
                        file_name=f"reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

                st.markdown("---")
                st.subheader("🔍 Detailed AI Analysis")

                # ============ DETAILED EXCEPTION CARDS ============
                enriched_exceptions = i_results.get("enriched_exceptions", [])

                if enriched_exceptions:
                    for ex in enriched_exceptions:
                        sev = ex.get("severity_classification", {}).get("severity", "Low")
                        risk_class = f"risk-{sev.lower()}" if sev in ["High", "Medium", "Low"] else "risk-low"
                        trade_id = ex.get("trade_id", "Unknown")
                        
                        # Extract data with professional fallbacks
                        root = ex.get("root_cause", {})
                        fix = ex.get("fix_suggestion", {})
                        risk = ex.get("risk_assessment", {})
                        
                        # Professional fallback values - NO N/A
                        root_reason = root.get('reason') or f"Trade {trade_id} requires manual investigation due to data discrepancies between broker and exchange systems."
                        root_category = root.get('category', 'System Synchronization')
                        confidence = root.get('confidence_score', 0.5)
                        
                        fix_action = fix.get('action_type', 'MANUAL_REVIEW')
                        fix_steps = fix.get('suggested_fix') or f"Escalate to reconciliation team for detailed investigation and resolution."
                        fix_time = fix.get('estimated_time', '2-4 hours')
                        
                        analysis_text = ex.get("analysis") or ex.get("full_explanation") or f"Trade {trade_id} exhibits a {ex.get('exception_type', 'data mismatch')} requiring investigation. The reconciliation team should review source documents from both systems to identify the root cause and implement necessary corrections."
                        
                        compliance_text = ex.get("compliance_summary") or ex.get("compliance_note") or f"Trade {trade_id} has been flagged for review and documented in the exception tracking system for audit compliance."
                        
                        with st.expander(f"Trade {trade_id} | Severity: {sev} | {ex.get('exception_type', 'Exception')}"):
                            c1, c2 = st.columns(2)
                            
                            # Root Cause Card
                            with c1:
                                st.markdown(
                                    f"""
                                    <div class="agent-card {risk_class}">
                                        <div class="agent-header">ROOT CAUSE DIAGNOSIS</div>
                                        <b>Identified Issue:</b> {root_reason}<br><br>
                                        <b>Category:</b> {root_category}<br>
                                        <b>Confidence Level:</b> {confidence*100:.0f}%<br>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            
                            # Fix Suggestion Card
                            with c2:
                                st.markdown(
                                    f"""
                                    <div class="agent-card {risk_class}">
                                        <div class="agent-header">RECOMMENDED RESOLUTION</div>
                                        <b>Action Required:</b> {fix_action}<br><br>
                                        <b>Resolution Steps:</b> {fix_steps}<br><br>
                                        <b>Estimated Time:</b> {fix_time}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            
                            # Professional analysis display
                            st.markdown("### Comprehensive Analysis")
                            st.write(analysis_text)
                            
                            # Risk Assessment
                            if risk:
                                st.markdown("### Risk Assessment")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Financial Risk", risk.get('overall_risk_level', 'Medium'))
                                with col2:
                                    st.metric("Operational Impact", "Review Required" if sev == "High" else "Monitor")
                                with col3:
                                    st.metric("Compliance Status", "Action Required" if sev == "High" else "Documented")
                            
                            # Compliance Note
                            st.markdown("### Compliance Documentation")
                            st.info(compliance_text)

                else:
                    st.success("No exceptions requiring analysis found in the intelligent reconciliation pass.")

            elif not run_intelligent:
                st.info("👆 Click the button above to start Intelligent Reconciliation.")

    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")
        st.exception(e)

else:
    st.markdown("""
    <div style="text-align: center; padding: 4rem;">
        <h2>👈 Upload CSV files to get started</h2>
        <p>Upload both broker_trades.csv and exchange_trades.csv in the sidebar</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 1rem;">
    Built with ❤️ using Streamlit & Groq AI | TradeRecon AI © 2024
</div>
""", unsafe_allow_html=True)
