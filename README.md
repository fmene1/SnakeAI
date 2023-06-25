# SnakeAI
A neural network is trained via **reinforcement learning** to play a custom implementation of the famous snake game.

## Project overview
The project contains the following files:
- [original_game.py](https://github.com/fmene1/SnakeAI/blob/main/original_game.py) - Human playable snake game logic, implemented with [pygame](https://www.pygame.org/news).
- [gameAI.py](https://github.com/fmene1/SnakeAI/blob/main/gameAI.py) - AI playable snake game logic, implemented with [pygame](https://www.pygame.org/news).
- [main.py](https://github.com/fmene1/SnakeAI/blob/main/main.py) - Main entry point containing the training loop.
- [agent.py](https://github.com/fmene1/SnakeAI/blob/main/agent.py) - AI agent making decisions.
- [model.py](https://github.com/fmene1/SnakeAI/blob/main/model.py) - Two layer neural network, implemented with [pytorch](https://pytorch.org/).
- [plot.py](https://github.com/fmene1/SnakeAI/blob/main/plot.py) - Interactive plots.
- [logger_helper.py](https://github.com/fmene1/SnakeAI/blob/main/logger_helper.py) - Logs generation.

## How to install
The file [requirements.txt](https://github.com/fmene1/SnakeAI/blob/main/requirements.txt) has the required packages.
For Windows the following command should automatically install the requirements.
`pip install -r requirements.txt`

## How to run
### AI Training
Run the simulation with
`python main.py`
### Human Snake Game
Run the game with
`python original_game.py`
Use arrow keys to move the snake and Esc to close the window.
