from typing import overload

import bpy
from .utils import *
import math
import random
import mathutils


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
        layout.prop_search(properties, "lightsaber_top", bpy.data, "objects", text="Lightsaber Top")
        layout.prop_search(properties, "lightsaber_bottom", bpy.data, "objects", text="Lightsaber Bottom")
        layout.prop(properties, "velocity")
        layout.prop(properties, "motionblur")
        layout.prop(properties, "lightsaber_motionblur")
        layout.prop(properties, "end_time_offset")
        layout.prop(properties, "laser_axis")
        layout.prop(properties, "object_mb_steps")
        layout.prop(properties, "laser_length")
        layout.prop(properties, "laser_time_range")
        layout.prop(properties, "start_at_emitter")

        layout.operator("laser_tracer.laser_tracer", text="Execute")


class Path:
    def __init__(self, start, t0, t1):
        self.start = start.copy()
        self.points = [self.start]
        self.t0 = min(t0, t1)
        self.t1 = max(t0, t1)

    def calculate_path(self, targets0: list, velocity):
        targets = [i for i in targets0 if i is not None]

        factor = (self.t1 - self.t0) * velocity

        for i in range(len(targets)):
            point = targets[i]
            n = (point - self.points[i]).normalized()

            end = self.points[i] + n * factor

            behind = n.dot(point - end)

            if behind < 0 and i < len(targets) - 1:
                # end is beyond the target point, target the next point
                factor = (point - end).length

                self.points.append(point.copy())
            else:
                self.points.append(end)

                break

    def dot_end_vec(self, point):
        if len(self.points) < 2:
            return 0

        n = self.points[-1] - self.points[-2]

        return n.dot(self.points[-1] - point)

    def copy(self):
        copy = Path(self.start.copy(), self.t0, self.t1)

        copy.points.clear()

        for i in range(len(self.points)):
            copy.points.append(self.points[i].copy())

        return copy

    # length until the point at the given index p
    def length(self, p=None):
        if p is None:
            p = len(self.points) - 1

        if p <= 0:
            return 0

        sum_length = 0

        for i in range(1, p + 1):
            sum_length += (self.points[i - 1] - self.points[i]).length

        return sum_length

    def velocity(self):
        return self.length() / (self.t1 - self.t0)

    # get a point on the path at the provided time
    def interpolate_point(self, t):
        if t > self.t1 - self.t0:
            return self.points[-1].copy()

        if len(self.points) < 2:
            return self.start.copy()

        s = t * self.velocity()

        for i in range(1, len(self.points)):
            l = self.length(p=i)

            if s < l:
                n = (self.points[i] - self.points[i - 1]).normalized()
                n *= l - s

                return self.points[i] - n

    def get_t_of_point(self, point):
        for i in range(1, len(self.points)):
            a = self.points[i - 1]
            n = self.points[i] - a

            r0 = (point[0] - a[0]) / n[0]
            r1 = (point[1] - a[1]) / n[1]
            r2 = (point[2] - a[2]) / n[2]

            if r0 == r1 == r2 and 0 <= r0 <= 1 or i == len(self.points) - 1:
                l = self.length(p=i - 1) + r0 * n.length

                return l / self.velocity()


