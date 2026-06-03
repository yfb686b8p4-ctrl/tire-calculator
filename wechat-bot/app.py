"""
企业微信 AI 对话机器人（DeepSeek）
===================================
自建应用接收消息 → 调用 DeepSeek → 回复用户

部署前准备：
1. 企业微信管理后台 → 应用管理 → 自建应用
2. 记录 CorpID / AgentID / Secret
3. 接收消息 → 设置回调 URL → 随机 Token + EncodingAESKey → 先选「明文模式」
4. 部署后把 URL 配上去：https://你的域名/wx
"""

import hashlib
import json
import time
from functools import wraps

import requests
from flask import Flask, request, make_response

import os
from dotenv import load_dotenv
load_dotenv()

# ==================== 配置 ====================
CORP_ID = os.getenv("WECOM_CORP_ID", "")         # 企业 ID
AGENT_ID = os.getenv("WECOM_AGENT_ID", "")        # 应用 ID
CORP_SECRET = os.getenv("WECOM_CORP_SECRET", "")  # 应用 Secret
WECOM_TOKEN = os.getenv("WECOM_TOKEN", "")        # 回调 Token
AES_KEY = os.getenv("WECOM_AES_KEY", "")          # 回调 EncodingAESKey

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ==================== 企微 access_token 缓存 ====================
_access_token: str = ""
_access_token_expires: float = 0


def get_access_token() -> str:
    global _access_token, _access_token_expires
    if _access_token and time.time() < _access_token_expires:
        return _access_token

    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    resp = requests.get(url, params={
        "corpid": CORP_ID,
        "corpsecret": CORP_SECRET,
    })
    data = resp.json()
    if data.get("errcode") != 0:
        raise Exception(f"获取 access_token 失败: {data}")
    _access_token = data["access_token"]
    _access_token_expires = time.time() + data["expires_in"] - 300
    return _access_token


# ==================== 用户会话 ====================
MAX_HISTORY = 10
sessions: dict[str, list[dict]] = {}

# ==================== Flask ====================
app = Flask(__name__)


@app.route("/wx", methods=["GET", "POST"])
def wx():
    """企业微信回调地址"""
    if request.method == "GET":
        return _verify_url(request)
    else:
        return _handle_message(request)


def _verify_url(req):
    """验证回调 URL"""
    signature = req.args.get("msg_signature", "")
    timestamp = req.args.get("timestamp", "")
    nonce = req.args.get("nonce", "")
    echostr = req.args.get("echostr", "")

    # 明文模式：直接返回 echostr
    tmp = sorted([WECOM_TOKEN, timestamp, nonce, echostr])
    tmp_str = "".join(tmp)
    if hashlib.sha1(tmp_str.encode()).hexdigest() == signature:
        return echostr
    return "fail"


def _handle_message(req):
    """接收并回复消息"""
    try:
        body = req.data.decode("utf-8")
        msg = json.loads(body)
    except Exception:
        return "success"

    # 企微会发 XML（加密）或 JSON（明文），这里处理 JSON
    msg_type = msg.get("MsgType", "")
    from_user = msg.get("FromUserName", "")
    to_user = msg.get("ToUserName", "")

    if msg_type != "text":
        _send_text(from_user, "暂不支持此类型消息，请用文字和我聊天 😊")
        return "success"

    content = msg.get("Content", "").strip()
    if not content:
        return "success"

    print(f"[用户 {from_user}] {content}")
    reply = _chat_with_deepseek(from_user, content)
    print(f"[AI 回复] {reply[:80]}...")
    _send_text(from_user, reply)
    return "success"


# ==================== 企微主动发消息 ====================

def _send_text(user_id: str, content: str):
    """通过企微 API 发送文本消息"""
    try:
        token = get_access_token()
        resp = requests.post(
            f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}",
            json={
                "touser": user_id,
                "msgtype": "text",
                "agentid": int(AGENT_ID),
                "text": {"content": content},
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("errcode") != 0:
            print(f"[发送失败] {data}")
    except Exception as e:
        print(f"[发送异常] {e}")


# ==================== DeepSeek 对话 ====================

SYSTEM_PROMPT = (
    "你是「小来福」，一个友好的 AI 助手，通过企业微信为用户提供服务。"
    "你的特点：\n"
    "- 用简洁清晰的中文回复\n"
    "- 问题复杂时分点回答\n"
    "- 语气亲切自然，适当用 emoji\n"
    "- 不知道就说不知道，不编造\n"
    "- 回复控制在 600 字以内"
)


def _chat_with_deepseek(user_id: str, content: str) -> str:
    if user_id not in sessions:
        sessions[user_id] = []

    history = sessions[user_id]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history
    messages.append({"role": "user", "content": content})

    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000,
            },
            timeout=30,
        )
        reply = resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        reply = f"抱歉，AI 暂时无法回复（{e}），请稍后重试。"

    history.append({"role": "user", "content": content})
    history.append({"role": "assistant", "content": reply})
    sessions[user_id] = history[-MAX_HISTORY * 2:]
    return reply


@app.route("/")
def health():
    return {"status": "ok", "model": DEEPSEEK_MODEL}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 企微 AI 机器人 → http://0.0.0.0:{port}/wx")
    app.run(host="0.0.0.0", port=port, debug=False)
