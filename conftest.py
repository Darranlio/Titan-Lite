import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 获取根目录和 app 目录
root_dir = Path(__file__).parent
app_dir = root_dir / "app"

# 将 app 目录加入 Python 搜索路径，解决内部导入问题
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# 加载 app/.env 环境变量
env_path = app_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # 如果不存在，设置一些默认值防止单测崩溃
    os.environ.setdefault("LLM_API_KEY", "dummy")
    os.environ.setdefault("DEEPSEEK_API_KEY", "dummy")
    os.environ.setdefault("LLM_BASE_URL", "https://api.deepseek.com")
    os.environ.setdefault("LLM_PROVIDER", "deepseek")
