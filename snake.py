import curses
import time
import random

HEARTBEAT = 15  # Number of milliseconds between each heartbeat.
NUM_EGGS = 100


class Egg:
    def __init__(self, width: int, height: int):
        self.x = random.randrange(width)
        self.y = random.randrange(1, height - 1)

        self.animation = '-\\|/-\\|/'
        self.phase = random.randrange(len(self.animation))
        self.speed = 250        # Milliseconds between each phase of animation.

        # Making the timers start at a random number means the spinning eggs spinning are not synchronised.
        self.timer = random.randrange(self.speed)           # Internal timer of each egg.

    def tick(self):
        self.timer += HEARTBEAT
        if self.timer >= self.speed:
            self.timer -= self.speed
            self.phase += 1
            if self.phase == len(self.animation):
                self.phase = 0

    def render(self, stdscr):
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(self.y, self.x, self.animation[self.phase])


class Snake:
    def __init__(self):

        self.speed = 15                                    # Milliseconds between each move of head.
        self.timer = 0

        # 0 = East, 1 = South, 2 = West, 3 = North.
        self.deltas = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.direction = 0
        self.prev_direction = 0

        self.segments = [(5, 5)]                            # Start with just a head segment.
        self.segment_dirs = {(5, 5): (self.prev_direction, self.direction)}

        self.eaten_egg = False
        self.dead = False

        self.head_chars = '▶▼◀▲'
        self.body_chars = {(0, 0): '─',
                           (0, 1): '┐',
                           (0, 3): '┘',
                           (1, 0): '└',
                           (1, 1): '│',
                           (1, 2): '┘',
                           (2, 1): '┌',
                           (2, 2): '─',
                           (2, 3): '└',
                           (3, 0): '┌',
                           (3, 2): '┐',
                           (3, 3): '│'}

    @staticmethod
    def clockwise(d: int) -> int:
        return (d + 1) % 4

    @staticmethod
    def anti_clockwise(d: int) -> int:
        return (d - 1) % 4

    def head(self):
        """Return coords of the head of the snake."""
        # Last item in the segment list is the head of the snake.
        return self.segments[-1]

    @staticmethod
    def in_grid(x: int, y: int, edge_x: int, edge_y: int) -> bool:
        """Return True if the parm coords are in the game grid. False otherwise."""
        return 0 <= x < edge_x and 1 <= y < edge_y - 1

    def next(self, x: int, y: int, d: int) -> (int, int):
        """Return coords of next move for parm coords and direction."""
        dx, dy = self.deltas[d]
        return x + dx, y + dy

    def eaten_itself(self, x: int, y: int) -> bool:
        if (x, y) not in self.segments:
            return False
        if self.segments.index((x, y)) == len(self.segments) - 1:
            return False
        return True

    def render(self, f):
        """Draw the snake on the parm image frame."""
        x, y = self.head()
        f.attron(curses.color_pair(2))
        f.attron(curses.A_BOLD)
        f.addstr(y, x, self.head_chars[self.direction])

        # Skip the last element of list (which is the head).
        for (x, y) in self.segments[:-1]:
            p, c = self.segment_dirs[(x, y)]
            f.addstr(y, x, self.body_chars[(p, c)])

    def move(self, w, h):
        x, y = self.head()
        self.segment_dirs[(x, y)] = (self.prev_direction, self.direction)

        # First, try heading straight ahead.
        d = self.direction
        px, py = self.next(x, y, d)

        # If that's no good...
        if not self.in_grid(px, py, w, h) or self.eaten_itself(x, y):
            # ... next, find out what Clockwise is like.
            d_cw = self.clockwise(d)
            x_cw, y_cw = self.next(x, y, d_cw)

            if not self.in_grid(x_cw, y_cw, w, h) or self.eaten_itself(x_cw, y_cw):
                # If still no good, try anticlockwise.
                d_acw = self.anti_clockwise(d)
                x_acw, y_acw = self.next(x, y, d_acw)

                if not self.in_grid(x_acw, y_acw, w, h) or self.eaten_itself(x_acw, y_acw):
                    # If still no good, then we're dead :(
                    self.dead = True
                else:
                    x, y, self.direction = x_acw, y_acw, d_acw
            else:
                x, y, self.direction = x_cw, y_cw, d_cw
        else:
            x, y = px, py

        if self.dead is False:
            self.segments.append((x, y))
            if self.eaten_egg:
                self.eaten_egg = False
            else:
                del self.segments[0]

        self.prev_direction = self.direction

    def tick(self, w, h):
        self.timer += HEARTBEAT
        if self.timer >= self.speed:
            self.timer = 0
            self.move(w, h)


def draw_menu(stdscr):

    k = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()
    height, width = 0, 0

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)

    eggs = []
    snake = Snake()

    # Loop where k is the last character pressed
    # while snake.dead is False:
    while k != ord('q') and snake.dead is False:
        new_height, new_width = stdscr.getmaxyx()
        if new_height != height or new_width != width:
            height, width = new_height, new_width
            eggs = []
            for i in range(NUM_EGGS):
                eggs.append(Egg(width=width, height=height))

        stdscr.clear()

        for egg in eggs:
            egg.render(stdscr)
            egg.tick()

        snake.render(stdscr)
        snake.tick(w=width, h=height)

        eaten_egg = None
        for egg in eggs:
            if snake.head() == (egg.x, egg.y):
                snake.eaten_egg = True
                eaten_egg = egg
                curses.beep()
        if eaten_egg is not None:
            eggs.remove(eaten_egg)
            eggs.append(Egg(width, height))

        # Rendering some text
        whstr = "Score: " + str(len(snake.segments))
        stdscr.addstr(0, 0, whstr, curses.color_pair(1))

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        stdscr.nodelay(True)
        time.sleep(HEARTBEAT / 1000)
        k = stdscr.getch()

        if k == curses.KEY_RIGHT:
            snake.direction = snake.clockwise(d=snake.direction)
        elif k == curses.KEY_LEFT:
            snake.direction = snake.anti_clockwise(d=snake.direction)


def main():
    curses.wrapper(draw_menu)


if __name__ == "__main__":
    main()
