"""
TradeRecon AI - Main Orchestrator
UPGRADED: Now powered by a single unified Intelligence Engine
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any
import pandas as pd

# Import the new Intelligence Engine
from agents import TradeReconIntelligenceEngine

# Load environment variables
def load_env():
    """Load .env file from project root"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"✅ Loaded .env from: {env_path}")
        return True
    else:
        print(f"❌ .env file not found at: {env_path}")
        return False

ENV_LOADED = load_env()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

class TradeReconOrchestrator:
    """
    Orchestrator that manages the Intelligence Engine
    """
    
    def __init__(self, api_key: str = None):
        """Initialize with the unified Intelligence Engine"""
        try:
            self.engine = TradeReconIntelligenceEngine(api_key=api_key or GROQ_API_KEY)
            self.agents_initialized = True
            print("✅ TradeRecon Orchestrator ready")
        except Exception as e:
            print(f"❌ Failed to initialize Intelligence Engine: {e}")
            self.agents_initialized = False
    
    def run_full_reconciliation(
        self,
        broker_df: pd.DataFrame,
        exchange_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Run complete reconciliation workflow with Intelligence Engine
        """
        if not self.agents_initialized:
            return {
                'error': 'Intelligence Engine not initialized. Check GROQ_API_KEY.',
                'summary': {},
                'enriched_exceptions': []
            }
        
        print("\n" + "="*60)
        print("🚀 TradeRecon Intelligence Engine - STARTING")
        print("="*60 + "\n")
        
        # Step 1: Run local reconciliation (matching logic)
        from matching import reconcile_trades
        results = reconcile_trades(broker_df, exchange_df)
        
        print(f"✅ Trade matching complete:")
        print(f"   Total: {results['total_trades']}")
        print(f"   Matched: {results['matched_count']}")
        print(f"   Exceptions: {results['mismatch_count'] + results['missing_count']}")
        
        # Step 2: Analyze each exception with the Intelligence Engine (1 call per exception)
        exceptions_df = results['exceptions']
        enriched_exceptions = []
        
        if len(exceptions_df) > 0:
            print(f"\n🤖 Analyzing {len(exceptions_df)} exceptions with Intelligence Engine...\n")
            
            for idx, row in exceptions_df.iterrows():
                exception_dict = row.to_dict()
                trade_id = exception_dict.get('trade_id', 'Unknown')
                
                print(f"   [{idx+1}/{len(exceptions_df)}] Processing Trade {trade_id}...")
                
                # SINGLE UNIFIED CALL
                ai_analysis = self.engine.analyze_exception(exception_dict)

                # Merge original data with AI insights
                enriched = {
                    **exception_dict,
                    'root_cause': ai_analysis.get('root_cause', {}),
                    'severity_classification': {'severity': ai_analysis.get('severity', 'Medium')},
                    'fix_suggestion': ai_analysis.get('fix_suggestion', {}),
                    'risk_assessment': ai_analysis.get('risk_assessment', {}),
                    'analysis': ai_analysis.get('full_explanation') or f"Trade {trade_id} requires investigation due to {exception_dict.get('exception_type', 'data mismatch')}. The reconciliation team should review source documents to identify root cause and implement corrections.",
                    'compliance_summary': ai_analysis.get('compliance_note') or f"Trade {trade_id} flagged for review and documented in exception tracking system for audit compliance.",
                    'severity': ai_analysis.get('severity', 'Medium')  # ADD THIS LINE - needed for report
                }

                enriched_exceptions.append(enriched)
                print(f"   ✅ Complete\n")
        
        # Step 3: Generate compliance report
        print("📄 Generating compliance report...")
        final_report = self.engine.generate_compliance_report(results, enriched_exceptions)
        
        # Compile final results
        final_results = {
            'summary': {
                'total_trades': results['total_trades'],
                'matched_count': results['matched_count'],
                'mismatch_count': results['mismatch_count'],
                'missing_count': results['missing_count'],
                'exceptions_processed': len(enriched_exceptions),
                'high_severity_count': sum(1 for e in enriched_exceptions 
                                          if e.get('severity_classification', {}).get('severity') == 'High'),
                'medium_severity_count': sum(1 for e in enriched_exceptions 
                                            if e.get('severity_classification', {}).get('severity') == 'Medium'),
                'low_severity_count': sum(1 for e in enriched_exceptions 
                                         if e.get('severity_classification', {}).get('severity') == 'Low'),
            },
            'exceptions': results['exceptions'],
            'enriched_exceptions': enriched_exceptions,
            'final_compliance_report': final_report
        }
        
        print("\n" + "="*60)
        print("✅ INTELLIGENCE ENGINE ANALYSIS COMPLETE!")
        print("="*60 + "\n")
        
        return final_results

# Global orchestrator instance
orchestrator = None

def get_orchestrator() -> TradeReconOrchestrator:
    """Get or create the global orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        orchestrator = TradeReconOrchestrator()
    return orchestrator

def run_full_reconciliation(broker_df: pd.DataFrame, exchange_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run complete autonomous reconciliation workflow
    """
    orch = get_orchestrator()
    return orch.run_full_reconciliation(broker_df, exchange_df)
