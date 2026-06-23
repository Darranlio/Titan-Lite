import os

# 配置：想要导出的文件后缀
ALLOWED_EXTENSIONS = {'.py', '.js', '.ts', '.md', '.json', '.yml', '.yaml', '.html', '.css', '.vue', '.Dockerfile'}
# 配置：必须忽略的目录
IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', '.vitepress', 'dist', 'venv', '.idea', '.vscode'}
# 配置：必须忽略的文件
IGNORE_FILES = {'package-lock.json', 'yarn.lock', 'export_code.py'}

def is_text_file(filename):
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

def export_project(output_file="project_context.txt"):
    root_dir = os.getcwd()
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 写入头部信息
        outfile.write(f"# Titan-Lite Project Codebase Export\n")
        outfile.write(f"# Root: {root_dir}\n\n")

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # 1. 过滤掉不需要的目录 (修改 dirnames 列表会影响 os.walk 的后续遍历)
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

            for filename in filenames:
                if filename in IGNORE_FILES:
                    continue
                    
                if is_text_file(filename):
                    filepath = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(filepath, root_dir)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            
                            # 写入文件分隔符和内容
                            outfile.write("=" * 50 + "\n")
                            outfile.write(f"FILE_PATH: {rel_path}\n")
                            outfile.write("=" * 50 + "\n")
                            outfile.write(content + "\n\n")
                            print(f"Exported: {rel_path}")
                    except Exception as e:
                        print(f"Skipped (Error): {rel_path} - {e}")

    print(f"\n✅ 完成！所有代码已保存到: {output_file}")

if __name__ == "__main__":
    export_project()
