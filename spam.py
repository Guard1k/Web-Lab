import requests

for i in range(10):
    r = requests.post("http://127.0.0.1:3000/tasks", json={"title": "spam"}, headers={
        "Idempotency-Key": str(i)
    })
    print(i, r.status_code, r.text)
