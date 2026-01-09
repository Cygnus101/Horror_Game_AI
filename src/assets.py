"""Asset loader with placeholders."""

import os

import pygame

from .constants import (
    ASSET_BG_BATH,
    ASSET_BG_LIVING,
    ASSET_DEAD_DOG,
    ASSET_DOG,
    ASSET_GHOST,
    ASSET_GHOST_RED,
    ASSET_PLAYER,
    ASSET_TENTACLE,
)


def resolve_path(asset_root, rel_path):
    primary = os.path.join(asset_root, rel_path)
    if os.path.exists(primary):
        return primary
    # Fallback to alternate folder names if present
    alt = rel_path.replace("backgrounds/", "room_backgrounds/").replace("sprites/", "simple_pixel_sprites_centered_v2/")
    alt_path = os.path.join(asset_root, alt)
    if os.path.exists(alt_path):
        return alt_path
    return primary


def load_image(asset_root, rel_path, size=None):
    path = resolve_path(asset_root, rel_path)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    # Placeholder
    if size is None:
        size = (64, 64)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill((60, 60, 80, 180))
    pygame.draw.rect(surf, (200, 80, 80), surf.get_rect(), 2)
    return surf


def load_assets(asset_root):
    return {
        "bg_living": load_image(asset_root, ASSET_BG_LIVING, (960, 540)),
        "bg_bath": load_image(asset_root, ASSET_BG_BATH, (960, 540)),
        "player": load_image(asset_root, ASSET_PLAYER),
        "dog": load_image(asset_root, ASSET_DOG),
        "dead_dog": load_image(asset_root, ASSET_DEAD_DOG),
        "ghost": load_image(asset_root, ASSET_GHOST),
        "ghost_red": load_image(asset_root, ASSET_GHOST_RED),
        "tentacle": load_image(asset_root, ASSET_TENTACLE),
    }
