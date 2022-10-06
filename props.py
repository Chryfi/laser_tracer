import bpy
from bpy.props import (BoolProperty, IntProperty, PointerProperty, StringProperty, FloatProperty)

from .utils import *


class LASER_TRACER_Props(bpy.types.PropertyGroup, LASER_TRACER_RegisterModule):
    trackers_root_collection: PointerProperty(name="Define the root collecion that contains all of the trackers.",
                                              type=bpy.types.Collection)
    laser_origin: PointerProperty(name="Define the origin object from which the laser bolts should originate.",
                                  type=bpy.types.Object)
    laser_obj: PointerProperty(name="Define the laser object.", type=bpy.types.Object)
    velocity: FloatProperty(name="Velocity", description="The velocity of the laser bolts in meters / frame.", default=3.5)
    motionblur: FloatProperty(name="Motionblur", description="The motionblur to take into the calculation. It should "
                                                             "be the same as the render motionblur.", default=1.0)
    end_time_offset: IntProperty(name="Time Offset", description="Define after how many frames after the first "
                                                                 "keyframe of the tracker the laser should impact.", default=1)

    def register():
        bpy.types.Scene.lasertracer = bpy.props.PointerProperty(type=LASER_TRACER_Props)

    #def unregister():
        #del bpy.types.Scene.lasertracer