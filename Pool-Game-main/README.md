# Pool-Game
My very own pool game made from using python and pygame

# Pool_game_v1.py
my first basic foundation for upcoming versions... it had many issues which were fixed in later versions
it may seem that all codes were uploaded on same day but infact i coded and fixed them locally before uploading what seems to be a work of a day actually took 2-3 weeks to complete and fix. a like and star would help me out a ton.

# Pool_game_v2.py .
it had many issues which were fixed in this version
I found the bug! The game always switches to AI after balls stop moving, regardless of whose turn it was. 

# Pool_game_v3.py
i found many more issues in previous versions and fixed them in this one
1. made the wooden cue visible
2. the turn the color of wooden cue to dark brown and the direction the white ball will be going in white
3. if computer/user pots a ball the turn should lie with the peron who potted it
4. {line 40
self.color0, 0 = color
SyntaxError: cannot assign to literal here. Maybe you meant '==' instead of '='?}
5. don't let the white ball roll on wooden parts on the edges of the table which are colored brown

### Summary of fixes
#### Issue                                   Fix Applied

1. Make wooden cue visible                 Created draw_cue_stick() function that draws a proper cue stick
2. Cue = dark brown, Trajectory = white    Cue stick drawn in DARK_BROWN (RGB: 60,30,10), trajectory line in WHITE
3. Keep turn if ball potted                Added potted_ball tracking - if a ball is potted, turn stays with current player
3. Syntax error on line 40                 Changed self.color0, 0 = color to self.color = color
4. Balls on wooden border                  Changed wall collision boundaries to be inside the brown border (BORDER_SIZE offset)

# Pool_game_v4.py
the balls were too stiff to move when hit by the while ball, so i made them either glide/slide to make them behave like a normal ball

Change              |Before              |After                                       |Effect

Friction            |0.985               |0.99                                        |Balls glide longer before stopping

Min Velocity        |0.05                |0.02                                        |Balls can move slower before stopping

Wall Bounce         |-1.0 (full bounce)  |-0.9 (slight energy loss)                   |More realistic wall bounces

Collision Physics   |Basic momentum      |Proper impulse-based elastic collision      |Better energy transfer between balls

Collision Checks    |1 per frame         |4 per frame                                 |More accurate collision detection

AI Power            |8-14                |10-16                                       |sStronger shots

#### Key Physics Improvements
1. Impulse-based collision: Uses proper physics formula with restitution (bounciness) for realistic energy transfer
2. Lower friction: Balls glide smoothly across the table
3. Lower velocity threshold: Balls can roll slowly before stopping naturally
4. Multiple collision checks: Prevents balls from passing through each other
5. Wall energy loss: Walls absorb some energy like real cushions

