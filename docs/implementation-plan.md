# 🎭 猜猜TA是谁 — 实现计划

> 原则：**先让它能玩，再让它好玩，最后让它上瘾**
> 
> 每个 Phase 结束时都有一个可运行的交付物，不是半成品

---

## Phase 0：原型设计（1天）

**目标**：确定视觉风格，产出可交互的 HTML 原型

**交付物**：一个可以直接在浏览器打开的高保真 HTML 文件

### 任务

| # | 任务 | 技能 | 产出 |
|---|------|------|------|
| 0.1 | 出3个风格变体（极简/游戏/暗黑科技） | `sketch` | 3个 HTML 文件 |
| 0.2 | 用户选定风格，加载设计 token | `popular-web-designs` | 配色/字体/间距确定 |
| 0.3 | 渐进揭秘模式高保真原型 | `claude-design` | 单文件交互原型 |
| 0.4 | 用浏览器截图验证视觉效果 | `agent-browser` | 截图确认 |

**验证标准**：
- [ ] 在手机浏览器打开不崩溃
- [ ] 线索卡片有动画效果
- [ ] 猜对/猜错有明确反馈
- [ ] 配色和字体协调

---

## Phase 1：最小可玩 — 渐进揭秘（3天）

**目标**：一个完整的"看线索→猜人名→得分数"循环

**交付物**：前端可玩的渐进揭秘模式（纯前端，JSON 题库，不需要后端）

### Day 1：前端骨架

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 1.1 | Vue 3 项目初始化 | `software-development` | `frontend/` | Vite + TS + Vant 4 + Pinia |
| 1.2 | 路由设计 | - | `src/router/index.ts` | 首页 / 游戏页 / 结果页 |
| 1.3 | 游戏状态 Store | `software-development` | `src/stores/game.ts` | currentClue, score, streak, answer |
| 1.4 | 首页（选难度+选模式） | - | `src/views/Home.vue` | 暂时只有渐进揭秘一个选项 |

**Vue 3 Store 关键设计**（避免踩 MBTI 项目的坑）：
```typescript
// ❌ 直接赋值可能不触发响应
answers.value[key] = answer

// ✅ 用展开运算符创建新对象
answers.value = { ...answers.value, [key]: answer }

// ✅ 用 computed 做派生状态
const canGuess = computed(() => currentClueIndex.value >= 0)
```

### Day 2：核心游戏逻辑

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 1.5 | 题库数据（50题） | `multi-search-engine` | `data/questions.json` | 10个分类×5题 |
| 1.6 | 线索展示组件 | - | `src/components/ClueCard.vue` | 翻牌动画，从模糊到清晰 |
| 1.7 | 答案输入组件 | - | `src/components/GuessInput.vue` | 输入框+确认按钮 |
| 1.8 | 答案验证（前端版） | `sds-tdd` | `src/utils/validator.ts` | 精确+别名+编辑距离 |
| 1.9 | 温度提示 | - | `src/components/TemperatureHint.ts` | cold/cool/warm/hot/boiling |

**validator.ts 测试先行**：
```typescript
// RED → 写测试
describe('validator', () => {
  it('exact match: 诸葛亮', () => {
    expect(validate('诸葛亮', '诸葛亮', [])).toBe(true)
  })
  it('alias match: 孔明', () => {
    expect(validate('孔明', '诸葛亮', ['孔明','卧龙'])).toBe(true)
  })
  it('fuzzy typo: 猪葛亮', () => {
    expect(validate('猪葛亮', '诸葛亮', [])).toBe(true)
  })
  it('wrong answer: 曹操', () => {
    expect(validate('曹操', '诸葛亮', [])).toBe(false)
  })
})
// GREEN → 实现
// REFACTOR → 优化
```

### Day 3：计分+结果+串联

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 1.10 | 计分系统（前端版） | - | `src/utils/scoring.ts` | 100×线索系数×难度×连击 |
| 1.11 | 结果页 | `claude-design` | `src/views/Result.vue` | 得分+评级+正确答案+再来一局 |
| 1.12 | 连击系统 | - | `src/stores/game.ts` | streak状态+combo动画 |
| 1.13 | 游戏流程串联 | `agent-browser` | - | 选难度→看线索→猜→结果→再来 |
| 1.14 | 浏览器全链路测试 | `agent-browser` | - | 截图每个关键状态 |

