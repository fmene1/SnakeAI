"""
Game modified for the AI
"""

import pygame
from pygame import Vector2
from enum import Enum
import random
import logger_helper

# --------------------------------------------------------
# If not set, follow the default debug configuration
DEBUG = None
LOG_FILENAME = None
DEBUG_FILENAME = None

# Window width
SCREEN_WIDTH = 640
# Window height
SCREEN_HEIGHT = 480
# Unit size
SECTION_SIZE = 20
# Base game speed
SPEED = 100
# Font size
FONT_SIZE = 25
# Maximum number of moves the Agent can take per snake length before the game is reset
STEPS_PER_LENGTH = 50


# --------------------------------------------------------

# Absolute directions
class Direction(Enum):
    NONE = Vector2(0, 0)
    RIGHT = Vector2(1, 0)
    DOWN = Vector2(0, 1)
    LEFT = Vector2(-1, 0)
    UP = Vector2(0, -1)


clockwise_directions = [d for d in Direction if d.name != "NONE"]


class Action(Enum):
    STRAIGHT = (1, 0, 0)
    RIGHT = (0, 1, 0)
    LEFT = (0, 0, 1)


# Set up logging
logger = logger_helper.setup_logger(__name__, LOG_FILENAME, DEBUG, DEBUG_FILENAME)


def parse_action(action: Action, direction: Direction) -> Direction:
    debug_message = f"Parsing action: {action} with direction {direction}. "
    idx = clockwise_directions.index(direction)
    match action:
        case Action.STRAIGHT:
            new_idx = idx
        case Action.RIGHT:
            # go clockwise
            new_idx = (idx + 1) % 4
        case Action.LEFT:
            # go counterclockwise
            new_idx = (idx - 1) % 4
        case _:
            raise ValueError(f"Couldn't parse action {action}.")
    debug_message += f"New direction is {clockwise_directions[new_idx]}."
    logger.debug(debug_message)
    return clockwise_directions[new_idx]


class Color(Enum):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (200, 0, 0)
    LIGHT_GREEN = (0, 255, 0)
    DARK_GREEN = (0, 128, 0)
    BLUE = (8, 21, 77)


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
                 direction: Direction = Direction.RIGHT):
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
            # pygame.draw.rect(self.screen, Color.LIGHT_GREEN.value, (s.x + SECTION_SIZE / 5, s.y + SECTION_SIZE / 5,
            #                                                         3 * SECTION_SIZE / 5, 3 * SECTION_SIZE / 5))

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

    def add_section(self):
        self.new_section = True

    def get_head_vertexes(self) -> [Vector2]:
        v_topl = self.head
        v_topr = self.head + Direction.RIGHT.value * SECTION_SIZE
        v_botl = self.head + Direction.DOWN.value * SECTION_SIZE
        v_botr = self.head + Direction.DOWN.value * SECTION_SIZE + Direction.RIGHT.value * SECTION_SIZE
        return [v_topl, v_topr, v_botr, v_botl]


class GameAI:
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
        # Attributes needed for the AI
        self.tick = 0

    def reset(self):
        self.tick = 0
        self.snake = Snake(self.screen, length=3, x=self.width // 2, y=self.height // 2)
        self.score = 0
        self.place_food()

    def next_tick(self, action: Action, speed: int = SPEED) -> (int, int, bool):
        self.tick += 1
        reward = 0
        game_over = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        self.snake.direction = parse_action(action, self.snake.direction)
        # Move snake
        self.snake.move()
        # Check if food eaten
        if self.food_collision():
            reward = 10
            self.score += 1
            self.place_food()
            self.snake.add_section()
        # Check game over
        if self.is_collision() or self.tick > STEPS_PER_LENGTH * self.snake.length:
            reward = -10
            game_over = True
            return reward, self.score, game_over
        # update ui and clock
        self.update_ui()
        self.clock.tick(speed)

        return reward, self.score, game_over

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

    def is_collision(self, direction: Vector2 = Direction.NONE):
        return self.wall_collision(direction) or self.snake_collision(direction)

    def wall_collision(self, direction: Vector2 = Direction.NONE):
        x = self.snake.head.x + direction.value[0] * SECTION_SIZE
        y = self.snake.head.y + direction.value[1] * SECTION_SIZE

        if x < SECTION_SIZE or x > self.width - 2 * SECTION_SIZE:
            logger.debug("Collision! Vertical wall hit.")
            return True
        if y < SECTION_SIZE or y > self.height - 2 * SECTION_SIZE:
            logger.debug("Collision! Horizontal wall hit.")
            return True
        return False

    def snake_collision(self, direction: Vector2 = Direction.NONE):
        if self.snake.head + direction.value * SECTION_SIZE in self.snake.body:
            logger.debug("Body collision.")
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
        log_message = f"Game over! Score is {self.score}."
        print(log_message)
        logger.info(log_message)
        self.reset()
