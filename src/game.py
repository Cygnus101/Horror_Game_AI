"""Main game loop and state."""

import math
import os
import random

import pygame

from . import assets
from .audio import make_beep
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
    FPS,
    GROUNDING_BASE_GAIN,
    GROUNDING_BASE_THIRST_COST,
    GROUNDING_COOLDOWN,
    GROUNDING_WINDOW,
    HEIGHT,
    HUNGER_DRAIN,
    HUNGER_DEATH,
    LIQUID_COOLDOWN,
    LIQUID_CURSE_TIME,
    LIQUID_FREEZE_TIME,
    LIQUID_TENTACLE_THRESHOLD,
    NOISE_DECAY,
    NOISE_FROM_FAN,
    NOISE_FROM_SINK,
    NOISE_FROM_TV,
    PLAYER_SPEED,
    ROOM_BATH,
    ROOM_LIVING,
    SAFE_ROOM_HOLD,
    SANITY_DEATH,
    SANITY_DRAIN,
    THIRST_DEATH,
    THIRST_DRAIN,
    WIDTH,
    WIN_NIGHTS,
    DAY_LENGTH,
)
from .entities import Interactable, Monster, Player
from .systems import BreachSystem, HallucinationSystem, MessageLog, TVSystem
from .ui import UI


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class GameState:
    def __init__(self, asset_root):
        self.asset_root = asset_root
        self.current_room = ROOM_LIVING
        self.living_rect = pygame.Rect(60, 60, 560, 420)
        self.bath_rect = pygame.Rect(660, 140, 240, 260)

        self.player = Player(self.living_rect.centerx, self.living_rect.centery)
        self.player.speed = PLAYER_SPEED

        self.sanity = 75.0
        self.hunger = 70.0
        self.thirst = 70.0
        self.noise = 0.0
        self.dread = 0.0

        self.inventory = {"food": 3, "water": 2, "liquid": 1}
        self.liquid_uses = 0
        self.liquid_last = -100.0
        self.liquid_freeze = 0.0
        self.curse_timer = 0.0

        self.msg_log = MessageLog()
        self.msg_log.add("You are trapped inside. Outside means death.")

        self.objects = []
        self.interactables = []
        self.build_objects()

        self.tv_system = TVSystem()
        self.breach_system = BreachSystem()
        self.hallucination_system = HallucinationSystem()

        self.monster = None
        self.hallucination = None
        self.hallucinating = False

        self.time = 0.0
        self.dead = False
        self.win = False
        self.death_cause = ""
        self.death_monster = ""

        self.safe_room_timer = 0.0
        self.env_cue = None
        self.device_cue_timer = 0.0
        self.light_flicker_timer = 0.0

        self.refill_timer = random.uniform(40.0, 80.0)
        self.refill_soon = False

        self.grounding_last = -100.0
        self.grounding_history = []

    def build_objects(self):
        self.objects = [
            {
                "name": "TV",
                "rect": pygame.Rect(self.living_rect.x + 80, self.living_rect.y + 70, 48, 32),
                "room": ROOM_LIVING,
                "sprite": ASSET_TV,
            },
            {
                "name": "Fan",
                "rect": pygame.Rect(self.living_rect.x + 220, self.living_rect.y + 120, 32, 32),
                "room": ROOM_LIVING,
                "sprite": ASSET_FAN,
            },
            {
                "name": "Cabinet",
                "rect": pygame.Rect(self.living_rect.x + 400, self.living_rect.y + 300, 44, 30),
                "room": ROOM_LIVING,
                "sprite": ASSET_SINK,
            },
            {
                "name": "Stash",
                "rect": pygame.Rect(self.living_rect.x + 300, self.living_rect.y + 260, 40, 30),
                "room": ROOM_LIVING,
                "sprite": ASSET_VENT,
            },
            {
                "name": "Outside Door",
                "rect": pygame.Rect(self.living_rect.x + 12, self.living_rect.y + 200, 26, 60),
                "room": ROOM_LIVING,
                "sprite": ASSET_DOOR,
            },
            {
                "name": "Window",
                "rect": pygame.Rect(self.living_rect.x + 220, self.living_rect.y + 20, 44, 26),
                "room": ROOM_LIVING,
                "sprite": ASSET_WINDOW,
            },
            {
                "name": "Vent",
                "rect": pygame.Rect(self.living_rect.x + 460, self.living_rect.y + 20, 36, 18),
                "room": ROOM_LIVING,
                "sprite": ASSET_VENT,
            },
            {
                "name": "Mirror",
                "rect": pygame.Rect(self.bath_rect.x + 150, self.bath_rect.y + 40, 36, 46),
                "room": ROOM_BATH,
                "sprite": ASSET_MIRROR,
            },
            {
                "name": "Sink",
                "rect": pygame.Rect(self.bath_rect.x + 40, self.bath_rect.y + 60, 40, 24),
                "room": ROOM_BATH,
                "sprite": ASSET_SINK,
            },
        ]

        self.interactables = [
            Interactable("TV", self.get_object_rect("TV"), "Press T to toggle TV"),
            Interactable("Fan", self.get_object_rect("Fan"), "Press F to toggle Fan"),
            Interactable("Cabinet", self.get_object_rect("Cabinet"), "Press E to search cabinet"),
            Interactable("Stash", self.get_object_rect("Stash"), "Press E to search stash"),
            Interactable("Outside Door", self.get_object_rect("Outside Door"), "Press E to open outside door"),
            Interactable("Mirror", self.get_object_rect("Mirror"), "Press B to ground yourself"),
            Interactable("Sink", self.get_object_rect("Sink"), "Press E to use sink"),
        ]

        self.stash_stock = {"Cabinet": 3, "Stash": 2}

    def get_object_rect(self, name):
        for obj in self.objects:
            if obj["name"] == name:
                return obj["rect"]
        return pygame.Rect(0, 0, 0, 0)

    def set_message(self, text):
        self.msg_log.add(text)

    def current_night(self):
        return int(self.time / DAY_LENGTH) + 1

    def switch_room(self):
        if self.current_room == ROOM_LIVING:
            self.current_room = ROOM_BATH
            self.player.rect.center = self.bath_rect.center
            self.set_message("You step into the bathroom.")
        else:
            self.current_room = ROOM_LIVING
            self.player.rect.center = self.living_rect.center
            self.set_message("You step into the living room.")

    def die(self, reason, monster_name=""):
        self.dead = True
        self.death_cause = reason
        self.death_monster = monster_name

    def use_item(self, idx):
        if idx == 1 and self.inventory["food"] > 0:
            self.inventory["food"] -= 1
            self.hunger = clamp(self.hunger + 30, 0, 100)
            self.set_message("You eat canned food.")
        elif idx == 2 and self.inventory["water"] > 0:
            self.inventory["water"] -= 1
            self.thirst = clamp(self.thirst + 32, 0, 100)
            self.set_message("You drink water.")
        elif idx == 3 and self.inventory["liquid"] > 0:
            if self.time - self.liquid_last < LIQUID_COOLDOWN:
                self.set_message("Your body rejects more liquid.")
                return
            self.inventory["liquid"] -= 1
            self.liquid_last = self.time
            self.liquid_uses += 1
            self.curse_timer = LIQUID_CURSE_TIME
            self.tv_system.truth_bias = 0.45
            if random.random() < 0.5:
                self.sanity = clamp(self.sanity + 28, 0, 100)
                self.set_message("The strange liquid calms your mind.")
            else:
                self.liquid_freeze = LIQUID_FREEZE_TIME
                self.set_message("Your body goes cold. Needs fade.")
            self.set_message("A heavy presence listens now.")

    def interact(self, name):
        if name == "Outside Door":
            self.die("Outside", "Outside")
            return
        if name in ("Cabinet", "Stash"):
            if self.stash_stock[name] <= 0:
                self.set_message("The stash is empty.")
                return
            self.stash_stock[name] -= 1
            if random.random() < 0.5:
                self.inventory["food"] += 1
                self.set_message("Found food.")
            else:
                self.inventory["water"] += 1
                self.set_message("Found water.")
            return
        if name == "Sink":
            self.inventory["water"] += 1
            self.noise = clamp(self.noise + 12, 0, 100)
            if random.random() < 0.3:
                self.sanity = clamp(self.sanity - 8, 0, 100)
                self.set_message("The water tastes wrong.")
            else:
                self.set_message("You refill a bottle.")
            return

    def grounding(self):
        if self.current_room != ROOM_BATH:
            return
        if self.time - self.grounding_last < GROUNDING_COOLDOWN:
            self.set_message("You need a moment before grounding again.")
            return
        self.grounding_last = self.time
        self.grounding_history = [t for t in self.grounding_history if self.time - t < GROUNDING_WINDOW]
        recent = len(self.grounding_history)
        self.grounding_history.append(self.time)
        factor = 1.0 / (1.0 + recent * 0.6)
        gain = GROUNDING_BASE_GAIN * factor
        thirst_cost = GROUNDING_BASE_THIRST_COST * (1.0 + recent * 0.4)
        self.thirst = clamp(self.thirst - thirst_cost, 0, 100)
        self.sanity = clamp(self.sanity + gain, 0, 100)
        self.hallucination = None
        self.hallucinating = False
        if factor < 0.7:
            self.set_message("It isn't working as well...")
        else:
            self.set_message("You steady yourself.")

    def update(self, dt):
        self.time += dt
        if self.curse_timer > 0:
            self.curse_timer -= dt
        else:
            self.tv_system.truth_bias = 0.75
        if self.liquid_freeze > 0:
            self.liquid_freeze -= dt

        if not self.dead and not self.win:
            self.update_meters(dt)
            self.update_refill(dt)
            self.update_systems(dt)
            self.update_monsters(dt)
            self.check_win()

    def update_meters(self, dt):
        minute = dt / 60.0
        if self.liquid_freeze <= 0:
            self.hunger = clamp(self.hunger - HUNGER_DRAIN * minute, 0, 100)
            self.thirst = clamp(self.thirst - THIRST_DRAIN * minute, 0, 100)
        sanity_drain = SANITY_DRAIN
        if self.tv_system.on:
            sanity_drain += 0.1
        if self.fan_on:
            sanity_drain -= 0.15
        if self.monster and self.monster.real:
            sanity_drain += 0.8
        self.sanity = clamp(self.sanity - sanity_drain * minute, 0, 100)

        noise_gain = 0.0
        if self.tv_system.on:
            noise_gain += NOISE_FROM_TV * minute
        if self.fan_on:
            noise_gain += NOISE_FROM_FAN * minute
        self.noise = clamp(self.noise + noise_gain - NOISE_DECAY * minute, 0, 100)

        if self.hunger <= HUNGER_DEATH:
            self.die("Hunger")
        if self.thirst <= THIRST_DEATH:
            self.die("Thirst")
        if self.sanity <= SANITY_DEATH:
            self.die("Sanity")

    def update_refill(self, dt):
        self.refill_timer -= dt
        self.refill_soon = self.refill_timer < 12.0
        if self.refill_timer <= 0:
            target = random.choice(list(self.stash_stock.keys()))
            self.stash_stock[target] += 1
            self.refill_timer = random.uniform(45.0, 90.0)
            if self.tv_system.on:
                self.set_message("TV: Supplies shifted in the dark.")

    def update_systems(self, dt):
        tv_events = self.tv_system.update(
            dt,
            {
                "refill_soon": self.refill_soon,
                "breach_rising": self.noise > 45 or self.curse_timer > 0,
                "real_near": self.monster is not None,
            },
        )
        for event in tv_events:
            self.set_message(event)
        if self.tv_system.dread_timer > 0:
            self.dread = clamp(self.dread + 8 * (dt / 1.0), 0, 100)

        breach = self.breach_system.update(
            dt,
            {
                "tv_on": self.tv_system.on,
                "fan_on": self.fan_on,
                "moving": self.player.moving,
                "curse": self.curse_timer > 0,
            },
        )
        if breach and not self.monster:
            self.spawn_breach()
        if self.hallucination_system.update(dt, self.sanity) and not self.hallucinating:
            if self.current_room == ROOM_LIVING and not self.monster:
                self.spawn_hallucination()

        if self.device_cue_timer > 0:
            self.device_cue_timer -= dt
        if self.light_flicker_timer > 0:
            self.light_flicker_timer -= dt

    def spawn_breach(self):
        entry = random.choice(["door", "window", "vent"])
        spawn_points = {
            "door": (self.living_rect.left + 40, self.living_rect.centery),
            "window": (self.living_rect.centerx, self.living_rect.top + 20),
            "vent": (self.living_rect.right - 30, self.living_rect.top + 30),
        }
        kind = "dead_girl"
        if self.liquid_uses >= LIQUID_TENTACLE_THRESHOLD:
            kind = "tentacle"
        self.monster = Monster(*spawn_points[entry], kind=kind, real=True)
        cue_rect = self.get_object_rect("Outside Door" if entry == "door" else "Window" if entry == "window" else "Vent")
        self.env_cue = {"type": entry, "rect": cue_rect, "room": ROOM_LIVING, "timer": 6.0}
        self.device_cue_timer = 5.0
        self.light_flicker_timer = 3.0
        self.dread = clamp(self.dread + 20, 0, 100)
        self.set_message("A breach rattles the house.")

    def spawn_hallucination(self):
        self.hallucinating = True
        self.hallucination = Monster(self.living_rect.centerx - 120, self.living_rect.centery, real=False)
        self.set_message("A shadow folds into the room.")

    def update_monsters(self, dt):
        if self.env_cue:
            self.env_cue["timer"] -= dt
            if self.env_cue["timer"] <= 0:
                self.env_cue = None

        if self.monster:
            blocked = self.current_room == ROOM_BATH
            if blocked:
                self.safe_room_timer += dt
            else:
                self.safe_room_timer = 0.0
            self.monster.update(dt, self.player.rect.center, blocked and self.safe_room_timer < SAFE_ROOM_HOLD)
            if self.monster.rect().colliderect(self.player.rect) and self.current_room == ROOM_LIVING:
                name = "Dead Girl" if self.monster.kind == "dead_girl" else "Tentacle Monster"
                self.die("Monster", name)
            if self.monster.life <= 0:
                self.monster = None
                self.safe_room_timer = 0.0

        if self.hallucination:
            self.hallucination.update(dt, self.player.rect.center, False)
            if self.current_room == ROOM_BATH:
                self.hallucination.life -= dt * 1.5
            if self.hallucination.life <= 0:
                self.hallucination = None
                self.hallucinating = False

        if self.hallucination and self.current_room == ROOM_LIVING:
            dist = math.hypot(self.hallucination.x - self.player.rect.centerx, self.hallucination.y - self.player.rect.centery)
            if dist < 90 and random.random() < 0.2:
                self.sanity = clamp(self.sanity - 2.0, 0, 100)

    def check_win(self):
        if self.time >= WIN_NIGHTS * DAY_LENGTH:
            self.win = True

    @property
    def fan_on(self):
        return any(obj["name"] == "Fan" and obj.get("on") for obj in self.objects)

    def toggle_device(self, name, state=None):
        for obj in self.objects:
            if obj["name"] == name:
                if state is None:
                    obj["on"] = not obj.get("on", False)
                else:
                    obj["on"] = state
                return obj["on"]
        return False


