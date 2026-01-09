"""Gameplay systems (messages, TV, breaches, hallucinations)."""

import random

from .config import (
    BREACH_BASE,
    BREACH_CURSE_BONUS,
    BREACH_FAN_BONUS,
    BREACH_MOVE_BONUS,
    BREACH_TV_BONUS,
    HALLUCINATION_BASE,
)


class MessageLog:
    def __init__(self, limit=5):
        self.limit = limit
        self.lines = []

    def add(self, text):
        self.lines.append(text)
        if len(self.lines) > self.limit:
            self.lines.pop(0)


class TVSystem:
    def __init__(self):
        self.on = False
        self.timer = 0.0
        self.next_broadcast = 9.0
        self.dread_timer = 0.0
        self.truth_bias = 0.75

    def set_on(self, state):
        self.on = state

    def update(self, dt, context):
        if not self.on:
            return []
        self.timer += dt
        events = []
        if self.timer >= self.next_broadcast:
            self.timer = 0.0
            self.next_broadcast = random.uniform(8.0, 14.0)
            events.append(self.broadcast(context))
            if random.random() < 0.2:
                self.dread_timer = 6.0
                events.append("The broadcast spikes with static.")
        if self.dread_timer > 0:
            self.dread_timer -= dt
        return [e for e in events if e]

    def broadcast(self, context):
        truthful = random.random() < self.truth_bias
        hints = []
        if context["refill_soon"]:
            hints.append(("RESOURCE", "Resource refill soon."))
        if context["breach_rising"]:
            hints.append(("BREACH", "Breach probability rising."))
        if context["real_near"]:
            hints.append(("REAL", "Real presence near."))
        if not hints:
            hints.append(("STATIC", "Signal drops to blue noise."))
        hint = random.choice(hints)
        if truthful:
            return f"TV: {hint[1]}"
        return f"TV: {random.choice(['All clear.', 'Static is harmless.', 'Stay in the living room.', 'No breach expected.'])}"


class BreachSystem:
    def __init__(self):
        self.timer = 0.0

    def update(self, dt, context):
        self.timer += dt
        if self.timer < 1.0:
            return False
        self.timer = 0.0
        base = BREACH_BASE
        if context["tv_on"]:
            base += BREACH_TV_BONUS
        if context["fan_on"]:
            base += BREACH_FAN_BONUS
        if context["moving"]:
            base += BREACH_MOVE_BONUS
        if context["curse"]:
            base += BREACH_CURSE_BONUS
        roll = random.random() < base
        return roll


class HallucinationSystem:
    def __init__(self):
        self.active = False
        self.timer = 0.0

    def update(self, dt, sanity):
        self.timer += dt
        if self.active:
            return False
        if self.timer < 1.5:
            return False
        self.timer = 0.0
        chance = HALLUCINATION_BASE + (1.0 - sanity / 100.0) * 0.14
        return random.random() < chance
