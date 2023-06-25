import torch
import random
from collections import deque
from gameAI import GameAI, Direction, parse_action, Action
from model import Linear_QNet, QTrainer
from plot import plot
import logger_helper

# --------------------------------------------------------
# If not set, follow the default debug configuration
DEBUG = None
LOG_FILENAME = None
DEBUG_FILENAME = None

INPUT_SIZE = 11
OUTPUT_SIZE = 3
HIDDEN_LAYER_SIZE = 256

MAX_MEMORY = 100_000
BATCH_SIZE = 1_000
MAX_GAMES = 1_000
# Percentage of MAX_GAMES in which we allow exploring
EXPLORING_PERCENTAGE = 0.08
# Last iteration with the possibility of taking a random action
MAX_EXPLORATION = MAX_GAMES * EXPLORING_PERCENTAGE
# Learning rate
LR = 0.001
# Discount rate (must be in (0,1), usually around 0.8-0.9)
GAMMA = 0.9
# Game speed
SPEED_INITIAL = 200
SPEED_FINAL = 100

# --------------------------------------------------------


# Set up logging
logger = logger_helper.setup_logger(__name__, LOG_FILENAME, DEBUG, DEBUG_FILENAME)


class Agent:
    def __init__(self):
        self.n_games = 0
        # Parameter controlling the chance to explore
        self.epsilon = 0
        # Discount rate
        self.gamma = GAMMA
        # Memory
        self.memory = deque(maxlen=MAX_MEMORY)
        # Model
        self.model = Linear_QNet(INPUT_SIZE, HIDDEN_LAYER_SIZE, OUTPUT_SIZE)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def remember(self, state, action_value, reward, next_state, game_over):
        # Add to memory the latest info, if the memory exceeds MAX_MEMORY we forget the oldest info memorized
        self.memory.append((state, action_value, reward, next_state, game_over))

    # Train with a big batch (at most BATCH_SIZE) data points
    def train_long_memory(self):
        # if we have more than the required BATCH_SIZE, we randomly select a sample from memory
        if len(self.memory) > BATCH_SIZE:
            batch = random.sample(self.memory, BATCH_SIZE)
        # otherwise we take everything we have
        else:
            batch = self.memory
        # We create tuples of every state, action, reward etc..
        # for example given batch = [(0,1,2),(3,4,5),(6,7,8)] zip(*batch) would return [(6,3,0), (7,4,1), (8,5,2)]
        states, actions, rewards, next_states, game_overs = zip(*batch)
        self.trainer.train_step(states, actions, rewards, next_states, game_overs)

    # Train with the last data point created
    def train_short_memory(self, state, action_value, reward, next_state, game_over):
        self.trainer.train_step(state, action_value, reward, next_state, game_over)

    # Produce an action from the model
    def get_action(self, state) -> Action:
        action_value = [0, 0, 0]
        # We need to balance exploration / exploitation
        # During the first iterations we favor taking random actions and exploring the environment,
        # with the probability of doing so linearly decreasing to zero until iteration MAX_GAMES*EXPLORING_PERCENTAGE
        self.epsilon = MAX_EXPLORATION - self.n_games
        if random.randint(0, 200) < self.epsilon:
            # Pick one of the options at random
            option = random.randint(0, 2)
            #print(f"Picking random option ", sep="")
        # We let the model decide the next move
        else:
            # The output is a tensor with three elements, to convert it into a valid action we execute the option
            # with maximum value (if there's a tie we always take the first one in the order STRAIGHT -> RIGHT -> LEFT)
            state_tensor = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state_tensor)
            option = torch.argmax(prediction).item()
            #print(f"Picking decided option ", sep="")

        action_value[option] = 1
        action_value = tuple(action_value)

        for action in Action:
            #print(f"Comparing {action.value} with {action_value}.")
            if action.value == action_value:
                #print(f"Found equality!")
                #print(action)
                return action


def get_state(game):
    danger = [int(game.is_collision(parse_action(a, game.snake.direction))) for a in Action]
    direction = [int(game.snake.direction == d) for d in Direction if d != Direction.NONE]
    food = [
        int(game.food.pos.x > game.snake.head.x),  # food right
        int(game.food.pos.y > game.snake.head.y),  # food down
        int(game.food.pos.x < game.snake.head.x),  # food left
        int(game.food.pos.y < game.snake.head.y)  # food up
    ]
    state = danger + direction + food
    log_state(state)
    return state


def log_state(state):
    danger_message = ""
    direction_message = ""
    food_message = ""
    danger = state[:3]
    direction = state[3:6]
    food = state[7:12]
    # Compose danger_message
    for a in Action:
        if danger:
            danger_message += f"{a.name} "
    if danger_message != "":
        danger_message = f"{danger_message}is dangerous."
    else:
        danger_message = "No danger ahead!"
    # Compose direction_message
    for d in Direction:
        if d != Direction.NONE and direction:
            direction_message = f"Snake is pointing {d.name}."
    dir_names = [d.name for d in Direction if d != Direction.NONE]
    for i, f in enumerate(food):
        if f:
            food_message += f" {dir_names[i]}"
    food_message = f"Food is{food_message}."
    log_message = f"Current state: {danger_message}\t{direction_message}\t{food_message}"
    logger.debug(log_message)


def train():
    scores = []
    mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = GameAI()
    while agent.n_games <= MAX_GAMES:
        speed = SPEED_INITIAL if agent.n_games <= MAX_EXPLORATION else SPEED_FINAL
        # get old state
        #print("Getting old state.")
        state_old = get_state(game)

        # get move
        action = agent.get_action(state_old)

        # perform move and get new state
        reward, score, game_over = game.next_tick(action, speed)
        #print("Getting new state.")
        state_new = get_state(game)

        # train short memory
        agent.train_short_memory(state_old, action.value, reward, state_new, game_over)

        # remember
        agent.remember(state_old, action.value, reward, state_new, game_over)

        if game_over:
            #print("--------GAME OVER!!!!-----------")
            # train long memory
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()
            log_message = f"Game number: {agent.n_games}\t\tScore: {score}\tCurrent record: {record}."
            print(log_message)
            logger.info(log_message)
            # Plotting
            scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            mean_scores.append(mean_score)
            plot(scores, mean_scores)


if __name__ == "__main__":
    train()
