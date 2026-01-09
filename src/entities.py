"""Entity definitions."""

import math
import random

import pygame

from .constants import AXE_RANGE, DOG_SPEED, GHOST_SPEED, HALLUCINATION_SPEED, PLAYER_SIZE, PLAYER_SPEED, TENTACLE_SPEED


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.rect.center = (x, y)
        self.speed = PLAYER_SPEED
        self.moving = False

    def move(self, dx, dy, bounds, obstacles, dt):
        self.moving = dx != 0 or dy != 0
        if not self.moving:
            return
        step_x = dx * self.speed * dt
        step_y = dy * self.speed * dt
        self.rect.x += step_x
        for obs in obstacles:
            if self.rect.colliderect(obs):
                if step_x > 0:
                    self.rect.right = obs.left
                elif step_x < 0:
                    self.rect.left = obs.right
        self.rect.y += step_y
        for obs in obstacles:
            if self.rect.colliderect(obs):
                if step_y > 0:
                    self.rect.bottom = obs.top
                elif step_y < 0:
                    self.rect.top = obs.bottom
        # Clamp to bounds
        if self.rect.left < bounds.left:
            self.rect.left = bounds.left
        if self.rect.right > bounds.right:
            self.rect.right = bounds.right
        if self.rect.top < bounds.top:
            self.rect.top = bounds.top
        if self.rect.bottom > bounds.bottom:
            self.rect.bottom = bounds.bottom


class Dog:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 22, 18)
        self.rect.center = (x, y)
        self.alive = True
        self.speed = DOG_SPEED
        self.bark_timer = 0.0

    def update(self, dt, target_pos):
        if not self.alive:
            return
        self.bark_timer = max(0.0, self.bark_timer - dt)
        tx, ty = target_pos
        dx = tx - self.rect.centerx
        dy = ty - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > 40:
            dx /= dist
            dy /= dist
            self.rect.x += dx * self.speed * dt
            self.rect.y += dy * self.speed * dt

    def bark(self):
        self.bark_timer = 0.6


class Ghost:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = GHOST_SPEED
        self.alpha = 255
        self.jitter = False
        self.attack_timer = 0.0
        self.visible = True
        self.banished = False
        self.banish_timer = 0.0

    def update(self, dt, target_pos):
        if self.banished:
            self.banish_timer -= dt
            if self.banish_timer <= 0:
                self.banished = False
            return
        self.attack_timer += dt
        tx, ty = target_pos
        if random.random() < 0.1:
            return
        angle = math.atan2(ty - self.y, tx - self.x)
        self.x += math.cos(angle) * self.speed * dt
        self.y += math.sin(angle) * self.speed * dt

    def rect(self):
        return pygame.Rect(int(self.x - 16), int(self.y - 24), 32, 48)

    def banish(self, duration):
        self.banished = True
        self.banish_timer = duration
        self.attack_timer = 0.0


class Hallucination:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = HALLUCINATION_SPEED
        self.life = 12.0

    def update(self, dt, target_pos):
        self.life -= dt
        tx, ty = target_pos
        angle = math.atan2(ty - self.y, tx - self.x)
        self.x += math.cos(angle) * self.speed * dt
        self.y += math.sin(angle) * self.speed * dt

    def rect(self):
        return pygame.Rect(int(self.x - 16), int(self.y - 24), 32, 48)


class Tentacle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = TENTACLE_SPEED

    def update(self, dt, target_pos):
        tx, ty = target_pos
        angle = math.atan2(ty - self.y, tx - self.x)
        self.x += math.cos(angle) * self.speed * dt
        self.y += math.sin(angle) * self.speed * dt

    def rect(self):
        return pygame.Rect(int(self.x - 24), int(self.y - 24), 48, 48)

    def in_range(self, player_pos):
        return distance((self.x, self.y), player_pos) <= AXE_RANGE
