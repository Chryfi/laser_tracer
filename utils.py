import bpy


class LASER_TRACER_RegisterModule():
    """
    Called by the blender register function
    """
    def register():
        pass

    """
    Called by the blender unregister function
    """
    def unregister():
        pass


# returns a curve datablock which starts at (0,0,0), all points will be shifted
def create_curve(a, b, curvename: str, spline_type='POLY'):
    return create_curve_points([a, b], curvename, spline_type)


# returns a curve datablock which starts at (0,0,0), all points will be shifted
def create_curve_points(points, curvename: str, spline_type='POLY'):
    curve_data = bpy.data.curves.new(curvename, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.use_path = True

    splines = curve_data.splines.new(spline_type)
    splines.points.add(len(points) - 1)
    splines.use_endpoint_u = True

    for p in range(len(splines.points)):
        #create the curve relative to (0,0,0)
        po = points[p] - points[0]
        splines.points[p].co = (po[0], po[1], po[2], 1)

    return curve_data


def get_fcurve(obj, channel: str):
    if not obj.animation_data is None and obj.animation_data.action:
        action = bpy.data.actions.get(obj.animation_data.action.name)
        fcu = action.fcurves.find(channel)

        return fcu


def convert_interpolation(fcurve, interp: str):
    if not fcurve is None:
        for pt in fcurve.keyframe_points:
            pt.interpolation = interp


def copy_object(object, target_collection):
    obj_copy = object.copy()
    obj_copy.data = object.data.copy()
    target_collection.objects.link(obj_copy)

    return obj_copy


def get_or_create_collection(parent_collection, name: str):
    collection = bpy.data.collections.get(name)

    if collection is None:
        collection = bpy.data.collections.new(name)

    if not parent_collection.children.get(name):
        if bpy.context.scene.collection.children.get(name):
            bpy.context.scene.collection.children.unlink(collection)

        parent_collection.children.link(collection)

    return collection


def call_euler_filter_ops():
    window = bpy.context.window
    screen = window.screen

    # avoid TOPBAR - for some reason it caused problems
    for area in screen.areas:
        if area.type != 'TOPBAR':
            oldtype = area.type
            area.type = 'GRAPH_EDITOR'
            override = {'window': window, 'screen': screen, 'area': area}

            bpy.ops.graph.euler_filter(override)
            area.type = oldtype

            break


def select_obj_only(obj):
    # make the obj the only selected active object
    if bpy.context.view_layer.objects.active is not None:
        bpy.context.view_layer.objects.active.select_set(False)

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)