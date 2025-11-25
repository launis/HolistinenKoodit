
with open('src/prompt_splitter.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "full_text =" in line:
            print(f"Line {i+1}: {repr(line)}")
