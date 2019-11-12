import time
from pygame.locals import *
import pygame, sys, os
import threading
import random
import argparse
from collections import Counter

# ----------- ARGS

parser = argparse.ArgumentParser(description='N-Puzzle game')
parser.add_argument("--width", default=1080, help="Width of the window in pixels")
parser.add_argument("--height", default=1080, help="Height of the window in pixels")
parser.add_argument("--n", default=50, help="N size of the puzzle (N*N cells)")
parser.add_argument("--agents", default=20, help="Number of agents have to be < N*N")
parser.add_argument("--speed", default=1, help="Speed of the agents the less the faster")
parser.add_argument("--objects", default=200, help="Objects to sort")
parser.add_argument("--t", default=10, help="Size of the memory")
parser.add_argument("--kp", default=0.1, help="Constant Kp prise")
parser.add_argument("--kd", default=0.3, help="Constant Kd depot")
parser.add_argument("--i", default=1, help="I possible move between actions")
parser.add_argument("--error", default=0, help="Error rate in recognition")
parser.add_argument("--levy", default=0, help="Levy flight probability")
parser.add_argument("--view", default=0, help="use vision instead of memory")

# ---------- INIT

args = parser.parse_args()
windowWidth = int(args.width)
windowHeight = int(args.height)
n = int(args.n)
agents_number = int(args.agents)
objects_number = int(args.objects)
speed = args.speed
t = int(args.t)
kp = float(args.kp)
kd = float(args.kd)
i_move = int(args.i)
error_rate = float(args.error)
levy = float(args.levy)
view = int(args.view)

objects_letter = ['A', 'B']

message_box = {}

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255)

id = 1
agents = []

sliderMax = 1
sliderMin = 0.000000001
sliderMaxT = 100
sliderMinT = 1
sliderMaxI = 30
sliderMinI = 1
sliderMaxError = 1
sliderMinError = 0
sliderMaxLevy = 1
sliderMinLevy = 0
bestScore = 0

pygame.init()
screen = pygame.display.set_mode((windowWidth + 300, windowHeight), 0, 32)
pygame.display.set_caption('Interactions Multi-Agents')

directions = [[1, 0], [0, 1], [-1, 0], [0, -1]]
LEFT = 0
UP = 1
RIGHT = 2
DOWN = 3


class Board:
    def __init__(self, nsize):
        self.n = nsize
        self.agents = []
        self.occupiedCase = [[0 for j in range(self.n)] for i in range(self.n)]
        self.objectOccupiedCase = [["" for j in range(self.n)] for i in range(self.n)]

    def add_object(self, x, y, type):
        self.objectOccupiedCase[y][x] = type

    def can_add_object_at(self, x, y):
        return self.objectOccupiedCase[y][x] == ""

    def get_object_at(self, x, y):
        return self.objectOccupiedCase[y][x]

    def add_agent(self, agent):
        self.occupiedCase[a.y][a.x] = a.id
        self.agents.append(agent)

    def carry_object(self, x, y):
        object = self.objectOccupiedCase[y][x]
        self.objectOccupiedCase[y][x] = ""
        return object

    def uncarry_object(self, x, y, object):
        if self.objectOccupiedCase[y][x] == "":
            self.objectOccupiedCase[y][x] = object
            return ""
        return object

    def move(self, agent, tx, ty):
        if self.occupiedCase[ty][tx] > 0:
            return False
        self.occupiedCase[ty][tx] = agent.id
        self.occupiedCase[agent.y][agent.x] = 0
        agent.set_pos(tx, ty)
        return True

    def agent_at(self, x, y):
        return self.occupiedCase[y][x]


