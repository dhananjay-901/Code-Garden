import pygame, math, random

pygame.init()

WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22)

BALL_R = 10
MIN_VEL = 0.03
BORDER = 30

WHITE=(255,255,255)
GREEN=(30,120,30)
BROWN=(100,50,20)
BLACK=(0,0,0)
GRAY=(200,200,200)

# --- GAME ---
class Game:
    def __init__(self):
        self.state="MENU"
        self.turn="PLAYER"
        self.score={"PLAYER":0,"AI":0}
        self.power=0
        self.dragging=False
        self.winner=None
        self.ai_level=None

game=Game()

# --- BALL ---
class Ball:
    def __init__(self,x,y,color,is_cue=False):
        self.pos=pygame.Vector2(x,y)
        self.vel=pygame.Vector2(0,0)
        self.color=color
        self.active=True
        self.is_cue=is_cue

    def move(self):
        if not self.active: return

        # limit max speed
        if self.vel.length()>10:
            self.vel.scale_to_length(10)

        self.pos += self.vel

        # ✅ HYBRID FRICTION MODEL
        speed = self.vel.length()

        if speed > 0:
            if speed > 4:
                friction = 0.985   # fast sliding
            elif speed > 1:
                friction = 0.975   # rolling
            else:
                friction = 0.94    # slow settling

            self.vel *= friction

            # slight table drag (adds realism)
            self.vel -= self.vel * 0.002

        # smooth stop
        if self.vel.length() < MIN_VEL:
            self.vel = pygame.Vector2(0,0)

        # walls
        if self.pos.x < BORDER+BALL_R:
            self.pos.x = BORDER+BALL_R
            self.vel.x *= -0.8
        if self.pos.x > WIDTH-BORDER-BALL_R:
            self.pos.x = WIDTH-BORDER-BALL_R
            self.vel.x *= -0.8
        if self.pos.y < BORDER+BALL_R:
            self.pos.y = BORDER+BALL_R
            self.vel.y *= -0.8
        if self.pos.y > HEIGHT-BORDER-BALL_R:
            self.pos.y = HEIGHT-BORDER-BALL_R
            self.vel.y *= -0.8

    def draw(self):
        if not self.active: return
        pygame.draw.circle(screen,(0,0,0),(int(self.pos.x+3), int(self.pos.y+3)),BALL_R)
        pygame.draw.circle(screen,self.color,(int(self.pos.x), int(self.pos.y)),BALL_R)

# --- COLLISION ---
def collide(b1, b2):
    if not b1.active or not b2.active: return

    delta = b2.pos - b1.pos
    dist = delta.length()

    if dist == 0:
        return

    if dist < BALL_R * 2:
        normal = delta.normalize()

        overlap = (BALL_R * 2 - dist) + 0.5
        b1.pos -= normal * (overlap / 2)
        b2.pos += normal * (overlap / 2)

        rel_vel = b1.vel - b2.vel
        vel_along = rel_vel.dot(normal)

        if vel_along > 0:
            return

        impulse = -1.05 * vel_along
        impulse_vec = normal * impulse

        b1.vel += impulse_vec
        b2.vel -= impulse_vec

# --- AIM ---
def draw_aim(cue):
    mouse = pygame.Vector2(pygame.mouse.get_pos())
    vec = cue.pos - mouse

    if vec.length() < 5:
        return

    direction = vec.normalize()

    pygame.draw.line(screen, WHITE, cue.pos, cue.pos + direction * 300, 2)

    ghost = cue.pos + direction * 60
    pygame.draw.circle(screen, GRAY, (int(ghost.x), int(ghost.y)), BALL_R, 1)

    pygame.draw.line(screen, BROWN,
        cue.pos - direction * 150,
        cue.pos - direction * 20, 8)

