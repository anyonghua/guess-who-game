const API_BASE = '/api'

async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`API error ${res.status}: ${err}`)
  }
  return res.json()
}

async function get(path: string) {
  return request(path)
}

async function post(path: string, data?: any) {
  return request(path, { method: 'POST', body: data ? JSON.stringify(data) : undefined })
}

export const api = {
  get,
  post,

  // 用户
  createPlayer: (nickname: string) => post('/user/create', { nickname }),
  getPlayer: (playerId: string) => get(`/user/${playerId}`),
  recordGame: (playerId: string, score: number, won: boolean) => post(`/user/${playerId}/game-result?score=${score}&won=${won}`),
  getLevels: () => get('/user/levels'),
  getItems: () => get('/user/items/list'),
  getAchievements: () => get('/user/achievements/list'),

  // 渐进揭秘
  startGame: (difficulty: string) => post('/game/progressive/progressive/start', { difficulty }),
  getClue: (sessionId: string) => get(`/game/progressive/progressive/${sessionId}/clue`),
  submitGuess: (sessionId: string, answer: string) => post(`/game/progressive/progressive/${sessionId}/guess`, { answer }),
  getResult: (sessionId: string) => get(`/game/progressive/progressive/${sessionId}/result`),

  // 二十问
  startTwentyQ: () => post('/game/twenty-q/start'),
  askQuestion: (sessionId: string, question: string) => post(`/game/twenty-q/${sessionId}/ask`, { question }),
  finalGuess: (sessionId: string, answer: string) => post(`/game/twenty-q/${sessionId}/final-guess`, { answer }),
  getTwentyQResult: (sessionId: string) => get(`/game/twenty-q/${sessionId}/result`),

  // 描述接龙
  startChain: () => post('/game/chain/start'),
  chainHint: (sessionId: string) => post(`/game/chain/${sessionId}/hint`),
  chainGuess: (sessionId: string, answer: string) => post(`/game/chain/${sessionId}/guess`, { answer }),
  getChainResult: (sessionId: string) => get(`/game/chain/${sessionId}/result`),

  // 排行榜 & 好友挑战
  getLeaderboard: () => get('/battle/leaderboard'),
  createChallenge: (playerName: string) => post('/battle/challenge/create', { player_name: playerName }),
  getChallenge: (challengeId: string) => get(`/battle/challenge/${challengeId}`),
  submitChallengeGuess: (challengeId: string, answer: string) => post(`/battle/challenge/${challengeId}/guess`, { answer }),

  // 题库
  getQuestionStats: () => get('/questions/stats'),

  // 每日挑战
  dailyStart: (playerName: string) => post('/daily/start', { player_name: playerName }),
  dailyClue: (sessionId: string) => get(`/daily/${sessionId}/clue`),
  dailyGuess: (sessionId: string, answer: string) => post(`/daily/${sessionId}/guess`, { answer }),
  dailyFinish: (sessionId: string, playerName: string) => post(`/daily/${sessionId}/finish`, { player_name: playerName }),
  dailyLeaderboard: (date?: string) => get('/daily/leaderboard' + (date ? `?date=${date}` : '')),
  dailyToday: () => get('/daily/today'),

  // 动态出题（变体）
  variantStart: () => post('/generator/start'),
  variantClue: (sessionId: string) => get(`/generator/${sessionId}/clue`),
  variantGuess: (sessionId: string, answer: string) => post(`/generator/${sessionId}/guess`, { answer }),
  generatorConfig: () => get('/generator/config'),
}
