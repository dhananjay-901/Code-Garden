import pygame
import math
import random

# --- Constants ---
WIDTH, HEIGHT = 800, 400
FPS = 60
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 215, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
BROWN = (139, 69, 19)

BALL_RADIUS = 10
POCKET_RADIUS = 18
FRICTION = 0.985
MAX_POWER = 20
MIN_VELOCITY = 0.05

# --- Setup Pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Pool: You vs AI")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)

# --- Vector Math Helper ---
def distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

# --- Classes ---

class Ball:
    def __init__(self, x, y, color, is_cue=False):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2()
        self.color = color
        self.radius = BALL_RADIUS
        self.is_cue = is_cue
        self.active = True

    def move(self):
        if not self.active: return
        self.pos += self.vel
        self.vel *= FRICTION
        if self.vel.length() < MIN_VELOCITY:
            self.vel = pygame.math.Vector2(0, 0)
        
        # Wall Collisions
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.vel.x *= -1
        elif self.pos.x + self.radius > WIDTH:
            self.pos.x = WIDTH - self.radius
            self.vel.x *= -1
        
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.vel.y *= -1
        elif self.pos.y + self.radius > HEIGHT:
            self.pos.y = HEIGHT - self.radius
            self.vel.y *= -1

    def draw(self, surface):
        if self.active:
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
            pygame.draw.circle(surface, (255,255,255), (int(self.pos.x - 3), int(self.pos.y - 3)), 3)

# --- Game Logic Functions ---

def resolve_collision(b1, b2):
    if not b1.active or not b2.active: return
    dist = b1.pos.distance_to(b2.pos)
    if dist < b1.radius + b2.radius:
        overlap = (b1.radius + b2.radius - dist) / 2
        direction = (b2.pos - b1.pos).normalize()
        b1.pos -= direction * overlap
        b2.pos += direction * overlap

        normal = b2.pos - b1.pos
        normal = normal.normalize()
        tangent = pygame.math.Vector2(-normal.y, normal.x)

        dpTan1 = b1.vel.dot(tangent)
        dpTan2 = b2.vel.dot(tangent)
        dpNorm1 = b1.vel.dot(normal)
        dpNorm2 = b2.vel.dot(normal)

        m1 = (dpNorm1 * (1 - 1) + 2 * 1 * dpNorm2) / (1 + 1)
        m2 = (dpNorm2 * (1 - 1) + 2 * 1 * dpNorm1) / (1 + 1)

        b1.vel = tangent * dpTan1 + normal * m2
        b2.vel = tangent * dpTan2 + normal * m1

