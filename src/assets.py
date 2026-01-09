"""Asset generation and loading."""

import os
import random

import pygame

from .config import (
    ASSET_DEAD_GIRL,
    ASSET_DOOR,
    ASSET_FAN,
    ASSET_HALLUCINATION,
    ASSET_JUMPSCARE_GIRL,
    ASSET_JUMPSCARE_TENTACLE,
    ASSET_MIRROR,
    ASSET_PLAYER,
    ASSET_SINK,
    ASSET_TENTACLE,
    ASSET_TV,
    ASSET_VENT,
    ASSET_WINDOW,
    WIDTH,
    HEIGHT,
)

ASSET_LIST = [
    ASSET_PLAYER,
    ASSET_DEAD_GIRL,
    ASSET_TENTACLE,
    ASSET_HALLUCINATION,
    ASSET_TV,
    ASSET_FAN,
    ASSET_DOOR,
    ASSET_WINDOW,
    ASSET_VENT,
    ASSET_MIRROR,
    ASSET_SINK,
    ASSET_JUMPSCARE_GIRL,
    ASSET_JUMPSCARE_TENTACLE,
]


def asset_path(root, name):
    return os.path.join(root, name)


def ensure_assets(asset_root):
    os.makedirs(asset_root, exist_ok=True)
    missing = [name for name in ASSET_LIST if not os.path.exists(asset_path(asset_root, name))]
    if not missing:
        return
    for name in missing:
        surface = build_asset(name)
        pygame.image.save(surface, asset_path(asset_root, name))


def build_asset(name):
    if name == ASSET_PLAYER:
        return build_player()
    if name == ASSET_DEAD_GIRL:
        return build_dead_girl()
    if name == ASSET_TENTACLE:
        return build_tentacle()
    if name == ASSET_HALLUCINATION:
        return build_hallucination()
    if name == ASSET_TV:
        return build_tv()
    if name == ASSET_FAN:
        return build_fan()
    if name == ASSET_DOOR:
        return build_door()
    if name == ASSET_WINDOW:
        return build_window()
    if name == ASSET_VENT:
        return build_vent()
    if name == ASSET_MIRROR:
        return build_mirror()
    if name == ASSET_SINK:
        return build_sink()
    if name == ASSET_JUMPSCARE_GIRL:
        return build_jumpscare_girl()
    if name == ASSET_JUMPSCARE_TENTACLE:
        return build_jumpscare_tentacle()
    return pygame.Surface((32, 32))


def build_player():
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(surf, (200, 200, 210), (8, 6, 16, 20))
    pygame.draw.rect(surf, (60, 60, 70), (8, 6, 16, 20), 2)
    pygame.draw.circle(surf, (220, 210, 200), (16, 8), 6)
    pygame.draw.circle(surf, (30, 30, 30), (13, 8), 2)
    pygame.draw.circle(surf, (30, 30, 30), (19, 8), 2)
    return surf


def build_dead_girl():
    surf = pygame.Surface((38, 38), pygame.SRCALPHA)
    pygame.draw.circle(surf, (210, 210, 220), (19, 16), 12)
    pygame.draw.rect(surf, (60, 60, 70), (8, 22, 22, 12))
    pygame.draw.circle(surf, (20, 20, 20), (15, 14), 3)
    pygame.draw.circle(surf, (20, 20, 20), (23, 14), 3)
    pygame.draw.line(surf, (150, 30, 30), (12, 28), (26, 28), 2)
    for x in range(8, 30, 4):
        pygame.draw.line(surf, (50, 50, 60), (x, 4), (x + 2, 20), 2)
    return surf


def build_tentacle():
    surf = pygame.Surface((42, 42), pygame.SRCALPHA)
    pygame.draw.circle(surf, (80, 20, 30), (21, 21), 16)
    for i in range(6):
        angle = i * 60
        dx = int(12 * random.uniform(0.7, 1.1))
        dy = int(12 * random.uniform(0.7, 1.1))
        pygame.draw.line(surf, (130, 30, 40), (21, 21), (21 + dx, 21 + dy), 4)
    pygame.draw.circle(surf, (240, 100, 100), (18, 18), 4)
    pygame.draw.circle(surf, (240, 100, 100), (26, 18), 4)
    return surf


def build_hallucination():
    surf = pygame.Surface((36, 36), pygame.SRCALPHA)
    pygame.draw.circle(surf, (160, 80, 170, 140), (18, 16), 11)
    pygame.draw.rect(surf, (120, 60, 130, 120), (10, 22, 16, 10))
    pygame.draw.circle(surf, (20, 20, 20, 120), (14, 15), 2)
    pygame.draw.circle(surf, (20, 20, 20, 120), (22, 15), 2)
    return surf


