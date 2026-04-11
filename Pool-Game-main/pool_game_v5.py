import pygame
import math
import random

# --- CONFIG ---
WIDTH, HEIGHT = 900, 500
FPS = 60

BALL_RADIUS = 10
POCKET_RADIUS = 18
FRICTION = 0.99
MIN_VEL = 0.05
BORDER = 30

WHITE = (255,255,255)
GREEN = (30,120,30)
BROWN = (100,50,20)
BLACK = (0,0,0)
GRAY = (200,200,200)

# --- INIT ---
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Immersive Pool")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22)

# --- OPTIONAL SOUNDS ---
def load_sound(name):
    try:
        return pygame.mixer.Sound(name)
    except:
        return None

hit_sound = load_sound("hit.wav")
pocket_sound = load_sound("pocket.wav")
shoot_sound = load_sound("shoot.wav")

# --- GAME CLASS ---
class Game:
    def __init__(self):
        self.state = "MENU"
        self.turn = "PLAYER"
        self.score = {"PLAYER":0, "AI":0}
        self.power = 0
        self.dragging = False
        self.winner = None

game = Game()

# --- BALL ---
class Ball:
    def __init__(self,x,y,color,is_cue=False):
        self.pos = pygame.Vector2(x,y)
        self.vel = pygame.Vector2(0,0)
        self.color = color
        self.active = True
        self.is_cue = is_cue

    def move(self):
        if not self.active: return

        self.pos += self.vel
        self.vel *= FRICTION

        if self.vel.length() < MIN_VEL:
            self.vel = pygame.Vector2(0,0)

        # walls
        left = BORDER + BALL_RADIUS
        right = WIDTH - BORDER - BALL_RADIUS
        top = BORDER + BALL_RADIUS
        bottom = HEIGHT - BORDER - BALL_RADIUS

        if self.pos.x < left or self.pos.x > right:
            self.vel.x *= -0.9
            self.pos.x = max(left, min(right, self.pos.x))

        if self.pos.y < top or self.pos.y > bottom:
            self.vel.y *= -0.9
            self.pos.y = max(top, min(bottom, self.pos.y))

    def draw(self, surf):
        if not self.active: return

        # shadow
        pygame.draw.circle(surf, (0,0,0), (int(self.pos.x+3), int(self.pos.y+3)), BALL_RADIUS)

        # ball
        pygame.draw.circle(surf, self.color, (int(self.pos.x), int(self.pos.y)), BALL_RADIUS)

        # shine
        pygame.draw.circle(surf, WHITE, (int(self.pos.x-3), int(self.pos.y-3)), 3)

# --- COLLISION ---
def collide(b1,b2):
    if not b1.active or not b2.active: return

    dist = b1.pos.distance_to(b2.pos)
    if dist < BALL_RADIUS*2:

        normal = (b2.pos - b1.pos).normalize()
        rel_vel = b1.vel - b2.vel

        vel_along = rel_vel.dot(normal)
        if vel_along > 0: return

        impulse = -1.8 * vel_along
        impulse_vec = normal * impulse

        b1.vel += impulse_vec
        b2.vel -= impulse_vec

        if hit_sound:
            hit_sound.play()

