
with open('prompts/VAIHE_1.txt', 'r', encoding='utf-8') as f:
    first_line = f.readline().strip()
    print(f"Length: {len(first_line)}")
    print(f"Content: {first_line}")
