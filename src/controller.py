import glob
import os
import sys

import pygame
from pygame import locals

try:
    sys.path.append(
        glob.glob(
            "/opt/carla-simulator/PythonAPI/carla/dist/carla-*%d.%d-%s.egg"
            % (sys.version_info.major, sys.version_info.minor, "win-amd64" if os.name == "nt" else "linux-x86_64")
        )[0]
    )
except IndexError:
    pass

import carla

"""
Welcome to CARLA manual control.

Use ARROWS or WASD keys for control.

    W            : throttle
    S            : brake
    A/D          : steer left/right
    Q            : toggle reverse
    Space        : hand-brake
    P            : toggle autopilot
    M            : toggle manual transmission
    ,/.          : gear up/down
    CTRL + W     : toggle constant velocity mode at 60 km/h

    L            : toggle next light type
    SHIFT + L    : toggle high beam
    Z/X          : toggle right/left blinker
    I            : toggle interior light

    TAB          : change sensor position
    ` or N       : next sensor
    [1-9]        : change to sensor [1-9]
    G            : toggle radar visualization
    C            : change weather (Shift+C reverse)
    Backspace    : change vehicle

    V            : Select next map layer (Shift+V reverse)
    B            : Load current selected map layer (Shift+B to unload)

    R            : toggle recording images to disk

    CTRL + R     : toggle recording of simulation (replacing any previous)
    CTRL + P     : start replaying last recorded simulation
    CTRL + +     : increments the start time of the replay by 1 second (+SHIFT = 10 seconds)
    CTRL + -     : decrements the start time of the replay by 1 second (+SHIFT = 10 seconds)

    F1           : toggle HUD
    H/?          : toggle help
    ESC          : quit
"""


