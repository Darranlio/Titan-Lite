import os
import json
import time
from sys_logger import SystemLogger

def test_atomic_clear_and_update():
    print("🚀 开始自测: 验证日志路径一致性与原子化清空...")
    
    # 模拟用户 sakura 的路径
    storage_root = "docs/projects/titan-lite/users/test_user"
    if not os.path.exists(storage_root):
        os.makedirs(storage_root, exist_ok=True)
        
    logger = SystemLogger(storage_root=storage_root)
    
    # 1. 模拟遗留状态
    print(">>> 写入遗留状态 (Generating Macro 90%)...")
    logger.info("Old Log Line", stage="Generating Macro", progress=90, task_type="batch")
    
    # 2. 模拟主进程点击启动 (立即原子清空)
    print(">>> 模拟主进程点击启动 (执行原子清空)...")
    logger.clear(stage="Initializing", progress=0, task_type="batch")
    
    # 3. 校验状态
    state = logger.get_latest()
    print(f">>> 当前状态: {state['stage']}, 进度: {state['progress']}, 任务: {state['task_type']}, 日志数: {len(state['logs'])}")
    
    if state['stage'] == "Initializing" and state['progress'] == 0 and len(state['logs']) == 0:
        print("✅ 第一阶段校验通过: 原子清空成功且无残留。")
    else:
        print("❌ 第一阶段校验失败！有残留。")
        return

    # 4. 模拟第一个 Action 进入
    print(">>> 模拟第一个 Action (Discovery) 启动...")
    logger.info("🔍 启动发现流程...", stage="Discovery", progress=10, task_type="batch")
    
    state = logger.get_latest()
    print(f">>> 动作后状态: {state['stage']}, 进度: {state['progress']}")
    
    if state['stage'] == "Discovery" and state['progress'] == 10:
        print("✅ 第二阶段校验通过: Action 状态已覆盖。")
    else:
        print("❌ 第二阶段校验失败！状态未更新。")
        return

    print("🎉 自测全部通过！代码逻辑严谨。")

if __name__ == "__main__":
    test_atomic_clear_and_update()
