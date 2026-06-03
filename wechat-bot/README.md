# 企业微信 AI 对话机器人（DeepSeek）

企业微信自建应用 + DeepSeek API = 员工/客户随时跟 AI 聊天

---

## 架构

```
用户发消息 → 企业微信 → 回调你的服务器 → DeepSeek → 回复用户
```

---

## 部署步骤

### 1. 企业微信后台配置

1. 登录 [企业微信管理后台](https://work.weixin.qq.com/)
2. **应用管理** → **自建应用** → 新建一个应用（比如叫「小来福」）
3. 记录三样东西：
   - **企业 ID**（我的企业 → 企业信息）
   - **AgentID**（应用详情页）
   - **Secret**（应用详情页）
4. **接收消息** → 设置 API 接收
   - URL：`https://你的域名/wx`
   - Token：随机填一个英文
   - EncodingAESKey：点随机生成
   - 先选**明文模式**（避免加解密复杂度）

### 2. 部署服务器

把代码推到你已有的服务器（或 GitHub Pages 不行，这需要后端），推荐：

```bash
# 方案 A：已有服务器
cd wechat-bot
pip install -r requirements.txt
cp .env.example .env   # 改成你的真实配置
python app.py
# 用 nginx 反代到 https://你的域名/wx

# 方案 B：免费托管（Railway / Render / Fly.io）
# 上传代码，设好环境变量即可
```

### 3. 验证

1. 在企业微信后台点**保存**，会发 GET 请求验证 URL
2. 在企业微信里找到这个应用，发一条文字消息
3. AI 应该回复你！

---

## 环境变量

| 变量 | 说明 |
|------|------|
| `WECOM_CORP_ID` | 企业微信企业 ID |
| `WECOM_AGENT_ID` | 应用 AgentID |
| `WECOM_CORP_SECRET` | 应用 Secret |
| `WECOM_TOKEN` | 回调 Token（自己定） |
| `WECOM_AES_KEY` | 回调 EncodingAESKey |
| `DEEPSEEK_API_KEY` | DeepSeek API key |

---

## ⚠️ 注意事项

- **必须 HTTPS**：企业微信回调只接受 443 端口
- **IP 白名单**：服务器 IP 需加入企业微信可信 IP
- **回复超时**：必须在 5 秒内返回 200，AI 回复异步调用 `message/send` 接口主动推送
