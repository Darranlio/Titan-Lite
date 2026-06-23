import os
import requests
import sys

# 目标：东方财富数据推送接口
url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=1&po=1&np=1&ut=b2884a393a59ad64002292a3e90d46a5&fltt=2&invt=2&fid0=f62&fs=m%3A90+t%3A2&stat=1&fields=f12&rt=52975239"

def test_connection(use_proxy):
    proxies = None
    if not use_proxy:
        # 强制清空当前进程的代理环境变量
        for k in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]:
            if k in os.environ: del os.environ[k]
        print("\n[测试] 禁用代理状态:")
    else:
        print(f"\n[测试] 使用系统当前代理 ({os.environ.get('https_proxy')}):")
    
    try:
        # 使用 verify=False 排除证书干扰，纯测链路
        resp = requests.get(url, timeout=5, verify=False)
        print(f"  ✅ 成功! 响应码: {resp.status_code}")
        return True
    except Exception as e:
        print(f"  ❌ 失败! 错误原因: {type(e).__name__}")
        return False

if __name__ == "__main__":
    # 1. 先测带代理（您的当前环境）
    test_connection(use_proxy=True)
    # 2. 再测不带代理
    test_connection(use_proxy=False)
