import os
import json
from datetime import datetime
from typing import Optional

class SystemLogger:
    """
    Titan-Alpha 身份感知日志管理器
    支持按用户隔离日志，解决多租户场景下的日志冲突。
    """
    def __init__(self, storage_root: str = "app/data"):
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        # 如果是绝对路径则直接使用，否则拼接在项目根目录下
        if os.path.isabs(storage_root):
            self.log_dir = storage_root
        else:
            self.log_dir = os.path.join(base_path, storage_root)
            
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 默认路径（兼容旧版本）
        self.log_file = os.path.join(self.log_dir, "agent_live.log")
        self.state_file = os.path.join(self.log_dir, "agent_state.json")

        # 专项路径
        self.log_batch_file = os.path.join(self.log_dir, "agent_batch.log")
        self.state_batch_file = os.path.join(self.log_dir, "agent_batch_state.json")
        self.log_single_file = os.path.join(self.log_dir, "agent_single.log")
        self.state_single_file = os.path.join(self.log_dir, "agent_single_state.json")
        self.default_task_type = None

    def set_default_task_type(self, task_type):
        self.default_task_type = task_type
        
    def info(self, msg, stage=None, progress=None, task_type=None):
        if task_type is None:
            task_type = self.default_task_type
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        
        # 确定写入的目标文件
        target_log = self.log_file
        target_state = self.state_file
        
        if task_type == "batch":
            target_log = self.log_batch_file
            target_state = self.state_batch_file
        elif task_type == "single":
            target_log = self.log_single_file
            target_state = self.state_single_file

        # 追加写入文件
        with open(target_log, "a", encoding="utf-8") as f:
            f.write(line)

        # 更新状态 - 彻底隔离，不再同步更新主状态
        if stage or progress is not None or task_type:
            state = self._read_state(task_type)
            if stage: state["stage"] = stage
            if progress is not None: state["progress"] = progress
            if task_type: state["task_type"] = task_type
            with open(target_state, "w") as f:
                json.dump(state, f)
        
        # 仍然打印到控制台方便查看
        print(line.strip())

    def force_idle(self, task_type=None):
        """强制重置状态为 Idle，用于解冻 UI"""
        target_state = self.state_file
        if task_type == "batch": target_state = self.state_batch_file
        elif task_type == "single": target_state = self.state_single_file
        
        state_data = {"stage": "Idle", "progress": 0, "task_type": task_type or "none"}
        with open(target_state, "w") as f:
            json.dump(state_data, f)
            
        if target_state != self.state_file:
            state_data["task_type"] = "none"
            with open(self.state_file, "w") as f:
                json.dump(state_data, f)

    def warning(self, msg, stage=None, progress=None):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] ⚠️ {msg}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line)
        print(line.strip())

    def error(self, msg, stage=None, progress=None):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] ❌ {msg}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line)
        print(line.strip())

    def _read_state(self, task_type=None):
        target_state = self.state_file
        if task_type == "batch": target_state = self.state_batch_file
        elif task_type == "single": target_state = self.state_single_file

        if os.path.exists(target_state):
            try:
                with open(target_state, "r") as f:
                    return json.load(f)
            except: pass
        return {"stage": "Idle", "progress": 0, "task_type": "none"}

    def get_latest(self, task_type=None):
        target_log = self.log_file
        if task_type == "batch": target_log = self.log_batch_file
        elif task_type == "single": target_log = self.log_single_file

        logs = []
        if os.path.exists(target_log):
            with open(target_log, "r", encoding="utf-8") as f:
                # 只取最后 50 行，保持轻量
                logs = f.readlines()[-50:]
        
        state = self._read_state(task_type)
        return {
            "logs": [l.strip() for l in logs],
            "stage": state["stage"],
            "progress": state["progress"],
            "task_type": state.get("task_type", "none")
        }

    def clear(self, stage="Idle", progress=0, task_type="none"):
        state_data = {"stage": stage, "progress": progress, "task_type": task_type}
        
        if task_type in ("none", "all"):
            # Clear everything
            for log_f in [self.log_file, self.log_batch_file, self.log_single_file]:
                if os.path.exists(log_f): open(log_f, 'w').close()
            for state_f in [self.state_file, self.state_batch_file, self.state_single_file]:
                with open(state_f, "w") as f: json.dump(state_data, f)
            return

        target_log = self.log_file
        target_state = self.state_file
        
        if task_type == "batch":
            target_log = self.log_batch_file
            target_state = self.state_batch_file
        elif task_type == "single":
            target_log = self.log_single_file
            target_state = self.state_single_file

        if os.path.exists(target_log):
            open(target_log, 'w').close()
        
        state_data = {"stage": stage, "progress": progress, "task_type": task_type}
        with open(target_state, "w") as f:
            json.dump(state_data, f)
        
        # 如果是清空专项日志，也重置主状态以防万一
        if target_state != self.state_file:
            with open(self.state_file, "w") as f:
                json.dump(state_data, f)


# 默认全局单例 (指向基础路径，用于兼容)
sys_logger = SystemLogger()
