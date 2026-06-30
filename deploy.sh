#!/bin/bash
# 部署脚本 - 在服务器上执行
set -e

APP_DIR="/var/www/guess-who-game"
REPO="https://github.com/anyonghua/guess-who-game.git"

echo "🎭 部署猜猜TA是谁..."

# 克隆或更新代码
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull
else
    git clone "$REPO" "$APP_DIR"
    cd "$APP_DIR"
fi

# 构建前端
cd frontend
npm ci
npm run build
cd ..

# 安装后端依赖
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据库
python3 -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"

# 导入题库（如果数据库为空）
python3 scripts/seed.py ../data/questions_sample.json 2>/dev/null || true

# 启动后端
pkill -f "uvicorn app.main:app" 2>/dev/null || true
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /var/log/guess-who.log 2>&1 &

# 配置 Nginx
cd ..
sudo cp nginx/guess-who.conf /etc/nginx/sites-available/guess-who
sudo ln -sf /etc/nginx/sites-available/guess-who /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo "✅ 部署完成！"
echo "   前端: http://$(hostname -I | awk '{print $1}')"
echo "   API:  http://$(hostname -I | awk '{print $1}'):8000"
