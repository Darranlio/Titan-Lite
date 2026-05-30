import os
import json
import shutil
from datetime import datetime

class ArchiveManager:
    """
    Titan-Alpha 数字化档案馆管理引擎
    支持研报的索引、筛选、批量删除与版本控制。
    """
    def __init__(self):
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.reports_root = os.path.join(base_path, "docs", "projects", "titan-lite", "reports")

    def get_all_reports(self):
        """扫描所有标的的元数据，构建全局研报索引"""
        all_entries = []
        if not os.path.exists(self.reports_root): return []

        for symbol in os.listdir(self.reports_root):
            symbol_path = os.path.join(self.reports_root, symbol)
            if not os.path.isdir(symbol_path) or symbol == "macro":
                continue
            
            meta_path = os.path.join(symbol_path, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        history = json.load(f)
                        for run in history:
                            # 丰富条目信息
                            run['symbol'] = symbol
                            # 检查是否存在相关附件
                            run['has_wechat'] = os.path.exists(os.path.join(symbol_path, "wechat_post.md"))
                            run['has_trade'] = os.path.exists(os.path.join(symbol_path, "trade.json"))
                            run['has_backtest'] = os.path.exists(os.path.join(symbol_path, "backtest.json"))
                            all_entries.append(run)
                except: pass
        
        # 按时间从新到旧排序
        # 优先使用 file 字段 (含有具体分钟的时间戳)
        all_entries.sort(key=lambda x: x.get('file', x['date']), reverse=True)
        return all_entries

    def delete_single_report(self, symbol, file_ts):
        """删除特定时间的某份研报文件"""
        symbol_path = os.path.join(self.reports_root, symbol)
        md_file = os.path.join(symbol_path, f"{file_ts}.md")
        
        # 1. 删除 MD 文件
        if os.path.exists(md_file):
            os.remove(md_file)
        
        # 2. 更新 metadata.json
        meta_path = os.path.join(symbol_path, "metadata.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    history = json.load(f)
                new_history = [h for h in history if h.get('file') != file_ts]
                with open(meta_path, "w") as f:
                    json.dump(new_history, f, indent=4)
            except: pass
        
        return True, f"研报 {symbol} ({file_ts}) 已从档案中抹除"

    def delete_full_archive(self, symbol):
        """彻底删除某标的的所有档案文件夹"""
        symbol_path = os.path.join(self.reports_root, symbol)
        if os.path.exists(symbol_path):
            shutil.rmtree(symbol_path)
            return True, f"标的 {symbol} 的所有历史档案已彻底销毁"
        return False, "找不到该档案"

# 导出单例
archive_manager = ArchiveManager()
