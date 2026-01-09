"""Rendering and HUD."""

import random

import pygame

from .config import (
    BLACK,
    BLUE,
    GREEN,
    HEIGHT,
    LIGHT_GRAY,
    PURPLE,
    RED,
    WHITE,
    WIDTH,
    YELLOW,
)


def draw_bar(surf, x, y, w, h, value, max_value, color, label, font):
    pygame.draw.rect(surf, (25, 25, 30), (x, y, w, h))
    fill = int((value / max_value) * w)
    pygame.draw.rect(surf, color, (x, y, fill, h))
    pygame.draw.rect(surf, (10, 10, 12), (x, y, w, h), 2)
    text = font.render(f"{label}: {int(value)}", True, WHITE)
    surf.blit(text, (x + 6, y + 2))


class UI:
    def __init__(self, screen, assets):
        self.screen = screen
        self.assets = assets
        self.font = pygame.font.SysFont("consolas", 18)
        self.big = pygame.font.SysFont("consolas", 30, bold=True)

    def draw_room(self, state):
        screen = self.screen
        screen.fill((18, 18, 22))
        pygame.draw.rect(screen, (35, 35, 40), state.living_rect)
        pygame.draw.rect(screen, (28, 28, 34), state.bath_rect)
        pygame.draw.rect(screen, (20, 20, 24), state.living_rect, 4)
        pygame.draw.rect(screen, (20, 20, 24), state.bath_rect, 4)
        self.draw_label("Living Room", state.living_rect.centerx - 60, state.living_rect.y - 22)
        self.draw_label("Bathroom", state.bath_rect.centerx - 40, state.bath_rect.y - 22)

    def draw_label(self, text, x, y):
        img = self.font.render(text, True, LIGHT_GRAY)
        self.screen.blit(img, (x, y))

    def draw_objects(self, state):
        screen = self.screen
        for obj in state.objects:
            if obj["room"] != state.current_room:
                continue
            sprite = self.assets.get(obj["sprite"])
            if sprite:
                screen.blit(sprite, obj["rect"].topleft)
            else:
                pygame.draw.rect(screen, (90, 90, 110), obj["rect"])
        if state.env_cue:
            cue = state.env_cue
            if cue["room"] == state.current_room:
                if cue["type"] == "door":
                    pygame.draw.line(screen, (150, 70, 60), cue["rect"].topleft, cue["rect"].bottomright, 3)
                elif cue["type"] == "window":
                    pygame.draw.rect(screen, (180, 200, 210), cue["rect"].inflate(6, 6), 2)
                elif cue["type"] == "vent":
                    pygame.draw.rect(screen, (120, 120, 140), cue["rect"].inflate(4, 4), 2)

    def draw_player(self, player_sprite, player_rect):
        self.screen.blit(player_sprite, player_rect.topleft)

    def draw_monster(self, monster, sprite, shadow=True, fan_mask=False):
        rect = monster.rect()
        if shadow and monster.real and not fan_mask:
            shadow_surf = pygame.Surface((44, 22), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (20, 20, 20, 150), (0, 0, 44, 22))
            self.screen.blit(shadow_surf, (rect.centerx - 22, rect.bottom - 6))
        if monster.real or not fan_mask:
            surface = sprite.copy()
            surface.set_alpha(monster.alpha)
            self.screen.blit(surface, rect.topleft)
        else:
            surface = sprite.copy()
            surface.set_alpha(80)
            self.screen.blit(surface, rect.topleft)

    def draw_hud(self, state):
        draw_bar(self.screen, 16, 16, 220, 20, state.sanity, 100, PURPLE, "Sanity", self.font)
        draw_bar(self.screen, 16, 42, 220, 20, state.hunger, 100, GREEN, "Hunger", self.font)
        draw_bar(self.screen, 16, 68, 220, 20, state.thirst, 100, BLUE, "Thirst", self.font)
        draw_bar(self.screen, 16, 94, 220, 14, state.noise, 100, YELLOW, "Noise", self.font)
        draw_bar(self.screen, 16, 112, 220, 14, state.dread, 100, RED, "Dread", self.font)

        inv = self.font.render(
            f"[1] Food {state.inventory['food']}  [2] Water {state.inventory['water']}  [3] Liquid {state.inventory['liquid']}",
            True,
            WHITE,
        )
        self.screen.blit(inv, (16, HEIGHT - 28))

        room = self.font.render(f"Room: {state.current_room}", True, WHITE)
        self.screen.blit(room, (WIDTH - 200, 16))

        timer = self.font.render(
            f"Night {state.current_night()} / {state.win_nights}  Time {int(state.time)}s",
            True,
            WHITE,
        )
        self.screen.blit(timer, (WIDTH - 280, 40))

        if state.msg_log.lines:
            y = HEIGHT - 110
            for line in state.msg_log.lines:
                text = self.font.render(line, True, LIGHT_GRAY)
                self.screen.blit(text, (16, y))
                y += 18

    def draw_prompt(self, prompt):
        if not prompt:
            return
        img = self.font.render(prompt, True, WHITE)
        self.screen.blit(img, (WIDTH / 2 - img.get_width() / 2, HEIGHT - 90))

    def draw_effects(self, state):
        if state.sanity < 35:
            strength = (35 - state.sanity) / 35
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, int(120 * strength)), overlay.get_rect(), 20)
            self.screen.blit(overlay, (0, 0))
        if state.hallucinating:
            noise = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for _ in range(40):
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                w = random.randint(20, 80)
                h = random.randint(2, 6)
                pygame.draw.rect(noise, (120, 80, 140, 30), (x, y, w, h))
            self.screen.blit(noise, (0, 0))
        if state.curse_timer > 0:
            glitch = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for _ in range(18):
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                w = random.randint(40, 120)
                h = random.randint(4, 10)
                pygame.draw.rect(glitch, (150, 100, 140, 40), (x, y, w, h))
            self.screen.blit(glitch, (0, 0))

    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        text = self.big.render("Paused - Press P to Resume", True, WHITE)
        self.screen.blit(text, (WIDTH / 2 - text.get_width() / 2, HEIGHT / 2 - 20))

    def draw_end(self, text, summary):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        msg = self.big.render(text, True, WHITE)
        self.screen.blit(msg, (WIDTH / 2 - msg.get_width() / 2, HEIGHT / 2 - 60))
        y = HEIGHT / 2 - 10
        for line in summary:
            sub = self.font.render(line, True, WHITE)
            self.screen.blit(sub, (WIDTH / 2 - sub.get_width() / 2, y))
            y += 18
        sub = self.font.render("Press R to restart or Q to quit.", True, WHITE)
        self.screen.blit(sub, (WIDTH / 2 - sub.get_width() / 2, HEIGHT / 2 + 70))

    def draw_jumpscare(self, img, monster_name):
        self.screen.blit(img, (0, 0))
        title = self.big.render(monster_name, True, WHITE)
        self.screen.blit(title, (WIDTH / 2 - title.get_width() / 2, 30))
