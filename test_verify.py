from fastapi.testclient import TestClient
from backend.app import app
c = TestClient(app)
r = c.post("/api/start", json={"user": "sunita", "lang": "hi"}).json()
print("sid:", r["sid"])
r = c.post("/api/chat", json={"sid": r["sid"], "text": "2 lakh", "lang": "hi"}).json()
print("stage:", r["stage"])
r = c.post("/api/chat", json={"sid": r["sid"], "text": "haan", "lang": "hi"}).json()
print("after haan stage:", r["stage"])
print("reply:", type(r["reply"]))
