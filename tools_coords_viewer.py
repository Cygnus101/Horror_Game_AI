#!/usr/bin/env python3
"""Simple image coordinate viewer for backgrounds.

Usage:
  python tools_coords_viewer.py assets/backgrounds/living_room.png
"""

import sys
import pygame


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools_coords_viewer.py <image_path>")
        return
    img_path = sys.argv[1]
    pygame.init()
    img = pygame.image.load(img_path).convert_alpha()
    screen = pygame.display.set_mode(img.get_size())
    pygame.display.set_caption("Coordinate Viewer")
    font = pygame.font.SysFont("consolas", 16)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.blit(img, (0, 0))
        mx, my = pygame.mouse.get_pos()
        text = font.render(f"x={mx} y={my}", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
