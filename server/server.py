import socketio
import os
from aiohttp import web
import random
# creates a new Async Socket IO Server
sio = socketio.AsyncServer(cors_allowed_origins='*')
# Creates a new Aiohttp Web Application
app = web.Application()
# Binds our Socket.IO server to our Web App
# instance
sio.attach(app)

# server variables

finished = []  # shared
wrong_tasks = []  # shared
players = []  # shared
k = []  # shared
c = []
run = False  # shared
tasks = []  # shared
charachters = ["ProfKemal", "ProfChristos", "ProfGianni",
               "ProfChristos", "ProfKhaled", "ProfMohammad", "ProfRyan", "ProfValentin"]


@sio.event
def connect(sid, environ):
    print('connect ', sid)


@sio.event
def my_message(sid, data):
    print('message ', data)


@sio.event
def disconnect(sid):
    global players
    players = []
    print('disconnect ', sid)


@sio.on('joinGame')
async def print_message(sid, message):
    print("joined game", message)
    indx = len(players)
    if message == "1":
        players.append({
            "pos": (300+random.randint(0, 5), 240+random.randint(0, 5)),
            "id": sid,
            "charachter": charachters[indx],
            "vision": "ok",
            "alive": True,
            "trapped": False,
            "isCrewMember": True
        })
    else:
        players.append({
            "pos": (100, 300),
            "id": sid,
            "charachter": "ProfSaquib",
            "vision": "ok",
            "alive": True,
            "trapped": False,
            "isCrewMember": False
        })
    await sio.emit("sendID", sid)


@sio.on('startGame')
async def start_game(sid, message):
    await sio.emit("runGame", {
        "players": players,

    })

# 0 move left
# 1 move right
# 2 move up
# 3 move down


@sio.on("updataPlayer")
async def updatePlayer(sid, message):
    await sio.emit("updatedPlayer", {
        "sid": sid,
        "move": message["move"],  # 0 - 3
        "trap": message["trap"],  # 0 - 1
        "ghost": message["ghost"],
        "isTrapped": message["isTrapped"],
        "crewMate": message["crewMate"]
    })


@sio.on("updateTasks")
async def updatePlayer(sid, message):
    await sio.emit("updatedTasks", {
        "sid": sid,
        "finished": message["finished"],
        "wrong": message["wrong"],
        "tasks": message["tasks"],
    })


@sio.on("endGame")
async def gameEnded(sid, message):
    await sio.emit("gameEnded", {
        "crew": message["crew"]
    })
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    web.run_app(app, port=port)
