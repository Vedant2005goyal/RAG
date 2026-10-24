import os

def require_env(name: str) -> str:
    """ Safely load enviornment variable else raise error. """
    
    if (value := os.getenv(name)) is None:
        raise ValueError(f"{name} enviornment variable is not set.")

    return value