**验证标准**：
- [ ] 能选难度开始游戏
- [ ] 线索逐条出现有动画
- [ ] 输入正确人名能猜对（别名/错别字也能过）
- [ ] 温度提示颜色变化正确
- [ ] 计分和星级评价正确
- [ ] 结果页显示正确答案
- [ ] "再来一局"正常工作
- [ ] 手机端不崩不溢出

---

## Phase 2：接入后端（3天）

**目标**：前后端分离，API 可独立测试

**交付物**：FastAPI 服务 + 前端对接 + PostgreSQL 题库

### Day 4：后端基础

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 2.1 | FastAPI 项目结构 | `software-development` | `backend/app/` | 已有骨架，补全 |
| 2.2 | 数据库模型 | - | `backend/app/models/` | Question, GameSession, Player |
| 2.3 | Alembic 迁移 | - | `backend/alembic/` | 建表脚本 |
| 2.4 | Docker Compose 启动 | - | `docker-compose.yml` | PG + Redis 一键起 |

### Day 5：后端核心 API

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 2.5 | 答案验证服务（后端版） | `sds-tdd` | `backend/app/services/validator.py` | 5层匹配 |
| 2.6 | 计分服务（后端版） | `sds-tdd` | `backend/app/services/scoring.py` | 三种模式计分 |
| 2.7 | 游戏 Session 管理 | - | `backend/app/services/session.py` | 创建/查询/更新 |
| 2.8 | 渐进揭秘 API | - | `backend/app/routers/game.py` | start/clue/guess/score |
| 2.9 | API 单元测试 | `sds-tdd` | `backend/tests/` | pytest, 覆盖率>80% |

**API 接口清单**：
```
POST /api/game/progressive/start    → 创建游戏会话，返回第1条线索
GET  /api/game/progressive/{id}/clue → 获取当前线索
POST /api/game/progressive/{id}/guess → 提交猜测，返回结果+温度+分数
GET  /api/game/progressive/{id}/result → 获取最终结果
```

### Day 6：前后端对接

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 2.10 | API 客户端封装 | - | `src/api/game.ts` | axios 实例+拦截器 |
| 2.11 | Store 改造 | `software-development` | `src/stores/game.ts` | 从本地逻辑→调API |
| 2.12 | 题库导入脚本 | - | `backend/scripts/seed.py` | JSON→PostgreSQL |
| 2.13 | 联调测试 | `agent-browser` | - | 前后端完整链路 |
| 2.14 | 错误处理+loading态 | - | 全局 | 网络错误/超时/重试 |

**验证标准**：
- [ ] API 独立可用（Swagger 文档可交互）
- [ ] 前端通过 API 玩完一局
- [ ] 答案验证后端版和前端版结果一致
- [ ] Docker Compose 一键启动全部服务
- [ ] 网络断开时有友好提示

---

## Phase 3：二十问模式（3天）

**目标**：AI 驱动的是非问答，带人格化回答

**交付物**：可玩的二十问模式

### Day 7：AI 引擎

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 3.1 | 二十问 Prompt 设计 | `dspy` | `backend/app/prompts/twenty_q.py` | system prompt + 规则 |
| 3.2 | 结构化输出约束 | `outlines` | `backend/app/services/twenty_q_engine.py` | JSON schema 强制 |
| 3.3 | 对话上下文管理 | - | `backend/app/services/session.py` | 每局维护消息历史 |
| 3.4 | 回答风格分级 | - | `backend/app/prompts/styles.py` | 标准/暗示/警告/调侃/紧张 |

**AI 回答的结构化输出**：
```json
{
  "answer": "否",
  "response": "不是哦，但他和中国渊源不浅。",
  "emotion": "hint",
  "confidence": 0.95,
  "remaining": 17
}
```

**关键设计：AI 不是自由发挥，而是基于标准答案表回答**
```
输入：用户问"这个人是中国人吗？"
    ↓
查表：twenty_q_meta.is_chinese = false
    ↓
AI角色：用好听的方式说"否"
    ↓
输出："不是哦，但他和中国渊源不浅。"
```

### Day 8：后端 API + 前端

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 3.5 | 二十问 API | - | `backend/app/routers/game.py` | start/ask/final-guess |
| 3.6 | 二十问对话页面 | `claude-design` | `src/views/TwentyQ.vue` | 聊天气泡式界面 |
| 3.7 | 问题输入组件 | - | `src/components/QuestionInput.vue` | 输入+快捷问题标签 |
| 3.8 | 剩余问题计数器 | - | `src/components/QuestionCounter.vue` | 进度条+数字 |

