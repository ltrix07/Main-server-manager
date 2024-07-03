import json


def read_json(file_path: str):
    with open(file_path, 'r') as f:
        return json.load(f)
