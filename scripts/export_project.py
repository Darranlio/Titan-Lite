import os

# 1. 核心黑名单：屏蔽依赖包、编译产物和隐藏目录，防止 txt 文件过大
IGNORE_DIRS = {
    '.git', '.idea', '.vscode', 'node_modules', 'dist', 'build', 
    'venv', '__pycache__', 'target', 'logs', 'vendor', 'out'
}

# 2. 扩展名黑名单：屏蔽图片、视频、压缩包和编译后的二进制文件
IGNORE_EXTS = {
    '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.zip', '.tar', '.gz', 
    '.class', '.jar', '.exe', '.dll', '.so', '.pyc', '.lock'
}

def generate_project_txt(root_path, output_file):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        
        # --- 第一部分：生成目录树结构 ---
        outfile.write("="*50 + "\n")
        outfile.write("1. PROJECT DIRECTORY STRUCTURE\n")
        outfile.write("="*50 + "\n\n")
        
        for root, dirs, files in os.walk(root_path):
            # 过滤不需要的目录
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            level = root.replace(root_path, '').count(os.sep)
            indent = ' ' * 4 * level
            outfile.write(f"{indent}[{os.path.basename(root)}/]\n")
            
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                if not any(f.endswith(ext) for ext in IGNORE_EXTS):
                    outfile.write(f"{subindent}{f}\n")

        # --- 第二部分：提取文件内容 ---
        outfile.write("\n\n" + "="*50 + "\n")
        outfile.write("2. PROJECT FILE CONTENTS\n")
        outfile.write("="*50 + "\n\n")

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if any(file.endswith(ext) for ext in IGNORE_EXTS):
                    continue

                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        relative_path = os.path.relpath(file_path, root_path)
                        # 给每个文件加上明显的开头和结尾标识，方便 AI 识别
                        outfile.write(f"--- START OF FILE: {relative_path} ---\n")
                        outfile.write(content)
                        outfile.write(f"\n--- END OF FILE: {relative_path} ---\n\n")
                except Exception as e:
                    # 如果遇到编码问题无法读取，记录错误但跳过，防止脚本中断
                    outfile.write(f"--- COULD NOT READ: {os.path.relpath(file_path, root_path)} (Error: {e}) ---\n\n")

if __name__ == "__main__":
    # 当前目录作为根目录，输出名为 project_context.txt
    PROJECT_ROOT = "."
    OUTPUT_TXT = "project_context.txt"

    print(f"🚀 正在扫描项目: {os.path.abspath(PROJECT_ROOT)}...")
    generate_project_txt(PROJECT_ROOT, OUTPUT_TXT)
    print(f"✅ 打包完成！请将生成的 {OUTPUT_TXT} 发给我。")
