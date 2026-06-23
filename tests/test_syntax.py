import ast
with open('app/main.py', 'r') as f:
    try:
        ast.parse(f.read())
        print("Syntax OK")
    except Exception as e:
        print(f"Syntax Error: {e}")
