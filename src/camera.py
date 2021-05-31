import glob
import os
import sys
import weakref

import numpy as np
import pygame

sys.path.append(
    glob.glob(
        "/opt/carla-simulator/PythonAPI/carla/dist/carla-*%d.%d-%s.egg"
        % (sys.version_info.major, sys.version_info.minor, "win-amd64" if os.name == "nt" else "linux-x86_64")
    )[0]
)

import carla


class CameraManager:
    def __init__(self, parent_actor, hud, gamma_correction):
        self.sensor = None
        self.surface = None
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        bound_y = 0.5 + self._parent.bounding_box.extent.y
        Attachment = carla.AttachmentType
        self._camera_transforms = [
            (carla.Transform(carla.Location(x=-5.5, z=2.5), carla.Rotation(pitch=8.0)), Attachment.SpringArm),
            (carla.Transform(carla.Location(x=1.6, z=1.7)), Attachment.Rigid),
            (carla.Transform(carla.Location(x=5.5, y=1.5, z=1.5)), Attachment.SpringArm),
            (carla.Transform(carla.Location(x=-8.0, z=6.0), carla.Rotation(pitch=6.0)), Attachment.SpringArm),
            (carla.Transform(carla.Location(x=-1, y=-bound_y, z=0.5)), Attachment.Rigid),
        ]
        self.transform_index = 1
        self._sensor_list = ["sensor.camera.rgb", carla.ColorConverter.Raw, "Camera RGB", {}]

        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()

        self.bp = bp_library.find(self._sensor_list[0])
        self.bp.set_attribute("image_size_x", str(hud.dim[0]))
        self.bp.set_attribute("image_size_y", str(hud.dim[1]))
        if self.bp.has_attribute("gamma"):
            self.bp.set_attribute("gamma", str(gamma_correction))

    def toggle_camera(self):
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.set_sensor()

    def set_sensor(self):
        if self.sensor is not None:
            self.sensor.destroy()
            self.surface = None
        self.sensor = self._parent.get_world().spawn_actor(
            self.bp,
            self._camera_transforms[self.transform_index][0],
            attach_to=self._parent,
            attachment_type=self._camera_transforms[self.transform_index][1],
        )
        # We need to pass the lambda a weak reference to self to avoid
        # circular reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))

    def toggle_recording(self):
        self.recording = not self.recording
        self.hud.notification("Recording %s" % ("On" if self.recording else "Off"))

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self:
            return
        image.convert(self._sensor_list[1])
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self.recording:
            image.save_to_disk("_out/%08d" % image.frame)
