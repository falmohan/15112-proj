import pygame
import random
import socketio
from os import path
import sys
import socket





run = False

finished = []  # shared - it holds finished tasks
wrong_tasks = []  # shared - it holds tasks that are done wrong
tasks = [] # holds total tasks in map

players = []  # shared
k = []  # shared - killer list
c = [] # crewmember/goodpeople list
playerIndx = -1
playerId = None
crewMate = None
win = None
screenw = 1440
screenh = 800
# objects that require collision
boundaries = []

# commands given in terminal
x = sys.argv[1]
if x == "1":
    crewMate = True # initiates a crew mate
else:
    crewMate = False # initiates a killer player

# creates an instance of socketio
sio = socketio.Client()

# connecting
@ sio.event
def connect():
    global run
    # initiates main window
    pygame.init()
    screenw = 1440
    screenh = 800
    win = pygame.display.set_mode((screenw, screenh))
    pygame.display.set_caption("Ready or Not")
    font = pygame.font.SysFont("comicsansms", 30)
    text = font.render("start", True, (196, 196, 196))
    # fills the screen with a color
    win.fill((196, 196, 196))
    # adds professor Saquib's image to screen
    prof = SpriteSheet("saquibimage.png")
    start_img = prof.get_mini( 0, 0, 1490, 1911, 2)
    start_img.set_colorkey((255, 255, 255))
    win.blit(start_img, [355, 0])

    # stores the (x,y) coordinates into
    # the variable as a tuple

    # superimposing the text onto our button
    win.blit(text, (screenw/2-30, screenh/2))
    pygame.display.flip()
    #X = True
    while (not run):
        # pygame.time.delay(10)
        # pygame.event.wait()
        # main game loop
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                print("QUIT")
                pygame.quit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if screenw/2-140 <= mouse[0] <= screenw/2+140 and screenh/2 <= mouse[1] <= screenh/2+40:
                    sio.emit("startGame", "dummy")
                    print("started Game")
                    run = True
                    # pygame.quit()
                    break
        if run == True:
            break
        # button click
        mouse = pygame.mouse.get_pos()
        color = (255, 255, 255)
        color_light = (170, 170, 170)
        color_dark = (100, 100, 100)
        # if mouse is on button, button is light colored
        if screenw/2 <= mouse[0] <= screenw/2+140 and screenh/2 <= mouse[1] <= screenh/2+40:
            pygame.draw.rect(win, color_light, [
                             screenw/2-140, screenh/2, 280, 40])

        # else button is dark colored
        else:
            pygame.draw.rect(win, color_dark, [
                             screenw/2-140, screenh/2, 280, 40])
        # superimposing the text onto our button
        win.blit(text, (screenw/2-30, screenh/2))
        pygame.display.flip()

        # updates the frames of the game
        pygame.display.update()
    print('connection established')


@ sio.event
def disconnect():
    print('disconnected from server')


@ sio.on("runGame")
def runGame(message):
    global run
    run = True
    pygame.quit()
    gameLoop(message)


@ sio.on("sendID")
def getID(message):
    global playerId
    if playerId == None:
        playerId = message


@ sio.on("updatedPlayer")
def updatedPlayer(message):

    global players, playerId, k
    #print(message, playerId, message["sid"])

    move = message["move"]
    if(playerId == message["sid"]):
        return

    for i in range(len(players)):
        if message["sid"] == players[i].id:
            if(message["crewMate"]):
                players[i].trapped = message["isTrapped"]
            if move == 0 and ((not hasattr(players[i], 'alive')) or players[i].trapped == False):
                players[i].moveLeft()
            elif move == 1 and ((not hasattr(players[i], 'alive')) or players[i].trapped == False):
                players[i].moveRight()
            elif move == 2 and ((not hasattr(players[i], 'alive')) or players[i].trapped == False):
                players[i].moveUp()
            elif move == 3 and ((not hasattr(players[i], 'alive')) or players[i].trapped == False):
                players[i].moveDown()
        if message["ghost"] == players[i].id:
            players[i].becomeGhost()
    if(message["trap"]):
        k[0].setTraps()


