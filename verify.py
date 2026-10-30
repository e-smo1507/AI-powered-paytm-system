import urllib.request
import json
import socket

# Check port 8100
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = s.connect_ex(('127.0.0.1', 8100))
s.close()
print("8100 open:", result == 0)

# Check index.html
try:
    req = urllib.request.Request('http://127.0.0.1:8100/')
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read().decode('utf-8', errors='replace')
    print("Saytm title:", "Saytm - Just say to pay" in body)
    print("toLocaleString gone:", "toLocaleString" not in body)
    print("Paytm gone:", "Paytm" not in body)
    # Check for any JS syntax error indicator in response
    print("No JS syntax error indicators found" if "Illegal return" not in body and "Unexpected identifier" not in body else "WARNING: syntax error found in response")
except Exception as e:
    print("Error fetching index:", e)

# Check agent.html 
#try:
#    req = urllib.request.Request('http://127.0.0.1:8100/agent')
#    with urllib.request.urlopen(req, timeout=10) as r:
#        body = r.read().decode('utf-8', errors='replace')
#    print("agent.html Saytm:", "Saytm - Just say to pay" in body)
#    print("agent.html toLocale:", "toLocaleString" not in body)
# except Exception as e:
#     print("Error fetching agent:", e)
