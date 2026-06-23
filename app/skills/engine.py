import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

class SkillEngine:
    """
    Titan-Lite Skill Engine
    Responsible for loading Markdown skills and injecting real-time data + knowledge anchors.
    Aligned with 'Core Engine 4.4' design.
    """
    def __init__(self, skills_dir: str = "app/skills"):
        self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.skills_dir = os.path.join(self.base_path, skills_dir)
        self.knowledge_path = os.path.join(self.skills_dir, "knowledge_anchors.json")
        os.makedirs(self.skills_dir, exist_ok=True)

    def load_skill(self, skill_name: str) -> str:
        """Loads a raw Markdown skill file."""
        file_path = os.path.join(self.skills_dir, f"{skill_name}.md")
        if not os.path.exists(file_path):
            return f"Error: Skill {skill_name} not found."
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_seasonal_context(self) -> str:
        """
        Retrieves soft seasonal anchors based on current date.
        Weight is kept low by phrasing them as 'Historical Context' rather than 'Directives'.
        """
        if not os.path.exists(self.knowledge_path):
            return ""
        
        try:
            with open(self.knowledge_path, "r", encoding="utf-8") as f:
                anchors = json.load(f)
            
            month = datetime.now().month
            quarter = f"Q{(month-1)//3 + 1}"
            
            data = anchors.get("seasonality", {}).get(quarter, {})
            if not data:
                return ""
            
            context = f"\n### [Historical Seasonal Context - {quarter}]\n"
            context += f"- **Typical Strong Sectors**: {', '.join(data.get('bull', []))}\n"
            context += f"- **Typical Weak Sectors**: {', '.join(data.get('bear', []))}\n"
            context += "- **Note**: Use this only as a secondary prior. Real-time data takes precedence.\n"
            return context
        except Exception:
            return ""

    def render_skill(self, skill_name: str, data: Dict[str, Any]) -> str:
        """
        Renders a skill by injecting dynamic data and knowledge anchors.
        """
        template = self.load_skill(skill_name)
        
        # Inject seasonal context if it's a macro/strategy skill
        if "macro" in skill_name or "strategy" in skill_name:
            seasonal = self.get_seasonal_context()
            template = template.replace("{{seasonal_context}}", seasonal)
        
        # Simple string replacement for other variables
        for key, value in data.items():
            placeholder = "{{" + key + "}}"
            template = template.replace(placeholder, str(value))
            
        return template

# Singleton Instance
skill_engine = SkillEngine()
