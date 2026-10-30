import sys
os.environ["PYTHONIOENCODING"] = "utf-8"
with open("frontend/index.html","r",encoding="utf-8") as f:
    lines=f.readlines()
for i in range(354,426):
    print(f"{i+1}: {repr(lines[i])}", file=sys.stdout.buffer)
print("---", file=sys.stdout.buffer)
