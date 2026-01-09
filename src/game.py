"""Main game loop and state."""

import math
import os
import random

import pygame

from .assets import load_assets
from .audio import make_beep
from .constants import (
    AXE_COOLDOWN,
    AXE_DAY,
    AXE_RANGE,
    DAY_SECONDS,
    FPS,
    GHOST_BANISH_TIME,
    GHOST_KILL_TIME,
    HEIGHT,
    HOUR_SECONDS,
    HUNGER_DRAIN_DAY,
    HUNGER_DRAIN_MORNING,
    HUNGER_DRAIN_NIGHT,
    METER_MAX,
    NOISE_DECAY,
    NOISE_FAN,
    NOISE_MOVE,
    NOISE_THRESHOLD_TENTACLE,
    NOISE_TORCH,
    NOISE_TV,
    PLAYER_SPEED,
    ROOM_BATH,
    ROOM_LIVING,
    SANITY_DRAIN_DAY,
    SANITY_DRAIN_MORNING,
    SANITY_DRAIN_NIGHT,
    STRANGE_LIQUID_COOLDOWN,
    STRANGE_LIQUID_CURSE,
    THIRST_DRAIN_DAY,
    THIRST_DRAIN_MORNING,
    THIRST_DRAIN_NIGHT,
    TV_OVERUSE_LIMIT,
    TV_OVERUSE_PENALTY,
    TV_SANITY_GAIN,
    WHITE,
    WIDTH,
)
from .entities import Dog, Ghost, Hallucination, Player, Tentacle, distance
from .systems import NoiseSystem, SpawnSystem, TimeSystem
from .ui import UI


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def in_cone(origin, target, direction, max_angle=40, max_distance=260):
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    dist = math.hypot(dx, dy)
    if dist > max_distance:
        return False
    if dist == 0:
        return True
    nx, ny = dx / dist, dy / dist
    dot = nx * direction[0] + ny * direction[1]
    angle = math.degrees(math.acos(clamp(dot, -1, 1)))
    return angle <= max_angle


