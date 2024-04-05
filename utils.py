from datetime import datetime
import os

# Directory where data from file will be written
DATA_DIRECTORY = "./data"

input_tokens_max = {
    "gpt-4": 15_800,
    "gpt-4-0125-preview": 127_900,
    "gpt-4-1106-preview": 127_900,
    "gpt-3.5-turbo-0125": 15_800,
    "gpt-3.5-turbo-instruct": 4096,
}


def get_token_limit(model_name: str) -> int:
    """Returns the token limit for the given model name.

    Args:
        model_name (str): The name of the model.

    Returns:
        int: The token limit for the model.
    """
    return input_tokens_max.get(model_name, 0)


def create_timestamped_directory(base_path=DATA_DIRECTORY):
    """Creates a directory named with the current timestamp.

    Args:
        base_path (str): The base directory where the new directory will be created.

    Returns:
        str: The path of the newly created directory.
    """
    # Generate a timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Create the directory path
    dir_path = os.path.join(base_path, timestamp)
    # Make the directory
    os.makedirs(dir_path, exist_ok=True)
    return dir_path
