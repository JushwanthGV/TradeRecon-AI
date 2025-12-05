# TradeRecon AI — Single-Engine Reconciliation

AI-powered trade reconciliation with a single unified Intelligence Engine that analyzes exceptions end-to-end, generates audit-ready reports, and exposes a streamlined Streamlit UI for operations teams. [file:130][file:129]

## Overview
TradeRecon AI reconciles broker and exchange trades, flags mismatches or missing records, and performs one-call AI analysis per exception to produce root cause, severity, fix suggestions, and risk assessments in a structured JSON format. [file:156][file:129] The orchestrator coordinates matching, exception analysis, and compliance report generation, with configuration via a `GROQ_API_KEY` in a `.env` file. [file:130]

## Features
- **Robust reconciliation engine**  
  Validates required columns (`trade_id`, `symbol`, `side`, `quantity`, `price`, `currency`, `trade_time`, `account_id`), compares broker vs exchange with tolerance for numeric fields and time drift, and classifies severity based on impact. [file:156]

- **Single-call Intelligence Engine**  
  Uses a unified prompt against `openai/gpt-oss-120b` with `llama-3.3-70b-versatile` as fallback, returning:
  - `root_cause` (category, professional explanation, confidence_score)  
  - `severity` (High/Medium/Low)  
  - `fix_suggestion` (action_type, suggested_fix, estimated_time)  
  - `risk_assessment` (financial, operational, compliance, overall_risk_level)  
  - `compliance_note` and `full_explanation` for audit logs. [file:129]

- **Automated compliance report generation**  
  Builds a plain-text, audit-ready compliance report including reconciliation metrics, severity distribution, detailed exception sections, and recommended actions. [file:129]

- **Streamlit-based UI**  
  Provides dashboards for total trades, matched, mismatched, and missing counts, exception tables, and intelligent reconciliation with export to PDF, Excel, Markdown, and JSON. [file:132]

- **Environment-driven configuration**  
  Loads `.env` from project root, validates presence of `GROQ_API_KEY`, and fails fast if not configured. [file:130]

## Architecture

### Components
- **`matching.py`**  
  - Merges broker and exchange trades on `trade_id`.  
  - Detects:
    - `missing_in_exchange` and `missing_in_broker` cases.  
    - `mismatch` cases across symbol, side, quantity, price, currency, account_id, and trade_time (with tolerance).  
  - Returns `results` dict with counts and an `exceptions` DataFrame. [file:156]

- **`intelligence_engine.py`**  
  - Class `TradeReconIntelligenceEngine` encapsulates Groq client, models, and prompt design.  
  - `analyze_exception()` runs a single chat completion per exception, parses JSON, and enriches with model metadata, retrying on JSON errors with a fallback model or generating a professional fallback analysis.  
  - `generate_compliance_report()` summarizes reconciliation results and analyzed exceptions into a structured, audit-ready text report. [file:129]

- **`main.py` (Orchestrator)**  
  - Loads environment.  
  - Instantiates `TradeReconIntelligenceEngine`.  
  - `run_full_reconciliation()`:
    - Runs `reconcile_trades()` to get base results. [file:156]  
    - Iterates exceptions, calling `engine.analyze_exception()` for each. [file:129]  
    - Builds `enriched_exceptions` and calls `engine.generate_compliance_report()`.  
    - Returns a dictionary with `summary`, raw `exceptions`, `enriched_exceptions`, and `final_compliance_report`. [file:130]

- **`app.py` (Streamlit UI)**  
  - Loads `.env`, sets Streamlit page config.  
  - Lets the user upload broker and exchange CSVs, runs reconciliation, and displays metrics and exceptions.  
  - Offers an “Intelligent Reconciliation” button that calls the orchestrator’s `run_full_reconciliation` and exposes:
    - Severity metrics.  
    - Detailed exception cards (root cause, fix recommendation, risk assessment, compliance note).  
    - Download buttons for Markdown, PDF, JSON, and Excel exports. [file:132][file:130]

## Requirements

Key dependencies (see `requirements.txt` for versions): [file:155]

- `streamlit`  
- `pandas`  
- `numpy`  
- `python-dotenv`  
- `requests`  
- `groq`  
- `openpyxl`  
- `reportlab`






Demo-Video link:
https://drive.google.com/file/d/1pqb09AvIkC7lLN1lIlTCBE9LlnyrQPtp/view?usp=drive_link
