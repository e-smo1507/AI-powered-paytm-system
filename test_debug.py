from backend.app import start, chat
sid, r = start()
print('after start stage', r.json()['stage'])
r = chat(sid, 'Haan')
print('after Haan stage:', r.json()['stage'])
r = chat(sid, 'Aage badho')
print('after Aage badho stage:', r.json()['stage'])
print(r.json()['reply'])