def build_tv():
    surf = pygame.Surface((48, 32), pygame.SRCALPHA)
    pygame.draw.rect(surf, (50, 60, 70), (2, 2, 44, 24))
    pygame.draw.rect(surf, (120, 120, 140), (6, 6, 36, 16))
    pygame.draw.rect(surf, (30, 30, 35), (0, 26, 48, 6))
    return surf


def build_fan():
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(surf, (70, 90, 110), (16, 16), 14)
    for angle in range(0, 360, 90):
        pygame.draw.line(surf, (160, 170, 180), (16, 16), (16 + int(12 * pygame.math.Vector2(1, 0).rotate(angle).x), 16 + int(12 * pygame.math.Vector2(1, 0).rotate(angle).y)), 3)
    pygame.draw.circle(surf, (40, 40, 50), (16, 16), 4)
    return surf


def build_door():
    surf = pygame.Surface((26, 60), pygame.SRCALPHA)
    pygame.draw.rect(surf, (90, 60, 40), (0, 0, 26, 60))
    pygame.draw.rect(surf, (70, 40, 20), (3, 3, 20, 54), 2)
    pygame.draw.circle(surf, (180, 180, 180), (20, 30), 2)
    return surf


def build_window():
    surf = pygame.Surface((44, 26), pygame.SRCALPHA)
    pygame.draw.rect(surf, (70, 90, 110), (0, 0, 44, 26))
    pygame.draw.rect(surf, (120, 150, 170), (4, 4, 16, 8))
    pygame.draw.rect(surf, (120, 150, 170), (24, 4, 16, 8))
    pygame.draw.rect(surf, (120, 150, 170), (4, 14, 16, 8))
    pygame.draw.rect(surf, (120, 150, 170), (24, 14, 16, 8))
    return surf


def build_vent():
    surf = pygame.Surface((36, 18), pygame.SRCALPHA)
    pygame.draw.rect(surf, (60, 60, 70), (0, 0, 36, 18))
    for i in range(4, 32, 6):
        pygame.draw.line(surf, (30, 30, 40), (i, 4), (i, 14), 2)
    return surf


def build_mirror():
    surf = pygame.Surface((36, 46), pygame.SRCALPHA)
    pygame.draw.rect(surf, (90, 90, 100), (0, 0, 36, 46))
    pygame.draw.rect(surf, (170, 180, 200), (4, 4, 28, 38))
    pygame.draw.rect(surf, (60, 60, 70), (0, 0, 36, 46), 2)
    return surf


def build_sink():
    surf = pygame.Surface((40, 24), pygame.SRCALPHA)
    pygame.draw.rect(surf, (90, 110, 130), (2, 6, 36, 16))
    pygame.draw.rect(surf, (140, 160, 180), (6, 8, 28, 8))
    pygame.draw.rect(surf, (60, 60, 70), (16, 0, 8, 6))
    return surf


def build_jumpscare_girl():
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill((15, 10, 10))
    pygame.draw.circle(surf, (220, 220, 230), (WIDTH // 2, HEIGHT // 2 - 20), 140)
    pygame.draw.circle(surf, (20, 20, 20), (WIDTH // 2 - 40, HEIGHT // 2 - 40), 25)
    pygame.draw.circle(surf, (20, 20, 20), (WIDTH // 2 + 40, HEIGHT // 2 - 40), 25)
    pygame.draw.rect(surf, (120, 20, 20), (WIDTH // 2 - 70, HEIGHT // 2 + 40, 140, 40))
    for _ in range(80):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        surf.set_at((x, y), (70, 20, 20))
    return surf


def build_jumpscare_tentacle():
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill((8, 8, 15))
    pygame.draw.circle(surf, (120, 30, 40), (WIDTH // 2, HEIGHT // 2), 160)
    for i in range(12):
        angle = i * 30
        dx = int(220 * pygame.math.Vector2(1, 0).rotate(angle).x)
        dy = int(220 * pygame.math.Vector2(1, 0).rotate(angle).y)
        pygame.draw.line(surf, (150, 40, 50), (WIDTH // 2, HEIGHT // 2), (WIDTH // 2 + dx, HEIGHT // 2 + dy), 16)
    pygame.draw.circle(surf, (240, 80, 90), (WIDTH // 2 - 60, HEIGHT // 2 - 40), 24)
    pygame.draw.circle(surf, (240, 80, 90), (WIDTH // 2 + 60, HEIGHT // 2 - 40), 24)
    for _ in range(120):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        surf.set_at((x, y), (30, 10, 40))
    return surf


def load_image(asset_root, name):
    return pygame.image.load(asset_path(asset_root, name)).convert_alpha()
