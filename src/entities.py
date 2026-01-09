"""Entity classes."""

import math
import random

import pygame

from .config import PLAYER_SIZE


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.rect.center = (x, y)
        self.speed = 190
        self.moving = False

    def move(self, dx, dy, bounds, dt):
        if dx == 0 and dy == 0:
            self.moving = False
            return
        self.moving = True
        step_x = dx * self.speed * dt
        step_y = dy * self.speed * dt
        self.rect.x += step_x
        self.rect.y += step_y
        # Keep inside bounds
        if self.rect.left < bounds.left:
            self.rect.left = bounds.left
        if self.rect.right > bounds.right:
            self.rect.right = bounds.right
        if self.rect.top < bounds.top:
            self.rect.top = bounds.top
        if self.rect.bottom > bounds.bottom:
            self.rect.bottom = bounds.bottom


class Monster:
    def __init__(self, x, y, kind="dead_girl", real=True):
        self.x = x
        self.y = y
        self.kind = kind
        self.real = real
        self.speed = 70 if kind == "dead_girl" else 90
        if not real:
            self.speed = 60
        self.alpha = 120 if not real else 255
        self.jitter = 2 if not real else 0
        self.life = 16.0 if real else 10.0

    def update(self, dt, target, blocked=False):
        if blocked:
            self.life -= dt * 0.7
            return
        tx, ty = target
        angle = math.atan2(ty - self.y, tx - self.x)
        self.x += math.cos(angle) * self.speed * dt
        self.y += math.sin(angle) * self.speed * dt
        self.life -= dt

    def rect(self):
        return pygame.Rect(int(self.x - 16), int(self.y - 16), 32, 32)

    def jittered_pos(self):
        if self.jitter:
            return self.x + random.randint(-2, 2), self.y + random.randint(-2, 2)
        return self.x, self.y


class Interactable:
    def __init__(self, name, rect, prompt):
        self.name = name
        self.rect = rect
        self.prompt = prompt

    def near(self, player_rect):
        return self.rect.colliderect(player_rect.inflate(40, 40))
