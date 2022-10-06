import bpy
from .utils import *
import math

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
        layout.prop(properties, "end_time_offset")

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
                t1 = int(fcurve.keyframe_points[0].co[0]) + properties.end_time_offset

                scene.frame_set(t1)
                tracker_pos = tracker.matrix_world.to_translation()

                # find the minimum distance for the velocity
                # behind and in front to later calculate the optimum point taking
                # motionblur correction into consideration
                t0_behind = -1
                min_distance_behind = math.inf
                t0_after = -1
                min_distance_after = math.inf

                for t in range(0, t1):
                    scene.frame_set(t)

                    start = origin.matrix_world.to_translation()

                    n = tracker_pos - start
                    n.normalize()

                    end = start + n * (t1 - t) * vel
                    test_behind = n.dot(end - tracker_pos)
                    diff = tracker_pos - end

                    if test_behind < 0:
                        if diff.length < min_distance_behind:
                            min_distance_behind = diff.length
                            t0_behind = t
                    else:
                        if diff.length < min_distance_after:
                            min_distance_after = diff.length
                            t0_after = t

                if t0_behind != -1 and t0_after != -1:
                    scene.frame_set(t0_behind)
                    start_behind = origin.matrix_world.to_translation()

                    scene.frame_set(t0_after)
                    start_after = origin.matrix_world.to_translation()

                    end = tracker_pos.copy()
                    # end = start + distance * (t1 - minT) * vel
                    new_end_behind = self.optim(start_behind, end, t0_behind, t1, motionblur)
                    vel_behind = (new_end_behind - start_behind).length / (t1 - t0_behind)

                    new_end_after = self.optim(start_after, end, t0_after, t1, motionblur)
                    vel_after = (new_end_after - start_after).length / (t1 - t0_after)

                    if abs(vel_after - vel) < abs(vel_behind - vel):
                        obj_name = tracker.name
                        curve_name = tracker.name + "_d" + str(round(vel_after - vel, 2))
                        self.create_laser_path(t0_after, t1, start_after, new_end_after, curve_name, obj_name, laser_obj)
                    else:
                        obj_name = tracker.name
                        curve_name = tracker.name + "_d" + str(round(vel_behind - vel, 2))
                        self.create_laser_path(t0_behind, t1, start_behind, new_end_behind, curve_name, obj_name, laser_obj)

        return {'FINISHED'}

    def optim(self, start, end, t0, t1, motionblur, r=10000):
        n = end - start

        n.normalize()

        new_end = end.copy()
        i = 0

        while True and i < r:
            new_vel = (start - new_end).length / (t1 - t0)
            motionblur_end = start + n * ((t1 - 1 - t0) * new_vel + motionblur * new_vel)
            new_end += end - motionblur_end

            # the motionblur_end should be at the original end
            if (motionblur_end - end).length < 0.000001:
                print("Found optimum")
                break

            i += 1

            if i == r:
                print("Didn't find optimum")

        return new_end

    def create_laser_path(self, t0, t1, start, end, curve_name: str, laser_name: str, laser_obj):
        # bpy.context.scene.frame_set(t1)
        lasers_coll = get_or_create_collection(bpy.context.scene.collection, "lasers")
        curves_coll = get_or_create_collection(lasers_coll, "curves")

        # setup curve
        curve = create_curve(start, end, curve_name + "_curve")

        curve.splines.active.points[0].co = (0, 0, 0, 1)
        curve.splines.active.points[1].co = (end - start).to_4d()
        curve.splines.active.points[1].co.w = 1

        curve_obj = bpy.data.objects.new(curve_name + "_curve", curve)
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
        laser.name = laser_name + "_laser"

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