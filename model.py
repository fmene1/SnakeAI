import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os
import logger_helper

# --------------------------------------------------------
# If not set, follow the default debug configuration
DEBUG = None
LOG_FILENAME = None
DEBUG_FILENAME = None
# --------------------------------------------------------

# Set up logging
logger = logger_helper.setup_logger(__name__, LOG_FILENAME, DEBUG, DEBUG_FILENAME)


class Linear_QNet(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        super().__init__()
        # Input layer
        self.layer1 = nn.Linear(input_size, hidden_size)
        # Hidden layer
        self.layer2 = nn.Linear(hidden_size, output_size)

    # This method makes the prediction
    def forward(self, x):
        # Apply first layer and then the activation function
        x = F.relu(self.layer1(x))
        # Apply second layer
        x = self.layer2(x)
        return x

    def save(self, filename: str = "model.pth"):
        model_folder_path = "./model"
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)
            logger.info(f"Folder not found, created one at path {model_folder_path}.")
        file_name = os.path.join(model_folder_path, filename)
        torch.save(self.state_dict(), file_name)
        logger.info(f"Created save file named {filename}.")


class QTrainer:
    def __init__(self, model, lr, gamma):
        self.lr = lr
        self.gamma = gamma
        self.model = model
        # We choose Adam algorithm as our optimizer. More info here: https://arxiv.org/pdf/1412.6980.pdf
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr)
        # We choose a simple mean squared loss function
        self.criterion = nn.MSELoss()

    def train_step(self, state, action_value, reward, next_state, game_over):
        state = torch.tensor(state, dtype=torch.float)
        action_value = torch.tensor(action_value, dtype=torch.float)
        reward = torch.tensor(reward, dtype=torch.float)
        next_state = torch.tensor(next_state, dtype=torch.float)

        # If we have a single datapoint all the tensors are in the form [...]. We want to reshape them in the form
        # [[...]] for future processing
        if len(state.shape) == 1:
            state = torch.unsqueeze(state, 0)
            action_value = torch.unsqueeze(action_value, 0)
            reward = torch.unsqueeze(reward, 0)
            next_state = torch.unsqueeze(next_state, 0)
            # Create a tuple with a single element
            game_over = (game_over,)

        # This is the number of games played we need to analyze
        n_iterations = len(game_over)

        # Implementing Bellman Equation

        # Phase 1
        # Get prediction based on current state and initialize target to its copy

        prediction = self.model(state)
        target = prediction.clone()

        # Phase 2
        # Calculate Q value
        # for every iteration we update the new target
        for i in range(n_iterations):
            # We add the reward to our Q
            # If the game is over, no new steps can be taken, we're done
            Q = reward[i]
            # If the game's not over, we also add the value of our future action discounted by gamma
            if not game_over[i]:
                Q += self.gamma * torch.max(self.model(next_state[i]))

            # Of the three values in the target for our current iteration, we only update the one corresponding to
            # the action actually taken.
            target[i][torch.argmax(action_value).item()] = Q
        # calculate the loss with the new computed Q value
        self.optimizer.zero_grad()
        loss = self.criterion(target, prediction)
        loss.backward()
        self.optimizer.step()