def check_pockets(balls):
    pockets = [
        (0, 0), (WIDTH//2, 0), (WIDTH, 0),
        (0, HEIGHT), (WIDTH//2, HEIGHT), (WIDTH, HEIGHT)
    ]
    
    for ball in balls:
        if not ball.active: continue
        for px, py in pockets:
            if distance(ball.pos, pygame.math.Vector2(px, py)) < POCKET_RADIUS:
                ball.active = False
                ball.vel = pygame.math.Vector2(0, 0)
                if ball.is_cue:
                    ball.active = True
                    ball.pos = pygame.math.Vector2(200, 200)
                    ball.vel = pygame.math.Vector2(0,0)

def check_balls_moving(balls):
    for ball in balls:
        if ball.active and ball.vel.length() > 0:
            return True
    return False

def ai_shoot(cue_ball, object_balls):
    if not cue_ball.active: return
    targets = [b for b in object_balls if b.active]
    if not targets: return
    target = random.choice(targets)
    diff = target.pos - cue_ball.pos
    angle = math.atan2(diff.y, diff.x)
    error = random.uniform(-0.1, 0.1)  # Increased error slightly
    power = random.uniform(8, 14)
    vel_x = math.cos(angle + error) * power
    vel_y = math.sin(angle + error) * power
    cue_ball.vel = pygame.math.Vector2(vel_x, vel_y)

# --- Main Game Loop ---

def main():
    running = True
    game_state = "PLAYER_AIM"  # Options: PLAYER_AIM, MOVING, AI_WAIT
    current_turn = "PLAYER"   # Track whose turn it is: PLAYER or AI
    
    # Create Balls
    balls = []
    cue_ball = Ball(200, 200, WHITE, is_cue=True)
    balls.append(cue_ball)

    # Rack of balls
    start_x = 500
    start_y = 200
    rows = 4
    colors = [RED, YELLOW, BLUE, RED, YELLOW, BLACK, RED, YELLOW, BLUE, RED]
    
    idx = 0
    for r in range(rows):
        for c in range(r + 1):
            if idx < len(colors):
                bx = start_x + r * (BALL_RADIUS * 2 + 2)
                by = start_y - (r * BALL_RADIUS) + (c * BALL_RADIUS * 2)
                balls.append(Ball(bx, by, colors[idx]))
                idx += 1

    drag_start = None
    
    while running:
        screen.fill(GREEN)
        
        # Draw Table
        pygame.draw.rect(screen, BROWN, (0,0,WIDTH, HEIGHT), 20)
        pockets = [(0,0), (WIDTH//2,0), (WIDTH,0), (0,HEIGHT), (WIDTH//2,HEIGHT), (WIDTH,HEIGHT)]
        for p in pockets:
            pygame.draw.circle(screen, BLACK, p, POCKET_RADIUS)

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if game_state == "PLAYER_AIM" and current_turn == "PLAYER":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        drag_start = pygame.mouse.get_pos()
                
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and drag_start:
                        mouse_pos = pygame.mouse.get_pos()
                        pull_vector = pygame.math.Vector2(cue_ball.pos) - pygame.math.Vector2(mouse_pos)
                        power = pull_vector.length()
                        power = min(power, 150) / 7.5
                        
                        if power > 1:
                            direction = pull_vector.normalize()
                            cue_ball.vel = direction * power
                            game_state = "MOVING"
                            drag_start = None

        # Logic Updates
        if game_state == "MOVING":
            for b in balls: 
                b.move()
            
            for i in range(len(balls)):
                for j in range(i + 1, len(balls)):
                    resolve_collision(balls[i], balls[j])
            
            check_pockets(balls)
            
            if not check_balls_moving(balls):
                # FIXED: Check whose turn it is to decide next turn
                if current_turn == "PLAYER":
                    current_turn = "AI"
                    game_state = "AI_WAIT"
                else:
                    current_turn = "PLAYER"
                    game_state = "PLAYER_AIM"

        elif game_state == "AI_WAIT" and current_turn == "AI":
            # Add small delay before AI shoots
            pygame.time.wait(500)  # Wait 500ms
            ai_shoot(cue_ball, balls)
            game_state = "MOVING"

        # Drawing - Cue Stick & Aim Line
        if game_state == "PLAYER_AIM" and current_turn == "PLAYER":
            mouse_pos = pygame.mouse.get_pos()
            aim_vector = pygame.math.Vector2(cue_ball.pos) - pygame.math.Vector2(mouse_pos)
            
            if aim_vector.length() > 0:
                # Draw cue stick (pulled back)
                pygame.draw.line(screen, BROWN, cue_ball.pos, mouse_pos, 6)
                
                # Draw aim trajectory
                aim_norm = aim_vector.normalize() * 200
                start_pred = cue_ball.pos
                end_pred = cue_ball.pos + aim_norm
                pygame.draw.line(screen, (255, 255, 255, 100), start_pred, end_pred, 2)

        # Draw Balls
        for b in balls:
            b.draw(screen)

        # UI
        if current_turn == "PLAYER":
            status_text = "Your Turn - Click & Drag to Shoot!"
        else:
            status_text = "Computer Thinking..."
        
        text = font.render(status_text, True, WHITE)
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()