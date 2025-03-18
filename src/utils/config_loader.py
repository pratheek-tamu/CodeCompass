import yaml
import os

def load_config(filepath="config.local.yaml", fallback_filepath="config.yaml"):
    config_path = os.path.join(os.path.dirname(__file__), "../../", filepath)

    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(__file__), "../../", fallback_filepath)

    with open(config_path) as file:
        return yaml.safe_load(file)
