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
DARK_BROWN = (60, 30, 10)

BALL_RADIUS = 10
POCKET_RADIUS = 18
FRICTION = 0.985
MAX_POWER = 20
MIN_VELOCITY = 0.05
BORDER_SIZE = 20  # Width of wooden border

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
        self.vel = pygame.math.Vector2(0, 0)
        self.color = color  # FIXED: Syntax error
        self.radius = BALL_RADIUS
        self.is_cue = is_cue
        self.active = True

    def move(self):
        if not self.active: return
        self.pos += self.vel
        self.vel *= FRICTION
        if self.vel.length() < MIN_VELOCITY:
            self.vel = pygame.math.Vector2(0, 0)
        
        # Wall Collisions - Keep balls inside the green area (inside brown border)
        inner_left = BORDER_SIZE + self.radius
        inner_right = WIDTH - BORDER_SIZE - self.radius
        inner_top = BORDER_SIZE + self.radius
        inner_bottom = HEIGHT - BORDER_SIZE - self.radius
        
        if self.pos.x < inner_left:
            self.pos.x = inner_left
            self.vel.x *= -1
        elif self.pos.x > inner_right:
            self.pos.x = inner_right
            self.vel.x *= -1
        
        if self.pos.y < inner_top:
            self.pos.y = inner_top
            self.vel.y *= -1
        elif self.pos.y > inner_bottom:
            self.pos.y = inner_bottom
            self.vel.y *= -1

    def draw(self, surface):
        if self.active:
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
            # Shine effect
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
                return ball  # Return the potted ball
    return None

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
    error = random.uniform(-0.1, 0.1)
    power = random.uniform(8, 14)
    vel_x = math.cos(angle + error) * power
    vel_y = math.sin(angle + error) * power
    cue_ball.vel = pygame.math.Vector2(vel_x, vel_y)

# --- Drawing Functions ---

def draw_cue_stick(surface, cue_ball, mouse_pos, is_visible):
    """Draw wooden cue stick and trajectory line"""
    if not is_visible or not cue_ball.active:
        return
    
    # Calculate direction from ball to mouse (pull back direction)
    mouse_vec = pygame.math.Vector2(mouse_pos)
    ball_vec = pygame.math.Vector2(cue_ball.pos)
    aim_vector = ball_vec - mouse_vec
    
    if aim_vector.length() < 5:  # Too close to aim
        return
    
    aim_direction = aim_vector.normalize()
    
    # Draw white trajectory line (direction ball will go)
    trajectory_start = cue_ball.pos
    trajectory_end = cue_ball.pos + aim_direction * 300
    pygame.draw.line(surface, WHITE, trajectory_start, trajectory_end, 2)
    
    # Draw cue stick (dark brown, on opposite side of aim)
    cue_start = cue_ball.pos - aim_direction * (BALL_RADIUS + 5)
    cue_end = cue_ball.pos - aim_direction * 150
    
    # Main cue stick (dark brown)
    pygame.draw.line(surface, DARK_BROWN, cue_start, cue_end, 8)
    # Cue tip (lighter brown)
    pygame.draw.line(surface, BROWN, cue_start, cue_start + aim_direction * 10, 8)

def main():
    running = True
    game_state = "PLAYER_AIM"
    current_turn = "PLAYER"
    
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
        
        # Draw Table with brown border
        pygame.draw.rect(screen, BROWN, (0, 0, WIDTH, HEIGHT), BORDER_SIZE)
        
        # Draw Pockets (inside the green area)
        pockets = [
            (BORDER_SIZE, BORDER_SIZE), 
            (WIDTH//2, BORDER_SIZE), 
            (WIDTH - BORDER_SIZE, BORDER_SIZE),
            (BORDER_SIZE, HEIGHT - BORDER_SIZE), 
            (WIDTH//2, HEIGHT - BORDER_SIZE), 
            (WIDTH - BORDER_SIZE, HEIGHT - BORDER_SIZE)
        ]
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
            
            # Check who potted a ball
            potted_ball = check_pockets(balls)
            
            if not check_balls_moving(balls):
                # FIXED: Keep turn if someone potted a ball
                if potted_ball is not None:
                    # Turn stays with current player (they potted a ball)
                    if current_turn == "PLAYER":
                        game_state = "PLAYER_AIM"
                    else:
                        game_state = "AI_WAIT"
                else:
                    # No ball potted, switch turns
                    if current_turn == "PLAYER":
                        current_turn = "AI"
                        game_state = "AI_WAIT"
                    else:
                        current_turn = "PLAYER"
                        game_state = "PLAYER_AIM"

        elif game_state == "AI_WAIT" and current_turn == "AI":
            pygame.time.wait(500)
            ai_shoot(cue_ball, balls)
            game_state = "MOVING"

        # Drawing - Cue Stick with Dark Brown Color and White Trajectory
        mouse_pos = pygame.mouse.get_pos()
        show_cue = (game_state == "PLAYER_AIM" and current_turn == "PLAYER")
        draw_cue_stick(screen, cue_ball, mouse_pos, show_cue)

        # Draw Balls
        for b in balls:
            b.draw(screen)

        # UI - Status Text
        if current_turn == "PLAYER":
            status_text = "Your Turn - Click & Drag backward to shoot!"
        else:
            status_text = "Computer Thinking..."
        
        text = font.render(status_text, True, WHITE)
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()