### Day 9：打磨

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 3.9 | AI 回答质量测试 | `sds-tdd` | `backend/tests/test_twenty_q.py` | 20个标准问题场景 |
| 3.10 | 快捷问题标签 | - | `src/components/QuickQuestions.vue` | "是中国人吗？""还活着吗？" |
| 3.11 | AI反问功能 | - | `backend/app/prompts/` | 偶尔反问玩家猜的是谁 |
| 3.12 | 联调+截图验证 | `agent-browser` | - | 完整二十问流程 |

**验证标准**：
- [ ] AI 回答准确率 > 95%（基于 twenty_q_meta 查表）
- [ ] 对话气泡有打字机效果
- [ ] 剩余问题数正确递减
- [ ] 最终猜测正确识别
- [ ] AI 回答有人格化语气（不是"是"/"否"干巴巴）

---

## Phase 4：描述接龙模式（2天）

**目标**：三种模式全部可玩

**交付物**：描述接龙模式 + 统一游戏入口

### Day 10：后端

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 4.1 | 描述接龙 API | - | `backend/app/routers/game.py` | start/guess/hint |
| 4.2 | 关键词过滤器 | - | `backend/app/services/keyword_filter.py` | 禁止包含名字的字 |
| 4.3 | 关键词生成 | - | `backend/app/services/clue_engine.py` | 从题库读取+随机选组 |

### Day 11：前端+串联

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 4.4 | 描述接龙页面 | `claude-design` | `src/views/DescriptionChain.vue` | 关键词卡片+翻牌 |
| 4.5 | 关键词卡片组件 | - | `src/components/KeywordCard.vue` | 翻转动画 |
| 4.6 | 统一游戏入口 | - | `src/views/Home.vue` | 三种模式选择 |
| 4.7 | 统一结果页 | - | `src/views/Result.vue` | 三种模式通用 |
| 4.8 | 全模式联调 | `agent-browser` | - | 三种模式各跑一遍 |

**验证标准**：
- [ ] 三个模式都能独立完成一局
- [ ] 关键词卡片翻转动画流畅
- [ ] 关键词不泄露答案（过滤器生效）
- [ ] 三种模式的计分逻辑独立正确

---

## Phase 5：题库扩充 + 数据质量（2天）

**目标**：题库从 50 题扩充到 500 题，质量可控

**交付物**：500 题高质量题库 + 验证报告

### Day 12：批量生成

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 5.1 | 题库生成 Prompt 模板 | - | `scripts/generate_questions.py` | 人名→JSON结构 |
| 5.2 | 批量生成 500 题 | - | `data/questions_raw.json` | LLM 批量调用 |
| 5.3 | 去重+格式校验 | - | `scripts/validate_questions.py` | JSON schema 校验 |

### Day 13：质量审核

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 5.4 | 事实核查（抽样） | `multi-search-engine` | - | 每分类抽10题联网验证 |
| 5.5 | 线索质量检查 | - | `scripts/quality_check.py` | 线索不能太直白也不能太模糊 |
| 5.6 | 难度评级校准 | - | `scripts/calibrate_difficulty.py` | 统计每个分类的猜对率 |
| 5.7 | 导入数据库 | - | `backend/scripts/seed.py` | JSON→PostgreSQL |

**题库质量标准**：
```
每道题必须满足：
  ✅ 8条渐进线索，从模糊到精确
  ✅ 3组描述关键词（每组3个词）
  ✅ 别名覆盖 ≥ 3个
  ✅ 二十问元数据完整
  ✅ 线索中不直接出现名字或名字的字
  ✅ 至少1条线索是冷知识（区分度）
```

---

## Phase 6：社交对战（4天）

**目标**：实时 1v1 对战 + 好友异步挑战

### Day 14-15：实时对战

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 6.1 | Socket.IO 服务 | - | `backend/app/services/realtime.py` | 连接/房间/消息 |
| 6.2 | 匹配系统 | - | `backend/app/services/matchmaking.py` | 随机匹配+防重复 |
| 6.3 | 对战房间管理 | - | `backend/app/services/room_manager.py` | 创建/加入/结算 |
| 6.4 | 对战前端页面 | `claude-design` | `src/views/Battle.vue` | 分屏+倒计时+实时状态 |
| 6.5 | 对战 Store | `software-development` | `src/stores/battle.ts` | Socket状态管理 |

