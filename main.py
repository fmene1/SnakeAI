from gameAI import GameAI, Direction, parse_action, Action
from plot import plot
import logger_helper
from agent import Agent
import agent

# --------------------------------------------------------
# If not set, follow the default debug configuration
DEBUG = None
LOG_FILENAME = None
DEBUG_FILENAME = None
# --------------------------------------------------------


# Set up logging
logger = logger_helper.setup_logger(__name__, LOG_FILENAME, DEBUG, DEBUG_FILENAME)


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
    debug_message = f"Current state: {danger_message}\t{direction_message}\t{food_message}"
    logger.debug(debug_message)


def train():
    scores = []
    mean_scores = []
    total_score = 0
    record = 0
    game_agent = Agent()
    game = GameAI()
    while game_agent.n_games <= agent.MAX_GAMES:
        speed = agent.SPEED_INITIAL if game_agent.n_games <= agent.MAX_EXPLORATION else agent.SPEED_FINAL
        # get old state
        state_old = get_state(game)

        # get move
        action = game_agent.get_action(state_old)

        # perform move and get new state
        reward, score, game_over = game.next_tick(action, speed)
        state_new = get_state(game)

        # train short memory
        game_agent.train_short_memory(state_old, action.value, reward, state_new, game_over)

        # remember
        game_agent.remember(state_old, action.value, reward, state_new, game_over)

        if game_over:
            # train long memory
            game.reset()
            game_agent.n_games += 1
            game_agent.train_long_memory()

            if score > record:
                record = score
                game_agent.model.save()
            log_message = f"Game number: {game_agent.n_games}\t\tScore: {score}\tCurrent record: {record}."
            print(log_message)
            logger.info(log_message)
            # Plotting
            scores.append(score)
            total_score += score
            mean_score = total_score / game_agent.n_games
            mean_scores.append(mean_score)
            plot(scores, mean_scores)


if __name__ == "__main__":
    train()
