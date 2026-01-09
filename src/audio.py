"""Procedural audio helpers."""

import array
import math

import pygame


def make_beep(freq=520, duration=0.25, volume=0.4, sample_rate=44100):
    length = int(sample_rate * duration)
    buf = array.array("h")
    amp = int(32767 * volume)
    for i in range(length):
        t = i / sample_rate
        buf.append(int(amp * math.sin(2 * math.pi * freq * t)))
    return pygame.mixer.Sound(buffer=buf.tobytes())