class GameState:
    def __init__(self, asset_root):
        self.asset_root = asset_root
        self.assets = load_assets(asset_root)
        self.ui = UI(pygame.display.get_surface())

        self.current_room = ROOM_LIVING
        self.living_bounds = pygame.Rect(40, 40, 880, 460)
        self.bath_bounds = pygame.Rect(80, 80, 800, 420)
        self.doorway_y = (240, 320)

        self.obstacles = {
            ROOM_LIVING: [
                pygame.Rect(360, 220, 180, 80),
                pygame.Rect(120, 380, 160, 40),
            ],
            ROOM_BATH: [
                pygame.Rect(520, 160, 200, 80),
                pygame.Rect(150, 300, 200, 60),
            ],
        }

        self.interact_zones = {
            "TV": pygame.Rect(140, 160, 80, 40),
            "Fan": pygame.Rect(260, 180, 40, 40),
            "Door": pygame.Rect(60, 240, 40, 80),
            "Sink": pygame.Rect(200, 220, 80, 40),
            "Bathtub": pygame.Rect(540, 160, 160, 80),
            "Mirror": pygame.Rect(620, 220, 80, 60),
            "Stash": pygame.Rect(420, 360, 80, 40),
            "TopDoor": pygame.Rect(440, 70, 80, 40),
        }

        self.player = Player(self.living_bounds.centerx, self.living_bounds.centery)
        self.player.speed = PLAYER_SPEED
        self.player_dir = (1, 0)

        self.dog = Dog(self.player.rect.centerx - 40, self.player.rect.centery + 20)
        self.dog_dead = False

        self.ghost = None
        self.hallucination = None
        self.tentacle = None

        self.sanity = 75.0
        self.hunger = 70.0
        self.thirst = 70.0
        self.torch_battery = 100.0
        self.torch_on = False

        self.inventory = {"food": 3, "water": 2, "liquid": 1}
        self.liquid_uses = 0
        self.liquid_last = -100.0
        self.curse_timer = 0.0

        self.noise = NoiseSystem()
        self.spawn = SpawnSystem()
        self.time_system = TimeSystem()

        self.messages = []
        self.max_messages = 5

        self.tv_on = False
        self.fan_on = False
        self.tv_time = 0.0
        self.tv_overuse = 0.0

        self.dead = False
        self.death_cause = ""
        self.death_monster = ""
        self.noise_peak = 0.0
        self.win = False

        self.ghost_attack_timer = 0.0
        self.ghost_hint_timer = 0.0
        self.hallucination_active = False
        self.tv_broadcast_timer = 0.0
        self.refill_timer = random.uniform(90.0, 140.0)
        self.refill_soon = False
        self.grounding_last = -100.0
        self.grounding_history = []

        self.has_axe = False
        self.axe_cooldown = 0.0
        self.bark_sound = make_beep(620, 0.2, 0.5)
        self.tv_static_timer = 0.0
        self.stash_stock = 4

    @property
    def day(self):
        return self.time_system.day()

    @property
    def hour(self):
        return self.time_system.hour()

    @property
    def phase(self):
        return self.time_system.phase()

    def add_message(self, text):
        self.messages.append(text)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def room_bounds(self):
        return self.living_bounds if self.current_room == ROOM_LIVING else self.bath_bounds

    def current_obstacles(self):
        return self.obstacles[self.current_room]

    def switch_room(self):
        self.current_room = ROOM_BATH if self.current_room == ROOM_LIVING else ROOM_LIVING
        bounds = self.room_bounds()
        self.player.rect.center = (bounds.centerx, bounds.centery)
        self.add_message(f"Entered {self.current_room}.")

    def check_room_connection(self):
        if self.current_room == ROOM_LIVING:
            if self.player.rect.right >= self.living_bounds.right - 2:
                if self.doorway_y[0] <= self.player.rect.centery <= self.doorway_y[1]:
                    self.current_room = ROOM_BATH
                    self.player.rect.center = (self.bath_bounds.left + 10, self.player.rect.centery)
                    self.add_message("You slip into the bathroom.")
        else:
            if self.player.rect.left <= self.bath_bounds.left + 2:
                if self.doorway_y[0] <= self.player.rect.centery <= self.doorway_y[1]:
                    self.current_room = ROOM_LIVING
                    self.player.rect.center = (self.living_bounds.right - 10, self.player.rect.centery)
                    self.add_message("You step back into the living room.")

    def update(self, dt):
        if self.dead or self.win:
            return
        self.time_system.update(dt)
        self.check_room_connection()
        self.update_day_state()
        self.update_meters(dt)
        self.update_noise(dt)
        self.update_events(dt)
        self.update_tv(dt)
        self.update_enemies(dt)
        self.update_dog(dt)
        self.check_win()

    def update_day_state(self):
        if self.day > 2 and not self.dog_dead:
            self.dog_dead = True
            self.dog.alive = False
            self.add_message("A heavy silence... the dog is gone.")
        if self.day == AXE_DAY:
            self.has_axe = True

    def update_meters(self, dt):
        minute = dt / 60.0
        if self.phase == "morning":
            self.hunger = clamp(self.hunger - HUNGER_DRAIN_MORNING * minute, 0, 100)
            self.thirst = clamp(self.thirst - THIRST_DRAIN_MORNING * minute, 0, 100)
            self.sanity = clamp(self.sanity - SANITY_DRAIN_MORNING * minute, 0, 100)
        elif self.phase == "day":
            self.hunger = clamp(self.hunger - HUNGER_DRAIN_DAY * minute, 0, 100)
            self.thirst = clamp(self.thirst - THIRST_DRAIN_DAY * minute, 0, 100)
            self.sanity = clamp(self.sanity - SANITY_DRAIN_DAY * minute, 0, 100)
        else:
            self.hunger = clamp(self.hunger - HUNGER_DRAIN_NIGHT * minute, 0, 100)
            self.thirst = clamp(self.thirst - THIRST_DRAIN_NIGHT * minute, 0, 100)
            self.sanity = clamp(self.sanity - SANITY_DRAIN_NIGHT * minute, 0, 100)

        if self.tv_on:
            self.sanity = clamp(self.sanity + TV_SANITY_GAIN * minute, 0, 100)
            self.tv_time += dt
            self.tv_overuse += dt
            if self.tv_overuse > TV_OVERUSE_LIMIT and random.random() < 0.02:
                self.sanity = clamp(self.sanity - TV_OVERUSE_PENALTY, 0, 100)
                self.add_message("The TV hum digs into your skull.")
        else:
            self.tv_overuse = max(0.0, self.tv_overuse - dt * 0.5)

        if self.fan_on:
            self.sanity = clamp(self.sanity + 0.2 * minute, 0, 100)

        if self.torch_on:
            self.torch_battery = clamp(self.torch_battery - 7.0 * minute, 0, 100)
            if self.torch_battery <= 0:
                self.torch_on = False

        if self.ghost and not self.ghost.banished:
            self.sanity = clamp(self.sanity - 0.7 * minute, 0, 100)

        if self.hallucination:
            dist = distance(self.player.rect.center, (self.hallucination.x, self.hallucination.y))
            if dist < 90 and random.random() < 0.2:
                self.sanity = clamp(self.sanity - 2.0, 0, 100)

        if self.hunger <= 0:
            self.kill("Hunger")
        if self.thirst <= 0:
            self.kill("Thirst")
        if self.sanity <= 0:
            self.kill("Sanity")

    def update_noise(self, dt):
        minute = dt / 60.0
        if self.tv_on:
            self.noise.add(NOISE_TV * minute)
        if self.fan_on:
            self.noise.add(NOISE_FAN * minute)
        if self.player.moving:
            self.noise.add(NOISE_MOVE * minute)
        if self.torch_on:
            self.noise.add(NOISE_TORCH * minute)
        self.noise.decay(NOISE_DECAY * minute)
        self.noise_peak = self.noise.peak

        if self.noise.value >= NOISE_THRESHOLD_TENTACLE and not self.tentacle:
            self.spawn_tentacle()
            self.add_message("Something drops from above.")

    def update_events(self, dt):
        if self.curse_timer > 0:
            self.curse_timer -= dt
        if not self.ghost and self.spawn.update_ghost(dt, self.day, self.current_room):
            self.spawn_ghost()
        if not self.hallucination and self.spawn.update_hallucination(dt, self.sanity, self.current_room):
            self.spawn_hallucination()

        if self.phase == "night" and not self.tentacle and self.day >= 4:
            if random.random() < 0.01:
                self.spawn_tentacle()
        if self.liquid_uses >= 3 and not self.tentacle:
            if random.random() < 0.015:
                self.spawn_tentacle()
        self.refill_timer -= dt
        self.refill_soon = self.refill_timer < 20.0
        if self.refill_timer <= 0:
            if random.random() < 0.5:
                self.inventory["food"] += 1
                self.add_message("You find a hidden can nearby.")
            else:
                self.inventory["water"] += 1
                self.add_message("A bottle is left by the sink.")
            self.refill_timer = random.uniform(120.0, 200.0)

    def update_tv(self, dt):
        if not self.tv_on:
            self.tv_broadcast_timer = 0.0
            return
        self.tv_broadcast_timer += dt
        if self.tv_broadcast_timer < 8.0:
            return
        self.tv_broadcast_timer = 0.0
        truth_bias = 0.75 if self.curse_timer <= 0 else 0.45
        truthful = random.random() < truth_bias
        hints = []
        if self.refill_soon:
            hints.append("Resource refill soon.")
        if self.ghost or self.tentacle:
            hints.append("Breath of something nearby.")
        if self.phase == "night":
            hints.append("Breach probability rising.")
        if not hints:
            hints.append("Static drifts across the screen.")
        if truthful:
            self.add_message(f"TV: {random.choice(hints)}")
        else:
            self.add_message(
                f"TV: {random.choice(['All clear.', 'No breach expected.', 'Stay by the door.', 'Nothing out there.'])}"
            )
        if random.random() < 0.2:
            self.sanity = clamp(self.sanity - 6, 0, 100)
            self.add_message("The broadcast buzzes inside your head.")

    def update_enemies(self, dt):
        if self.ghost:
            self.ghost.update(dt, self.player.rect.center)
            if self.ghost.banished:
                return
            self.ghost_attack_timer += dt
            if self.ghost_attack_timer >= GHOST_KILL_TIME:
                self.kill("Monster", "Dead Girl")
            if self.torch_on and self.torch_hits(self.ghost.rect()):
                self.ghost.banish(GHOST_BANISH_TIME)
                self.ghost_attack_timer = 0.0
                self.add_message("The torch burns her away.")
            self.ghost_hint_timer = max(0.0, self.ghost_hint_timer - dt)
        if self.hallucination:
            self.hallucination.update(dt, self.player.rect.center)
            if self.hallucination.life <= 0:
                self.hallucination = None
                self.hallucination_active = False
        if self.tentacle:
            self.tentacle.update(dt, self.player.rect.center)
            if self.tentacle.rect().colliderect(self.player.rect):
                self.kill("Monster", "Tentacle Monster")

        if self.axe_cooldown > 0:
            self.axe_cooldown -= dt

    def update_dog(self, dt):
        if self.dog.alive:
            self.dog.update(dt, self.player.rect.center)

    def kill(self, cause, monster_name=""):
        self.dead = True
        self.death_cause = cause
        self.death_monster = monster_name

    def check_win(self):
        if self.time_system.time >= DAY_SECONDS * 5:
            self.win = True

    def time_breakdown(self):
        total = self.time_system.time
        day = self.time_system.day()
        hour = self.time_system.hour()
        minute = int((total % HOUR_SECONDS) / (HOUR_SECONDS / 60.0))
        return day, hour, minute

    def spawn_ghost(self):
        x = self.living_bounds.centerx if self.current_room == ROOM_LIVING else self.bath_bounds.centerx
        y = self.living_bounds.centery if self.current_room == ROOM_LIVING else self.bath_bounds.centery
        self.ghost = Ghost(x, y)
        self.ghost_attack_timer = 0.0
        if self.dog.alive:
            self.dog.bark()
            self.bark_sound.play()
            self.add_message("The dog barks at the air.")
        self.add_message("A girl appears in the corner of your eye.")

    def spawn_hallucination(self):
        self.hallucination = Hallucination(self.living_bounds.centerx - 160, self.living_bounds.centery)
        self.hallucination_active = True
        self.add_message("A hollow figure drifts near.")

    def spawn_tentacle(self):
        self.tentacle = Tentacle(self.living_bounds.right - 60, self.living_bounds.top + 60)

    def torch_hits(self, target_rect):
        origin = self.player.rect.center
        return in_cone(origin, target_rect.center, self.player_dir)

    def use_item(self, idx):
        if idx == 1 and self.inventory["food"] > 0:
            self.inventory["food"] -= 1
            self.hunger = clamp(self.hunger + 30, 0, 100)
            self.add_message("You eat food.")
        elif idx == 2 and self.inventory["water"] > 0:
            self.inventory["water"] -= 1
            self.thirst = clamp(self.thirst + 30, 0, 100)
            self.add_message("You drink water.")
        elif idx == 3 and self.inventory["liquid"] > 0:
            if self.time_system.time - self.liquid_last < STRANGE_LIQUID_COOLDOWN:
                self.add_message("Your body rejects more liquid.")
                return
            self.inventory["liquid"] -= 1
            self.liquid_last = self.time_system.time
            self.liquid_uses += 1
            self.curse_timer = STRANGE_LIQUID_CURSE
            self.hunger = clamp(self.hunger + 25, 0, 100)
            self.thirst = clamp(self.thirst + 25, 0, 100)
            self.sanity = clamp(self.sanity - 8, 0, 100)
            self.add_message("The liquid soothes your body, but twists your mind.")

    def axe_attack(self):
        if not self.has_axe or self.axe_cooldown > 0:
            return
        self.axe_cooldown = AXE_COOLDOWN
        if self.tentacle and self.tentacle.in_range(self.player.rect.center):
            self.tentacle = None
            self.add_message("You sever the tentacle.")

    def interact(self):
        if self.current_room == ROOM_LIVING and self.interact_zones["Door"].colliderect(self.player.rect):
            self.kill("Outside", "Outside")
            return
        if self.current_room == ROOM_LIVING and self.interact_zones["TopDoor"].colliderect(self.player.rect):
            self.current_room = ROOM_BATH
            self.player.rect.center = (self.bath_bounds.left + 40, self.player.rect.centery)
            self.add_message("You slip into the bathroom.")
            return
        if self.current_room == ROOM_LIVING and self.interact_zones["TV"].colliderect(self.player.rect):
            self.tv_on = not self.tv_on
            self.add_message("TV on." if self.tv_on else "TV off.")
            return
        if self.current_room == ROOM_LIVING and self.interact_zones["Fan"].colliderect(self.player.rect):
            self.fan_on = not self.fan_on
            self.add_message("Fan on." if self.fan_on else "Fan off.")
            return
        if self.current_room == ROOM_LIVING and self.interact_zones["Stash"].colliderect(self.player.rect):
            if self.stash_stock <= 0:
                self.add_message("The stash is empty.")
                return
            self.stash_stock -= 1
            if random.random() < 0.5:
                self.inventory["food"] += 1
                self.add_message("You find food.")
            else:
                self.inventory["water"] += 1
                self.add_message("You find water.")
            return
        if self.current_room == ROOM_BATH and self.interact_zones["Sink"].colliderect(self.player.rect):
            self.inventory["water"] += 1
            self.add_message("You fill a bottle.")

    def grounding(self):
        if self.current_room != ROOM_BATH:
            return
        if self.time_system.time - self.grounding_last < 6.0:
            self.add_message("You need a moment to steady yourself.")
            return
        self.grounding_last = self.time_system.time
        self.grounding_history = [t for t in self.grounding_history if self.time_system.time - t < 60.0]
        recent = len(self.grounding_history)
        self.grounding_history.append(self.time_system.time)
        factor = 1.0 / (1.0 + recent * 0.6)
        self.sanity = clamp(self.sanity + 14 * factor, 0, 100)
        self.thirst = clamp(self.thirst - 6 * (1.0 + recent * 0.4), 0, 100)
        if self.hallucination:
            self.hallucination = None
            self.hallucination_active = False
        if factor < 0.8:
            self.add_message("It isn't working as well...")
        else:
            self.add_message("You steady your breathing.")


