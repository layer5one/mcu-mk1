import random

TOOL_METADATA = {
    "name": "random_number",
    "title": "Random Number",
    "description": "Generate a random integer between min and max"
}

def run(min: int = 0, max: int = 100):
    return {"value": random.randint(min, max)}
