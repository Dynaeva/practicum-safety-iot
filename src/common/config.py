import yaml
from src.common.contract import validate_config

def load_config(path: str = "configs/config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    validate_config(cfg)   # <-- ошибка в yaml-формате
    return cfg