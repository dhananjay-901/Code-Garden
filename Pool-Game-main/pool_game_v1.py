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
FRICTION = 0.985  # Deceleration factor
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
        self.vel = pygame.math.Vector2(0, 0)
        self.color = color
        self.radius = BALL_RADIUS
        self.is_cue = is_cue
        self.active = True # False if in pocket

    def move(self):
        if not self.active: return

        # Apply velocity
        self.pos += self.vel

        # Apply Friction
        self.vel *= FRICTION

        # Stop completely if slow enough
        if self.vel.length() < MIN_VELOCITY:
            self.vel = pygame.math.Vector2(0, 0)

        # Wall Collisions (Bounce)
        # Left/Right
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.vel.x *= -1
        elif self.pos.x + self.radius > WIDTH:
            self.pos.x = WIDTH - self.radius
            self.vel.x *= -1
        
        # Top/Bottom
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.vel.y *= -1
        elif self.pos.y + self.radius > HEIGHT:
            self.pos.y = HEIGHT - self.radius
            self.vel.y *= -1

    def draw(self, surface):
        if self.active:
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
            # Shine effect
            pygame.draw.circle(surface, (255,255,255), (int(self.pos.x - 3), int(self.pos.y - 3)), 3)

# --- Game Logic Functions ---

def resolve_collision(b1, b2):
    """Handles elastic collision between two balls"""
    if not b1.active or not b2.active: return

    dist = b1.pos.distance_to(b2.pos)
    if dist < b1.radius + b2.radius:
        # 1. Resolve Overlap (prevent sticking)
        overlap = (b1.radius + b2.radius - dist) / 2
        direction = (b2.pos - b1.pos).normalize()
        b1.pos -= direction * overlap
        b2.pos += direction * overlap

        # 2. Resolve Velocity (Elastic Collision)
        normal = b2.pos - b1.pos
        normal = normal.normalize()
        
        # Tangent vector
        tangent = pygame.math.Vector2(-normal.y, normal.x)

        # Project velocities onto normal and tangent
        dpTan1 = b1.vel.dot(tangent)
        dpTan2 = b2.vel.dot(tangent)
        
        dpNorm1 = b1.vel.dot(normal)
        dpNorm2 = b2.vel.dot(normal)

        # Conservation of momentum (masses are equal)
        # In 1D elastic collision, velocities are swapped
        m1 = (dpNorm1 * (1 - 1) + 2 * 1 * dpNorm2) / (1 + 1)
        m2 = (dpNorm2 * (1 - 1) + 2 * 1 * dpNorm1) / (1 + 1)

        # Update velocities
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
                # If cue ball, respawn
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
    """Simple AI: Finds closest ball and shoots at it"""
    if not cue_ball.active: return
    
    # Find valid target
    targets = [b for b in object_balls if b.active]
    if not targets: return # Game over logic could go here

    # Pick random target (or closest)
    target = random.choice(targets)
    
    # Calculate angle
    diff = target.pos - cue_ball.pos
    angle = math.atan2(diff.y, diff.x)
    
    # Add slight inaccuracy to make it beatable
    error = random.uniform(-0.05, 0.05)
    power = random.uniform(10, 15)
    
    vel_x = math.cos(angle + error) * power
    vel_y = math.sin(angle + error) * power
    
    cue_ball.vel = pygame.math.Vector2(vel_x, vel_y)

# --- Main Game Loop ---

def main():
    running = True
    game_state = "PLAYER_AIM" # PLAYER_AIM, MOVING, AI_AIM
    
    # Create Balls
    balls = []
    cue_ball = Ball(200, 200, WHITE, is_cue=True)
    balls.append(cue_ball)

    # Rack of balls (Triangle formation)
    start_x = 500
    start_y = 200
    rows = 4
    colors = [RED, YELLOW, BLUE, RED, YELLOW, BLACK, RED, YELLOW, BLUE, RED] # Simplified colors
    
    idx = 0
    for r in range(rows):
        for c in range(r + 1):
            if idx < len(colors):
                bx = start_x + r * (BALL_RADIUS * 2 + 2)
                by = start_y - (r * BALL_RADIUS) + (c * BALL_RADIUS * 2)
                balls.append(Ball(bx, by, colors[idx]))
                idx += 1

    # Mouse Interaction Variables
    drag_start = None
    drag_current = None
    
    turn_timer = 0

    while running:
        screen.fill(GREEN)
        
        # Draw Table Borders
        pygame.draw.rect(screen, BROWN, (0,0,WIDTH, HEIGHT), 20)
        
        # Draw Pockets
        pockets = [(0,0), (WIDTH//2,0), (WIDTH,0), (0,HEIGHT), (WIDTH//2,HEIGHT), (WIDTH,HEIGHT)]
        for p in pockets:
            pygame.draw.circle(screen, BLACK, p, POCKET_RADIUS)

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Player Input
            if game_state == "PLAYER_AIM":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left click start drag
                        drag_start = pygame.mouse.get_pos()
                        drag_current = pygame.mouse.get_pos()
                
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and drag_start:
                        # Calculate power vector
                        mouse_pos = pygame.mouse.get_pos()
                        # Vector from ball to mouse
                        pull_vector = pygame.math.Vector2(cue_ball.pos) - pygame.math.Vector2(mouse_pos)
                        
                        # Cap power
                        power = pull_vector.length()
                        power = min(power, 150) / 7.5 # Scale down to velocity
                        
                        if power > 1:
                            direction = pull_vector.normalize()
                            cue_ball.vel = direction * power
                            game_state = "MOVING"

        # Logic Updates
        if game_state == "MOVING":
            # Physics Steps
            for b in balls: b.move()
            
            # Collisions
            for i in range(len(balls)):
                for j in range(i + 1, len(balls)):
                    resolve_collision(balls[i], balls[j])
            
            check_pockets(balls)
            
            if not check_balls_moving(balls):
                # Switch to AI
                game_state = "AI_WAIT"

        elif game_state == "AI_WAIT":
            turn_timer += 1
            if turn_timer > 30: # Small delay before AI shoots
                ai_shoot(cue_ball, balls)
                game_state = "MOVING"
                turn_timer = 0

        # Drawing
        
        # Draw Trajectory Guide (Only when aiming)
        if game_state == "PLAYER_AIM":
            mouse_pos = pygame.mouse.get_pos()
            
            # Calculate Aim Line (Visualizing the shot)
            aim_vector = pygame.math.Vector2(cue_ball.pos) - pygame.math.Vector2(mouse_pos)
            
            # Draw Cue Stick (Pull back mechanic visual)
            # If we are dragging, draw the stick pulled back
            if drag_start:
                 pygame.draw.line(screen, BROWN, cue_ball.pos, mouse_pos, 6)
            
            # Draw Aim Helper (Line extending from ball)
            if aim_vector.length() > 0:
                aim_norm = aim_vector.normalize() * 200
                # Predict trajectory (simple straight line)
                start_pred = cue_ball.pos
                end_pred = cue_ball.pos + aim_norm
                pygame.draw.line(screen, (255, 255, 255, 100), start_pred, end_pred, 2)

        # Draw Balls
        for b in balls:
            b.draw(screen)

        # UI / Status
        status_text = "Your Turn" if game_state == "PLAYER_AIM" else "Moving..." if game_state == "MOVING" else "Computer Thinking..."
        if game_state == "AI_WAIT": status_text = "Computer Turn"
        
        text = font.render(status_text, True, WHITE)
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
