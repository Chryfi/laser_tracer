import bpy
from .utils import *

class LASER_TRACER_PT(bpy.types.Panel):
    bl_label = "Laser Tracer"
    bl_idname = "LASER_TRACER_PT"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Laser Tracer"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        properties = scene.lasertracer

        layout.prop_search(properties, "trackers_root_collection", bpy.data, "collections", text="Trackers")
        layout.prop_search(properties, "laser_origin", scene, "objects", text="Emitter")
        layout.prop_search(properties, "laser_obj", bpy.data, "objects", text="Laser")
        layout.prop(properties, "velocity")
        layout.prop(properties, "motionblur")

        layout.operator("laser_tracer.laser_tracer", text="Execute")


class LASER_TRACER_OT(bpy.types.Operator):
    bl_label = "Laser Tracer"
    bl_idname = "laser_tracer.laser_tracer"

    def execute(self, context):
        scene = context.scene
        properties = scene.lasertracer
        trackers = properties.trackers_root_collection.objects
        vel = properties.velocity  # meters / frame
        motionblur = properties.motionblur
        origin = properties.laser_origin
        laser_obj = properties.laser_obj

        if laser_obj is None or origin is None or trackers is None:
            return {'CANCELLED'}

        # with motionblur 1 because of the disappearance at the next frame
        # the laser is interpolated with approximately motionblur 0.5
        if motionblur == 1:
            motionblur = 0.5

        for tracker in trackers:
            if tracker is None:
                continue

            fcurve = get_fcurve(tracker, "location")

            if not fcurve is None:
                # end point should be at the next frame where the sparks begin to show
                t1 = int(fcurve.keyframe_points[0].co[0]) + 1

                scene.frame_set(t1)
                trackerPos = tracker.matrix_world.to_translation()

                minT = -1
                minDistance = -1

                # find the minimum distance for the velocity
                for t in range(0, t1):
                    scene.frame_set(t)

                    distance = trackerPos - origin.matrix_world.to_translation()

                    distance.normalize()

                    end = origin.matrix_world.to_translation() + distance * (t1 - t) * vel
                    diff = trackerPos - end

                    if minDistance == -1:
                        minDistance = diff.length
                        minT = t
                    elif diff.length < minDistance:
                        minDistance = diff.length
                        minT = t

                if minT != -1:
                    scene.frame_set(minT)

                    distance = trackerPos - origin.matrix_world.to_translation()

                    distance.normalize()

                    end = origin.matrix_world.to_translation() + distance * (t1 - minT) * vel
                    motionblurdiff = end - (origin.matrix_world.to_translation() + distance * ((t1 - 1 - minT) * vel + motionblur * vel))
                    # motionblurdiff = trackerPos - (origin.matrix_world.to_translation() + distance * ((t1 - 1 - minT) * vel + motionblur * vel))
                    # test = trackerPos - distance * motionblur * vel
                    # new_vel = (trackerPos - origin.matrix_world.to_translation()).length / (t1 - minT)

                    # TODO (just a little bit) because motionblur diff it makes the path longer - velocity slower -> motionblur slower -> optimization problem
                    self.create_laser_path(minT, t1, origin.matrix_world.to_translation(), end + motionblurdiff, tracker.name, laser_obj)

        return {'FINISHED'}

    def create_laser_path(self, t0, t1, start, end, name: str, laser_obj):
        # bpy.context.scene.frame_set(t1)
        lasers_coll = get_or_create_collection(bpy.context.scene.collection, "lasers")
        curves_coll = get_or_create_collection(lasers_coll, "curves")

        # setup curve
        curve = create_curve(start, end, name + "_curve")

        curve.splines.active.points[0].co = (0, 0, 0, 1)
        curve.splines.active.points[1].co = (end - start).to_4d()
        curve.splines.active.points[1].co.w = 1

        curve_obj = bpy.data.objects.new(name + "_curve", curve)
        curves_coll.objects.link(curve_obj)
        curve_obj.location = start

        # animate evaluation time
        curve.eval_time = 0
        curve.keyframe_insert('eval_time', frame=t0)
        curve.eval_time = t1 - t0
        curve.keyframe_insert('eval_time', frame=t1)
        curve.path_duration = t1 - t0

        convert_interpolation(get_fcurve(curve, "eval_time"), 'LINEAR')

        # add constraint to object to curve
        laser = copy_object(laser_obj, lasers_coll)
        laser.name = name + "_laser"

        laser.hide_render = True
        laser.keyframe_insert('hide_render', frame=t0 - 1)
        laser.hide_render = False
        laser.keyframe_insert('hide_render', frame=t0)

        laser.hide_render = False
        laser.keyframe_insert('hide_render', frame=t1 - 1)
        laser.hide_render = True
        laser.keyframe_insert('hide_render', frame=t1)

        constraint = laser.constraints.new('FOLLOW_PATH')
        constraint.target = curve_obj
        constraint.use_curve_follow = True