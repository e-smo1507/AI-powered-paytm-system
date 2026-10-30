with open('frontend/index.html','r',encoding='utf-8') as f:
    lines=f.readlines()
new=lines[:356]+lines[422:]
with open('frontend/index.html','w',encoding='utf-8') as f:
    f.writelines(new)
print('Done')