class LASER_TRACER_OT(bpy.types.Operator):
    bl_label = "Laser Tracer"
    bl_idname = "laser_tracer.laser_tracer"

    def execute(self, context):
        scene = context.scene
        self.props = scene.lasertracer
        trackers = self.props.trackers_root_collection.objects
        vel = self.props.velocity  # meters / frame
        motionblur = self.props.motionblur
        emitter = self.props.laser_origin
        laser_obj = self.props.laser_obj
        lightsaber_top = self.props.lightsaber_top
        lightsaber_bottom = self.props.lightsaber_bottom
        time_range = self.props.laser_time_range
        lightsaber_mb = self.props.lightsaber_motionblur
        start_at_emitter = self.props.start_at_emitter

        if laser_obj is None or emitter is None or trackers is None or (bool(lightsaber_top) ^ bool(lightsaber_bottom)):
            return {'CANCELLED'}

        # with motionblur 1 because of the disappearance at the next frame
        # the laser is interpolated with approximately motionblur 0.5
        if motionblur == 1:
            motionblur = 0.5

        emitter_fcurve = get_fcurve(emitter, "location")

        for tracker_index in range(len(trackers)):
            tracker = trackers[tracker_index]
            if tracker is None:
                continue

            fcurve = get_fcurve(tracker, "location")

            if not fcurve is None:
                # end point should be at the next frame where the sparks begin to show
                t1 = int(fcurve.keyframe_points[0].co[0]) + self.props.end_time_offset

                scene.frame_set(t1)
                tracker_pos = tracker.matrix_world.to_translation()

                # find the minimum distance for the velocity
                # behind and in front to later calculate the optimum point taking
                # motionblur correction into consideration

                # first pair: laser hits before target
                # second pair: laser shot behind target
                compare = [[math.inf, None], [math.inf, None]]

                reflect_point = None
                rand = random.random()
                use_reflect = lightsaber_top is not None and lightsaber_bottom is not None

                start_t = max(0, t1 - time_range)

                if start_at_emitter:
                    if tracker_index >= len(emitter_fcurve.keyframe_points):
                        break

                    start_t = int(emitter_fcurve.keyframe_points[tracker_index].co[0]) + self.props.end_time_offset
                    t1 = start_t + time_range

                scene.frame_set(start_t)

                origin = emitter.matrix_world.to_translation()

                for t in range(start_t, t1):
                    scene.frame_set(t)
                    #TODO use motionblur for the origin too?
                    if not start_at_emitter:
                        origin = emitter.matrix_world.to_translation()

                    if start_at_emitter:
                        path = Path(origin, start_t, t)
                    else:
                        path = Path(origin, t, t1)

                    new_vel = vel

                    if use_reflect:
                        # find the first point in time where the laser might hit the lightsaber
                        for tr in range(start_t, t1):
                            #calculate the lightsaber position with motionblur
                            scene.frame_set(tr)
                            ls = lightsaber_top.matrix_world.to_translation() - lightsaber_bottom.matrix_world.to_translation()
                            reflect_point0 = lightsaber_bottom.matrix_world.to_translation() + ls * rand

                            scene.frame_set(tr + 1)
                            ls = lightsaber_top.matrix_world.to_translation() - lightsaber_bottom.matrix_world.to_translation()
                            reflect_point1 = lightsaber_bottom.matrix_world.to_translation() + ls * rand

                            reflect_point = reflect_point0 + (reflect_point1 - reflect_point0) * lightsaber_mb

                            n = (reflect_point - origin).normalized()

                            # test if the laser actually would fly behind the reflection point
                            if start_at_emitter and (reflect_point - origin).dot((origin + new_vel * (tr - start_t) * n + n * new_vel * motionblur) - reflect_point) > 0:
                                break

                            
                            r0 = (reflect_point[0] - origin[0]) / n[0]

                            if (tr - t) * vel <= r0 <= (tr - t + 1) * vel:
                                """pathreflection = Path(origin, t, tr)

                                pathreflection.calculate_path([reflect_point], vel)

                                # optimise the reflection so that the laser gets bend at the reflection point
                                if pathreflection.dot_end_vec(reflect_point) < 0:
                                    new_ref_path = self.optim(pathreflection, reflect_point + n * laser_length * 0.5, motionblur)
                                    new_vel = new_ref_path.velocity()"""
                                break

                    path.calculate_path([reflect_point, tracker_pos], new_vel)

                    test_behind = path.dot_end_vec(tracker_pos)

                    diff = tracker_pos - path.points[-1]

                    if test_behind < 0:
                        if diff.length < compare[0][0]:
                            compare[0][0] = diff.length
                            compare[0][1] = path
                    else:
                        if diff.length < compare[1][0]:
                            compare[1][0] = diff.length
                            compare[1][1] = path

                if compare[0][1] is not None and compare[1][1] is not None:
                    optim_path0 = self.optim(compare[0][1], tracker_pos, motionblur)
                    optim_path1 = self.optim(compare[1][1], tracker_pos, motionblur)

                    if abs(optim_path0.velocity() - vel) < abs(optim_path1.velocity() - vel):
                        laser_vel = optim_path0.velocity()
                        laser_path = optim_path0
                    else:
                        laser_vel = optim_path1.velocity()
                        laser_path = optim_path1

                    curve_name = tracker.name + "_d" + str(round(laser_vel - vel, 2))
                    self.create_laser_path(laser_path, curve_name, tracker.name, laser_obj)

        return {'FINISHED'}

    def optim(self, path: Path, end, motionblur, r=1000):
        t0 = path.t0
        t1 = path.t1

        new_path = path.copy()
        i = 0

        while True and i < r:
            new_v = new_path.velocity()
            mt = t1 - t0 - 1 + motionblur
            motionblur_end = new_path.interpolate_point(mt)

            f = new_v * new_path.get_t_of_point(end) - new_v * mt

            new_path.points[-1] += f * (new_path.points[-1] - new_path.points[-2]).normalized()

            # the motionblur_end should be at the original end
            if (motionblur_end - end).length < 0.0001:
                print("Found optimum with " + str(i + 1) + " iterations.")
                break

            i += 1

        if i == r:
            print("Didn't find optimum")

        return new_path

    def create_laser_path(self, path, curve_name: str, laser_name: str, laser_obj):

        # bpy.context.scene.frame_set(t1)
        lasers_coll = get_or_create_collection(bpy.context.scene.collection, "lasers")
        curves_coll = get_or_create_collection(lasers_coll, "curves")

        # setup curve
        curve = create_curve_points(path.points, curve_name + "_curve")

        curve_obj = bpy.data.objects.new(curve_name + "_curve", curve)
        curves_coll.objects.link(curve_obj)
        curve_obj.location = path.points[0]

        laser = copy_object(laser_obj, lasers_coll)
        laser.name = laser_name + "_laser"

        laser.hide_render = True
        laser.keyframe_insert('hide_render', frame=path.t0 - 1)
        laser.hide_render = False
        laser.keyframe_insert('hide_render', frame=path.t0)

        laser.hide_render = False
        laser.keyframe_insert('hide_render', frame=path.t1 - 1)
        laser.hide_render = True
        laser.keyframe_insert('hide_render', frame=path.t1)

        if self.props.lightsaber_top is not None and self.props.lightsaber_bottom is not None:
            n = mathutils.Vector((0,0,0))
            axis = self.props.laser_axis
            f = 1

            # axis is -X, -Y, -Z
            if len(axis) == 2:
                axis = axis[1]
                f = -1

            n[ord(axis) - 88] = f

            laser.location = curve_obj.location.copy()
            laser.keyframe_insert('location', frame=path.t0)
            laser.location = curve_obj.location + n * (path.t1 - path.t0) * path.velocity()
            laser.keyframe_insert('location', frame=path.t1)

            laser.cycles.motion_steps = self.props.object_mb_steps

            convert_interpolation(get_fcurve(laser, "location", ord(axis) - 88), 'LINEAR')

            modifier = laser.modifiers.new(type='CURVE', name="curve")
            modifier.object = curve_obj
            modifier.deform_axis = ("POS_" if f == 1 else "NEG_") + self.props.laser_axis
        else:
            # animate evaluation time
            curve.eval_time = 0
            curve.keyframe_insert('eval_time', frame=path.t0)
            curve.eval_time = path.t1 - path.t0
            curve.keyframe_insert('eval_time', frame=path.t1)
            curve.path_duration = path.t1 - path.t0

            convert_interpolation(get_fcurve(curve, "eval_time"), 'LINEAR')

            # add constraint to object to curve

            constraint = laser.constraints.new('FOLLOW_PATH')
            constraint.target = curve_obj
            constraint.use_curve_follow = True
