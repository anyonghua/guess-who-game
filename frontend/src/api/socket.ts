import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

export function connectSocket(): Socket {
  if (!socket) {
    socket = io({
      transports: ['websocket', 'polling'],
    })
  }
  return socket
}

export function getSocket(): Socket {
  return connectSocket()
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}