@ sio.on("updatedTasks")
def updatedTasks(message):
    global finished, wrong_tasks, tasks
    finished = []
    #print("rec", message["tasks"])
    for x in message["finished"]:
        task = Task(x["pos"], x["category"])
        task.active = False
        finished.append(task)
    wrong_tasks = []
    for x in message["wrong"]:
        print("add wrong task")
        task = Task(x["pos"], x["category"])
        wrong_tasks.append(task)
    tasks = []
    for x in message["tasks"]:
        task = Task(x["pos"], x["category"])
        task.loadTask()
        tasks.append(task)


def sendUpdatePlayer(player, props):
    # print(player.x)
    global crewMate
    sio.emit("updataPlayer", {
        "pos": (player.x, player.y),
        "move": props["move"],
        "trap": props["trap"],
        "ghost": props["ghost"],
        "isTrapped": props["isTrapped"],
        "crewMate": crewMate
    })


def sendUpdateTasks(props):
    # print(player.x)
    sio.emit("updateTasks", {
        "finished": props["finished"],
        "wrong": props["wrong"],
        "tasks": props["tasks"],

    })


def endGame(crew):
    sio.emit("endGame", {
        "crew": crew
    })


# connect socket to server
sio.connect('http://localhost:8080')


@sio.on("gameEnded")
def gameEnded(message):
    global run
    print("end game")
    run = False
    if message["crew"] == True:
        print("Crew Win")
    else:
        print("Killer win")


def joinGame():
    global x
    sio.emit("joinGame", x)


# creating tasks for players to complete
joinGame()