class Game:
    def __init__(self, asset_root):
        self.state = GameState(asset_root)
        self.ui = self.state.ui
        self.intro = True

    def handle_input(self, event):
        state = self.state
        if event.type == pygame.KEYDOWN:
            if self.intro:
                if event.key == pygame.K_RETURN:
                    self.intro = False
                return
            if state.dead or state.win:
                if event.key == pygame.K_r:
                    self.state = GameState(state.asset_root)
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                return
            if event.key == pygame.K_TAB:
                state.switch_room()
            if event.key == pygame.K_e:
                state.interact()
            if event.key == pygame.K_t and state.current_room == ROOM_LIVING:
                if state.interact_zones["TV"].colliderect(state.player.rect):
                    state.tv_on = not state.tv_on
                    state.add_message("TV on." if state.tv_on else "TV off.")
            if event.key == pygame.K_f and state.current_room == ROOM_LIVING:
                if state.interact_zones["Fan"].colliderect(state.player.rect):
                    state.fan_on = not state.fan_on
                    state.add_message("Fan on." if state.fan_on else "Fan off.")
            if event.key == pygame.K_b:
                if self.near_grounding():
                    state.grounding()
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                state.use_item(int(event.unicode))
            if event.key == pygame.K_SPACE:
                state.axe_attack()
            if event.key == pygame.K_l:
                state.torch_on = not state.torch_on
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                state.torch_on = not state.torch_on

    def update(self, dt):
        state = self.state
        if self.intro or state.dead or state.win:
            return
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
            state.player_dir = (dx, dy)
        state.player.move(dx, dy, state.room_bounds(), state.current_obstacles(), dt)
        state.update(dt)

    def render(self):
        state = self.state
        bg = state.assets["bg_living"] if state.current_room == ROOM_LIVING else state.assets["bg_bath"]
        state.ui.screen.blit(bg, (0, 0))

        # Draw dog
        if state.dog.alive:
            state.ui.screen.blit(state.assets["dog"], state.dog.rect.topleft)
        elif state.dog_dead and state.current_room == ROOM_LIVING:
            state.ui.screen.blit(state.assets["dead_dog"], (200, 420))

        # Draw enemies
        if state.ghost and not state.ghost.banished:
            sprite = state.assets["ghost_red"] if state.ghost.attack_timer > 6.0 else state.assets["ghost"]
            shadow_alpha = 140 if not state.fan_on else 60
            shadow = pygame.Surface((40, 16), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (20, 20, 20, shadow_alpha), (0, 0, 40, 16))
            state.ui.screen.blit(shadow, (state.ghost.rect().centerx - 20, state.ghost.rect().bottom - 6))
            if random.random() < 0.1:
                ghost_sprite = sprite.copy()
                ghost_sprite.set_alpha(180)
            else:
                ghost_sprite = sprite
            state.ui.screen.blit(ghost_sprite, state.ghost.rect().topleft)
            if state.tv_on and state.current_room == ROOM_LIVING:
                dist = distance(state.player.rect.center, (state.ghost.x, state.ghost.y))
                if dist < 160:
                    tv_rect = state.interact_zones["TV"]
                    static = pygame.Surface((tv_rect.w, tv_rect.h), pygame.SRCALPHA)
                    for _ in range(10):
                        x = random.randint(0, tv_rect.w)
                        y = random.randint(0, tv_rect.h)
                        pygame.draw.rect(static, (200, 200, 200, 120), (x, y, 6, 2))
                    state.ui.screen.blit(static, tv_rect.topleft)

        if state.hallucination:
            sprite = state.assets["ghost"].copy()
            sprite.set_alpha(120)
            state.ui.screen.blit(sprite, state.hallucination.rect().topleft)

        if state.tentacle:
            state.ui.screen.blit(state.assets["tentacle"], state.tentacle.rect().topleft)

        # Player
        state.ui.screen.blit(state.assets["player"], state.player.rect.topleft)

        # Torch cone
        if state.torch_on:
            cone = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            origin = state.player.rect.center
            pygame.draw.polygon(
                cone,
                (200, 200, 140, 60),
                [
                    origin,
                    (origin[0] + state.player_dir[0] * 260 - state.player_dir[1] * 120,
                     origin[1] + state.player_dir[1] * 260 + state.player_dir[0] * 120),
                    (origin[0] + state.player_dir[0] * 260 + state.player_dir[1] * 120,
                     origin[1] + state.player_dir[1] * 260 - state.player_dir[0] * 120),
                ],
            )
            state.ui.screen.blit(cone, (0, 0))

        state.ui.draw_hud(state)
        state.ui.draw_effects(state)
        state.ui.draw_prompt(self.current_prompt())

        if self.intro:
            state.ui.draw_intro()
        if state.dead:
            monster_surface = None
            monster_name = state.death_cause
            if state.death_cause == "Monster":
                monster_name = state.death_monster
                if monster_name == "Dead Girl":
                    monster_surface = state.assets["ghost_red"]
                elif monster_name == "Tentacle Monster":
                    monster_surface = state.assets["tentacle"]
            state.ui.draw_death(state, monster_surface, monster_name)
            d, h, m = state.time_breakdown()
            summary = [
                f"Time survived: Day {d} Hour {h:02d}:{m:02d}",
                f"Cause: {state.death_cause}",
                f"Liquid uses: {state.liquid_uses}",
                f"TV time: {int(state.tv_time)}s",
                f"Noise peak: {int(state.noise_peak)}",
            ]
            state.ui.draw_summary(summary)
        if state.win:
            d, h, m = state.time_breakdown()
            summary = [
                f"Time survived: Day {d} Hour {h:02d}:{m:02d}",
                "You survived all five days.",
                f"Liquid uses: {state.liquid_uses}",
                f"TV time: {int(state.tv_time)}s",
                f"Noise peak: {int(state.noise_peak)}",
            ]
            state.ui.draw_death(state, None, "Survived")
            state.ui.draw_summary(summary)

    def current_prompt(self):
        state = self.state
        if state.current_room == ROOM_LIVING:
            if state.interact_zones["Door"].colliderect(state.player.rect):
                return "Press E to open the door"
            if state.interact_zones["TopDoor"].colliderect(state.player.rect):
                return "Press E to enter bathroom"
            if state.interact_zones["TV"].colliderect(state.player.rect):
                return "Press T to toggle TV"
            if state.interact_zones["Fan"].colliderect(state.player.rect):
                return "Press F to toggle Fan"
            if state.interact_zones["Stash"].colliderect(state.player.rect):
                return "Press E to search stash"
        if state.current_room == ROOM_BATH:
            if state.interact_zones["Sink"].colliderect(state.player.rect):
                return "Press E to use sink"
            if self.near_grounding():
                return "Press B to ground yourself"
        return ""

    def near_grounding(self):
        state = self.state
        if state.current_room != ROOM_BATH:
            return False
        return state.interact_zones["Sink"].colliderect(state.player.rect) or state.interact_zones["Mirror"].colliderect(state.player.rect)


def run_game():
    pygame.init()
    try:
        pygame.mixer.init()
    except pygame.error:
        pass
    pygame.display.set_mode((WIDTH, HEIGHT))
    asset_root = os.path.join(os.path.dirname(__file__), "..", "assets")
    asset_root = os.path.abspath(asset_root)
    clock = pygame.time.Clock()
    game = Game(asset_root)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_input(event)
        game.update(dt)
        game.render()
        pygame.display.flip()

    pygame.quit()
