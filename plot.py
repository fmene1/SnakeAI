import matplotlib.pyplot as plt
from IPython import display
from IPython.utils import io
import logger_helper

# --------------------------------------------------------
# If not set, follow the default debug configuration
DEBUG = None
LOG_FILENAME = None
DEBUG_FILENAME = None
# --------------------------------------------------------

# Set up logging
logger = logger_helper.setup_logger(__name__, LOG_FILENAME, DEBUG, DEBUG_FILENAME)

#Activate interactive mode
plt.ion()


def plot(scores, mean_scores):
    # We need to suppress the output of the IPython module to prevent annoying console messages
    with io.capture_output() as captured:
        display.clear_output(wait=True)
        display.display(plt.gcf())
        plt.clf()
        plt.title("Training...")
        plt.xlabel("Games played")
        plt.ylabel("Score")
        plt.plot(scores)
        plt.plot(mean_scores)
        plt.ylim(ymin=0)
        plt.text(len(scores) - 1, scores[-1], str(scores[-1]))
        plt.text(len(mean_scores) - 1, mean_scores[-1], str(mean_scores[-1]))
        plt.show(block=False)
        plt.pause(.1)
