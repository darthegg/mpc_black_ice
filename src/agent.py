import glob
import os
import sys

import pygame

sys.path.append(
    glob.glob(
        "/opt/carla-simulator/PythonAPI/carla/dist/carla-*%d.%d-%s.egg"
        % (sys.version_info.major, sys.version_info.minor, "win-amd64" if os.name == "nt" else "linux-x86_64")
    )[0]
)

import carla

from src.controller import KeyboardControl
from src.interface import HUD
from src.world import World


class Agent:
    """Player class."""

    def __init__(self, args):
        pygame.init()
        pygame.font.init()

        self.client = carla.Client(args.host, args.port)
        self.client.set_timeout(2.0)

        self.display = pygame.display.set_mode((args.width, args.height), pygame.HWSURFACE | pygame.DOUBLEBUF)

        self.hud = HUD(args.width, args.height)
        self.world = World(self.client.get_world(), self.hud, args)

        self.controller = KeyboardControl(self.world, args.autopilot)

        self.clock = pygame.time.Clock()

    def run(self):
        while self.controller.end_control is not True:
            self.clock.tick_busy_loop(60)
            self.controller.parse_events(self.client, self.world, self.clock)
            self.world.tick(self.clock)
            self.world.render(self.display)
            pygame.display.flip()

        if self.world and self.world.recording_enabled:
            self.client.stop_recorder()

        if self.world is not None:
            self.world.destroy()

        pygame.quit()
