import pytest
from analytical_engine import analytical_engine
from unittest.mock import MagicMock, patch

def test_translation_purity():
    """Verify that translation is now handled by AnalyticalEngine."""
    summary_en = "NVIDIA is a leader in AI computing."
    
    # Patch the existing client instance on the singleton
    with patch.object(analytical_engine.client.chat.completions, 'create') as mock_create:
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "英伟达是AI计算的领导者。"
        mock_create.return_value = mock_response
        
        res = analytical_engine.translate_business_summary(summary_en)
        assert "英伟达" in res
        assert "AI" in res
        mock_create.assert_called_once()

def test_fact_sheet_generation():
    """Verify Fact Sheet structure."""
    verify_data = {
        "fact_score": 85,
        "fact_check": "Everything looks good.",
        "divergence": "Bullish Divergence",
        "insider": "Heavy Buying"
    }
    
    fact_sheet = analytical_engine.generate_fact_sheet("NVDA", verify_data)
    
    assert "[FACT SHEET - NVDA]" in fact_sheet
    assert "85" in fact_sheet
    assert "Bullish Divergence" in fact_sheet
    assert "Heavy Buying" in fact_sheet