class Agent(threading.Thread):
    def __init__(self, board, id, x, y):
        threading.Thread.__init__(self)
        self.board = board
        self.x = x
        self.y = y
        self.id = id
        self.memory = []
        self.carry = ""

    def random_move(self):
        if random.uniform(0, 1) < levy:
            ite = random.randint(10, 25)
        else:
            ite = random.randint(1, i_move)
        tx, ty = directions[random.randint(0, len(directions) - 1)]
        return self.try_a_move(self.x + tx * ite, self.y + ty * ite)

    def try_a_move(self, tx, ty):
        if tx < 0 or tx > board.n - 1 or ty < 0 or ty > board.n - 1:
            return "error"
        result = self.board.move(self, tx, ty)
        return result

    def set_pos(self, tx, ty):
        type = self.board.get_object_at(self.x, self.y)
        self.x = tx
        self.y = ty
        if type == "":
            type = "0"
        elif random.uniform(0, 1) < error_rate:
            # choose a random element to see instead of the real one, can be the real one
            type = random.choice(objects_letter)
        self.memory.append(type)

        if len(self.memory) > t:
            self.memory = self.memory[-t:]

    def run(self):
        while True:
            if speed > 0:
                time.sleep(speed)

            type = self.board.get_object_at(self.x, self.y)

            if view == 1:
                current_view = []
                for tx in range(self.x - 3, self.x + 3):
                    for ty in range(self.y - 3, self.y + 3):
                        if n > tx >= 0 and n > ty >= 0:
                            current_view.append(self.board.get_object_at(tx, ty))
                self.memory = current_view
            c = Counter(self.memory)
            f = 0

            if len(self.memory) > 0:
                f = c[type] / len(self.memory)
                if self.carry != "":
                    f = c[self.carry] / len(self.memory)

            r = random.uniform(0, 1)
            # print("Carry :", self.carry, 'f:', f, 'type:', type)
            if len(type) == 0 and self.carry != "" and f > 0:
                p_depot = (f / (kd + f)) * (f / (kd + f))
                # print("p_depot:", p_depot, " r:",r)
                if r < p_depot:
                    self.carry = board.uncarry_object(self.x, self.y, self.carry)
                    continue

            if f > 0 and len(type) != 0 and self.carry == "":
                p_prise = (kp / (kp + f)) * (kp / (kp + f))
                if r < p_prise:
                    # print("Carry")
                    self.carry = board.carry_object(self.x, self.y)
                    continue

            self.random_move()


board = Board(n)

# static initialisations of agents and objectives
# agents = [Agent(board, 1, 0, 0, 9, 0), Agent(board, 2, 9, 0, 1, 0)]

# random initialisations of agents and objectives

for i in range(agents_number):
    while True:
        x = random.randint(0, board.n - 1)
        y = random.randint(0, board.n - 1)
        if board.occupiedCase[y][x] == 0:
            break
    a = Agent(board, id, x, y)
    agents.append(a)
    board.add_agent(a)
    id += 1

basicFont = pygame.font.SysFont(None, 32)

objects_text = {}
for letter in objects_letter:
    objects_text[letter] = basicFont.render(letter, True, BLACK)

i = 0
while i < objects_number:
    x = random.randint(0, board.n - 1)
    y = random.randint(0, board.n - 1)
    type = objects_letter[random.randint(0, len(objects_letter) - 1)]
    if board.can_add_object_at(x, y):
        board.add_object(x, y, type)
        i += 1

cellWidth = windowWidth / board.n
cellHeight = windowHeight / board.n

