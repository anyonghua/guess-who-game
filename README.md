# 🎭 猜猜TA是谁 (Guess Who)

一个有趣的猜人名小游戏，支持三种核心玩法、单人闯关和社交对战模式。

## 🎮 玩法模式

### 🔦 渐进揭秘 (Progressive Reveal)
系统逐步揭露线索，越早猜对分数越高。像剥洋葱一样层层揭秘！

### ❓ 二十问 (20 Questions)  
只能问是非题，用策略性提问缩小范围。20个问题内破案！

### 🤝 描述接龙 (Description Chain)
用最少的关键词让别人猜，考验表达能力和默契度。

## 🕹️ 游戏模式

- **单人闯关**：5大章节，从名人殿堂到终极挑战
- **实时对战**：1v1 竞速猜、出题互坑、默契挑战
- **好友挑战**：异步对战，分享战绩卡
- **多人大厅**：淘汰赛、积分赛、主题房间

## 🛠️ 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + TypeScript + Vant 4 |
| 后端 | FastAPI (Python) |
| 数据库 | PostgreSQL + Redis |
| 实时通信 | Socket.IO |
| AI引擎 | LLM API (动态出题) |

## 📁 项目结构

```
guess-who-game/
├── frontend/          # Vue 3 前端
├── backend/           # FastAPI 后端
├── docs/              # 设计文档
├── data/              # 题库数据
└── docker-compose.yml # 一键部署
```

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/anyonghua/guess-who-game.git
cd guess-who-game

# 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 启动前端
cd frontend
npm install
npm run dev
```

## 📄 License

MIT
