import requests
base='http://127.0.0.1:5000'
paths=['/login','/admin','/librarian','/dashboard','/api/login']
for path in paths:
    try:
        r=requests.get(base+path, timeout=10)
        print(path, r.status_code, r.headers.get('content-type',''), r.headers.get('server',''))
        print('location', r.headers.get('Location'))
    except Exception as e:
        print(path, 'ERR', e)
try:
    r=requests.post(base+'/api/login', json={'username':'x','password':'y'}, timeout=10)
    print('/api/login POST', r.status_code, r.text)
except Exception as e:
    print('/api/login POST ERR', e)