class Task:

    def __init__(self, position, category):

        self.active = False
        self.x = position[0]
        self.y = position[1]
        self.width = 2
        self.height = 2
        self.category = category
        task = SpriteSheet("taskpage.png")
        self.page = task.get_image(0, 0, 409, 511)
        self.page.set_colorkey((0, 0, 0))
        self.font = pygame.font.SysFont("comicsansms", 20)
        icsprite = SpriteSheet("icon.png")
        self.icon = icsprite.get_mini(0, 0, 860, 1070, 40)
        self.icon.set_colorkey((247, 247, 247))
        buttons = SpriteSheet("button1.png")
        self.button = buttons.get_image(0, 0, 195, 52)
        self.button.set_colorkey((0, 0, 0))

    # places task icon in the task's position
    def placeTask(self):
        win.blit(self.icon, [self.x, self.y])

    # loads the main page of the task
    def loadPage(self):
        win.blit(self.page, [500, 150])

    # loads the question and choices from questions folder
    def loadTask(self):
        if self.category == "History":
            file = open("HistoryQuestions.txt")
            q = file.readlines()
            i = random.randrange(0, len(q) - 1)
            line = q[i][:-1]
            q_a = line.split("@")
            self.question = self.font.render(q_a[0], True, (0, 0, 0))
            self.choices = q_a[1:-1]
            self.correct = q_a[-1]

    # loads the questions, choices and buttons in the main task page
    def displayTask(self):

        y = 350
        win.blit(self.question, (700 - self.question.get_width() //
                                 2, 260 - self.question.get_height() // 2))
        self.button1 = pygame.Rect(610, 350, 189, 44)
        self.button2 = pygame.Rect(610, 420, 189, 44)
        self.button3 = pygame.Rect(610, 490, 189, 44)

        answer1 = self.font.render(self.choices[0], True, (0, 0, 0))
        answer2 = self.font.render(self.choices[1], True, (0, 0, 0))
        answer3 = self.font.render(self.choices[2], True, (0, 0, 0))

        self.buttons = [self.button1, self.button2, self.button3]
        win.blit(self.button, [600, 340])
        win.blit(self.button, [600, 415])
        win.blit(self.button, [600, 485])

        answers = [answer1, answer2, answer3]
        for answer in answers:
            win.blit(answer, (675, y))
            y += 70

        self.dict = {str(self.button1): "Button 1", str(self.button2): "Button 2",
                     str(self.button3): "Button 3"}

    # if a wrong button is pressed
    def displayWrong(self):
        wrong = self.font.render("Wrong!", True, (0, 0, 0))
        win.blit(wrong, (665, 300))
        comeback = self.font.render("you failed this task", True, (0, 0, 0))
        win.blit(comeback, (620, 350))

    # get the center point from left corner and width
    def centerPoint(self):
        centerx = (self.x - 1) + (self.width / 2)
        centery = (self.y - 1) + (self.height / 2)
        centerPoint = (centerx, centery)
        return centerPoint


# draws the main map of the game
class GameMap:

    def __init__(self):
        self.map = SpriteSheet("fpi2.png")
        self.bar = SpriteSheet("taskbar.png")
        self.barimage = self.bar.get_image(0, 0, 540, 33)
        self.barimage.set_colorkey((0, 0, 0))
        self.mmap = self.map.get_image(0, 0, 2880, 1600)
        self.playerwin = False
        self.killerwin = False

    # displays map image on screen
    def drawMap(self):
        win.blit(self.mmap, [0, 0])

    # adds the task bar image onto the screen
    def taskBar(self, progress):
        # length of finished tasks adds on to the taskbar
        load = 25 * progress
        bar = pygame.Rect(0, 0, load, 25)
        pygame.draw.rect(win, [20, 100, 20], bar)
        win.blit(self.barimage, [0, 0])

    def players_win(self):
        print("players win!")
    def killer_win(self):
        print("killer wins!")

filePathRef = __file__
# class to handle sprite sheets and extract images
# ---------------------------------------------------------------------------------------
# class gotten from http://programarcadegames.com/python_examples/en/sprite_sheets/
class SpriteSheet:

    def __init__(self, filename):
        # load sheet
        self.dir = path.dirname(filePathRef)
        img_dir = path.join(self.dir, "Images")
        try:
            self.sheet = pygame.image.load(
                path.join(img_dir, filename)).convert()
        except:
            self.sheet = pygame.image.load(
                path.join(img_dir, "icon.png")).convert()
            pass

    def get_image(self, x, y, width, height):
        # grab image out of spritesheet
        image = pygame.Surface((width, height))
        image.blit(self.sheet, (0, 0), (x, y, width, height))
        image = pygame.transform.scale(image, (width * 1, height * 1))
        return image

    def get_mini(self, x, y, width, height, scale):
        # grab image out of spritesheet
        image = pygame.Surface((width, height))
        image.blit(self.sheet, (0, 0), (x, y, width, height))
        image = pygame.transform.scale(
            image, (width // scale, height // scale))
        return image

    def get_images(self, state):
        up = [self.get_image(0, 96, 32, 32), self.get_image(32, 96, 32, 32),
              self.get_image(64, 96, 32, 32), self.get_image(96, 96, 32, 32)]
        down = [self.get_image(0, 0, 32, 32), self.get_image(32, 0, 32, 32),
                self.get_image(64, 0, 32, 32), self.get_image(96, 0, 32, 32)]
        left = [self.get_image(0, 32, 32, 32), self.get_image(32, 32, 32, 32),
                self.get_image(64, 32, 32, 32), self.get_image(96, 32, 32, 32)]
        right = [self.get_image(0, 64, 32, 32), self.get_image(32, 64, 32, 32),
                 self.get_image(64, 64, 32, 32), self.get_image(96, 64, 32, 32)]

        if state == "up":
            return up
        if state == "down":
            return down
        if state == "right":
            return right
        if state == "left":
            return left
# ------------------------------------------------------------------------------------------

# main player class
class Player:

    def __init__(self, points, playerId, character, vision):
        self.x = points[0]
        self.y = points[1]
        self.prof = character
        self.character = SpriteSheet(self.prof + ".png")
        self.vision = vision
        self.width = 32
        self.height = 32
        self.speed = 1
        self.allow_trap = True
        self.step = 0
        self.currstance = self.character.get_images("down")[0]
        self.currstance.set_colorkey((0, 0, 0))
        self.id = playerId

    # updates players image and position after each movement
    def drawPlayer(self):
        win.blit(self.currstance, [self.x, self.y])

    def moveUp(self):
        movement = self.y - self.speed
        # if a boundary is in the way, disable movement
        if self.detectWallsY(movement) == True:
            self.y = self.y
        # else move and update movement images
        else:
            self.y -= self.speed
            images = self.character.get_images("up")
            self.currstance = images[int(self.step)]
            self.currstance.set_colorkey((0, 0, 0))
            if self.step < 4 and self.step + 0.1 < 4:
                self.step += 0.1
                self.step = round(self.step, 1)
            else:
                self.step = 0

    # function to detect boundaries in y axis
    def detectWallsY(self, movement):
        for boundary in boundaries:
            check = collide(pygame.Rect(self.x, movement,
                                        self.width, self.height), boundary)
            if check == True:
                return check

    # function to detect boundaries in x axis
    def detectWallsX(self, movement):
        for boundary in boundaries:
            check = collide(pygame.Rect(movement, self.y,
                                        self.width, self.height), boundary)
            if check == True:
                return check

    def moveDown(self):
        # if a boundary is in the way, disable movement
        movement = self.y + self.speed
        if self.detectWallsY(movement) == True:
            self.y = self.y
        # else move and update movement images
        else:
            self.y += self.speed
            images = self.character.get_images("down")
            self.currstance = images[int(self.step)]
            self.currstance.set_colorkey((0, 0, 0))
            if self.step < 4 and self.step + 0.1 < 4:
                self.step += 0.1
                self.step = round(self.step, 1)
            else:
                self.step = 0

    def moveRight(self):
        movement = self.x + self.speed
        # if a boundary is in the way, disable movement
        if self.detectWallsX(movement) == True:
            self.x = self.x
        # else move and update images
        else:
            self.x += self.speed
            images = self.character.get_images("right")
            self.currstance = images[int(self.step)]
            self.currstance.set_colorkey((0, 0, 0))
            if self.step < 4 and self.step + 0.1 < 4:
                self.step += 0.1
                self.step = round(self.step, 1)
            else:
                self.step = 0

    def moveLeft(self):
        movement = self.x - self.speed
        # if a boundary is in the way, disable movement
        if self.detectWallsX(movement) == True:
            self.x = self.x
        # else move and update images
        else:
            self.x -= self.speed
            images = self.character.get_images("left")
            self.currstance = images[int(self.step)]
            self.currstance.set_colorkey((0, 0, 0))
            if self.step < 4 and self.step + 0.1 < 4:
                self.step += 0.1
                self.step = round(self.step, 1)
            else:
                self.step = 0

    # get the center point from left corner and width
    def centerPoint(self):
        centerx = (self.x - 1) + (self.width / 2)
        centery = (self.y - 1) + (self.height / 2)
        centerPoint = (centerx, centery)
        return centerPoint


class Killer(Player):

    def __init__(self, points, playerId, character, vision):
        super().__init__(points, playerId, character, vision)
        self.curr_traps = [] # traps that are in inventory
        self.active_traps = [] # traps that are placed in map
        for i in range(6): # total number of traps = 6
            trap = Trap(points) # creates 6 instances of traps
            self.curr_traps.append(trap) # places traps in inventory

    # ability to place traps
    def setTraps(self):
        if len(self.curr_traps) != 0: # if inventory isnt empty
            T = self.curr_traps.pop() # pop trap from inventory
            p = (self.x, self.y) # position of trap is position of player
            T.draw(p) # draw the trap image
            T.setTrapID(len(self.curr_traps)) # give the trap a unique id
            self.active_traps.append(T) # append it in the active trap list

    # called when player gets unstuck from traps
    def deleteTrap(self, i):
        self.active_traps.pop(i)


class Trap:

    def __init__(self, position):
        self.x = position[0]
        self.y = position[1]
        self.active = False
        self.color = (192, 192, 192)
        self.trapID = None
        # trap sprite sheet and extracting images
        self.image = SpriteSheet("traps.png")
        self.open_trap = self.image.get_mini(14, 54, 126, 51, 4)
        self.locked_trap = self.image.get_mini(190, 30, 135, 75, 4)
        self.open_trap.set_colorkey((166, 172, 186))
        self.locked_trap.set_colorkey((166, 172, 186))

    # gives trap a unique id
    def setTrapID(self, tid):
        self.trapID = tid

    # draws the trap on screen onto given position
    def draw(self, position):
        self.active = True
        self.x = position[0]
        self.y = position[1]
        win.blit(self.open_trap, [self.x, self.y])
        # pygame.draw.circle(win, self.color, position, 10)

    # draws a locked trap for if player gets stuck in a trap
    def drawLocked(self, position):
        self.active = True
        self.x = position[0]
        self.y = position[1]
        win.blit(self.locked_trap, [self.x, self.y])

    # traps players given a list of players
    def trapCrewmember(self, crewmembers):
        for crewmember in crewmembers:
            if(not hasattr(crewmember, 'alive')):
                continue
            # if distance of player is close enough to trap, player gets trapped
            member = crewmember.centerPoint()
            distance = ((member[0] - self.x) ** 2 +
                        (self.y - member[1]) ** 2) ** 0.5
            if distance < 20:
                crewmember.trapped = True
                crewmember.setTrapID(self.trapID)

    # gets the center point of trap from its width and height
    def centerPoint(self):
        centerx = (self.x - 1) + (self.width / 2)
        centery = (self.y - 1) + (self.height / 2)
        centerPoint = (centerx, centery)
        return centerPoint


class CrewMember(Player):

    def __init__(self, points, playerId, character, vision, alive, task_list=[]):
        super().__init__(points, playerId, character, vision)
        self.alive = alive
        self.task_list = task_list
        self.trapped = False
        self.count = 0
        self.cID = None
        self.ctrapID = None

    def addTasklist(self, lst):
        self.task_list = lst

    # if dead, the dead image gets loaded
    def becomeGhost(self):
        if self.alive == True:
            self.prof = "Dead" + self.prof
            self.character = SpriteSheet((self.prof + ".png"))
            self.alive = False
            self.currstance = self.character.get_images("down")[0]
            self.currstance.set_colorkey((0, 0, 0))

    # sharing the trapid of the trap if player got stuck in trap
    def setTrapID(self, tId):
        self.ctrapID = tId

# a mini map of the game
class Map:

    def __init__(self):
        # scale = /7
        self.width = screenw / 7
        self.height = screenh / 7 - (10)
        self.posx = screenw - 550
        self.posy = 10

    # creates mini map
    def createMap(self):

        pygame.draw.rect(win, (50, 50, 50), (self.posx, self.posy, self.width, self.height))
        # draws boundaries in the minimap to display rooms
        for boundary in boundaries:
            if boundary[2] > 100 or boundary[3] > 100:
                pygame.draw.rect(win, (0, 0, 0),
                                 (890 + boundary[0] / 7, 10 + boundary[1] / 7, boundary[2] / 7 + 2, boundary[3] / 7))

    # display rectangles for the alive players in the mini map
    def showPlayers(self, crewmembers):

        for cm in crewmembers:

            if cm.alive == True:
                pygame.draw.rect(win, (60, 180, 140), (890 + (cm.x / 7),
                                                       10 + (cm.y / 7), cm.width / 7, cm.height / 7))

    # display circles for placed traps in the mini map
    def showTraps(self, traps):
        for trap in traps:
            pygame.draw.circle(win, (192, 192, 192),
                               (780 + (trap.x / 5), 460 + (trap.y / 5)), 10 / 5)

    # display rectangle for killer in the mini map
    def showKillers(self, killers):
        for kl in killers:
            pygame.draw.rect(win, (255, 0, 0), (890 + (kl.x / 7),
                                                10 + (kl.y / 7), kl.width / 7, kl.height / 7))


# helper function to provide distance between two centerpoints
def distance(a, b):
    points1 = a.centerPoint()
    points2 = b.centerPoint()
    distance = ((points1[0] - points2[0]) ** 2 +
                (points1[1] - points2[1]) ** 2) ** 0.5
    return distance

# helper function that checks for collision between objects
def collide(a, b):
    if pygame.Rect.colliderect(a, b):
        return True


# MAIN LOOP
def gameLoop(message):

    global playerIndx, crewMate, finished, wrong_tasks, tasks, run, c, k, players, screenh, screenw, win, boundaries, playerId
    # pygame.quit()
    pygame.init()
    win = pygame.display.set_mode((screenw, screenh))
    pygame.display.set_caption("test")
    clock = pygame.time.Clock()
    print(message)
    playersArr = message["players"]
    # set game up and variables
    i = 0
    for el in playersArr:
        if el["id"] == playerId:
            playerIndx = i
        if(el["isCrewMember"]):
            crew = CrewMember(el["pos"], el["id"],
                              el["charachter"], el["vision"], el["alive"])
            c.append(crew)
            players.append(crew)
        else:
            killer = Killer(el["pos"], el["id"],
                            el["charachter"], el["vision"])
            k.append(killer)
            players.append(killer)
        i += 1
    run = True
    # creates all tasks in map
    task1 = Task([60, 90], "History")
    task2 = Task([258, 421], "History")
    task3 = Task([1027, 410], "History")
    task4 = Task([65, 380], "History")
    task5 = Task([840, 700], "History")
    task6 = Task([170, 660], "History")
    task7 = Task([120, 730], "History")
    task8 = Task([450, 190], "History")
    task9 = Task([500, 510], "History")
    task10 = Task([1366, 200], "History")
    task11 = Task([1328, 447], "History")
    task12 = Task([1100, 205], "History")
    task13 = Task([1210, 135], "History")
    task14 = Task([890, 210], "History")
    task15 = Task([70, 90], "History")
    task16 = Task([300, 421], "History")
    task17 = Task([1010, 410], "History")
    task18 = Task([70, 380], "History")
    task19 = Task([870, 700], "History")
    task20 = Task([200, 660], "History")
    task21 = Task([160, 730], "History")
    task22 = Task([500, 190], "History")
    task23 = Task([550, 510], "History")
    task24 = Task([405, 526], "History")
    task25 = Task([450, 695], "History")
    task26 = Task([71, 200], "History")
    task27 = Task([1176, 576], "History")
    task28 = Task([160, 302], "History")
    task29 = Task([1320, 292], "History")
    task30 = Task([1040, 530], "History")
    task31 = Task([1365, 200], "History")
    task32 = Task([1080, 696], "History")

    tasks = [task1, task2, task3, task4, task5, task6, task7, task8,
             task9, task10, task11, task12, task13, task14, task15,
             task16, task17, task18, task19, task20, task21, task22,
             task23, task24, task25, task26, task27, task28, task29,
             task30, task31, task32,
             ]  # shared
    b = GameMap()
    boundaries = [pygame.Rect(0, 0, 45, 800), pygame.Rect(0, 770, 1397, 39),
                  pygame.Rect(1403, 0, 45, 800), pygame.Rect(40, 0, 1355, 110),
                  pygame.Rect(1197, 105, 97, 27), pygame.Rect(
                      1146, 105, 51, 50),
                  pygame.Rect(866, 105, 285, 99), pygame.Rect(
                      807, 105, 23, 38),
                  pygame.Rect(813, 174, 26, 10), pygame.Rect(797, 105, 12, 29),
                  pygame.Rect(786, 105, 13, 20), pygame.Rect(777, 105, 10, 12),
                  pygame.Rect(767, 105, 20, 6), pygame.Rect(528, 105, 239, 41),
                  pygame.Rect(486, 105, 47, 41), pygame.Rect(472, 105, 13, 53),
                  pygame.Rect(460, 105, 12, 64), pygame.Rect(425, 105, 34, 73),
                  pygame.Rect(425, 150, 20, 20), pygame.Rect(
                      193, 105, 238, 100),
                  pygame.Rect(99, 105, 42, 41), pygame.Rect(144, 105, 49, 52),
                  pygame.Rect(51, 196, 40, 31), pygame.Rect(51, 290, 40, 31),
                  pygame.Rect(147, 289, 40, 31), pygame.Rect(51, 387, 40, 31),
                  pygame.Rect(147, 387, 40, 31), pygame.Rect(45, 483, 49, 11),
                  pygame.Rect(45, 495, 99, 28), pygame.Rect(45, 520, 241, 120),
                  pygame.Rect(239, 662, 47, 48), pygame.Rect(199, 685, 28, 25),
                  pygame.Rect(46, 724, 97, 37), pygame.Rect(
                      336, 567, 288, 120),
                  pygame.Rect(430, 327, 50, 241), pygame.Rect(
                      435, 300, 26, 27),
                  pygame.Rect(480, 320, 142, 148), pygame.Rect(
                      394, 281, 40, 178),
                  pygame.Rect(237, 280, 155, 44), pygame.Rect(
                      192, 280, 46, 190),
                  pygame.Rect(288, 481, 48, 32), pygame.Rect(389, 518, 35, 41),
                  pygame.Rect(480, 497, 93, 36), pygame.Rect(819, 321, 10, 8),
                  pygame.Rect(827, 314, 15, 15), pygame.Rect(838, 302, 13, 25),
                  pygame.Rect(847, 293, 13, 34), pygame.Rect(860, 280, 49, 52),
                  pygame.Rect(672, 323, 237, 117), pygame.Rect(
                      672, 466, 191, 7),
                  pygame.Rect(1007, 520, 100, 46), pygame.Rect(
                      864, 522, 93, 43),
                  pygame.Rect(816, 544, 51, 21), pygame.Rect(
                      767, 567, 380, 120),
                  pygame.Rect(911, 282, 198, 138), pygame.Rect(
                      1106, 283, 43, 282),
                  pygame.Rect(1152, 333, 90, 113), pygame.Rect(
                      1298, 330, 91, 109),
                  pygame.Rect(1154, 282, 44, 31), pygame.Rect(
                      1299, 282, 93, 28),
                  pygame.Rect(1298, 187, 94, 26), pygame.Rect(
                      239, 325, 154, 64),
                  pygame.Rect(828, 130, 42, 74),
                  ]
    s = Map() #mini map
    run = True  # shared
    pressed_left = False
    pressed_right = False
    pressed_up = False
    pressed_down = False
    space = 0
    opened_task = False
    task_opened = False

    for task in tasks:
        task.loadTask()

    font1 = pygame.font.SysFont("comicsansms", 20)
    complete = font1.render("Complete!", True, (0, 0, 0))

    print("player index")
    print(playerIndx)
    curr_task_opened = None
    start_ticks = pygame.time.get_ticks()  # starter tick
    print("run", run)
    while run:
        #print("run", run)
        # pygame.time.delay(5)
        #print("after delay")
        setTrap = 0
        isTaskChange = False
        # event checking
        for event in pygame.event.get():
            #print("event", event)
            # print(players)
            if event.type == pygame.QUIT: #player leaves if game closes
                print("exited")
                run = False
                pygame.quit()
                sys.exit()
                return

                # return
            if event.type == pygame.KEYDOWN:  # check for key presses
                if event.key == pygame.K_LEFT:
                    pressed_left = True
                elif event.key == pygame.K_RIGHT:  # right arrow turns right
                    pressed_right = True
                elif event.key == pygame.K_UP:  # up arrow goes up
                    pressed_up = True
                elif event.key == pygame.K_DOWN:  # down arrow goes down
                    pressed_down = True
                if event.key == pygame.K_0 and crewMate == False:  # set the Trap
                    # print("set trap")
                    k[0].setTraps()
                    setTrap = 1

                # player escaping traps
                if crewMate and players[playerIndx].trapped == True:
                    if event.key == pygame.K_p: # if p key is pressed 10 times
                        space += 1
                        print(space)
                    if space == 10:
                        players[playerIndx].trapped = False # player is no longer trapped
                        space = 0
                        # remove the trap
                        if len(k[0].active_traps) > 1:
                            for i in range(len(k[0].active_traps) - 1):
                                if k[0].active_traps[i].trapID == players[playerIndx].ctrapID:
                                    k[0].deleteTrap(i)
                        else:
                            k[0].deleteTrap(0)

            # detect answers when there is an opened task
            elif event.type == pygame.MOUSEBUTTONDOWN and task_opened == True:
                #print("click task")
                task = curr_task_opened
                mouse_pos = event.pos
                # checks if mouse position is over answer buttons
                for button in task.buttons:  # checks clicks in each button
                    # if the correct button was clicked, close task
                    if button.collidepoint(mouse_pos) and task.dict[str(button)] == task.correct:
                        isTaskChange = True
                        # prints current location of mouse
                        print('button was pressed at {0}'.format(mouse_pos))
                        task.active = False
                        task_opened = False
                        if len(tasks) != 0:
                            finished.append(tasks.pop(tasks.index(task)))
                    # if the wrong button was clicked, task stays in map
                    # task becomes insolvable
                    elif button.collidepoint(mouse_pos) and task.dict[str(button)] != task.correct:
                        isTaskChange = True
                        wrong_tasks.append(tasks.pop(tasks.index(task)))
                        #print("wrong task")
            elif event.type == pygame.KEYUP:  # check for key releases
                if event.key == pygame.K_LEFT:  # left arrow turns left
                    pressed_left = False
                elif event.key == pygame.K_RIGHT:  # right arrow turns right
                    pressed_right = False
                elif event.key == pygame.K_UP:  # up arrow goes up
                    pressed_up = False
                elif event.key == pygame.K_DOWN:  # down arrow goes down
                    pressed_down = False
        win.fill((0, 0, 0))
        b.drawMap() # draws map of game
        b.taskBar(len(finished)) # updates task progress
        s.createMap() # create mini map
        s.showPlayers(c) # show players in mini map
        #s.showTraps(k[0].active_traps) # show traps in mini map
        s.showKillers(k) # show killers in mini map

        if len(k[0].active_traps) != 0: # draw active traps
            for i in k[0].active_traps:
                if i.active == True:
                    i.draw((i.x, i.y))
        # place all the task icons in map
        for task in tasks:
            task.placeTask()
        #print("wrong tasks", wrong_tasks)
        for task in wrong_tasks:
            task.placeTask()

        # check if players are within killer's distance
        ghostID = -1
        #print("is killer")
        if crewMate == False:
            for cm in c:
                killdistance = distance(k[0], cm)
                if killdistance < 100:
                    keys = pygame.key.get_pressed()
                    # if theyre within distance, killer can kill with spacebar
                    if keys[pygame.K_SPACE]:
                        ghostID = cm.id
                        cm.becomeGhost()
                        break

        if crewMate == True: # crewmates solve tasks if theyre within distance
            for task in tasks:
                region = distance(players[playerIndx], task)
                if region < 50 and players[playerIndx].alive == True:
                    task.active = True
                    task.loadPage()
                    task.displayTask()
                    curr_task_opened = task
                    task_opened = True

            for task in wrong_tasks:
                region = distance(players[playerIndx], task)
                if region < 50:
                    task.loadPage()
                    task.displayWrong()


        #print("wrong tasks", wrong_tasks)
        # print("pressed left", pressed_left)
        if isTaskChange == True:
            print("wrong tasks", len(wrong_tasks))
            wrong_tasksArr = []
            finishedArr = []
            tasksArr = []
            for task in wrong_tasks:
                wrong_tasksArr.append({
                    "pos": [task.x, task.y],
                    "category": task.category
                })
            for task in finished:
                finishedArr.append({
                    "pos": [task.x, task.y],
                    "category": task.category
                })
            for task in tasks:
                tasksArr.append({
                    "pos": [task.x, task.y],
                    "category": task.category
                })
            #print("send", wrong_tasksArr)
            sendUpdateTasks(
                {"finished": finishedArr, "wrong": wrong_tasksArr,  "tasks": tasksArr})

        # if((pygame.time.get_ticks()-start_ticks) % 10 == 0):
        # print("traps")
        isTrapped = False
        if(crewMate == True):
            isTrapped = players[playerIndx].trapped
        moveDirection = -1
        if pressed_left and ((not hasattr(players[playerIndx], 'alive')) or players[playerIndx].trapped == False):
            players[playerIndx].moveLeft()
            moveDirection = 0
        elif pressed_right and ((not hasattr(players[playerIndx], 'alive')) or players[playerIndx].trapped == False):
            players[playerIndx].moveRight()
            moveDirection = 1
        elif pressed_up and ((not hasattr(players[playerIndx], 'alive')) or players[playerIndx].trapped == False):
            players[playerIndx].moveUp()
            moveDirection = 2
        elif pressed_down and ((not hasattr(players[playerIndx], 'alive')) or players[playerIndx].trapped == False):
            players[playerIndx].moveDown()
            moveDirection = 3
        sendUpdatePlayer(players[playerIndx], {
                         "move": moveDirection, "trap": setTrap,  "ghost": ghostID, "isTrapped": isTrapped})
        traps = k[0].active_traps
        for trap in traps:
            trap.trapCrewmember(players)
        # render
        # print("render")
        for player in players:
            player.drawPlayer()
        #print("win check")
        if len(finished) >= 20 or (pygame.time.get_ticks()-start_ticks >= 1000*60*10):
            b.players_win()
            endGame(True)
            pygame.quit()
            return
        killerWin = True
        #print("lose check")
        for player in players:
            if hasattr(player, 'alive') and player.alive == True:
                killerWin = False
                break
        if killerWin == True:
            b.killer_win()
            endGame(False)
            pygame.quit()
            return
        pygame.display.update()
        #print("run", run)
    #print("run", run)
    pygame.quit()


# multiplayer code
# add start button
# x = input()
# if x == "start":
#     sio.emit("startGame", "dummy")
