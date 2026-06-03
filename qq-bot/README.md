# QQ 机器人 AI 对话

QQ 官方开放平台机器人 + DeepSeek

## 部署步骤

### 1. 注册 QQ 机器人

1. 打开 [QQ 开放平台](https://q.qq.com/)
2. 创建机器人，获取 **BotAppID** + **BotToken**
3. 设置机器人权限：群聊、私聊消息

### 2. 运行

```bash
cd qq-bot
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填上 QQ_BOT_APPID / QQ_BOT_TOKEN / DEEPSEEK_API_KEY
python bot.py
```

### 3. 使用

- **私聊**：直接给机器人发消息
- **群聊**：@机器人 + 消息内容

## 注意事项

- QQ 机器人需要沙箱环境或正式发布后才能被其他用户使用
- 首次创建的机器人只有开发者自己可以测试