### Day 16-17：好友挑战 + 战绩卡

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 6.6 | 好友挑战 API | - | `backend/app/routers/battle.py` | 创建/接受/提交/结果 |
| 6.7 | 挑战分享页 | `claude-design` | `src/views/Challenge.vue` | 邀请码+答题+对比 |
| 6.8 | 战绩卡生成 | `claude-design` | `backend/app/services/share_card.py` | HTML→截图 |
| 6.9 | 排行榜（Redis） | - | `backend/app/services/ranking.py` | Sorted Set |
| 6.10 | 对战全链路测试 | `agent-browser` | - | 两个浏览器模拟对战 |

**验证标准**：
- [ ] 两个浏览器能匹配到同一局
- [ ] 实时同步不延迟 > 1s
- [ ] 断线重连不丢状态
- [ ] 好友挑战码可分享
- [ ] 战绩卡图片可生成
- [ ] 排行榜实时更新

---

## Phase 7：用户系统 + 经济（3天）

**目标**：登录、成长、道具、商业化

### Day 18-19：用户系统

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 7.1 | 微信登录 | - | `backend/app/services/auth.py` | OAuth 2.0 |
| 7.2 | 用户档案 | - | `backend/app/models/player.py` | 等级/经验/称号 |
| 7.3 | 成就系统 | - | `backend/app/services/achievement.py` | 条件触发+通知 |
| 7.4 | 个人中心页 | `claude-design` | `src/views/Profile.vue` | 数据+成就+设置 |

### Day 20：经济系统

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 7.5 | 道具系统 | - | `backend/app/services/inventory.py` | 背包+使用 |
| 7.6 | 商店页 | `claude-design` | `src/views/Shop.vue` | 道具列表+购买 |
| 7.7 | 体力系统 | - | `backend/app/services/stamina.py` | 恢复/消耗/购买 |

---

## Phase 8：部署上线（2天）

**目标**：生产环境部署，可公开访问

### Day 21-22

| # | 任务 | 技能 | 文件 | 说明 |
|---|------|------|------|------|
| 8.1 | Nginx 配置 | `software-development` | `nginx/` | SPA + API 反代 |
| 8.2 | HTTPS 证书 | - | - | Let's Encrypt |
| 8.3 | CI/CD 管道 | `sds-ci-cd` | `.github/workflows/` | lint→test→build→deploy |
| 8.4 | 探索性 QA | `dogfood` | - | 全功能找 bug |
| 8.5 | 性能优化 | `sds-performance` | - | 首屏加载/API响应 |
| 8.6 | 监控告警 | - | - | 错误率/响应时间 |

---

## 总览

```
Phase 0  原型设计     1天   ←  视觉定调
Phase 1  渐进揭秘     3天   ←  最小可玩 ✅
Phase 2  接入后端     3天   ←  前后端分离
Phase 3  二十问       3天   ←  AI引擎
Phase 4  描述接龙     2天   ←  三种模式全通
Phase 5  题库扩充     2天   ←  500题
Phase 6  社交对战     4天   ←  核心社交
Phase 7  用户+经济    3天   ←  商业化
Phase 8  部署上线     2天   ←  上线 🚀
───────────────────────────
总计                23天
```

### 里程碑

| 里程碑 | Phase | 可演示的内容 |
|--------|-------|-------------|
| **MVP Alpha** | 1 | "能玩了" — 渐进揭秘一局完整 |
| **MVP Beta** | 4 | "三种模式都能玩" — 单机完整体验 |
| **Public Beta** | 6 | "能对战了" — 社交功能上线 |
| **v1.0** | 8 | "正式上线" — 全功能公开 |

### 关键风险

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| AI 回答不准确 | 中 | 高 | 靠 twenty_q_meta 查表兜底，AI只负责润色 |
| 答案验证漏判 | 中 | 高 | 5层匹配+用户申诉+社区纠错 |
| 题库质量参差 | 高 | 中 | 人工审核+脚本质检+玩家反馈 |
| 实时对战延迟 | 低 | 中 | Socket.IO + Redis pub/sub |
| 前端手感差 | 中 | 高 | Phase 0 先定调，Phase 1 反复调交互 |
