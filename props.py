import bpy
from bpy.props import (BoolProperty, IntProperty, EnumProperty, PointerProperty, StringProperty, FloatProperty)

from .utils import *


class LASER_TRACER_Props(bpy.types.PropertyGroup, LASER_TRACER_RegisterModule):
    trackers_root_collection: PointerProperty(name="Define the root collecion that contains all of the trackers",
                                              type=bpy.types.Collection)
    laser_origin: PointerProperty(name="Define the origin object from which the laser bolts should originate",
                                  type=bpy.types.Object)
    lightsaber_top: PointerProperty(name="Tip of the lightsaber object. If this is defined, the laser bolts will be "
                                         "reflected off the lightsaber",
                                    type=bpy.types.Object)
    lightsaber_bottom: PointerProperty(name="Bottom of the lightsaber object. If this is defined, the laser bolts "
                                            "will be reflected off the lightsaber",
                                       type=bpy.types.Object)
    laser_obj: PointerProperty(name="Define the laser object.", type=bpy.types.Object)
    velocity: FloatProperty(name="Velocity", description="The velocity of the laser bolts in meters / frame", default=3.5)
    motionblur: FloatProperty(name="Motionblur", description="The motionblur to take into the calculation. It should "
                                                             "be the same as the render motionblur", default=1.0)
    end_time_offset: IntProperty(name="Time Offset",
                                 description="Define after how many frames after the first keyframe of the tracker "
                                             "the laser should impact.", default=1)
    object_mb_steps: IntProperty(name="Object Motionblur Steps",
                                 description="Define the motionblur steps each laser object should have. This should "
                                             "be increased when lightsaber reflection is used", default=1)
    laser_axis: EnumProperty(name="Laser Axis",
                             description="Axis of the laser. This would be used for the modifiers / constraints",
                             items={('X', 'X', 'X'), ('Y', 'Y', 'Y'), ('Z', 'Z', 'Z'), ('-X', '-X', '-X'), \
                                   ('-Y', '-Y', '-Y'), ('-Z', '-Z', '-Z')}, default='Y')

    def register():
        bpy.types.Scene.lasertracer = bpy.props.PointerProperty(type=LASER_TRACER_Props)

    #def unregister():
        #del bpy.types.Scene.lasertracer