# 🎭 猜猜TA是谁 - 后端服务

FastAPI 后端，提供游戏核心逻辑、AI出题引擎、对战服务和社交功能。

## 快速开始

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动后访问 http://localhost:8000/docs 查看 Swagger 文档

## 核心模块

- `app/services/clue_engine.py` - 线索生成引擎
- `app/services/twenty_q_engine.py` - 二十问AI回答引擎
- `app/services/scoring.py` - 计分系统
- `app/services/validator.py` - 答案验证（模糊匹配）
