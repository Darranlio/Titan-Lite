import pytest
import os
import json
from datetime import datetime
from app.skills.engine import SkillEngine

@pytest.fixture
def skill_engine():
    # Use the default app/skills directory for testing if it exists, 
    # or a mock one if needed. Here we use the actual one.
    return SkillEngine()

def test_load_skill(skill_engine):
    # Test loading an existing skill
    content = skill_engine.load_skill("cio_macro_strategy")
    assert "# Skill: CIO Global Macro Strategy & Outlook" in content
    assert "{{seasonal_context}}" in content

def test_load_non_existent_skill(skill_engine):
    content = skill_engine.load_skill("non_existent_skill")
    assert "Error: Skill non_existent_skill not found." in content

def test_get_seasonal_context(skill_engine):
    context = skill_engine.get_seasonal_context()
    month = datetime.now().month
    quarter = f"Q{(month-1)//3 + 1}"
    
    if context:
        assert f"### [Historical Seasonal Context - {quarter}]" in context
        assert "**Typical Strong Sectors**" in context
        assert "**Typical Weak Sectors**" in context
    else:
        # If knowledge_anchors.json is missing or quarter not found
        assert context == ""

def test_render_skill(skill_engine):
    data = {
        "candidates": "['AAPL', 'TSLA']",
        "winners": "['AAPL']",
        "benchmarks": "S&P 500: +1.2%",
        "sector_perf": "Tech: Strong",
        "hot": "AI, Inflation"
    }
    
    rendered = skill_engine.render_skill("cio_macro_strategy", data)
    
    assert "# Skill: CIO Global Macro Strategy & Outlook" in rendered
    assert "['AAPL', 'TSLA']" in rendered
    assert "['AAPL']" in rendered
    assert "S&P 500: +1.2%" in rendered
    assert "Tech: Strong" in rendered
    assert "AI, Inflation" in rendered
    
    # Check if seasonal context was injected (it contains {{seasonal_context}} in the template)
    # The render_skill method replaces {{seasonal_context}} if macro/strategy is in name
    assert "### [Historical Seasonal Context" in rendered