for a in agents:
    a.start()

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
    screen.fill(WHITE)
    score = 0
    for i in range(board.n):
        for j in range(board.n):
            color = WHITE
            idOfCurrentAgent = board.occupiedCase[j][i]
            type = board.get_object_at(i, j)

            if type == 'A':
                color = GREEN
            elif type == 'B':
                color = RED
            if idOfCurrentAgent > 0:
                color = BLUE

            pygame.draw.rect(screen, BLACK, (i * cellWidth, j * cellHeight, cellWidth, cellHeight))
            pygame.draw.rect(screen, color, (i * cellWidth + 3, j * cellHeight + 3, cellWidth - 6, cellHeight - 6))

            if type != "":
                textRect = objects_text[type].get_rect()
                textRect.centerx = i * cellWidth + cellWidth / 2
                textRect.centery = j * cellHeight + cellHeight / 2
                screen.blit(objects_text[type], textRect)

    textSlider = basicFont.render("Speed : " + str(speed)[:5], True, BLACK)
    area = textSlider.get_rect()
    area.centerx = windowWidth + 150
    area.centery = 30
    screen.blit(textSlider, area)

    slider = pygame.draw.rect(screen, BLACK, (windowWidth + 30, 60, 240, 20))
    pygame.draw.rect(screen, BLACK, (windowWidth + 30 + 240 * ((speed + sliderMin) / sliderMax) - 15, 50, 30, 40))

    textSlider = basicFont.render("t : " + str(t), True, BLACK)
    area = textSlider.get_rect()
    area.centerx = windowWidth + 150
    area.centery = 120
    screen.blit(textSlider, area)

    slider_t = pygame.draw.rect(screen, BLACK, (windowWidth + 30, 150, 240, 20))
    pygame.draw.rect(screen, BLACK, (windowWidth + 30 + 240 * ((t + sliderMinT) / sliderMaxT) - 15, 140, 30, 40))

    textSlider = basicFont.render("i : " + str(i_move), True, BLACK)
    area = textSlider.get_rect()
    area.centerx = windowWidth + 150
    area.centery = 210
    screen.blit(textSlider, area)

    slider_i = pygame.draw.rect(screen, BLACK, (windowWidth + 30, 240, 240, 20))
    pygame.draw.rect(screen, BLACK, (windowWidth + 30 + 240 * ((i_move + sliderMinI) / sliderMaxI) - 15, 230, 30, 40))

    textSlider = basicFont.render("error percentage : " + str(error_rate), True, BLACK)
    area = textSlider.get_rect()
    area.centerx = windowWidth + 150
    area.centery = 300
    screen.blit(textSlider, area)

    slider_error = pygame.draw.rect(screen, BLACK, (windowWidth + 30, 330, 240, 20))
    pygame.draw.rect(screen, BLACK,
                     (windowWidth + 30 + 240 * ((error_rate + sliderMinError) / sliderMaxError) - 15, 320, 30, 40))

    textSlider = basicFont.render("levy probability : " + str(levy), True, BLACK)
    area = textSlider.get_rect()
    area.centerx = windowWidth + 150
    area.centery = 390
    screen.blit(textSlider, area)

    slider_levy = pygame.draw.rect(screen, BLACK, (windowWidth + 30, 420, 240, 20))
    pygame.draw.rect(screen, BLACK,
                     (windowWidth + 30 + 240 * ((levy + sliderMinLevy) / sliderMaxLevy) - 15, 410, 30, 40))

    pygame.display.update()
    pygame.event.get()
    if pygame.mouse.get_pressed()[0]:
        pos = pygame.mouse.get_pos()
        if pos[0] > windowWidth:
            if pos[1] < 100:
                speed = ((max(windowWidth + 30, pos[0]) - (windowWidth + 30)) / 240 + sliderMin) * sliderMax
            elif pos[1] < 200:
                t = int(((max(windowWidth + 30, pos[0]) - (windowWidth + 30) + sliderMinT) / 240) * sliderMaxT)
            elif pos[1] < 300:
                i_move = max(1, int(
                    ((max(windowWidth + 30, pos[0]) - (windowWidth + 30) + sliderMinI) / 240) * sliderMaxI))
            elif pos[1] < 400:
                error_rate = (((max(windowWidth + 30, pos[0]) - (
                            windowWidth + 30) + sliderMinError) / 240) * sliderMaxError)
            elif pos[1] < 500:
                levy = (((max(windowWidth + 30, pos[0]) - (
                        windowWidth + 30) + sliderMinLevy) / 240) * sliderMaxLevy)
    pygame.time.delay(100)
