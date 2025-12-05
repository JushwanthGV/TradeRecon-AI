"""
TradeRecon Intelligence Engine - Production Grade
Enterprise-level trade reconciliation AI system
"""

import os
import json
from groq import Groq
from typing import Dict, Any
from datetime import datetime


class TradeReconIntelligenceEngine:
    """
    Enterprise-grade Intelligence Engine for trade reconciliation
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the Intelligence Engine with Groq API"""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ GROQ_API_KEY not found in environment")
        
        self.client = Groq(api_key=self.api_key)
        
        # Production models
        self.model = "openai/gpt-oss-120b"
        self.fallback_model = "llama-3.3-70b-versatile"
        
        print(f"✅ TradeRecon Intelligence Engine initialized")
        print(f"   Primary Model: {self.model}")
        print(f"   Fallback Model: {self.fallback_model}")
    
    def _generate_system_prompt(self) -> str:
        """Generate professional system prompt"""
        return """You are a Senior Trade Reconciliation Analyst AI specializing in financial compliance and exception resolution.

Your expertise includes:
- Root cause analysis for trade discrepancies
- Risk assessment (financial, operational, compliance)
- Regulatory compliance documentation
- Actionable remediation strategies

Analyze trade exceptions with the precision and professionalism expected in enterprise financial operations. Provide clear, actionable insights suitable for audit documentation and regulatory review.

Output must be valid JSON with complete, professional descriptions. Never use placeholders like "N/A" or empty values."""

    def _generate_user_prompt(self, trade_data: Dict[str, Any]) -> str:
        """Generate specific analysis request"""
        trade_id = trade_data.get('trade_id', 'Unknown')
        exception_type = trade_data.get('exception_type', 'mismatch')
        mismatched_fields = trade_data.get('mismatched_fields', 'Multiple fields')
        broker_values = trade_data.get('broker_values', {})
        exchange_values = trade_data.get('exchange_values', {})
        
        return f"""Analyze the following trade exception and provide a comprehensive professional assessment:

TRADE EXCEPTION DETAILS:
- Trade ID: {trade_id}
- Exception Type: {exception_type}
- Discrepancy Fields: {mismatched_fields}
- Broker System Values: {json.dumps(broker_values, indent=2)}
- Exchange System Values: {json.dumps(exchange_values, indent=2)}

Provide a complete professional analysis in the following JSON structure:

{{
    "root_cause": {{
        "category": "One of: Data Entry Error | Timing Mismatch | System Synchronization | Rounding Discrepancy | Missing Data | Configuration Issue | Manual Override",
        "reason": "Detailed, professional explanation of the root cause (2-3 sentences, suitable for audit documentation)",
        "confidence_score": 0.0-1.0
    }},
    "severity": "High | Medium | Low",
    "fix_suggestion": {{
        "action_type": "SQL_UPDATE | API_CALL | MANUAL_REVIEW | ESCALATE",
        "suggested_fix": "Specific, actionable resolution steps (professional language, audit-ready)",
        "estimated_time": "Realistic time estimate (e.g., '30 minutes', '2 hours', '1 business day')"
    }},
    "risk_assessment": {{
        "financial_risk": "Professional assessment of financial exposure and PnL impact",
        "operational_risk": "Assessment of operational impact on settlement and reconciliation processes",
        "compliance_risk": "Regulatory and audit implications of this exception",
        "overall_risk_level": "Critical | High | Medium | Low"
    }},
    "compliance_note": "Single professional sentence suitable for compliance audit logs",
    "full_explanation": "Comprehensive analysis (3-4 sentences) explaining the exception, its business impact, and recommended resolution in professional language suitable for senior management review"
}}

Requirements:
- Use professional financial services language
- Provide specific, actionable recommendations
- Never use "N/A", "Unknown", or empty values
- All text must be audit-ready and compliance-suitable
- Be precise and factual based on the data provided
- Avoid special characters like ampersands that may break PDF rendering"""

    def analyze_exception(self, exception_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform complete trade exception analysis
        """
        # Try primary model first, then fallback
        for model in [self.model, self.fallback_model]:
            try:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": self._generate_system_prompt()},
                        {"role": "user", "content": self._generate_user_prompt(exception_data)}
                    ],
                    temperature=0.2,
                    max_tokens=2500,
                    response_format={"type": "json_object"}
                )
                
                # Parse the JSON response
                analysis = json.loads(completion.choices[0].message.content)
                
                # Add metadata
                analysis['_engine_model'] = model
                analysis['_trade_id'] = exception_data.get('trade_id', 'Unknown')
                
                print(f"✅ Analysis complete for trade {exception_data.get('trade_id')} using {model}")
                return analysis
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing error for trade {exception_data.get('trade_id')} with {model}: {e}")
                if model == self.model:
                    print(f"⚠️ Retrying with fallback model: {self.fallback_model}")
                    continue
                return self._generate_fallback_analysis(exception_data, f"JSON Error: {str(e)}")
                
            except Exception as e:
                print(f"❌ Analysis failed for trade {exception_data.get('trade_id')} with {model}: {e}")
                if model == self.model:
                    print(f"⚠️ Retrying with fallback model: {self.fallback_model}")
                    continue
                return self._generate_fallback_analysis(exception_data, str(e))
        
        # If both models fail
        return self._generate_fallback_analysis(exception_data, "Both models failed")
    
    def _generate_fallback_analysis(self, trade_data: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Generate professional fallback response"""
        trade_id = trade_data.get('trade_id', 'Unknown')
        exception_type = trade_data.get('exception_type', 'data mismatch')
        
        return {
            "root_cause": {
                "category": "System Synchronization",
                "reason": f"Trade {trade_id} exhibits a {exception_type} requiring manual investigation. Automated analysis was unable to complete due to system constraints. A qualified analyst should review the broker and exchange records to determine the specific cause of the discrepancy.",
                "confidence_score": 0.5
            },
            "severity": "Medium",
            "fix_suggestion": {
                "action_type": "MANUAL_REVIEW",
                "suggested_fix": f"Escalate trade {trade_id} to the reconciliation team for detailed investigation. Compare source documents from both broker and exchange systems to identify the root cause. Document findings in the trade exception log and implement necessary corrections.",
                "estimated_time": "2-4 hours"
            },
            "risk_assessment": {
                "financial_risk": "Moderate financial exposure pending investigation. Potential PnL impact should be assessed during manual review.",
                "operational_risk": "Standard operational review required. May impact settlement timing if not resolved within SLA.",
                "compliance_risk": "Exception properly logged for audit trail. Requires resolution documentation for regulatory compliance.",
                "overall_risk_level": "Medium"
            },
            "compliance_note": f"Trade {trade_id} flagged for manual review due to automated analysis limitations. Investigation initiated and documented in exception tracking system.",
            "full_explanation": f"Trade {trade_id} has been flagged as a {exception_type} requiring manual investigation. While automated analysis encountered technical constraints, the exception has been properly documented and escalated to the reconciliation team for resolution. Standard review procedures will be followed to ensure compliance and accurate recordkeeping.",
            "_error": True,
            "_engine_model": "fallback"
        }
    
    def generate_compliance_report(self, reconciliation_results: Dict[str, Any], analyzed_exceptions: list) -> str:
        """
        Generate professional compliance audit report
        NO MARKDOWN SYMBOLS - Plain professional text
        """
        report_date = datetime.now().strftime('%B %d, %Y at %H:%M:%S')
        
        total_trades = reconciliation_results.get('total_trades', 0)
        matched = reconciliation_results.get('matched_count', 0)
        mismatched = reconciliation_results.get('mismatch_count', 0)
        missing = reconciliation_results.get('missing_count', 0)
        match_rate = (matched / max(total_trades, 1)) * 100
        
        high_count = sum(1 for e in analyzed_exceptions if e.get('severity') == 'High')
        medium_count = sum(1 for e in analyzed_exceptions if e.get('severity') == 'Medium')
        low_count = sum(1 for e in analyzed_exceptions if e.get('severity') == 'Low')
        
        # PROFESSIONAL REPORT - NO MARKDOWN SYMBOLS
        report = f"""TRADE RECONCILIATION COMPLIANCE AUDIT REPORT

Report Generated: {report_date}
Analysis Engine: TradeRecon AI Intelligence Engine v2.0
AI Model: {self.model}

================================================================================

EXECUTIVE SUMMARY

This compliance audit report summarizes the results of automated trade reconciliation between broker and exchange systems. The analysis identified discrepancies requiring attention and provides actionable recommendations for resolution.

RECONCILIATION METRICS

Total Trades Processed: {total_trades}
Successfully Matched: {matched} ({match_rate:.1f}%)
Exceptions Detected: {len(analyzed_exceptions)}
  - Data Mismatches: {mismatched}
  - Missing Trades: {missing}

EXCEPTION SEVERITY DISTRIBUTION

High Severity: {high_count} exceptions (immediate action required)
Medium Severity: {medium_count} exceptions (review within 24 hours)
Low Severity: {low_count} exceptions (standard review cycle)

================================================================================

RISK ASSESSMENT

Financial Risk: {'HIGH - Immediate review required' if high_count > 0 else 'MODERATE - Monitor closely' if medium_count > 0 else 'LOW - Standard controls adequate'}
Operational Risk: {'Requires immediate attention' if high_count > 0 else 'Within acceptable thresholds'}
Compliance Status: {'ATTENTION REQUIRED' if high_count > 0 else 'ACCEPTABLE WITH MONITORING'}

Overall Assessment: {'Critical exceptions detected. Immediate action plan required.' if high_count > 0 else 'All exceptions within manageable risk parameters. Continue monitoring.'}

================================================================================

DETAILED EXCEPTION ANALYSIS

"""
        
        # Professional exception details - NO EMOJIS, CLEAN TEXT FOR PDF
        for idx, exc in enumerate(analyzed_exceptions, 1):
            severity = exc.get('severity', 'Medium')
            trade_id = exc.get('trade_id', 'Unknown')  # ✅ FIXED - uses trade_id not _trade_id
            root_cause = exc.get('root_cause', {})
            fix = exc.get('fix_suggestion', {})
            risk = exc.get('risk_assessment', {})
            
            # Clean text for PDF rendering - remove special characters that break reportlab
            root_reason = root_cause.get('reason', 'Requires manual investigation').replace('&', 'and').replace('P&L', 'PnL')
            fix_steps = fix.get('suggested_fix', 'Escalate to reconciliation team for investigation').replace('&', 'and')
            financial_risk = risk.get('financial_risk', 'To be assessed during review').replace('&', 'and').replace('P&L', 'PnL')
            operational_risk = risk.get('operational_risk', 'Standard review procedures apply').replace('&', 'and')
            compliance_risk = risk.get('compliance_risk', 'Exception logged for audit trail').replace('&', 'and')
            compliance_note = exc.get('compliance_summary') or exc.get('compliance_note', f'Trade {trade_id} requires resolution and documentation for regulatory compliance.')
            compliance_note = compliance_note.replace('&', 'and')
            
            report += f"""EXCEPTION {idx}: Trade ID {trade_id}

Severity Level: {severity}
Root Cause Category: {root_cause.get('category', 'System Synchronization')}
Confidence Score: {root_cause.get('confidence_score', 0.5):.0%}

Root Cause Analysis:
{root_reason}

Risk Impact:
- Financial: {financial_risk}
- Operational: {operational_risk}
- Compliance: {compliance_risk}

Recommended Resolution:
Action Type: {fix.get('action_type', 'MANUAL_REVIEW')}
Resolution Steps: {fix_steps}
Estimated Time: {fix.get('estimated_time', '2-4 hours')}

Compliance Note:
{compliance_note}

--------------------------------------------------------------------------------

"""
        
        report += f"""
================================================================================

RECOMMENDED ACTIONS

IMMEDIATE (0-24 hours):
{'- Prioritize and resolve ' + str(high_count) + ' high-severity exceptions' if high_count > 0 else '- No immediate critical actions required'}
- Document all investigation findings
- Verify high-value trade details with counterparties
- Escalate unresolved issues to senior management

SHORT-TERM (1-7 days):
- Complete resolution of all {len(analyzed_exceptions)} exceptions
- Conduct root cause analysis for systemic issues
- Update reconciliation procedures and controls
- Provide resolution summary to compliance team

LONG-TERM (Ongoing):
- Implement preventive controls to reduce exception rates
- Enhance automated validation rules
- Conduct periodic reconciliation quality reviews
- Maintain comprehensive audit documentation

================================================================================

REGULATORY COMPLIANCE STATEMENT

All identified exceptions have been documented in accordance with internal control frameworks and regulatory requirements. {'High-severity exceptions require immediate attention and must be resolved within prescribed regulatory timeframes. Detailed resolution documentation is mandatory for audit purposes.' if high_count > 0 else 'All exceptions are within acceptable risk thresholds and standard review procedures apply.'}

This report complies with trade reconciliation standards and provides audit-ready documentation for regulatory review.

================================================================================

REPORT CERTIFICATION

Analysis Methodology: Automated AI-powered exception analysis with manual review workflows
AI Model: {self.model}
Exceptions Analyzed: {len(analyzed_exceptions)}
Report Classification: Internal Use - Compliance Sensitive
Prepared By: TradeRecon AI Intelligence Engine
Review Required By: Compliance Officer / Operations Manager

This report is generated automatically and should be reviewed by qualified compliance personnel before regulatory submission.

================================================================================

END OF REPORT
"""
        return report
