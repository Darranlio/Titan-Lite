import os
import re

def sanitize_md_files():
    base_dir = "docs/projects/titan-lite"
    users_dir = os.path.join(base_dir, "users")
    
    if not os.path.exists(users_dir):
        print(">>> 未找到用户目录，无需消杀。")
        return

    print(">>> 正在启动存量研报路径消杀程序...")
    
    # 匹配 Vue 组件导入语句
    patterns = [
        (re.compile(r"import (\w+) from '\.\./\.\./(\w+)\.vue'"), r"import \1 from '../../../../\2.vue'"),
        (re.compile(r"import (\w+) from '\./ArchiveManager\.vue'"), r"import \1 from '../../../reports/ArchiveManager.vue'")
    ]

    for root, dirs, files in os.walk(users_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                # 计算文件深度（相对于 docs/projects/titan-lite）
                rel_path = os.path.relpath(file_path, base_dir)
                depth = len(rel_path.split(os.sep)) - 1
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                new_content = content
                
                # 针对深度为 4 的文件（users/NAME/reports/SYMBOL/FILE.md）
                if depth == 4:
                    # 修复 ReportArtifacts, BacktestChart 等
                    new_content = re.sub(r"import (\w+) from '\.\./\.\./(\w+)\.vue'", r"import \1 from '../../../../\2.vue'", new_content)
                
                # 针对深度为 3 的文件（users/NAME/reports/index.md）
                elif depth == 3:
                    # 修复 ArchiveManager
                    new_content = re.sub(r"import (\w+) from '\./ArchiveManager\.vue'", r"import \1 from '../../../reports/ArchiveManager.vue'", new_content)

                if new_content != content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"  [Fixed] {rel_path} (Depth: {depth})")

    print("\n✅ 消杀完成。正在触发重新构建...")
    os.system("cd docs && npm run docs:build")

if __name__ == "__main__":
    sanitize_md_files()
