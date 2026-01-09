import requests
import time
from config import settings

class WeComBot:
    def __init__(self):
        # 使用配置
        self.CORP_ID = settings.WECOM_CORP_ID
        self.CORP_SECRET = settings.WECOM_CORP_SECRET
        self.AGENTS = settings.WECOM_AGENTS
        self.token = None
        self.token_expires = 0

    def get_token(self):
        if self.token and time.time() < self.token_expires:
            return self.token
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.CORP_ID}&corpsecret={self.CORP_SECRET}"
        try:
            resp = requests.get(url).json()
            if resp.get('errcode') == 0:
                self.token = resp['access_token']
                self.token_expires = time.time() + 7000
                return self.token
        except: pass
        return None

    def upload_image(self, img_bytes, filename="chart.png"):
        token = self.get_token()
        if not token: return None
        url = f"https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={token}&type=image"
        files = {'media': (filename, img_bytes, 'image/png')}
        try:
            resp = requests.post(url, files=files).json()
            return resp.get('media_id')
        except: return None

    def send_markdown(self, content, mode="private"):
        agent_id = self.AGENTS.get(mode, self.AGENTS["private"])
        self._send(agent_id, "markdown", {"content": content})

    def send_image(self, media_id, mode="private"):
        agent_id = self.AGENTS.get(mode, self.AGENTS["private"])
        self._send(agent_id, "image", {"media_id": media_id})

    def _send(self, agent_id, msg_type, content_dict):
        token = self.get_token()
        if not token: return
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        data = {"touser": "@all", "msgtype": msg_type, "agentid": agent_id, msg_type: content_dict}
        requests.post(url, json=data)