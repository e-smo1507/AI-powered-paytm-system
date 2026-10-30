import sys
for f in ['frontend/index.html', 'frontend/agent.html']:
    data = open(f, encoding='utf-8', errors='surrogateescape').read()
    for i, line in enumerate(data.split(chr(10))):
        if 'toLocaleString' in line:
            safe = line.translate(str.maketrans('\ufffd', '?'))
            sys.stdout.write(f'{f}: {i+1}: {safe}\n')
