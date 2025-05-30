from abc import ABC, abstractmethod
import pygame
import random
import os
import threading
from pygame.locals import *

# --- CONSTANTS ---
BACKGROUND_WIDTH  = 1200
BACKGROUND_HEIGHT = 800
FPS               = 80

# margins where no obstacles spawn
EDGE_MARGIN       = 100
PLAYABLE_MIN_X    = EDGE_MARGIN
PLAYABLE_MAX_X    = BACKGROUND_WIDTH - EDGE_MARGIN
MID_X             = BACKGROUND_WIDTH // 2

# colors
WHITE = (255, 255, 255)
GREEN = (  0, 255,   0)
GRAY  = (100, 100, 100)

# --- ASSET PATHS ---
game_folder   = os.path.dirname(__file__)
assets_folder = os.path.join(game_folder, "Assets")
car_folder    = os.path.join(assets_folder, "Car")
obj_folder    = os.path.join(assets_folder, "Object")
png_folder    = os.path.join(game_folder, "Bahan", "PNG")
grass_folder  = os.path.join(png_folder, "Tiles", "Grass")

# --- PYGAME INIT ---
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((BACKGROUND_WIDTH, BACKGROUND_HEIGHT))
pygame.display.set_caption("No Brake Car")
clock = pygame.time.Clock()

# --- UTILITY FUNCS ---
def play_sound(path):
    pygame.mixer.Channel(1).play(pygame.mixer.Sound(path))

def play_sound_threaded(path):
    threading.Thread(target=play_sound, args=(path,)).start()

def draw_text(txt, size, color, x, y):
    font = pygame.font.SysFont(None, size)
    surf = font.render(txt, True, color)
    rect = surf.get_rect(center=(x,y))
    screen.blit(surf, rect)

