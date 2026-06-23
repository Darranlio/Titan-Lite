from typing import Dict, Any

# Standard Deep Research Workflow for a Single Ticker
# Sequential execution to ensure consistency
TICKER_DEEP_RESEARCH_WORKFLOW = {
    "id": "ticker_deep_research",
    "steps": [
        {
            "id": "analysis_phase",
            "mode": "SEQUENTIAL",
            "actions": ["deep_analysis"]
        },
        {
            "id": "export_phase",
            "mode": "SEQUENTIAL",
            "actions": ["persistence", "system_build"]
        }
    ]
}

# Full Market Scan Workflow
# End-to-end orchestration from discovery to final build
MARKET_SCAN_WORKFLOW = {
    "id": "market_scan",
    "steps": [
        {
            "id": "risk_check",
            "mode": "SEQUENTIAL",
            "actions": ["macro_risk"]
        },
        {
            "id": "discovery_phase",
            "mode": "SEQUENTIAL",
            "actions": ["discovery", "fast_filter"]
        },
        {
            "id": "multi_ticker_analysis",
            "mode": "SEQUENTIAL",
            "actions": ["batch_ticker_executor"]
        },
        {
            "id": "visualization_phase",
            "mode": "PARALLEL",
            "actions": ["fetch_sector_heatmap", "valuation_scatter"]
        },
        {
            "id": "market_summary",
            "mode": "SEQUENTIAL",
            "actions": ["market_panorama", "system_build"]
        }
    ]
}