# --- POCKETS ---
pockets = [
    (BORDER,BORDER),(WIDTH//2,BORDER),(WIDTH-BORDER,BORDER),
    (BORDER,HEIGHT-BORDER),(WIDTH//2,HEIGHT-BORDER),(WIDTH-BORDER,HEIGHT-BORDER)
]

def check_pockets(balls):
    for b in balls:
        if not b.active: continue

        for p in pockets:
            if b.pos.distance_to(p) < POCKET_RADIUS:
                if pocket_sound: pocket_sound.play()

                if b.is_cue:
                    b.pos = pygame.Vector2(200,250)
                    b.vel = pygame.Vector2(0,0)
                else:
                    b.active = False
                    game.score[game.turn] += 1
                return True
    return False

# --- AI ---
def ai_shoot(cue, balls):
    targets = [b for b in balls if b.active and not b.is_cue]
    if not targets: return

    t = random.choice(targets)
    direction = (t.pos - cue.pos).normalize()

    error = random.uniform(-0.2,0.2)
    power = random.uniform(8,15)

    angle = math.atan2(direction.y, direction.x) + error

    cue.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * power

# --- AIM SYSTEM ---
def draw_aim(cue):
    mouse = pygame.Vector2(pygame.mouse.get_pos())
    vec = cue.pos - mouse

    if vec.length() < 5: return

    dir = vec.normalize()

    # line
    pygame.draw.line(screen, WHITE, cue.pos, cue.pos + dir*300,2)

    # ghost ball
    ghost = cue.pos + dir*60
    pygame.draw.circle(screen, GRAY, (int(ghost.x),int(ghost.y)), BALL_RADIUS,1)

    # cue stick
    pygame.draw.line(screen, BROWN,
        cue.pos - dir*150,
        cue.pos - dir*20, 8)

# --- SETUP ---
def create_balls():
    balls = []
    cue = Ball(200,250,WHITE,True)
    balls.append(cue)

    colors = [(255,0,0),(255,255,0),(0,0,255)]*4
    idx=0

    for r in range(4):
        for c in range(r+1):
            x = 600 + r*22
            y = 250 + (c-r/2)*22
            balls.append(Ball(x,y,colors[idx%len(colors)]))
            idx+=1

    return balls, cue

balls, cue = create_balls()

# --- HELPERS ---
def balls_moving():
    return any(b.vel.length()>0 for b in balls if b.active)

# --- DRAW TABLE ---
def draw_table():
    screen.fill(GREEN)
    pygame.draw.rect(screen, BROWN, (0,0,WIDTH,HEIGHT), BORDER)

    for p in pockets:
        pygame.draw.circle(screen, BLACK, p, POCKET_RADIUS)

# --- MENU ---
def draw_menu():
    screen.fill(GREEN)
    t = font.render("POOL GAME", True, WHITE)
    s = font.render("Click to Start", True, WHITE)
    screen.blit(t,(WIDTH//2-80, HEIGHT//2-40))
    screen.blit(s,(WIDTH//2-100, HEIGHT//2))

# --- MAIN LOOP ---
running = True

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game.state == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.state = "PLAYER"

        elif game.state == "PLAYER":
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.dragging = True

            if event.type == pygame.MOUSEBUTTONUP and game.dragging:
                vec = cue.pos - pygame.Vector2(pygame.mouse.get_pos())
                if vec.length() > 0:
                    cue.vel = vec.normalize() * (game.power * 0.25)

                    if shoot_sound: shoot_sound.play()

                    game.state = "MOVING"
                    game.dragging = False
                    game.power = 0

    # --- LOGIC ---
    if game.state == "PLAYER":
        if game.dragging:
            game.power = min(game.power + 0.8, 100)

    elif game.state == "MOVING":
        for b in balls:
            b.move()

        for i in range(len(balls)):
            for j in range(i+1,len(balls)):
                collide(balls[i],balls[j])

        potted = check_pockets(balls)

        if not balls_moving():
            if not potted:
                game.turn = "AI" if game.turn=="PLAYER" else "PLAYER"

            if game.turn == "AI":
                game.state = "AI"
            else:
                game.state = "PLAYER"

    elif game.state == "AI":
        pygame.time.wait(500)
        ai_shoot(cue, balls)
        game.state = "MOVING"

    # --- DRAW ---
    if game.state == "MENU":
        draw_menu()

    else:
        draw_table()

        for b in balls:
            b.draw(screen)

        if game.state == "PLAYER":
            draw_aim(cue)

            # power bar
            pygame.draw.rect(screen, WHITE, (20, HEIGHT-20, game.power*2, 10))

        # UI
        ui = font.render(f"Turn: {game.turn} | Player: {game.score['PLAYER']} AI: {game.score['AI']}", True, WHITE)
        screen.blit(ui,(10,10))

    pygame.display.flip()

pygame.quit()