# --- BASE SPRITE ---
class GameObject(ABC, pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        self.image = image
        self.rect  = image.get_rect()
        self.hit   = False

    @abstractmethod
    def update(self): pass

# --- PLAYER ---
class Player(GameObject):
    def __init__(self, image):
        super().__init__(image)
        self.rect.center = (MID_X, BACKGROUND_HEIGHT//2)
        self.speed       = 3
        self.slippery    = False
        self.slide_dir   = 0
        self.slide_count = 0
        self.slide_dur   = 30

    def set_slippery(self, state):
        self.slippery = state

    def update(self):
        keys = pygame.key.get_pressed()
        if not self.slippery:
            if keys[K_RIGHT] and self.rect.right  < PLAYABLE_MAX_X:
                self.rect.x += self.speed
            if keys[K_LEFT]  and self.rect.left   > PLAYABLE_MIN_X:
                self.rect.x -= self.speed
            if keys[K_DOWN]  and self.rect.bottom < BACKGROUND_HEIGHT:
                self.rect.y += self.speed
            if keys[K_UP]    and self.rect.top    > 0:
                self.rect.y -= self.speed
        else:
            self.slide_count += 1
            if self.slide_count <= self.slide_dur:
                if self.slide_count % 10 == 0:
                    self.slide_dir = random.choice([-1,1])
                self.rect.x += self.speed * self.slide_dir
            else:
                self.slide_count = 0
                self.slippery    = False
            self.speed = 2 if self.slippery else 4

# --- OBSTACLES & ITEMS ---
class CarLeft(GameObject):
    def __init__(self, image):
        super().__init__(image)
        self.speed = random.randint(1,3)
        self.spawn()
    def spawn(self):
        self.rect.x = random.randint(PLAYABLE_MIN_X, MID_X - self.rect.width)
        self.rect.y = -self.rect.height
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > BACKGROUND_HEIGHT:
            self.kill()

class CarRight(GameObject):
    def __init__(self, image):
        super().__init__(image)
        self.speed = random.randint(1,3)
        self.spawn()
    def spawn(self):
        self.rect.x = random.randint(MID_X, PLAYABLE_MAX_X - self.rect.width)
        self.rect.y = BACKGROUND_HEIGHT + self.rect.height
    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()

class Oli(GameObject):
    def __init__(self, image):
        super().__init__(image)
        self.speed = 2
        self.spawn()
    def spawn(self):
        self.rect.x = random.randint(PLAYABLE_MIN_X, PLAYABLE_MAX_X - self.rect.width)
        self.rect.y = -self.rect.height
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > BACKGROUND_HEIGHT:
            self.kill()

class Bensin(GameObject):
    def __init__(self, image):
        super().__init__(image)
        self.speed = 2
        self.spawn()
    def spawn(self):
        self.rect.x = random.randint(PLAYABLE_MIN_X, PLAYABLE_MAX_X - self.rect.width)
        self.rect.y = -self.rect.height
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > BACKGROUND_HEIGHT:
            self.kill()


# --- ARROW MARKINGS ---
class PanahJalan(GameObject):
    def __init__(self, image, x_pos):
        super().__init__(image)
        self.speed = 2
        self.rect.x = x_pos
        self.rect.y = -self.rect.height
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > BACKGROUND_HEIGHT:
            self.kill()

# --- LOAD IMAGES ---
car_images    = [pygame.image.load(os.path.join(car_folder, f"car_{i}.png")).convert_alpha() for i in range(8)]
oil_img       = pygame.image.load(os.path.join(obj_folder, "oil.png")).convert_alpha()
bensin_img    = pygame.image.load(os.path.join(obj_folder, "last.png")).convert_alpha()
arrow_img     = pygame.transform.scale(
    pygame.image.load(os.path.join(obj_folder, "arrow_white.png")).convert_alpha(),
    (100,50)
)
rumput        = pygame.image.load(os.path.join(grass_folder, "land_grass01.png")).convert_alpha()
rumput_kiri   = pygame.transform.scale(rumput, (144, BACKGROUND_HEIGHT))
rumput_kanan  = rumput_kiri
tribune       = pygame.transform.rotate(
    pygame.image.load(os.path.join(obj_folder, "tribune.png")).convert_alpha(), 90
)
tribune_kiri  = pygame.transform.scale(tribune, (144, BACKGROUND_HEIGHT))
tribune_kanan = tribune_kiri

# --- COMPUTE ARROW POSITIONS ---
ARROW_COUNT = 10
arrow_width = arrow_img.get_width()
step = (PLAYABLE_MAX_X - PLAYABLE_MIN_X - arrow_width) / (ARROW_COUNT - 1)
arrow_positions = [int(PLAYABLE_MIN_X + i * step) for i in range(ARROW_COUNT)]

# --- SPRITE GROUPS ---
all_players = pygame.sprite.GroupSingle()
group_left  = pygame.sprite.Group()
group_right = pygame.sprite.Group()
group_oil   = pygame.sprite.Group()
group_bensin= pygame.sprite.Group()
group_pohon = pygame.sprite.Group()
group_arrow = pygame.sprite.Group()

# --- GAME STATE ---
SCENE_MENU     = 0
SCENE_PLAY     = 1
SCENE_GAMEOVER = 2
scene          = SCENE_MENU
current_car    = 0
player         = None
health         = 100
score          = 0

# --- FUNCTIONS ---
def draw_menu():
    screen.fill(GRAY)
    img  = car_images[current_car]
    rect = img.get_rect(center=(MID_X, BACKGROUND_HEIGHT//2 - 50))
    screen.blit(img, rect)
    draw_text("<- PILIH MOBIL MU->", 24, WHITE, MID_X, BACKGROUND_HEIGHT//2 + 10)
    draw_text("SPACE = Start",       28, WHITE, MID_X, BACKGROUND_HEIGHT//2 + 70)


def reset_game():
    global player, health, score
    # clear
    for grp in (group_left, group_right, group_oil, group_bensin, group_arrow): grp.empty()
    all_players.empty()
    # new player
    player = Player(car_images[current_car])
    all_players.add(player)
    health = 100; score = 0
    # initial obstacles
    group_left.add(CarLeft(random.choice(car_images)))
    group_right.add(CarRight(random.choice(car_images)))
    group_oil.add(Oli(oil_img)); group_bensin.add(Bensin(bensin_img))
    # initial arrows
    for x in arrow_positions:
        group_arrow.add(PanahJalan(arrow_img, x))

# --- SPAWN EVENT ---
SPAWN_EVENT = USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, 1500)

# background music
pygame.mixer.music.load("sound/backsound.mp3")
pygame.mixer.music.set_volume(0.4)
pygame.mixer.music.play(-1)

# --- MAIN LOOP ---
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == QUIT: running = False
        elif scene == SCENE_MENU and event.type == KEYDOWN:
            if event.key == K_LEFT: current_car = (current_car - 1) % len(car_images)
            elif event.key == K_RIGHT: current_car = (current_car + 1) % len(car_images)
            elif event.key == K_SPACE: reset_game(); scene = SCENE_PLAY
        elif scene == SCENE_PLAY and event.type == SPAWN_EVENT:
            group_left.add(CarLeft(random.choice(car_images)))
            group_right.add(CarRight(random.choice(car_images)))
            group_oil.add(Oli(oil_img)); group_bensin.add(Bensin(bensin_img))
            for x in arrow_positions: group_arrow.add(PanahJalan(arrow_img, x))
        elif scene == SCENE_GAMEOVER and event.type == KEYDOWN:
            if event.key == K_r: reset_game(); scene = SCENE_PLAY
            elif event.key == K_m: scene = SCENE_MENU
            elif event.key == K_ESCAPE: running = False

    # update
    if scene == SCENE_PLAY:
        all_players.update()
        group_left.update(); group_right.update(); group_oil.update(); group_bensin.update();group_arrow.update()
        # collisions
        if pygame.sprite.spritecollide(player, group_left, True) or pygame.sprite.spritecollide(player, group_right, True):
            play_sound_threaded("sound/Duar.mp3"); health = 0
        if pygame.sprite.spritecollide(player, group_oil, True):
            play_sound_threaded("sound/ngepot.mp3"); player.set_slippery(True); health = max(0, health -5)
        if pygame.sprite.spritecollide(player, group_bensin, True): health = min(100, health +5)
        score += 0.1
        if health <= 0: scene = SCENE_GAMEOVER

    # draw
    screen.fill(GRAY)
    screen.blit(tribune_kiri,  (-40, 0)); screen.blit(tribune_kanan, (BACKGROUND_WIDTH-120,0))
    screen.blit(rumput_kiri,   (-90,0)); screen.blit(rumput_kanan,  (BACKGROUND_WIDTH-60,0))
    if scene == SCENE_MENU: draw_menu()
    elif scene == SCENE_PLAY:
        group_left.draw(screen); group_right.draw(screen); group_oil.draw(screen); group_bensin.draw(screen); group_pohon.draw(screen); group_arrow.draw(screen); all_players.draw(screen)
        pygame.draw.rect(screen, GREEN, (10,10,health,20)); pygame.draw.rect(screen, WHITE, (10,10,100,20),2)
        draw_text(f"Score: {int(score)}", 30, WHITE, 100, 50)
    else:
        draw_text("GAME OVER",      50, WHITE, MID_X, BACKGROUND_HEIGHT//3)
        draw_text(f"Final Score: {int(score)}", 30, WHITE, MID_X, BACKGROUND_HEIGHT//2)
        draw_text("R = Restart",    24, WHITE, MID_X, BACKGROUND_HEIGHT//2 +60)
        draw_text("M = Menu",       24, WHITE, MID_X, BACKGROUND_HEIGHT//2 +90)
        draw_text("ESC = Exit",     24, WHITE, MID_X, BACKGROUND_HEIGHT//2 +120)
    pygame.display.flip()
pygame.quit()
