"""实时对战服务 - Socket.IO + 匹配 + 房间管理"""

import uuid
import time
import random
import socketio
from sqlalchemy import select, func
from app.database import async_session
from app.models import Question, GameSession
from app.services.validator import validate_answer

# Socket.IO 服务器
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# 内存状态
waiting_players = {}  # {player_id: sid}
rooms = {}  # {room_id: RoomState}
player_rooms = {}  # {sid: room_id}
player_names = {}  # {sid: name}


class RoomState:
    def __init__(self, room_id, player1_sid, player2_sid, question):
        self.room_id = room_id
        self.players = {player1_sid: {"score": 0, "streak": 0, "last_answer": None},
                        player2_sid: {"score": 0, "streak": 0, "last_answer": None}}
        self.question = question
        self.clue_index = 0
        self.clues = question.progressive_clues or []
        self.started_at = time.time()
        self.round_timer = 30  # 每轮30秒
        self.is_active = True
        self.round_num = 0
        self.max_rounds = 5  # 共5轮

    def get_state(self):
        return {
            "room_id": self.room_id,
            "clue_index": self.clue_index,
            "clue": self.clues[self.clue_index] if self.clue_index < len(self.clues) else "",
            "round_num": self.round_num,
            "max_rounds": self.max_rounds,
            "players": {
                sid: {"score": p["score"], "streak": p["streak"]}
                for sid, p in self.players.items()
            },
            "is_active": self.is_active,
        }


async def get_random_question():
    """从题库随机选一道题"""
    async with async_session() as db:
        q = await db.execute(
            select(Question).order_by(func.random()).limit(1)
        )
        return q.scalar_one_or_none()


# === Socket.IO 事件 ===

@sio.event
async def connect(sid, environ):
    print(f"[Battle] Player connected: {sid}")
    await sio.emit('connected', {'sid': sid}, room=sid)


@sio.event
async def disconnect(sid):
    print(f"[Battle] Player disconnected: {sid}")
    # 清理匹配队列
    if sid in waiting_players:
        del waiting_players[sid]
    # 通知对手
    room_id = player_rooms.get(sid)
    if room_id and room_id in rooms:
        room = rooms[room_id]
        room.is_active = False
        opponents = [s for s in room.players if s != sid]
        for opp in opponents:
            await sio.emit('opponent_left', {'message': '对手已离开'}, room=opp)
    # 清理
    player_rooms.pop(sid, None)
    player_names.pop(sid, None)


@sio.event
async def set_name(sid, data):
    """设置玩家昵称"""
    player_names[sid] = data.get("name", "无名者")


@sio.event
async def find_match(sid, data):
    """匹配对手"""
    name = data.get("name", "无名者")
    player_names[sid] = name

    # 检查是否已在房间
    if sid in player_rooms:
        await sio.emit('error', {'message': '你已在对战中'}, room=sid)
        return

    # 查找等待中的对手
    waiting_sid = None
    for wsid in list(waiting_players.keys()):
        if wsid != sid:
            waiting_sid = wsid
            break

    if waiting_sid:
        # 匹配成功！
        del waiting_players[waiting_sid]
        await start_battle(sid, waiting_sid)
    else:
        # 加入等待队列
        waiting_players[sid] = True
        await sio.emit('waiting', {'message': '正在匹配对手...'}, room=sid)


@sio.event
async def cancel_match(sid, data):
    """取消匹配"""
    waiting_players.pop(sid, None)
    await sio.emit('match_cancelled', room=sid)


async def start_battle(sid1, sid2):
    """开始对战"""
    question = await get_random_question()
    if not question:
        await sio.emit('error', {'message': '题库为空'}, room=sid1)
        await sio.emit('error', {'message': '题库为空'}, room=sid2)
        return

    room_id = str(uuid.uuid4())[:8]
    room = RoomState(room_id, sid1, sid2, question)
    rooms[room_id] = room
    player_rooms[sid1] = room_id
    player_rooms[sid2] = room_id

    # 加入 Socket.IO 房间
    sio.enter_room(sid1, room_id)
    sio.enter_room(sid2, room_id)

    # 通知双方
    p1_name = player_names.get(sid1, "玩家1")
    p2_name = player_names.get(sid2, "玩家2")

    await sio.emit('battle_start', {
        'room_id': room_id,
        'opponent': p2_name,
        'clue': room.clues[0] if room.clues else "",
        'clue_index': 0,
        'round_num': 1,
        'max_rounds': room.max_rounds,
    }, room=sid1)

    await sio.emit('battle_start', {
        'room_id': room_id,
        'opponent': p1_name,
        'clue': room.clues[0] if room.clues else "",
        'clue_index': 0,
        'round_num': 1,
        'max_rounds': room.max_rounds,
    }, room=sid2)


