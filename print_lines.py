import os
path = 'frontend/index.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines[354:424], start=355):
    print(f"{i}: {repr(line)}")
