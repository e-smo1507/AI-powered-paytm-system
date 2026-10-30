from fastapi.testclient import TestClient
from backend.app import app

c = TestClient(app)
r = c.post('/api/start', json={'user':'sunita','lang':'hi'}).json()
sid = r['sid']
r2 = c.post('/api/chat', json={'sid':sid,'text':'Haan','lang':'hi'}).json()
print('stage:', r2['stage'])
print('reply repr:', repr(r2['reply']))
r3 = c.post('/api/chat', json={'sid':sid,'text':'Aage badho','lang':'hi'}).json()
print('after aage badho stage:', r3['stage'])
print('reply repr:', repr(r3['reply']))
print('handheld:', r3['handoff'])
