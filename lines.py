import sys
with open('frontend/index.html','rb') as f:
    lines=f.read().splitlines()
for i in range(354,424):
    try:
        s=lines[i].decode('utf-8')
    except:
        s=lines[i].decode('utf-8',errors='replace')
    print(f"{i+1}: {s}", file=sys.stdout.buffer)
