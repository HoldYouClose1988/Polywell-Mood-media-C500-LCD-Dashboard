from pathlib import Path
import yaml

def load_config(path="/etc/polywell-c500/dashboard.yml"):
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("configuration root must be a mapping")
    return data
