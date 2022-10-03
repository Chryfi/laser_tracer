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


# return the curve datablock
def create_curve(a, b, curvename: str):
    curveData = bpy.data.curves.new(curvename, type='CURVE')
    curveData.dimensions = '3D'
    curveData.use_path = True

    nurbsline = curveData.splines.new('NURBS')
    nurbsline.points.add(1)
    nurbsline.use_endpoint_u = True

    nurbsline.points[0].co = (a[0], a[1], a[2], 1)
    nurbsline.points[1].co = (b[0], b[1], b[2], 1)

    return curveData


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