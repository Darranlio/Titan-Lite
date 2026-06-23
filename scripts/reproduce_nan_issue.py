import json
import math
from app.utils import sanitize_json_data

# 1. 模拟包含 NaN 的原始数据
raw_data = {
    "symbol": "TEST",
    "price": float('nan'),
    "metrics": [1.0, 2.0, float('nan'), float('inf')],
    "history": [
        {"date": "2026-06-06", "upside": float('nan')}
    ]
}

print(">>> 原始数据 (包含 NaN/Inf):")
print(raw_data)

# 2. 尝试标准 json.dumps (通常在 Python 中会成功，但在 FastAPI/Starlette 中会根据配置失败)
# 关键在于验证 sanitize_json_data 转换后的结果
try:
    clean_data = sanitize_json_data(raw_data)
    print("\n>>> 消杀后的数据:")
    print(clean_data)
    
    # 3. 验证序列化结果 (JSON 不允许 NaN)
    json_str = json.dumps(clean_data)
    print("\n>>> 最终 JSON 字符串 (NaN 应该变成 null):")
    print(json_str)
    
    if "nan" in json_str.lower() or "inf" in json_str.lower():
        print("\n❌ 失败: JSON 中仍包含非法值")
    else:
        print("\n✅ 成功: JSON 符合标准规范")

except Exception as e:
    print(f"\n❌ 执行出错: {e}")

