
import re

with open('prompts/VAIHE_1.txt', 'r', encoding='utf-8') as f:
    content = f.read(300)

pattern = r"(?m)^VAIHE 1:.{0,100}(?<!-)$"
match = re.search(pattern, content)

print(f"Pattern: {pattern}")
print(f"Content repr: {repr(content)}")
if match:
    print(f"MATCH FOUND: {repr(match.group())}")
else:
    print("NO MATCH")
