bl_info = {
    "name": "Laser Tracer",
    "author": "Christian F. (known as Chryfi)",
    "version": (1, 1, 0),
    "blender": (3, 0, 0),
    "location": "3D window toolshelf > laser tracer tab",
    "description": "",
    "warning": "",
    "category": "Object"
}

import bpy

from .laser_tracer import *
from .props import *
from .utils import *

classes = (
LASER_TRACER_Props,
LASER_TRACER_PT,
LASER_TRACER_OT
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

        if issubclass(cls, LASER_TRACER_RegisterModule):
            cls.register()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

        if issubclass(cls, LASER_TRACER_RegisterModule):
            cls.unregister()


if __name__ == "__main__":
    register()