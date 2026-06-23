import asyncio
import os
import sys
import time
from typing import Dict, Any

# Ensure we can import from app/
sys.path.append(os.path.abspath("app"))

from orchestrator.engine import TitanWorkflowEngine
from orchestrator.workflows import MARKET_SCAN_WORKFLOW
from orchestrator.context import UserContext
from sys_logger import sys_logger

async def run_self_test():
    print("🚀 Starting Full-Flow Self-Test (Dashboard Edition)...")
    
    # 1. Setup User Context
    user_id = "test_admin"
    storage_root = f"docs/projects/titan-lite/users/{user_id}"
    user_ctx = UserContext(
        user_id=user_id,
        role="ADMIN",
        storage_root=storage_root
    )
    
    # 2. Initialize Logger for this user
    sys_logger.__init__(storage_root=user_ctx.storage_root)
    # sys_logger.clear() # Keep logs for debugging if needed
    
    # 3. Initialize Workflow Engine
    engine = TitanWorkflowEngine()
    job_id = f"test_dash_{int(time.time())}"
    
    print(f"📦 Job ID: {job_id}")
    print(f"📂 Storage: {storage_root}")

    # 4. Execute Market Scan Workflow
    try:
        context = await engine.execute(
            job_id=job_id,
            ticker="MARKET",
            workflow_dsl=MARKET_SCAN_WORKFLOW,
            user_ctx=user_ctx,
            initial_payload={"market": "Global"}
        )
        
        print("\n✅ Workflow Execution Completed!")
        
        # 5. Verify Dashboard Artifacts
        report_dir = os.path.join(storage_root, "reports", "macro")
        reports = sorted([r for r in os.listdir(report_dir) if r.endswith(".md") and r != "index.md"], reverse=True)
        
        if reports:
            latest_report = os.path.join(report_dir, reports[0])
            print(f"  [OK] Latest Dashboard Report: {latest_report}")
            with open(latest_report, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Check for Cockpit Header
                if "## 🎛️ 策略驾驶舱" in content:
                    print("  [OK] Found Cockpit Header.")
                if "### 🚀 快捷研报导航" in content:
                    print("  [OK] Found Navigation Matrix.")
                
                # Check for Image references
                if "![Valuation Scatter]" in content:
                    print("  [OK] Found Scatter Plot reference.")
                
                # Check for Interactive Glossary Anchors
                import re
                anchors = re.findall(r'\[.*?\]\(#.*?\)', content)
                if anchors:
                    print(f"  [OK] Found {len(anchors)} Glossary anchors (e.g., {anchors[0]}).")
                else:
                    print("  [WARN] No Glossary anchors found in the report body.")
                
                # Check for Encyclopedia Section
                if "百科" in content or "术语解释" in content:
                    print("  [OK] Found Encyclopedia/Glossary section.")
                else:
                    print("  [FAIL] Encyclopedia section missing!")

                # Check for Chinese content
                if any('\u4e00' <= char <= '\u9fff' for char in content):
                    print("  [OK] Content is in Chinese.")
                else:
                    print("  [FAIL] Content is NOT in Chinese!")

        else:
            print(f"  [FAIL] No macro report found in {report_dir}")

    except Exception as e:
        print(f"\n❌ Self-Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_self_test())
