"""HUD and rendering helpers."""

import random

import pygame

from .constants import BLUE, GREEN, HEIGHT, LIGHT_GRAY, PURPLE, RED, WHITE, WIDTH, YELLOW


def draw_bar(surf, x, y, w, h, value, max_value, color, label, font):
    pygame.draw.rect(surf, (25, 25, 30), (x, y, w, h))
    fill = int((value / max_value) * w)
    pygame.draw.rect(surf, color, (x, y, fill, h))
    pygame.draw.rect(surf, (10, 10, 12), (x, y, w, h), 2)
    text = font.render(f"{label}: {int(value)}", True, WHITE)
    surf.blit(text, (x + 6, y + 2))


class UI:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("consolas", 18)
        self.big = pygame.font.SysFont("consolas", 30, bold=True)

    def draw_hud(self, state):
        draw_bar(self.screen, 16, 16, 220, 20, state.sanity, 100, PURPLE, "Sanity", self.font)
        draw_bar(self.screen, 16, 42, 220, 20, state.hunger, 100, GREEN, "Hunger", self.font)
        draw_bar(self.screen, 16, 68, 220, 20, state.thirst, 100, BLUE, "Thirst", self.font)
        draw_bar(self.screen, 16, 94, 220, 14, state.torch_battery, 100, YELLOW, "Torch", self.font)

        room = self.font.render(f"Room: {state.current_room}", True, WHITE)
        self.screen.blit(room, (WIDTH - 200, 16))

        clock = self.font.render(
            f"Day {state.day} Hour {state.hour:02d} ({state.phase})", True, WHITE
        )
        self.screen.blit(clock, (WIDTH - 260, 40))

        inv = self.font.render(
            f"[1] Food {state.inventory['food']}  [2] Water {state.inventory['water']}  [3] Liquid {state.inventory['liquid']}",
            True,
            WHITE,
        )
        self.screen.blit(inv, (16, HEIGHT - 28))

        if state.has_axe:
            axe = self.font.render("Axe ready (SPACE)", True, WHITE)
            self.screen.blit(axe, (WIDTH - 200, 64))

        if state.messages:
            y = HEIGHT - 110
            for msg in state.messages:
                text = self.font.render(msg, True, LIGHT_GRAY)
                self.screen.blit(text, (16, y))
                y += 18

    def draw_prompt(self, text):
        if not text:
            return
        img = self.font.render(text, True, WHITE)
        self.screen.blit(img, (WIDTH / 2 - img.get_width() / 2, HEIGHT - 90))

    def draw_intro(self):
        self.screen.fill((10, 10, 12))
        lines = [
            "Horror House Survival",
            "Survive five days inside the house.",
            "Move: WASD/Arrows  Interact: E  Switch Room: TAB",
            "TV: T  Fan: F  Ground: B  Torch: L or RMB",
            "Use Items: 1-3  Axe: SPACE (Day 5)",
            "Press Enter to start.",
        ]
        for i, line in enumerate(lines):
            img = self.big.render(line, True, WHITE)
            self.screen.blit(img, (WIDTH / 2 - img.get_width() / 2, 120 + i * 42))

    def draw_effects(self, state):
        if state.sanity < 35:
            strength = (35 - state.sanity) / 35
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, int(120 * strength)), overlay.get_rect(), 20)
            self.screen.blit(overlay, (0, 0))
        if state.hallucination_active:
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

    def draw_death(self, state, monster_surface, monster_name):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((200, 20, 20, 80))
        self.screen.blit(overlay, (0, 0))
        if monster_surface:
            scaled = pygame.transform.smoothscale(monster_surface, (240, 360))
            self.screen.blit(scaled, (WIDTH // 2 - 120, HEIGHT // 2 - 200))
        title = self.big.render(monster_name, True, WHITE)
        self.screen.blit(title, (WIDTH / 2 - title.get_width() / 2, 20))

    def draw_summary(self, lines):
        y = HEIGHT / 2 + 120
        for line in lines:
            text = self.font.render(line, True, WHITE)
            self.screen.blit(text, (WIDTH / 2 - text.get_width() / 2, y))
            y += 18
        sub = self.font.render("Press R to restart or ESC to quit.", True, WHITE)
        self.screen.blit(sub, (WIDTH / 2 - sub.get_width() / 2, HEIGHT - 60))
