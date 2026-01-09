"""Simple procedural audio for jumpscares."""

import math
import array

import pygame


def make_beep(freq=440, duration=0.6, volume=0.5, sample_rate=44100):
    length = int(sample_rate * duration)
    buf = array.array("h")
    amp = int(32767 * volume)
    for i in range(length):
        t = i / sample_rate
        val = int(amp * math.sin(2 * math.pi * freq * t))
        buf.append(val)
    return pygame.mixer.Sound(buffer=buf.tobytes())
