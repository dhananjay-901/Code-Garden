const canvas = document.getElementById('pong');
const ctx = canvas.getContext('2d');

const WIDTH = canvas.width;
const HEIGHT = canvas.height;

// Paddle settings
const PADDLE_WIDTH = 12;
const PADDLE_HEIGHT = 80;
const PADDLE_MARGIN = 14;
const PADDLE_SPEED = 5; // AI paddle speed

// Ball settings
const BALL_SIZE = 14;
const BALL_SPEED = 5;

// Game state
let leftPaddleY = HEIGHT / 2 - PADDLE_HEIGHT / 2;
let rightPaddleY = HEIGHT / 2 - PADDLE_HEIGHT / 2;
let ballX = WIDTH / 2 - BALL_SIZE / 2;
let ballY = HEIGHT / 2 - BALL_SIZE / 2;
let ballVx = BALL_SPEED * (Math.random() > 0.5 ? 1 : -1);
let ballVy = BALL_SPEED * (Math.random() * 2 - 1);

function drawRect(x, y, w, h, color) {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, w, h);
}

function drawCircle(x, y, r, color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2, false);
  ctx.closePath();
  ctx.fill();
}

function drawNet() {
  ctx.strokeStyle = "#444";
  ctx.beginPath();
  ctx.setLineDash([8, 16]);
  ctx.moveTo(WIDTH / 2, 0);
  ctx.lineTo(WIDTH / 2, HEIGHT);
  ctx.stroke();
  ctx.setLineDash([]);
}

function draw() {
  // Background
  drawRect(0, 0, WIDTH, HEIGHT, "#111");

  // Net
  drawNet();

  // Left paddle (player)
  drawRect(PADDLE_MARGIN, leftPaddleY, PADDLE_WIDTH, PADDLE_HEIGHT, "#00f");

  // Right paddle (AI)
  drawRect(WIDTH - PADDLE_MARGIN - PADDLE_WIDTH, rightPaddleY, PADDLE_WIDTH, PADDLE_HEIGHT, "#f00");

  // Ball
  drawCircle(ballX + BALL_SIZE / 2, ballY + BALL_SIZE / 2, BALL_SIZE / 2, "#fff");
}

function update() {
  // Ball movement
  ballX += ballVx;
  ballY += ballVy;

  // Ball collision with top/bottom walls
  if (ballY <= 0) {
    ballY = 0;
    ballVy *= -1;
  }
  if (ballY + BALL_SIZE >= HEIGHT) {
    ballY = HEIGHT - BALL_SIZE;
    ballVy *= -1;
  }

  // Ball collision with left paddle
  if (
    ballX <= PADDLE_MARGIN + PADDLE_WIDTH &&
    ballY + BALL_SIZE > leftPaddleY &&
    ballY < leftPaddleY + PADDLE_HEIGHT
  ) {
    ballX = PADDLE_MARGIN + PADDLE_WIDTH;
    ballVx *= -1;

    // Add some "spin" based on contact point
    let hitY = ballY + BALL_SIZE / 2 - (leftPaddleY + PADDLE_HEIGHT / 2);
    ballVy = hitY * 0.2;
  }

  // Ball collision with right paddle
  if (
    ballX + BALL_SIZE >= WIDTH - PADDLE_MARGIN - PADDLE_WIDTH &&
    ballY + BALL_SIZE > rightPaddleY &&
    ballY < rightPaddleY + PADDLE_HEIGHT
  ) {
    ballX = WIDTH - PADDLE_MARGIN - PADDLE_WIDTH - BALL_SIZE;
    ballVx *= -1;

    let hitY = ballY + BALL_SIZE / 2 - (rightPaddleY + PADDLE_HEIGHT / 2);
    ballVy = hitY * 0.2;
  }

  // Ball out of bounds (reset)
  if (ballX < 0 || ballX > WIDTH) {
    ballX = WIDTH / 2 - BALL_SIZE / 2;
    ballY = HEIGHT / 2 - BALL_SIZE / 2;
    ballVx = BALL_SPEED * (Math.random() > 0.5 ? 1 : -1);
    ballVy = BALL_SPEED * (Math.random() * 2 - 1);
  }

  // AI paddle movement (follows ball Y, but limited speed)
  let aiTargetY = ballY + BALL_SIZE / 2 - PADDLE_HEIGHT / 2;
  if (rightPaddleY + PADDLE_HEIGHT / 2 < aiTargetY) {
    rightPaddleY += PADDLE_SPEED;
  } else if (rightPaddleY + PADDLE_HEIGHT / 2 > aiTargetY) {
    rightPaddleY -= PADDLE_SPEED;
  }
  // Clamp AI paddle position
  rightPaddleY = Math.max(0, Math.min(HEIGHT - PADDLE_HEIGHT, rightPaddleY));
}

function gameLoop() {
  update();
  draw();
  requestAnimationFrame(gameLoop);
}

// Control left paddle with mouse Y
canvas.addEventListener("mousemove", function(e) {
  const rect = canvas.getBoundingClientRect();
  const mouseY = e.clientY - rect.top;
  leftPaddleY = mouseY - PADDLE_HEIGHT / 2;
  leftPaddleY = Math.max(0, Math.min(HEIGHT - PADDLE_HEIGHT, leftPaddleY));
});

// Start game
gameLoop();