class Game:
    def __init__(self, asset_root):
        self.asset_root = asset_root
        self.state = GameState(asset_root)
        self.assets = {}
        self.load_assets()
        self.ui = UI(self.screen, self.assets)
        self.intro = True
        self.pause = False
        self.death_sound_played = False
        self.sounds = {
            "dead_girl": make_beep(380, 0.8, 0.6),
            "tentacle": make_beep(180, 1.0, 0.7),
        }

    def load_assets(self):
        self.assets = {
            "player": assets.load_image(self.asset_root, ASSET_PLAYER),
            "dead_girl": assets.load_image(self.asset_root, ASSET_DEAD_GIRL),
            "tentacle": assets.load_image(self.asset_root, ASSET_TENTACLE),
            "hallucination": assets.load_image(self.asset_root, ASSET_HALLUCINATION),
            ASSET_TV: assets.load_image(self.asset_root, ASSET_TV),
            ASSET_FAN: assets.load_image(self.asset_root, ASSET_FAN),
            ASSET_DOOR: assets.load_image(self.asset_root, ASSET_DOOR),
            ASSET_WINDOW: assets.load_image(self.asset_root, ASSET_WINDOW),
            ASSET_VENT: assets.load_image(self.asset_root, ASSET_VENT),
            ASSET_MIRROR: assets.load_image(self.asset_root, ASSET_MIRROR),
            ASSET_SINK: assets.load_image(self.asset_root, ASSET_SINK),
            "jumpscare_girl": assets.load_image(self.asset_root, ASSET_JUMPSCARE_GIRL),
            "jumpscare_tentacle": assets.load_image(self.asset_root, ASSET_JUMPSCARE_TENTACLE),
        }

    @property
    def screen(self):
        return pygame.display.get_surface()

    def reset(self):
        self.state = GameState(self.asset_root)
        self.death_sound_played = False
        self.intro = False

    def handle_input(self, event):
        state = self.state
        if event.type == pygame.KEYDOWN:
            if self.intro:
                if event.key == pygame.K_RETURN:
                    self.intro = False
                return
            if event.key == pygame.K_p:
                self.pause = not self.pause
            if state.dead or state.win:
                if event.key == pygame.K_r:
                    self.reset()
                if event.key == pygame.K_q:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                return
            if event.key == pygame.K_TAB:
                state.switch_room()
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                state.use_item(int(event.unicode))
            if event.key == pygame.K_e:
                self.try_interact()
            if event.key == pygame.K_t:
                if self.near_object("TV"):
                    tv_state = state.toggle_device("TV")
                    state.tv_system.set_on(tv_state)
                    state.set_message("TV on." if tv_state else "TV off.")
            if event.key == pygame.K_f:
                if self.near_object("Fan"):
                    fan_state = state.toggle_device("Fan")
                    state.set_message("Fan on." if fan_state else "Fan off.")
            if event.key == pygame.K_b:
                if self.near_object("Mirror") or self.near_object("Sink"):
                    state.grounding()

    def near_object(self, name):
        state = self.state
        rect = state.get_object_rect(name)
        return rect.colliderect(state.player.rect.inflate(40, 40)) and state.current_room == self.object_room(name)

    def object_room(self, name):
        for obj in self.state.objects:
            if obj["name"] == name:
                return obj["room"]
        return ROOM_LIVING

    def try_interact(self):
        state = self.state
        for obj in state.interactables:
            if obj.near(state.player.rect) and state.current_room == self.object_room(obj.name):
                state.interact(obj.name)
                return

    def update(self, dt):
        state = self.state
        if self.pause or state.dead or state.win or self.intro:
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
        bounds = state.living_rect if state.current_room == ROOM_LIVING else state.bath_rect
        state.player.move(dx, dy, bounds, dt)
        state.update(dt)

    def render(self):
        state = self.state
        self.ui.draw_room(state)
        self.ui.draw_objects(state)

        player_sprite = self.assets["player"]
        self.ui.draw_player(player_sprite, state.player.rect)

        fan_mask = state.fan_on
        if state.monster and state.current_room == ROOM_LIVING:
            sprite = self.assets["dead_girl"] if state.monster.kind == "dead_girl" else self.assets["tentacle"]
            self.ui.draw_monster(state.monster, sprite, shadow=True, fan_mask=fan_mask)
        if state.hallucination and state.current_room == ROOM_LIVING:
            sprite = self.assets["hallucination"]
            self.ui.draw_monster(state.hallucination, sprite, shadow=False, fan_mask=fan_mask)

        if state.device_cue_timer > 0 and state.tv_system.on:
            tv_rect = state.get_object_rect("TV")
            static = pygame.Surface((tv_rect.w, tv_rect.h), pygame.SRCALPHA)
            for _ in range(10):
                x = random.randint(0, tv_rect.w)
                y = random.randint(0, tv_rect.h)
                pygame.draw.rect(static, (200, 200, 200, 120), (x, y, 6, 2))
            self.screen.blit(static, tv_rect.topleft)

        if state.light_flicker_timer > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((20, 20, 30, 40))
            self.screen.blit(overlay, (0, 0))

        self.ui.draw_hud(state)
        prompt = self.current_prompt()
        self.ui.draw_prompt(prompt)
        self.ui.draw_effects(state)

        if self.intro:
            self.draw_intro()
        if self.pause:
            self.ui.draw_pause()
        if state.dead:
            self.draw_death()
        if state.win:
            self.draw_win()

    def current_prompt(self):
        state = self.state
        for obj in state.interactables:
            if obj.near(state.player.rect) and state.current_room == self.object_room(obj.name):
                return obj.prompt
        return ""

    def draw_intro(self):
        lines = [
            "Horror House Survival",
            "You are trapped inside. Outside means death.",
            "Move: WASD/Arrows  Interact: E  Switch Room: TAB",
            "TV: T  Fan: F  Grounding: B  Use Items: 1-3",
            "Survive three nights.",
            "Press Enter to start.",
        ]
        self.screen.fill((10, 10, 12))
        for i, line in enumerate(lines):
            img = self.ui.big.render(line, True, (240, 240, 240))
            self.screen.blit(img, (WIDTH / 2 - img.get_width() / 2, 120 + i * 42))

    def draw_death(self):
        state = self.state
        summary = [
            f"Time survived: {int(state.time)}s",
            f"Cause: {state.death_cause}",
            f"Liquid uses: {state.liquid_uses}",
        ]
        if state.death_cause == "Monster":
            summary.append(f"Monster: {state.death_monster}")
        if state.death_cause == "Outside":
            summary.append("Monster: Outside")
        if state.death_cause == "Monster":
            if state.death_monster == "Dead Girl":
                if not self.death_sound_played:
                    self.sounds["dead_girl"].play()
                    self.death_sound_played = True
                self.ui.draw_jumpscare(self.assets["jumpscare_girl"], "Dead Girl")
            else:
                if not self.death_sound_played:
                    self.sounds["tentacle"].play()
                    self.death_sound_played = True
                self.ui.draw_jumpscare(self.assets["jumpscare_tentacle"], "Tentacle Monster")
            self.ui.draw_end("You Died", summary)
        else:
            self.ui.draw_end("You Died", summary)

    def draw_win(self):
        state = self.state
        summary = [
            f"Time survived: {int(state.time)}s",
            "You held out through the nights.",
        ]
        self.ui.draw_end("You Survived", summary)


def run_game():
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_mode((WIDTH, HEIGHT))
    asset_root = os.path.join(os.path.dirname(__file__), "..", "assets")
    asset_root = os.path.abspath(asset_root)
    assets.ensure_assets(asset_root)

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