class KeyboardControl:
    """Class that handles keyboard input."""

    def __init__(self, world, start_in_autopilot):
        self._carsim_enabled = False
        self._carsim_road = False
        self._autopilot_enabled = start_in_autopilot
        if isinstance(world.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            self._lights = carla.VehicleLightState.NONE
            world.player.set_autopilot(self._autopilot_enabled)
            world.player.set_light_state(self._lights)
        elif isinstance(world.player, carla.Walker):
            self._control = carla.WalkerControl()
            self._autopilot_enabled = False
            self._rotation = world.player.get_transform().rotation
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0
        world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)

    def parse_events(self, client, world, clock):
        if isinstance(self._control, carla.VehicleControl):
            current_lights = self._lights
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                elif event.key == locals.K_BACKSPACE:
                    if self._autopilot_enabled:
                        world.player.set_autopilot(False)
                        world.restart()
                        world.player.set_autopilot(True)
                    else:
                        world.restart()
                elif event.key == locals.K_F1:
                    world.hud.toggle_info()
                elif event.key == locals.K_v and pygame.key.get_mods() & locals.KMOD_SHIFT:
                    world.next_map_layer(reverse=True)
                elif event.key == locals.K_v:
                    world.next_map_layer()
                elif event.key == locals.K_b and pygame.key.get_mods() & locals.KMOD_SHIFT:
                    world.load_map_layer(unload=True)
                elif event.key == locals.K_b:
                    world.load_map_layer()
                elif event.key == locals.K_h or (
                    event.key == locals.K_SLASH and pygame.key.get_mods() & locals.KMOD_SHIFT
                ):
                    world.hud.help.toggle()
                elif event.key == locals.K_TAB:
                    world.camera_manager.toggle_camera()
                elif event.key == locals.K_c and pygame.key.get_mods() & locals.KMOD_SHIFT:
                    world.next_weather(reverse=True)
                elif event.key == locals.K_c:
                    world.next_weather()
                elif event.key == locals.K_g:
                    world.toggle_radar()
                elif event.key == locals.K_BACKQUOTE:
                    world.camera_manager.next_sensor()
                elif event.key == locals.K_n:
                    world.camera_manager.next_sensor()
                elif event.key == locals.K_w and (pygame.key.get_mods() & locals.KMOD_CTRL):
                    if world.constant_velocity_enabled:
                        world.player.disable_constant_velocity()
                        world.constant_velocity_enabled = False
                        world.hud.notification("Disabled Constant Velocity Mode")
                    else:
                        world.player.enable_constant_velocity(carla.Vector3D(17, 0, 0))
                        world.constant_velocity_enabled = True
                        world.hud.notification("Enabled Constant Velocity Mode at 60 km/h")
                elif event.key > locals.K_0 and event.key <= locals.K_9:
                    world.camera_manager.set_sensor(event.key - 1 - locals.K_0)
                elif event.key == locals.K_r and not (pygame.key.get_mods() & locals.KMOD_CTRL):
                    world.camera_manager.toggle_recording()
                elif event.key == locals.K_r and (pygame.key.get_mods() & locals.KMOD_CTRL):
                    if world.recording_enabled:
                        client.stop_recorder()
                        world.recording_enabled = False
                        world.hud.notification("Recorder is OFF")
                    else:
                        client.start_recorder("manual_recording.rec")
                        world.recording_enabled = True
                        world.hud.notification("Recorder is ON")
                elif event.key == locals.K_p and (pygame.key.get_mods() & locals.KMOD_CTRL):
                    # stop recorder
                    client.stop_recorder()
                    world.recording_enabled = False
                    # work around to fix camera at start of replaying
                    current_index = world.camera_manager.index
                    world.destroy_sensors()
                    # disable autopilot
                    self._autopilot_enabled = False
                    world.player.set_autopilot(self._autopilot_enabled)
                    world.hud.notification("Replaying file 'manual_recording.rec'")
                    # replayer
                    client.replay_file("manual_recording.rec", world.recording_start, 0, 0)
                    world.camera_manager.set_sensor(current_index)
                elif event.key == locals.K_k and (pygame.key.get_mods() & locals.KMOD_CTRL):
                    print("k pressed")
                    world.player.enable_carsim("d:/CVC/carsim/DataUE4/ue4simfile.sim")
                elif event.key == locals.K_j and (pygame.key.get_mods() & locals.KMOD_CTRL):
                    self._carsim_road = not self._carsim_road
                    world.player.use_carsim_road(self._carsim_road)
                    print("j pressed, using carsim road =", self._carsim_road)
                # elif event.key == K_i and (pygame.key.get_mods() & KMOD_CTRL):
                #     print("i pressed")
                #     imp = carla.Location(z=50000)
                #     world.player.add_impulse(imp)
                elif event.key == locals.K_MINUS and (pygame.key.get_mods() & locals.KMOD_CTRL):
                    if pygame.key.get_mods() & locals.KMOD_SHIFT:
                        world.recording_start -= 10
                    else:
                        world.recording_start -= 1
                    world.hud.notification("Recording start time is %d" % (world.recording_start))
                elif event.key == locals.K_EQUALS and (pygame.key.get_mods() & locals.KMOD_CTRL):
                    if pygame.key.get_mods() & locals.KMOD_SHIFT:
                        world.recording_start += 10
                    else:
                        world.recording_start += 1
                    world.hud.notification("Recording start time is %d" % (world.recording_start))
                if isinstance(self._control, carla.VehicleControl):
                    if event.key == locals.K_q:
                        self._control.gear = 1 if self._control.reverse else -1
                    elif event.key == locals.K_m:
                        self._control.manual_gear_shift = not self._control.manual_gear_shift
                        self._control.gear = world.player.get_control().gear
                        world.hud.notification(
                            "%s Transmission" % ("Manual" if self._control.manual_gear_shift else "Automatic")
                        )
                    elif self._control.manual_gear_shift and event.key == locals.K_s:
                        self._control.gear = max(-1, self._control.gear - 1)
                    elif self._control.manual_gear_shift and event.key == locals.K_w:
                        self._control.gear = self._control.gear + 1
                    elif event.key == locals.K_p and not pygame.key.get_mods() & locals.KMOD_CTRL:
                        self._autopilot_enabled = not self._autopilot_enabled
                        world.player.set_autopilot(self._autopilot_enabled)
                        world.hud.notification("Autopilot %s" % ("On" if self._autopilot_enabled else "Off"))
                    elif event.key == locals.K_l and pygame.key.get_mods() & locals.KMOD_CTRL:
                        current_lights ^= carla.VehicleLightState.Special1
                    elif event.key == locals.K_l and pygame.key.get_mods() & locals.KMOD_SHIFT:
                        current_lights ^= carla.VehicleLightState.HighBeam
                    elif event.key == locals.K_l:
                        # Use 'L' key to switch between lights:
                        # closed -> position -> low beam -> fog
                        if not self._lights & carla.VehicleLightState.Position:
                            world.hud.notification("Position lights")
                            current_lights |= carla.VehicleLightState.Position
                        else:
                            world.hud.notification("Low beam lights")
                            current_lights |= carla.VehicleLightState.LowBeam
                        if self._lights & carla.VehicleLightState.LowBeam:
                            world.hud.notification("Fog lights")
                            current_lights |= carla.VehicleLightState.Fog
                        if self._lights & carla.VehicleLightState.Fog:
                            world.hud.notification("Lights off")
                            current_lights ^= carla.VehicleLightState.Position
                            current_lights ^= carla.VehicleLightState.LowBeam
                            current_lights ^= carla.VehicleLightState.Fog
                    elif event.key == locals.K_i:
                        current_lights ^= carla.VehicleLightState.Interior
                    elif event.key == locals.K_z:
                        current_lights ^= carla.VehicleLightState.LeftBlinker
                    elif event.key == locals.K_x:
                        current_lights ^= carla.VehicleLightState.RightBlinker

        if not self._autopilot_enabled:
            if isinstance(self._control, carla.VehicleControl):
                self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
                self._control.reverse = self._control.gear < 0
                # Set automatic control-related vehicle lights
                if self._control.brake:
                    current_lights |= carla.VehicleLightState.Brake
                else:  # Remove the Brake flag
                    current_lights &= ~carla.VehicleLightState.Brake
                if self._control.reverse:
                    current_lights |= carla.VehicleLightState.Reverse
                else:  # Remove the Reverse flag
                    current_lights &= ~carla.VehicleLightState.Reverse
                if current_lights != self._lights:  # Change the light state only if necessary
                    self._lights = current_lights
                    world.player.set_light_state(carla.VehicleLightState(self._lights))
            elif isinstance(self._control, carla.WalkerControl):
                self._parse_walker_keys(pygame.key.get_pressed(), clock.get_time(), world)
            world.player.apply_control(self._control)

    def _parse_vehicle_keys(self, keys, milliseconds):
        if keys[locals.K_UP]:
            self._control.throttle = min(self._control.throttle + 0.01, 1)
        else:
            self._control.throttle = 0.0

        if keys[locals.K_DOWN]:
            self._control.brake = min(self._control.brake + 0.2, 1)
        else:
            self._control.brake = 0

        steer_increment = 5e-4 * milliseconds
        if keys[locals.K_LEFT] or keys[locals.K_a]:
            if self._steer_cache > 0:
                self._steer_cache = 0
            else:
                self._steer_cache -= steer_increment
        elif keys[locals.K_RIGHT] or keys[locals.K_d]:
            if self._steer_cache < 0:
                self._steer_cache = 0
            else:
                self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.hand_brake = keys[locals.K_SPACE]

    def _parse_walker_keys(self, keys, milliseconds, world):
        self._control.speed = 0.0
        if keys[locals.K_DOWN]:
            self._control.speed = 0.0
        if keys[locals.K_LEFT] or keys[locals.K_a]:
            self._control.speed = 0.01
            self._rotation.yaw -= 0.08 * milliseconds
        if keys[locals.K_RIGHT] or keys[locals.K_d]:
            self._control.speed = 0.01
            self._rotation.yaw += 0.08 * milliseconds
        if keys[locals.K_UP]:
            self._control.speed = (
                world.player_max_speed_fast if pygame.key.get_mods() & locals.KMOD_SHIFT else world.player_max_speed
            )
        self._control.jump = keys[locals.K_SPACE]
        self._rotation.yaw = round(self._rotation.yaw, 1)
        self._control.direction = self._rotation.get_forward_vector()

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == locals.K_ESCAPE) or (key == locals.K_q and pygame.key.get_mods() & locals.KMOD_CTRL)
