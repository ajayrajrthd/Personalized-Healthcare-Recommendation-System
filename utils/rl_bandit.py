from dataclasses import dataclass
import random
from .db import bandit_update

ALGORITHMS = ["content", "collab", "hybrid", "graph"]

@dataclass
class EpsilonGreedy:
    epsilon: float = 0.2

    def choose(self) -> str:
        if random.random() < self.epsilon:
            return random.choice(ALGORITHMS)
        # Exploit: simple heuristic order
        return "hybrid"

    def update(self, algorithm: str, clicked: bool):
        bandit_update(algorithm, clicked)
