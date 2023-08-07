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
    motionblur: FloatProperty(name="Laser Motionblur", description="The motionblur to take into the calculation. It should "
                                                             "be the same as the render motionblur", default=1.0, min=0.0)
    end_time_offset: IntProperty(name="Time Offset",
                                 description="Define after how many frames after the first keyframe of the tracker "
                                             "the laser should impact.", default=1)
    laser_time_range: IntProperty(name="Time Range",
                                  description="How long the range of frames to search for should be each laser. Save "
                                              "some performance..", default=200, min=2)
    object_mb_steps: IntProperty(name="Object Motionblur Steps",
                                 description="Define the value for the \"motionblur steps\" setting for each laser object. This should "
                                             "be increased when lightsaber reflection is used, as the hard edge needs more steps.", default=1, min=1, max=7)
    lightsaber_motionblur: FloatProperty(name="Lightsaber Motionblur", description="", default=1.0, min=0.0)
    """laser_length: FloatProperty(name="Laser Length",
                                description="The length of the laser bolt to use for things like reflection",
                                default=1.0, min=0.0)"""
    start_at_emitter: BoolProperty(name="Start at emitter", description="When this is enabled, the start time of each laser is determined by the next keyframe of the emitter.")
    laser_axis: EnumProperty(name="Laser Axis",
                             description="Axis of the laser. This would be used for the modifiers / constraints",
                             items={('X', 'X', 'X'), ('Y', 'Y', 'Y'), ('Z', 'Z', 'Z'), ('-X', '-X', '-X'), \
                                   ('-Y', '-Y', '-Y'), ('-Z', '-Z', '-Z')}, default='Y')

    def register():
        bpy.types.Scene.lasertracer = bpy.props.PointerProperty(type=LASER_TRACER_Props)

    #def unregister():
        #del bpy.types.Scene.lasertracer