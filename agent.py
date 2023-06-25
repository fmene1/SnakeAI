import torch
import random
from collections import deque
from gameAI import Action
from model import Linear_QNet, QTrainer
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
EXPLORING_PERCENTAGE = 0.07
# Last iteration with the possibility of taking a random action
MAX_EXPLORATION = int(MAX_GAMES * EXPLORING_PERCENTAGE)
# The probability of taking a random action during the first iteration, must be <1
INITIAL_EXPLORING_PROBABILITY = 0.6
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
        # Model and trainer
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
        upper_limit = int(MAX_EXPLORATION / (1 - INITIAL_EXPLORING_PROBABILITY))
        if random.randint(0, upper_limit) < self.epsilon:
            # Pick one of the options at random
            option = random.randint(0, 2)
            debug_message = "Picking random option "
        # We let the model decide the next move
        else:
            # The output is a tensor with three elements, to convert it into a valid action we execute the option
            # with maximum value (if there's a tie we always take the first one in the order STRAIGHT -> RIGHT -> LEFT)
            state_tensor = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state_tensor)
            option = torch.argmax(prediction).item()
            debug_message = "Picking predicted option "

        action_value[option] = 1
        action_value = tuple(action_value)

        for action in Action:
            if action.value == action_value:
                debug_message += f"{action}."
                logger.debug(debug_message)
                return action
