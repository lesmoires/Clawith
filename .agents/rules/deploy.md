---
trigger: always_on
---

你完成功能开发之后你需要帮我同时部署和更新到生产环境和开发环境

## 部署流程

### 1. 如果修改了前端代码（src/ 下任何文件）或 frontend/VERSION，必须先重新构建：
```bash
cd frontend && rm -rf dist node_modules/.vite && npm run build && cp public/logo.png dist/ && cp public/logo.svg dist/ && rm -f dist.zip && cd dist && zip -r ../dist.zip . && cd ..
```
**不能直接用仓库里已有的旧 dist.zip 部署！**

> **重要**：必须先 `rm -rf dist node_modules/.vite` 清除 Vite 缓存，否则 build 可能输出旧内容。构建后检查 `dist/assets/` 下的 JS 文件 hash 是否变化来确认。

### 2. 推送到 GitHub 主分支

### 3. 部署到服务器（两台都用 Docker）

#### 生产环境
- 地址：82.156.53.84，SSH: `ssh -p 10022 qinrui@82.156.53.84`，密码：`Clawith-JHJHBGL`
- Clawith admin 账号：admin / Wisdom343536
- 前端端口 3008，通过 129.226.64.9 中转到 try.clawith.ai
- Clawith 目录：`/home/qinrui/Clawith`

#### 开发环境
- 地址：192.168.106.163，SSH: `ssh root@192.168.106.163`，密码：`dataelem`
- Clawith admin 账号：admin123 / admin123
- Clawith 目录：`/home/work/Clawith`

#### 更新步骤（两台服务器相同）：
```bash
cd <Clawith目录>
git stash 2>/dev/null; git pull origin main

# 更新后端：docker cp 进容器 + 清缓存 + restart
docker cp backend/app clawith-backend-1:/app/
docker exec clawith-backend-1 find /app -name "__pycache__" -exec rm -rf {} + 2>/dev/null
docker compose restart backend

# 更新前端：docker cp dist.zip + 解压 + restart
docker cp frontend/dist.zip clawith-frontend-1:/usr/share/nginx/html/dist.zip
docker exec clawith-frontend-1 sh -c "cd /usr/share/nginx/html && unzip -o dist.zip"
docker compose restart frontend
```

## 注意事项
- 如果有危险操作，先更新开发环境测试，确认没问题再更新生产环境
- SSH 到生产环境需要加 `-o PubkeyAuthentication=no` 避免 key 认证失败
- 如果需要测试 Agent 功能，没有特别说明的话，默认使用 **Morty** 这个 Agent 进行测试
- 当你启用浏览器进行验证的时候，登录平台时浏览器会帮你记住密码，所以不用你填写密码，直接点击登录即可。
- 所有更新，不仅要考虑我们自己开发和生产环境，还需要考虑其他已经部署我们平台的用户，在升级到新版本时会碰到的问题，如果需要升级方案等操作，请一并提供出来。