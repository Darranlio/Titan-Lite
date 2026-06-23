import os
import json
import shutil
import sys

# 增加 app 路径到 sys.path 模拟运行环境
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "app"))

from archive_manager import ArchiveManager
from utils import sanitize_json_data

# 1. 准备模拟测试环境
TEST_ROOT = "test_reports"
if os.path.exists(TEST_ROOT): shutil.rmtree(TEST_ROOT)
os.makedirs(os.path.join(TEST_ROOT, "reports", "AAPL"), exist_ok=True)

# 2. 写入一个包含非法 NaN 的 metadata.json
bad_data = [
    {
        "date": "2026-06-06",
        "file": "2026-06-06_1200",
        "price": float('nan'),
        "upside": float('nan')
    }
]

# 模拟磁盘上已经存在的非法数据
with open(os.path.join(TEST_ROOT, "reports", "AAPL", "metadata.json"), "w") as f:
    json.dump(bad_data, f)

# 3. 初始化 ArchiveManager
mgr = ArchiveManager(storage_root=TEST_ROOT)

try:
    # 模拟 /archive/list 的完整链路
    results = mgr.get_all_reports()
    final_output = sanitize_json_data(results)
    
    # 验证 JSON 序列化
    json_str = json.dumps(final_output)
    
    if "null" in json_str and "nan" not in json_str.lower():
        print("✅ [SELF-TEST PASSED] Invalid NaN values in disk files are correctly sanitized and serializable.")
        print(f"Serialized Output: {json_str}")
    else:
        print("❌ [SELF-TEST FAILED] JSON output still contains invalid values.")
except Exception as e:
    print(f"❌ [SELF-TEST ERROR] {e}")
finally:
    if os.path.exists(TEST_ROOT): shutil.rmtree(TEST_ROOT)

