import turtle
import math

# Set up the screen
screen = turtle.Screen()
screen.title("Beating Heart Animation")
screen.bgcolor("black")
screen.setup(width=600, height=600)
screen.tracer(0)  # Turns off automatic screen updates for smooth animation

# Create the pen
pen = turtle.Turtle()
pen.speed(0)
pen.hideturtle()

def heart_x(t):
    """Parametric equation for X coordinate."""
    return 16 * math.sin(t) ** 3

def heart_y(t):
    """Parametric equation for Y coordinate."""
    return 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)

def draw_heart(scale, color):
    """Draws a complete filled heart shape at a given scale factor."""
    pen.color(color)
    pen.fillcolor(color)
    pen.begin_fill()
    
    # Trace the mathematical formula from 0 to 2*pi
    t = 0
    while t < 2 * math.pi:
        x = heart_x(t) * scale
        y = heart_y(t) * scale
        
        if t == 0:
            pen.up()
            pen.goto(x, y)
            pen.down()
        else:
            pen.goto(x, y)
        t += 0.05
        
    pen.end_fill()

# Animation configuration variables
scale_factor = 12   # Starting scale size
growing = True      # Direction of the pulse animation

def animate():
    global scale_factor, growing
    pen.clear()
    
    # 1. Draw a faint background glow layer
    draw_heart(scale_factor * 1.15, "#30000a")
    
    # 2. Draw a bright outer glow layer
    draw_heart(scale_factor * 1.05, "#800020")
    
    # 3. Draw the main solid crimson heart
    draw_heart(scale_factor, "#e60026")
    
    # 4. Optional: Add romantic center text
    pen.up()
    pen.goto(0, -15)
    pen.color("white")
    pen.write("I ♥ Python", align="center", font=("Arial", 16, "bold"))
    
    # Update the window canvas visually
    screen.update()
    
    # Alter the sizing boundaries to trigger the bounce
    if growing:
        scale_factor += 0.15
        if scale_factor >= 14.5:  # Maximum expansion size
            growing = False
    else:
        scale_factor -= 0.15
        if scale_factor <= 12.0:  # Minimum contraction size
            growing = True
            
    # Loop the animation function every 15 milliseconds
    screen.ontimer(animate, 15)

# Initialize the animation loop
animate()

# Keep the window open until user closes it
turtle.done()
