import requests
import time

BASE_URL = "http://localhost:8000"

def run_test():
    print("1. 获取验证码...")
    res = requests.post(f"{BASE_URL}/auth/send-code?email=test@example.com")
    code = res.json().get("debug_code", "123456")
    
    print("2. 注册账号...")
    requests.post(f"{BASE_URL}/auth/register?username=testuser&password=testpass&email=test@example.com&code={code}")
    
    print("3. 登录获取 Token...")
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": "testuser", "password": "testpass"})
    token = res.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("4. 触发全市场扫描...")
    res = requests.post(f"{BASE_URL}/run", json={"market": "Global", "mode": "solo"}, headers=headers)
    print(res.json())
    
    print("5. 检查日志流转...")
    time.sleep(3)
    res = requests.get(f"{BASE_URL}/logs", headers=headers)
    logs = res.json().get("logs", "")
    print(f"日志获取成功: 长度 {len(logs)}")
    
    print("6. 触发安全终止...")
    res = requests.post(f"{BASE_URL}/stop?task_type=all", headers=headers)
    print(res.json())
    
    print("7. 验证系统存活...")
    time.sleep(1)
    res = requests.get(f"{BASE_URL}/")
    print(f"系统状态: {res.json()}")

run_test()
