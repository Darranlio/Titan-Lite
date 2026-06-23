import requests

try:
    # We don't have a valid token here, but we can check if it returns 401
    res = requests.post("http://localhost:8000/stop?task_type=all")
    print(res.status_code, res.text)
except Exception as e:
    print(e)
