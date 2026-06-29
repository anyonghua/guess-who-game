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
  // === 渐进揭秘 ===
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

  // === 二十问 ===
  startTwentyQ() {
    return request('/game/twenty-q/start', { method: 'POST' })
  },

  askQuestion(sessionId: string, question: string) {
    return request(`/game/twenty-q/${sessionId}/ask`, {
      method: 'POST',
      body: JSON.stringify({ question }),
    })
  },

  finalGuess(sessionId: string, answer: string) {
    return request(`/game/twenty-q/${sessionId}/final-guess`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    })
  },

  getTwentyQResult(sessionId: string) {
    return request(`/game/twenty-q/${sessionId}/result`)
  },

  // === 题库 ===
  getQuestionStats() {
    return request('/questions/stats')
  },
}
