"""
Blooming Rose Animation — Python + Pygame
==========================================
Requirements: pip install pygame
Run:          python blooming_rose.py

Tested with Python 3.12 and Pygame 2.x
"""

import pygame
import math
import random
import sys
from dataclasses import dataclass, field
from typing import List, Tuple

# ─── Constants ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 700
FPS = 60
BLOOM_DURATION = 4.0    # seconds to fully open
HOLD_DURATION  = 2.5    # seconds held open
CLOSE_DURATION = 3.0    # seconds to close
CYCLE = BLOOM_DURATION + HOLD_DURATION + CLOSE_DURATION

# Rose colour palette (all valid 0-255 RGB)
PETAL_DEEP   = (140,  20,  40)
PETAL_MID    = (200,  50,  70)
PETAL_BRIGHT = (240,  90, 100)
PETAL_LIGHT  = (255, 160, 150)
PETAL_TIP    = (255, 210, 190)
SHADOW       = ( 80,  10,  25)

# Garden palette
SKY_TOP    = ( 10,  15,  35)
SKY_BOT    = ( 25,  45,  80)
GROUND_COL = ( 18,  45,  22)
LEAF_DARK  = ( 20,  70,  30)
LEAF_MID   = ( 35, 100,  45)
LEAF_LIGHT = ( 60, 140,  55)
STEM_COL   = ( 30,  80,  35)
FIREFLY    = (220, 255, 150)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


