import os
import yaml
from typing import Dict, Any
from pathlib import Path


def load_config(config_path: str = None) -> Dict[str, Any]:
    if config_path is None:
        config_path = os.environ.get('LIVELIST_CONFIG')

    if config_path is None:
        # Try project root
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / 'config.yaml'

    # Load YAML
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f) or {}
    return config
