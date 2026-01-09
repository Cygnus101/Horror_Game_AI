"""Systems for time, meters, noise, and spawning."""

import random

from .constants import (
    BREACH_BASE,
    BREACH_CURSE_BONUS,
    DAY_HOURS,
    HALLUCINATION_BASE,
    HOUR_SECONDS,
    HOURS_PER_DAY,
    MORNING_HOURS,
)


class TimeSystem:
    def __init__(self):
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    def day(self):
        return int(self.time // (HOUR_SECONDS * HOURS_PER_DAY)) + 1

    def hour(self):
        hour_in_day = int((self.time % (HOUR_SECONDS * HOURS_PER_DAY)) // HOUR_SECONDS) + 1
        return hour_in_day

    def phase(self):
        hour = self.hour()
        if hour in MORNING_HOURS:
            return "morning"
        if hour in DAY_HOURS:
            return "day"
        return "night"


class NoiseSystem:
    def __init__(self):
        self.value = 0.0
        self.peak = 0.0

    def add(self, amount):
        self.value = min(100, self.value + amount)
        self.peak = max(self.peak, self.value)

    def decay(self, amount):
        self.value = max(0.0, self.value - amount)


class SpawnSystem:
    def __init__(self):
        self.ghost_timer = 0.0
        self.hallucination_timer = 0.0
        self.tentacle_ready = False

    def update_ghost(self, dt, day, room):
        self.ghost_timer += dt
        if self.ghost_timer < 10.0:
            return False
        self.ghost_timer = 0.0
        if day <= 2 and room != "Living Room":
            return False
        base = 0.2 if day <= 2 else 0.35
        return random.random() < base

    def update_hallucination(self, dt, sanity, room):
        self.hallucination_timer += dt
        if self.hallucination_timer < 6.0:
            return False
        self.hallucination_timer = 0.0
        if room != "Living Room":
            return False
        chance = HALLUCINATION_BASE + (1.0 - sanity / 100.0) * 0.2
        return random.random() < chance

    def breach_roll(self, curse_active):
        chance = BREACH_BASE + (BREACH_CURSE_BONUS if curse_active else 0)
        return random.random() < chance