def lerp_color(c1: Tuple, c2: Tuple, t: float) -> Tuple:
    t = max(0.0, min(1.0, t))
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def ease_in_out(t: float) -> float:
    """Smooth cubic ease-in-out."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out_elastic(t: float) -> float:
    """Slight elastic overshoot for petals snapping open."""
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    p = 0.3
    s = p / 4
    return math.pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / p) + 1.0


def rotate_point(x: float, y: float, cx: float, cy: float, angle: float):
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    dx, dy = x - cx, y - cy
    return (cx + dx * cos_a - dy * sin_a,
            cy + dx * sin_a + dy * cos_a)


def clamp_color(c: Tuple) -> Tuple:
    return tuple(max(0, min(255, v)) for v in c)


# ─── Firefly ──────────────────────────────────────────────────────────────────
@dataclass
class Firefly:
    x: float
    y: float
    vx: float
    vy: float
    phase: float          # offset for glow pulse
    radius: float
    lifetime: float = 0.0

    def update(self, dt: float):
        self.lifetime += dt
        # gentle wander
        self.vx += random.uniform(-12, 12) * dt
        self.vy += random.uniform(-12, 12) * dt
        # dampen
        self.vx *= 0.97
        self.vy *= 0.97
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        # soft boundary wrap
        if self.x < 0:   self.x = WIDTH
        if self.x > WIDTH:  self.x = 0
        if self.y < 50:  self.vy =  abs(self.vy)
        if self.y > HEIGHT - 80: self.vy = -abs(self.vy)

    def draw(self, surf: pygame.Surface, t: float):
        alpha = 0.5 + 0.5 * math.sin(t * 2.8 + self.phase)
        glow_r = int(self.radius * (2.5 + alpha))
        # outer glow
        glow_surf = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
        for r in range(glow_r, 0, -1):
            a = int(80 * (r / glow_r) * alpha)
            col = (220, 255, 150, a)
            pygame.draw.circle(glow_surf, col,
                               (glow_r + 1, glow_r + 1), r)
        surf.blit(glow_surf,
                  (int(self.x) - glow_r - 1, int(self.y) - glow_r - 1),
                  special_flags=pygame.BLEND_RGBA_ADD)
        # bright core
        core_alpha = int(220 * alpha)
        core_col = (220, 255, 150, core_alpha)
        core_surf = pygame.Surface((self.radius * 2 + 2, self.radius * 2 + 2),
                                   pygame.SRCALPHA)
        pygame.draw.circle(core_surf, core_col,
                           (int(self.radius) + 1, int(self.radius) + 1),
                           int(self.radius))
        surf.blit(core_surf,
                  (int(self.x) - int(self.radius) - 1,
                   int(self.y) - int(self.radius) - 1),
                  special_flags=pygame.BLEND_RGBA_ADD)


def make_fireflies(n: int) -> List[Firefly]:
    return [
        Firefly(
            x=random.uniform(30, WIDTH - 30),
            y=random.uniform(100, HEIGHT - 150),
            vx=random.uniform(-15, 15),
            vy=random.uniform(-10, 10),
            phase=random.uniform(0, math.tau),
            radius=random.uniform(1.5, 3.0),
        )
        for _ in range(n)
    ]


# ─── Leaf ─────────────────────────────────────────────────────────────────────
@dataclass
class Leaf:
    cx: float
    cy: float
    angle: float          # base orientation (radians)
    length: float
    width: float
    flip: int = 1         # +1 or -1

    def draw(self, surf: pygame.Surface, progress: float):
        if progress <= 0:
            return
        t = ease_in_out(progress)
        # leaf control points in local space
        tip_x = self.length * t
        ctrl1_x, ctrl1_y = self.length * 0.3, self.width * 0.6 * self.flip * t
        ctrl2_x, ctrl2_y = self.length * 0.7, self.width * 0.7 * self.flip * t
        tip_y  = 0.0

        # sample a bezier curve for the leaf outline
        def bezier(p0, p1, p2, p3, steps=18):
            pts = []
            for i in range(steps + 1):
                s = i / steps
                iv = 1 - s
                bx = iv**3*p0[0] + 3*iv**2*s*p1[0] + 3*iv*s**2*p2[0] + s**3*p3[0]
                by = iv**3*p0[1] + 3*iv**2*s*p1[1] + 3*iv*s**2*p2[1] + s**3*p3[1]
                pts.append((bx, by))
            return pts

        top_side = bezier(
            (0, 0),
            (ctrl1_x, ctrl1_y),
            (ctrl2_x, ctrl2_y),
            (tip_x, tip_y),
        )
        bot_side = bezier(
            (tip_x, tip_y),
            (ctrl2_x, -ctrl2_y),
            (ctrl1_x, -ctrl1_y),
            (0, 0),
        )
        pts_local = top_side + bot_side

        # rotate and translate
        def to_world(px, py):
            rx, ry = (px * math.cos(self.angle) - py * math.sin(self.angle),
                      px * math.sin(self.angle) + py * math.cos(self.angle))
            return (self.cx + rx, self.cy + ry)

        poly = [to_world(px, py) for px, py in pts_local]
        if len(poly) >= 3:
            # shadow layer
            shadow_poly = [(x + 4, y + 4) for x, y in poly]
            pygame.draw.polygon(surf, clamp_color(LEAF_DARK), shadow_poly)
            pygame.draw.polygon(surf, LEAF_MID, poly)
            # mid-vein highlight
            vein = [to_world(tip_x * s / 16, 0) for s in range(17)]
            if len(vein) >= 2:
                pygame.draw.lines(surf, LEAF_LIGHT, False, vein, 1)


# ─── Petal ────────────────────────────────────────────────────────────────────
@dataclass
class Petal:
    """One rose petal defined in a local coordinate frame centred on the rose."""
    layer: int            # 0 = innermost
    index: int            # position within layer
    total: int            # petals in this layer
    layer_radius: float   # distance of petal base from centre
    petal_length: float
    petal_width: float
    base_angle: float     # azimuth in the petal circle
    open_angle: float     # how far the petal droops when fully open (radians)
    delay: float          # normalised 0-1 bloom start delay
    color_t: float        # 0 = deep, 1 = light

    def _get_color(self, highlight: bool = False) -> Tuple:
        if highlight:
            c = lerp_color(PETAL_MID, PETAL_TIP, self.color_t)
        else:
            c = lerp_color(PETAL_DEEP, PETAL_BRIGHT, self.color_t)
        return clamp_color(c)

    def draw(self, surf: pygame.Surface, cx: float, cy: float,
             bloom: float, cam_wobble: float):
        """bloom: 0 = closed bud, 1 = fully open."""
        # Per-petal delayed bloom
        local_t = max(0.0, (bloom - self.delay) / (1.0 - self.delay + 1e-6))
        local_t = min(1.0, local_t)
        open_t  = ease_out_elastic(local_t) if self.layer > 1 else ease_in_out(local_t)

        # Petal droops outward as it opens
        droop = self.open_angle * open_t

        # Petal base position (in screen space, using simplified 3D projection)
        az = self.base_angle + cam_wobble * 0.04
        # Perspective: petals that angle away from viewer are shorter
        depth_factor = 0.85 + 0.15 * math.cos(az)

        bx = cx + self.layer_radius * math.cos(az) * depth_factor
        by = cy + self.layer_radius * math.sin(az) * 0.45 * depth_factor

        # Petal length grows with bloom
        pl = self.petal_length * open_t * depth_factor
        pw = self.petal_width  * open_t * depth_factor

        if pl < 2:
            return

        # Tip of petal
        tip_angle = az + droop
        tx = bx + pl * math.cos(tip_angle)
        ty = by + pl * math.sin(tip_angle) * 0.5 - pl * 0.35 * open_t   # rises as blooms

        # Control points for a nice curled petal shape
        perp = az + math.pi / 2
        c1x = bx + pl * 0.35 * math.cos(tip_angle) + pw * 0.55 * math.cos(perp)
        c1y = by + pl * 0.35 * math.sin(tip_angle) * 0.5 + pw * 0.4  * math.sin(perp)
        c2x = bx + pl * 0.7  * math.cos(tip_angle) + pw * 0.4 * math.cos(perp)
        c2y = by + pl * 0.7  * math.sin(tip_angle) * 0.5 + pw * 0.3  * math.sin(perp)
        c3x = bx + pl * 0.35 * math.cos(tip_angle) - pw * 0.55 * math.cos(perp)
        c3y = by + pl * 0.35 * math.sin(tip_angle) * 0.5 - pw * 0.4  * math.sin(perp)
        c4x = bx + pl * 0.7  * math.cos(tip_angle) - pw * 0.4 * math.cos(perp)
        c4y = by + pl * 0.7  * math.sin(tip_angle) * 0.5 - pw * 0.3  * math.sin(perp)

        def bez4(p0, p1, p2, p3, n=20):
            pts = []
            for i in range(n + 1):
                s = i / n
                iv = 1 - s
                x = iv**3*p0[0]+3*iv**2*s*p1[0]+3*iv*s**2*p2[0]+s**3*p3[0]
                y = iv**3*p0[1]+3*iv**2*s*p1[1]+3*iv*s**2*p2[1]+s**3*p3[1]
                pts.append((x, y))
            return pts

        left_edge  = bez4((bx, by), (c1x, c1y), (c2x, c2y), (tx, ty))
        right_edge = bez4((tx, ty), (c4x, c4y), (c3x, c3y), (bx, by))
        poly = left_edge + right_edge

        if len(poly) < 3:
            return

        # Shadow offset
        depth_shade = 0.6 + 0.4 * depth_factor
        base_col    = self._get_color(False)
        shaded_col  = clamp_color(tuple(int(v * depth_shade * 0.7) for v in base_col))

        # Draw shadow
        shadow_poly = [(x + 3 * depth_factor, y + 2) for x, y in poly]
        pygame.draw.polygon(surf, shaded_col, shadow_poly)

        # Draw petal body
        pygame.draw.polygon(surf, clamp_color(base_col), poly)

        # Highlight strip along left edge
        hi_col = self._get_color(True)
        if len(left_edge) >= 2:
            pygame.draw.lines(surf, hi_col, False, left_edge, max(1, int(pw * 0.15)))

        # Soft inner shadow near base
        if self.layer == 0:
            inner_col = clamp_color(tuple(max(0, v - 40) for v in base_col))
            if len(left_edge) > 4:
                pygame.draw.polygon(surf, inner_col,
                                    left_edge[:6] + [(bx, by)],)


# ─── Rose ─────────────────────────────────────────────────────────────────────
class Rose:
    def __init__(self, cx: float, cy: float):
        self.cx = cx
        self.cy = cy
        self.petals: List[Petal] = []
        self.leaves: List[Leaf] = []
        self._build()

    def _build(self):
        # Layer config: (count, radius, length, width, open_angle, color_t, delay_max)
        layers = [
            (5,  0,   28, 10, 0.55, 0.05, 0.00),   # innermost tight petals
            (6,  14,  38, 14, 0.80, 0.25, 0.08),
            (8,  26,  52, 18, 1.10, 0.50, 0.15),
            (10, 40,  65, 22, 1.35, 0.72, 0.22),
            (12, 56,  78, 26, 1.55, 0.88, 0.30),
            (14, 74,  90, 30, 1.70, 1.00, 0.38),
        ]
        for layer_i, (count, radius, pl, pw, oa, ct, delay_max) in enumerate(layers):
            rot_off = layer_i * (math.pi / count / 1.5)   # spiral offset
            for j in range(count):
                az = j * math.tau / count + rot_off
                delay = (j / count) * delay_max + layer_i * 0.05
                self.petals.append(Petal(
                    layer=layer_i, index=j, total=count,
                    layer_radius=radius,
                    petal_length=pl,
                    petal_width=pw,
                    base_angle=az,
                    open_angle=oa,
                    delay=min(delay, 0.85),
                    color_t=ct,
                ))

        # Leaves
        leaf_data = [
            (self.cx - 60, self.cy + 90,  -0.6, 70, 22, -1),
            (self.cx + 55, self.cy + 100,  0.5, 65, 20,  1),
            (self.cx - 40, self.cy + 140, -0.9, 55, 18, -1),
            (self.cx + 35, self.cy + 150,  0.8, 50, 16,  1),
        ]
        for cx, cy, ang, ln, wid, flip in leaf_data:
            self.leaves.append(Leaf(cx, cy, ang, ln, wid, flip))

    def draw(self, surf: pygame.Surface, bloom: float, cam_wobble: float):
        # Leaves (drawn before rose)
        leaf_t = min(1.0, bloom * 1.4)
        for leaf in self.leaves:
            leaf.draw(surf, leaf_t)

        # Stem
        stem_h = int(lerp(0, 160, ease_in_out(min(1.0, bloom * 1.8))))
        if stem_h > 1:
            stem_pts = [
                (int(self.cx), int(self.cy + 10)),
                (int(self.cx) - 5, int(self.cy + stem_h // 2)),
                (int(self.cx), int(self.cy + stem_h)),
            ]
            pygame.draw.lines(surf, STEM_COL,   False, stem_pts, 5)
            pygame.draw.lines(surf, LEAF_LIGHT, False, stem_pts, 1)

        # Bud/sepal base (always visible when blooming starts)
        bud_t = ease_in_out(min(1.0, bloom * 3.0))
        if bud_t > 0:
            sepal_col = clamp_color(lerp_color(LEAF_DARK, LEAF_MID, bud_t))
            for i in range(5):
                ang = i * math.tau / 5 + math.pi / 2
                sx = self.cx + 14 * math.cos(ang) * bud_t
                sy = self.cy + 7  * math.sin(ang) * bud_t + 8
                sepal_poly = [
                    (self.cx, self.cy + 8),
                    (sx - 4, sy), (sx, sy - 12), (sx + 4, sy)
                ]
                pygame.draw.polygon(surf, sepal_col, sepal_poly)

        # Petals — back to front (by layer, innermost last so they overlap correctly)
        for petal in self.petals:
            petal.draw(surf, self.cx, self.cy, bloom, cam_wobble)

        # Rose centre (stigma)
        centre_t = ease_in_out(min(1.0, bloom * 2.0))
        if centre_t > 0:
            cr = int(lerp(2, 9, centre_t))
            cc = clamp_color(lerp_color(PETAL_DEEP, (255, 200, 60), centre_t * 0.4))
            pygame.draw.circle(surf, cc, (int(self.cx), int(self.cy)), cr)
            pygame.draw.circle(surf, clamp_color((255, 220, 80)),
                               (int(self.cx) - 2, int(self.cy) - 2), max(1, cr // 3))


# ─── Background ───────────────────────────────────────────────────────────────
class Garden:
    def __init__(self, w: int, h: int):
        self.w = w
        self.h = h
        # Pre-bake the static sky gradient into a surface
        self.sky = pygame.Surface((w, h))
        for y in range(h):
            t = y / h
            col = lerp_color(SKY_TOP, SKY_BOT, t)
            pygame.draw.line(self.sky, col, (0, y), (w, y))

        # Random background foliage blobs
        self.foliage = []
        for _ in range(22):
            self.foliage.append({
                'x': random.randint(0, w),
                'y': random.randint(h // 2, h - 40),
                'r': random.randint(22, 65),
                'col': random.choice([LEAF_DARK, LEAF_MID,
                                      (25, 60, 28), (15, 55, 25)]),
            })

        # Far moon / soft light source
        self.moon_x = w * 0.78
        self.moon_y = h * 0.14

    def draw(self, surf: pygame.Surface, t: float):
        surf.blit(self.sky, (0, 0))

        # Subtle moon glow
        for r in range(55, 0, -5):
            alpha = int(18 * (1 - r / 55))
            glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (200, 220, 255, alpha),
                               (r, r), r)
            surf.blit(glow_surf,
                      (int(self.moon_x) - r, int(self.moon_y) - r),
                      special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.circle(surf, (230, 240, 255),
                           (int(self.moon_x), int(self.moon_y)), 18)

        # Ground
        ground_y = int(self.h * 0.72)
        pygame.draw.rect(surf, GROUND_COL, (0, ground_y, self.w, self.h - ground_y))
        # ground highlight stripe
        pygame.draw.line(surf, clamp_color(lerp_color(GROUND_COL, (80, 160, 80), 0.35)),
                         (0, ground_y), (self.w, ground_y), 2)

        # Foliage blobs
        for b in self.foliage:
            pygame.draw.ellipse(surf, b['col'],
                                (b['x'] - b['r'], b['y'] - b['r'] // 2,
                                 b['r'] * 2, b['r']))

        # Atmospheric depth haze at horizon
        haze = pygame.Surface((self.w, 60), pygame.SRCALPHA)
        for i in range(60):
            a = int(18 * (1 - i / 60))
            pygame.draw.line(haze, (80, 130, 80, a), (0, i), (self.w, i))
        surf.blit(haze, (0, ground_y - 30))


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
    pygame.display.set_caption("🌹 Blooming Rose")
    clock = pygame.time.Clock()

    garden    = Garden(WIDTH, HEIGHT)
    rose      = Rose(WIDTH // 2, int(HEIGHT * 0.48))
    fireflies = make_fireflies(18)

    # Camera wobble state
    cam_wobble = 0.0
    cam_target = 0.0
    cam_vel    = 0.0

    elapsed = 0.0
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)     # clamp to avoid spiral on focus-loss
        elapsed += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

        # ── Bloom cycle ───────────────────────────────────────────────────────
        cycle_t  = elapsed % CYCLE
        if cycle_t < BLOOM_DURATION:
            bloom = cycle_t / BLOOM_DURATION
        elif cycle_t < BLOOM_DURATION + HOLD_DURATION:
            bloom = 1.0
        else:
            bloom = 1.0 - (cycle_t - BLOOM_DURATION - HOLD_DURATION) / CLOSE_DURATION
        bloom = max(0.0, min(1.0, bloom))

        # ── Gentle camera sway ─────────────────────────────────────────────
        # Drift cam target slowly
        if random.random() < 0.008:
            cam_target = random.uniform(-1.0, 1.0)
        spring_k = 1.8
        damping  = 3.5
        cam_vel += (cam_target - cam_wobble) * spring_k * dt
        cam_vel -= cam_vel * damping * dt
        cam_wobble += cam_vel * dt

        # ── Draw ──────────────────────────────────────────────────────────────
        garden.draw(screen, elapsed)

        # Soft spotlight under the rose
        spot_r = 180
        spot_surf = pygame.Surface((spot_r * 2, spot_r), pygame.SRCALPHA)
        for r in range(spot_r, 0, -4):
            a = int(22 * (1 - r / spot_r) * bloom)
            pygame.draw.ellipse(spot_surf, (255, 200, 150, a),
                                (spot_r - r, (spot_r - r // 2) // 2,
                                 r * 2, r))
        screen.blit(spot_surf,
                    (rose.cx - spot_r, rose.cy + 40))

        # Rose
        rose.draw(screen, bloom, cam_wobble)

        # Fireflies
        for ff in fireflies:
            ff.update(dt)
            ff.draw(screen, elapsed)

        # Subtle vignette
        vig = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for r in range(0, 200, 8):
            a = int(r * 0.22)
            pygame.draw.rect(vig, (0, 0, 0, min(a, 80)),
                             (r, r, WIDTH - 2 * r, HEIGHT - 2 * r), 8)
        screen.blit(vig, (0, 0))

        # FPS counter (subtle, top-left)
        fps_val = clock.get_fps()
        font    = pygame.font.SysFont("monospace", 13)
        fps_txt = font.render(f"{fps_val:.0f} fps", True, (80, 100, 80))
        screen.blit(fps_txt, (8, 6))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()