@sio.event
async def submit_battle_guess(sid, data):
    """对战中提交猜测"""
    room_id = player_rooms.get(sid)
    if not room_id or room_id not in rooms:
        await sio.emit('error', {'message': '不在对战中'}, room=sid)
        return

    room = rooms[room_id]
    if not room.is_active:
        return

    answer = data.get("answer", "").strip()
    if not answer:
        return

    # 验证答案
    result = validate_answer(answer, room.question.name, room.question.aliases or [])
    player = room.players[sid]
    player["last_answer"] = answer

    if result["correct"]:
        # 计分
        multiplier = [8, 7, 6, 5, 4, 3, 2, 1]
        m = multiplier[min(room.clue_index, 7)]
        points = 100 * m
        player["score"] += points
        player["streak"] += 1

        # 通知双方
        p1_name = player_names.get(sid, "玩家")
        for s in room.players:
            await sio.emit('round_result', {
                'correct_player': p1_name,
                'correct_sid': sid,
                'answer': room.question.name,
                'points': points,
                'scores': {s2: room.players[s2]["score"] for s2 in room.players},
                'is_you': s == sid,
            }, room=s)

        # 下一轮
        room.round_num += 1
        if room.round_num >= room.max_rounds:
            await end_battle(room_id)
        else:
            # 新题目
            new_q = await get_random_question()
            if new_q:
                room.question = new_q
                room.clues = new_q.progressive_clues or []
                room.clue_index = 0
                for s in room.players:
                    room.players[s]["last_answer"] = None
                    room.players[s]["streak"] = 0
                await sio.emit('new_round', {
                    'round_num': room.round_num + 1,
                    'max_rounds': room.max_rounds,
                    'clue': room.clues[0] if room.clues else "",
                    'clue_index': 0,
                }, room=room_id)
            else:
                await end_battle(room_id)
    else:
        # 猜错，给反馈
        await sio.emit('wrong_answer', {
            'message': '不对！',
            'clue_index': room.clue_index,
        }, room=sid)

        # 如果双方都猜错了，推进线索
        all_wrong = all(p["last_answer"] and not validate_answer(
            p["last_answer"], room.question.name, room.question.aliases or []
        )["correct"] for p in room.players.values())

        if all_wrong and room.clue_index < len(room.clues) - 1:
            room.clue_index += 1
            for s in room.players:
                room.players[s]["last_answer"] = None
            await sio.emit('next_clue', {
                'clue': room.clues[room.clue_index],
                'clue_index': room.clue_index,
            }, room=room_id)


async def end_battle(room_id):
    """结束对战"""
    room = rooms.get(room_id)
    if not room:
        return

    room.is_active = False
    scores = {sid: room.players[sid]["score"] for sid in room.players}

    # 确定胜者
    max_score = max(scores.values())
    winners = [sid for sid, sc in scores.items() if sc == max_score]
    is_draw = len(winners) > 1

    for sid in room.players:
        is_winner = sid in winners
        opponent_sid = [s for s in room.players if s != sid][0]
        await sio.emit('battle_end', {
            'result': 'draw' if is_draw else ('win' if is_winner else 'lose'),
            'your_score': scores[sid],
            'opponent_score': scores[opponent_sid],
            'opponent_name': player_names.get(opponent_sid, "对手"),
            'answer': room.question.name,
        }, room=sid)

    # 清理
    for sid in room.players:
        player_rooms.pop(sid, None)
    del rooms[room_id]


@sio.event
async def next_battle_clue(sid, data):
    """请求下一条线索（对战中）"""
    room_id = player_rooms.get(sid)
    if not room_id or room_id not in rooms:
        return
    room = rooms[room_id]
    if not room.is_active:
        return
    if room.clue_index < len(room.clues) - 1:
        room.clue_index += 1
        await sio.emit('next_clue', {
            'clue': room.clues[room.clue_index],
            'clue_index': room.clue_index,
        }, room=room_id)
