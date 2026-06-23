import os
import re

def sanitize_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换 NaN 为 null, 替换 Infinity 为 null
    # 注意要处理可能的空格或大小写
    new_content = re.sub(r'\bNaN\b', 'null', content)
    new_content = re.sub(r'\bInfinity\b', 'null', new_content)
    new_content = re.sub(r'\b-Infinity\b', 'null', new_content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    base_dir = "docs/projects/titan-lite"
    print(">>> 正在启动磁盘物理数据消杀 (NaN -> null)...")
    
    count = 0
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                if sanitize_json_file(file_path):
                    print(f"  [Sanitized] {file_path}")
                    count += 1
    
    print(f"\n✅ 消杀完成，共修复 {count} 个 JSON 文件。")

if __name__ == "__main__":
    main()
