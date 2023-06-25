"""
Original game
"""

import pygame
from pygame import Vector2
from enum import Enum
import random


# Absolute directions
class Direction(Enum):
    NONE = Vector2(0, 0)
    RIGHT = Vector2(1, 0)
    LEFT = Vector2(-1, 0)
    UP = Vector2(0, -1)
    DOWN = Vector2(0, 1)


class Color(Enum):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (200, 0, 0)
    LIGHT_GREEN = (0, 255, 0)
    DARK_GREEN = (0, 128, 0)
    BLUE = (8, 21, 77)


# --------------------------------------------------------
# Window width
SCREEN_WIDTH = 640
# Window height
SCREEN_HEIGHT = 480
# Unit size
SECTION_SIZE = 20
# Base game speed
SPEED = 10
# Font size
FONT_SIZE = 25


# --------------------------------------------------------

class Food:
    def __init__(self, screen: pygame.display, x: int = 0, y: int = 0):
        self.screen = screen
        self.pos = Vector2(self.randomize())

    def draw(self):
        pygame.draw.rect(self.screen, Color.RED.value, (self.pos.x, self.pos.y, SECTION_SIZE, SECTION_SIZE))

    def __str__(self):
        return f"Food at position {self.pos}."

    def randomize(self):
        width, height = self.screen.get_size()
        x = random.randint(1, (width - 2 * SECTION_SIZE) // SECTION_SIZE) * SECTION_SIZE
        y = random.randint(1, (height - 2 * SECTION_SIZE) // SECTION_SIZE) * SECTION_SIZE
        return x, y


class Snake:
    def __init__(self, screen: pygame.display, length: int = 3, x: int = 0, y: int = 0,
                 direction: (int, int) = Direction.NONE):
        self.screen = screen
        self.length = length
        self.head = Vector2(x, y)
        self.direction = direction
        self.body = [Vector2(self.head.x - i * SECTION_SIZE, self.head.y) for i in range(1, length)]
        # Check if we need to add a new section on next movement
        self.new_section = False

    def draw(self):
        # Draw head
        # Base section
        pygame.draw.rect(self.screen, Color.DARK_GREEN.value, (self.head.x, self.head.y, SECTION_SIZE, SECTION_SIZE))

        # Lighter inline
        pygame.draw.rect(self.screen, Color.LIGHT_GREEN.value, (self.head.x + SECTION_SIZE / 5, self.head.y +
                                                                SECTION_SIZE / 5,
                                                                3 * SECTION_SIZE / 5, 3 * SECTION_SIZE / 5))
        # Draw body
        for s in self.body:
            # Base section
            pygame.draw.rect(self.screen, Color.DARK_GREEN.value, (s.x, s.y, SECTION_SIZE, SECTION_SIZE))

            # Lighter inline
            #pygame.draw.rect(self.screen, Color.LIGHT_GREEN.value, (s.x + SECTION_SIZE / 5, s.y + SECTION_SIZE / 5,
            #                                                        3 * SECTION_SIZE / 5, 3 * SECTION_SIZE / 5))

    def move(self):
        if self.direction == Direction.NONE:
            return
        old_head = self.head.copy()
        self.body.insert(0, old_head)
        self.head += self.direction.value * SECTION_SIZE
        if not self.new_section:
            self.body.pop()
        else:
            self.length += 1
            self.new_section = False

        #print(f"After movement: {self.head} {self.body}")

    def add_section(self):
        self.new_section = True


class Game:
    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT):
        pygame.init()
        # Game window dimensions
        self.width = width
        self.height = height
        # Create display
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Snake Game")
        # Clock
        self.clock = pygame.time.Clock()
        # Font
        self.font = pygame.font.Font(None, FONT_SIZE)
        # Initial game state
        # Snake starts at length 3, at the center of the screen, facing right
        self.snake = Snake(self.screen, length=3, x=width // 2, y=height // 2)
        self.score = 0
        self.food = None
        self.place_food()

    def run(self):
        while True:
            self.next_tick()

    def reset(self):
        self.snake = Snake(self.screen, length=3, x=self.width // 2, y=self.height // 2)
        self.score = 0

    def next_tick(self):
        # Read user input
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    pygame.quit()
                    quit()
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_ESCAPE:
                            pygame.quit()
                            quit()
                        case pygame.K_RIGHT if self.snake.direction != Direction.LEFT:
                            self.snake.direction = Direction.RIGHT
                        case pygame.K_LEFT if self.snake.direction != Direction.RIGHT:
                            self.snake.direction = Direction.LEFT
                        case pygame.K_UP if self.snake.direction != Direction.DOWN:
                            self.snake.direction = Direction.UP
                        case pygame.K_DOWN if self.snake.direction != Direction.UP:
                            self.snake.direction = Direction.DOWN
        # Move snake
        self.snake.move()
        # Check if food eaten
        if self.food_collision():
            self.score += 1
            self.place_food()
            self.snake.add_section()
        # Check game over
        if self.wall_collision() or self.snake_collision():
            self.game_over()
        # update ui and clock
        self.update_ui()
        self.clock.tick(SPEED)

    def place_food(self):
        self.food = Food(self.screen)
        # If the food is spawned in the snake, replace it
        if self.food.pos in self.snake.body:
            self.place_food()
        else:
            self.food = Food(self.screen)

    def update_ui(self):
        # Fill display
        self.screen.fill(Color.BLACK.value)
        # Draw outer walls
        self.draw_walls()
        # Draw snake
        self.snake.draw()
        #Draw food
        self.food.draw()
        self.display_score()
        pygame.display.flip()

    def display_score(self):
        text = self.font.render(f"Score: {self.score}", True, Color.WHITE.value)
        self.screen.blit(text, [0, 0])

    def wall_collision(self):
        if self.snake.head.x < SECTION_SIZE or self.snake.head.x > self.width - 2 * SECTION_SIZE:
            return True
        if self.snake.head.y < SECTION_SIZE or self.snake.head.y > self.height - 2 * SECTION_SIZE:
            #print("Wall collision.")
            return True
        return False

    def snake_collision(self):
        if self.snake.head in self.snake.body:
            #print("Body collision.")
            return True
        return False

    def food_collision(self):
        if self.food.pos.x + SECTION_SIZE > self.snake.head.x > self.food.pos.x - SECTION_SIZE:
            if self.food.pos.y + SECTION_SIZE > self.snake.head.y > self.food.pos.y - SECTION_SIZE:
                return True
        return False

    def draw_walls(self):
        rect = self.screen.get_rect()
        pygame.draw.rect(self.screen, Color.BLUE.value, rect, width=SECTION_SIZE)

    def game_over(self):
        print(f"Game over! Score is {self.score}.")
        self.reset()


if __name__ == '__main__':
    game = Game()
    game.run()
