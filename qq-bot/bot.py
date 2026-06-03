"""
QQ 机器人 AI 对话（DeepSeek）
===============================
QQ 官方 Bot API + DeepSeek

部署前：
1. 去 https://q.qq.com/ 注册开发者，创建机器人
2. 拿到 BotAppID + BotToken
3. 设置环境变量，启动即可
"""

import asyncio
import os
from collections import defaultdict

import botpy
from botpy import logging
from botpy.message import Message
from botpy.ext.cog_yaml import read

import requests
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

MAX_HISTORY = 10
sessions: dict[str, list[dict]] = defaultdict(list)

SYSTEM_PROMPT = (
    "你是「小来福」，一个通过 QQ 聊天的 AI 助手。"
    "特点：\n"
    "- 简洁中文回复\n"
    "- 复杂问题分点回答\n"
    "- 语气亲切，适当用 emoji\n"
    "- 不编造，不知道就说不知道\n"
    "- 回复控制在 500 字以内"
)


def chat_deepseek(user_id: str, content: str) -> str:
    """调用 DeepSeek"""
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
        reply = f"AI 暂时挂了：{e}"

    history.append({"role": "user", "content": content})
    history.append({"role": "assistant", "content": reply})
    sessions[user_id] = history[-MAX_HISTORY * 2:]
    return reply


class AIBot(botpy.Client):
    """AI 对话机器人"""

    async def on_ready(self):
        print(f"🤖 QQ 机器人已上线：{self.robot.name}")

    async def on_at_message_create(self, message: Message):
        """群里 @ 机器人"""
        content = message.content.strip()
        print(f"[群聊 @] {message.author.username}: {content}")
        reply = chat_deepseek(message.author.id, content)
        await message.reply(content=reply)

    async def on_direct_message_create(self, message: Message):
        """私聊"""
        content = message.content.strip()
        print(f"[私聊] {message.author.username}: {content}")
        reply = chat_deepseek(message.author.id, content)
        await message.reply(content=reply)

    async def on_group_at_message_create(self, message: Message):
        """群 @（同上，兼容不同事件名）"""
        return await self.on_at_message_create(message)


if __name__ == "__main__":
    # botpy 默认读 config.yaml，也可以用环境变量
    intents = botpy.Intents.all()
    client = AIBot(intents=intents)

    # 优先从环境变量读取
    app_id = os.getenv("QQ_BOT_APPID", "")
    token = os.getenv("QQ_BOT_TOKEN", "")

    if app_id and token:
        client.run(appid=app_id, secret=token)
    else:
        print("请设置 QQ_BOT_APPID 和 QQ_BOT_TOKEN 环境变量，或在 config.yaml 中配置")