# --- POCKETS ---
pockets=[(BORDER,BORDER),(WIDTH//2,BORDER),(WIDTH-BORDER,BORDER),
         (BORDER,HEIGHT-BORDER),(WIDTH//2,HEIGHT-BORDER),(WIDTH-BORDER,HEIGHT-BORDER)]

def check_pockets(balls):
    potted=False
    for b in balls:
        if not b.active: continue
        for p in pockets:
            if b.pos.distance_to(p)<18:
                if b.is_cue:
                    b.pos = pygame.Vector2(200,250)
                    b.vel = pygame.Vector2(0,0)
                else:
                    b.active=False
                    game.score[game.turn]+=1
                    potted=True
    return potted

def check_game_over(balls):
    return all(not b.active or b.is_cue for b in balls)

# --- AI ---
def ai_shoot(cue, balls):
    targets=[b for b in balls if b.active and not b.is_cue]

    if game.ai_level=="EASY":
        target=random.choice(targets)
        error=0.4
        power=random.uniform(5,9)

    elif game.ai_level=="MEDIUM":
        target=random.choice(targets)
        error=0.2
        power=random.uniform(6,11)

    else:
        target=min(targets, key=lambda b: cue.pos.distance_to(b.pos))
        error=0.05
        power=random.uniform(8,13)

    direction=(target.pos-cue.pos).normalize()
    angle=math.atan2(direction.y,direction.x)+random.uniform(-error,error)

    cue.vel=pygame.Vector2(math.cos(angle),math.sin(angle))*power

# --- SETUP ---
def create_balls():
    balls=[]
    cue=Ball(200,250,WHITE,True)
    balls.append(cue)

    colors=[(255,0,0),(255,255,0),(0,0,255)]*4
    idx=0

    for r in range(4):
        for c in range(r+1):
            x=600+r*22
            y=250+(c-r/2)*22
            balls.append(Ball(x,y,colors[idx%len(colors)]))
            idx+=1

    return balls,cue

balls,cue=create_balls()

def balls_moving():
    return any(b.vel.length()>0 for b in balls if b.active)

# --- MENU ---
def draw_menu():
    screen.fill(GREEN)
    title = font.render("Select Difficulty", True, WHITE)
    screen.blit(title,(WIDTH//2-100,150))

    options=["EASY","MEDIUM","HARD"]
    rects=[]

    for i,opt in enumerate(options):
        r=pygame.Rect(WIDTH//2-60,220+i*40,120,30)
        pygame.draw.rect(screen,GRAY,r)
        txt=font.render(opt,True,BLACK)
        screen.blit(txt,(r.x+20,r.y+5))
        rects.append((opt,r))

    return rects

# --- LOOP ---
running=True

while running:
    clock.tick(60)

    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False

        if game.state=="MENU":
            buttons=draw_menu()
            if e.type==pygame.MOUSEBUTTONDOWN:
                for name,rect in buttons:
                    if rect.collidepoint(e.pos):
                        game.ai_level=name
                        game.state="PLAYER"

        elif game.state=="PLAYER":
            if e.type==pygame.MOUSEBUTTONDOWN:
                game.dragging=True

            if e.type==pygame.MOUSEBUTTONUP:
                vec=cue.pos-pygame.Vector2(pygame.mouse.get_pos())
                if vec.length()>0:
                    cue.vel=vec.normalize()*(game.power*0.15)
                    game.power=0
                    game.dragging=False
                    game.state="MOVING"

        elif game.state=="GAME_OVER":
            if e.type==pygame.MOUSEBUTTONDOWN:
                balls,cue=create_balls()
                game=Game()

    # --- LOGIC ---
    if game.state=="PLAYER":
        if game.dragging:
            game.power=min(game.power+0.8,100)

    elif game.state=="MOVING":
        for b in balls:
            b.move()

        for _ in range(4):
            for i in range(len(balls)):
                for j in range(i+1,len(balls)):
                    collide(balls[i],balls[j])

        potted=check_pockets(balls)

        if not balls_moving():
            if check_game_over(balls):
                game.state="GAME_OVER"
                game.winner = "PLAYER" if game.score["PLAYER"]>game.score["AI"] else "AI"
                continue

            if not potted:
                game.turn="AI" if game.turn=="PLAYER" else "PLAYER"

            game.state="AI" if game.turn=="AI" else "PLAYER"

    elif game.state=="AI":
        pygame.time.wait(400)
        ai_shoot(cue, balls)
        game.state="MOVING"

    # --- DRAW ---
    if game.state=="MENU":
        draw_menu()

    else:
        screen.fill(GREEN)
        pygame.draw.rect(screen,BROWN,(0,0,WIDTH,HEIGHT),BORDER)

        for p in pockets:
            pygame.draw.circle(screen,BLACK,p,18)

        for b in balls:
            b.draw()

        if game.state=="PLAYER":
            draw_aim(cue)
            pygame.draw.rect(screen,WHITE,(20,HEIGHT-20,game.power*2,10))

        if game.state=="GAME_OVER":
            text=font.render(f"{game.winner} WINS!",True,WHITE)
            screen.blit(text,(WIDTH//2-80,HEIGHT//2))

        ui=font.render(f"{game.turn} | {game.ai_level}",True,WHITE)
        screen.blit(ui,(10,10))

    pygame.display.flip()

pygame.quit()