import os
from datetime import datetime

class SystemLogger:
    """
    Titan-Alpha 进程感知日志管理器
    使用文件作为中转，解决多进程内存不共享导致的日志同步问题。
    """
    def __init__(self):
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.log_file = os.path.join(base_path, "app", "data", "agent_live.log")
        self.state_file = os.path.join(base_path, "app", "data", "agent_state.json")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def info(self, msg, stage=None, progress=None):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        
        # 追加写入文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line)
        
        # 更新状态
        if stage or progress is not None:
            import json
            state = self._read_state()
            if stage: state["stage"] = stage
            if progress is not None: state["progress"] = progress
            with open(self.state_file, "w") as f:
                json.dump(state, f)
        
        print(line.strip())

    def _read_state(self):
        import json
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except: pass
        return {"stage": "Idle", "progress": 0}

    def get_latest(self):
        logs = []
        if os.path.exists(self.log_file):
            with open(self.log_file, "r", encoding="utf-8") as f:
                # 只取最后 50 行，保持轻量
                logs = f.readlines()[-50:]
        
        state = self._read_state()
        return {
            "logs": [l.strip() for l in logs],
            "stage": state["stage"],
            "progress": state["progress"]
        }

    def clear(self):
        if os.path.exists(self.log_file):
            open(self.log_file, 'w').close()
        with open(self.state_file, "w") as f:
            import json
            json.dump({"stage": "Idle", "progress": 0}, f)

# 导出单例
sys_logger = SystemLogger()
