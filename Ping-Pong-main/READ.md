🎮 Project Description: Simple 2D Pong Game (Web Implementation)
This project implements a classic 2D Pong game using HTML5 Canvas, JavaScript, and CSS. It is a single-player vs. AI setup where the user controls the left paddle and the computer controls the right paddle.

Key Features:
Technology Stack: HTML, CSS, and pure JavaScript.

Game Area: A fixed-size canvas element (800x400 pixels) for rendering.

Visuals: Simple, distinct elements:

Dark background (#111).

Blue player paddle (#00f).

Red AI paddle (#f00).

White ball (#fff).

A dashed gray net in the center.

Player Control (Left Paddle): The player controls the vertical position of their paddle using the mouse Y-coordinate via a mousemove event listener. The paddle movement is clamped to stay within the canvas boundaries.

AI Control (Right Paddle): The AI paddle moves to track the center of the ball's Y-position, limited by a defined PADDLE_SPEED (5 pixels per frame), creating a simple but challenging opponent.

Ball Physics:

The ball moves with constant velocity (ballVx, ballVy).

Collision with the top and bottom walls reverses the vertical velocity (ballVy *= -1).

Collision with a paddle reverses the horizontal velocity (ballVx *= -1).

"Spin" Mechanics: Upon hitting a paddle, the ball's vertical velocity (ballVy) is adjusted based on the distance between the ball's center and the paddle's center of contact, adding dynamic angles to the return shot.

Scoring/Reset: When the ball goes off the left or right side of the screen, the game resets the ball to the center with a new, randomized initial direction.

