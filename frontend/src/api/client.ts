const API_BASE = 'http://localhost:8000/api'

async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  // 游戏
  startGame(difficulty = 'normal') {
    return request('/game/progressive/start', {
      method: 'POST',
      body: JSON.stringify({ difficulty }),
    })
  },

  submitGuess(sessionId: string, answer: string) {
    return request(`/game/progressive/${sessionId}/guess`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    })
  },

  getResult(sessionId: string) {
    return request(`/game/progressive/${sessionId}/result`)
  },

  // 题库
  getQuestionStats() {
    return request('/questions/stats')
  },
}
