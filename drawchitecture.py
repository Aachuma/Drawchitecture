bl_info = {
    "name": "Drawchitecture",
    "description": "creates temporary workplanes by strokes or points for drawing in 3D with the grease pencil",
    "author": "Philipp Sommer",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "View3D",
    # "warning": "", # used for warning icon and text in addons panel
    # "wiki_url": ""
    # "tracker_url": "",
    "support": "TESTING",
    "category": "Paint"
}
import bpy
import math
import mathutils

from bpy.types import Panel
from math import *
from mathutils import Vector, Matrix
import numpy as np

bpy.types.Scene.gp_active = bpy.props.StringProperty(name='gp_active', description='saves last used GP',
                                                     default='empty', options={'HIDDEN'})
bpy.types.Scene.del_stroke = bpy.props.BoolProperty(name='del_stroke', description='V/H/3D: deletes last stroke',
                                                    default=False, options={'HIDDEN'})
bpy.types.Scene.expand_system = bpy.props.BoolProperty(name='expand_system', description='expands system tools',
                                                       default=True, options={'HIDDEN'})
bpy.types.Scene.expand_grid = bpy.props.BoolProperty(name='expand_grid', description='expands grid settings',
                                                     default=True, options={'HIDDEN'})
bpy.types.Scene.grid_scale = bpy.props.FloatVectorProperty(name='grid_scale',
                                                           description='saves the grid size of the workplane',
                                                           default=(1.0, 1.0, 0))
bpy.types.Scene.grid_count = bpy.props.IntVectorProperty(name='grid_count',
                                                         description='saves the grid size of the workplane',
                                                         default=(100, 100, 0))
bpy.types.Scene.plane_location = bpy.props.FloatVectorProperty(name='plane_location',
                                                               description='global memory for wp location',
                                                               default=(0.0, 0.0, 0.0))


def update_offset(self, context):
    """updates the position of the plane when the Factor in UI is change
    """
    if 'workplane_TEMPORARY' in (obj.name for obj in bpy.data.objects):
        wp = bpy.data.objects['workplane_TEMPORARY']
        # rotation in euler
        eu = wp.rotation_euler
        # offset factor in UI
        factor_offset = bpy.context.scene.plane_offset
        # Defining Vector for Translation in Z Axis and rotating it to be the normal of the plane
        vec_offset = Vector((0, 0, factor_offset))
        vec_offset.rotate(eu)

        loc = bpy.context.scene.plane_location
        vec_loc = Vector((loc[0], loc[1], loc[2]))
        wp.location = vec_loc + vec_offset


bpy.types.Scene.plane_offset = bpy.props.FloatProperty(name='plane_offset',
                                                       description='plane offset in normal-direction of plane',
                                                       default=0.0,
                                                       update=update_offset)


def cross(a, b):
    """ simple cross product formula for calculating normal vector
    """
    c = Vector((a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0]))
    return c


def activate_gp():
    """activate last GP or create GP
    """
    if bpy.context.scene.gp_active == 'empty':
        # if gp objects exist choose random gp object if not yet initialized as active gp object
        for obj in bpy.data.objects:
            if obj.type == 'GPENCIL':
                bpy.context.scene.gp_active = obj.name
                bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]
                break
        # if no gp objects exist add new gp object
        if bpy.context.scene.gp_active == 'empty':
            print('activate_gp: no gp object detected, creating new GP')
            add_GP()
            return {'GP added'}
    else:
        name_active = bpy.context.scene.gp_active
        # if there is an object with the same name as the saved GP, activate it
        if (name_active in (gp_obj.name for gp_obj in bpy.data.objects)):
            bpy.context.view_layer.objects.active = bpy.data.objects[name_active]
            return {'FINISHED'}
        else:
            print('activate_gp: gp object not found, creating new GP')
            add_GP()
            return {'GP added'}


def add4arrays():
    """ add 4x Array-modifier to active Object (Plane) to achieve grid-like-Workplane
    """
    obj = bpy.context.active_object
    step = radians(90)
    for i in range(0, 2):
        modifier = obj.modifiers.new(name='AR' + str(i), type='ARRAY')
        modifier.count = 100
        modifier.relative_offset_displace[0] = cos(step * i)
        modifier.relative_offset_displace[1] = sin(step * i)
    for i in range(2, 4):
        modifier = obj.modifiers.new(name='AR' + str(i), type='ARRAY')
        modifier.count = 2
        modifier.relative_offset_displace[0] = cos(step * i)
        modifier.relative_offset_displace[1] = sin(step * i)
    obj.modifiers['AR0'].count = bpy.context.scene.grid_count[0]
    obj.modifiers['AR1'].count = bpy.context.scene.grid_count[1]


def add_GP():
    """Create standard GP object
    """
    deselect_all()
    a = []
    b = []
    name = gpencil_obj_name()
    # list of grease_pencil object names before adding new one
    for o in bpy.data.grease_pencil:
        a.append(o.name)

    # adding new GP Object
    bpy.ops.object.gpencil_add(location=(0, 0, 0), rotation=(0, 0, 0), type='EMPTY')
    # empty Grease Pencil Object at 0,0,0 otherwise gp stroke point coordinates are offset
    # name + Number by counting all other GP Objects
    bpy.context.view_layer.objects.active.name = name
    # lock in place at 0,0,0 because point.coordinates refer to GP Origin
    bpy.context.view_layer.objects.active.lock_location = [True for x in range(3)]

    # find out the name of newly created grease_pencil object to rename it properly
    for o in bpy.data.grease_pencil:
        b.append(o.name)
    newgpname = list(set(b) - set(a))
    # name + Number same as GP Object
    bpy.data.grease_pencil[newgpname[0]].name = name
    save_active_gp()
    # name + Number by counting all other grease_pencil objects
    # bpy.data.grease_pencil[newgpname[0]].name = gpname()


def add_workplane_3p():
    """Creates Plane through 3 selected points of active GP Object (selected in Editmode)
    """
    selected_points = []

    if bpy.context.view_layer.objects.active.type == 'GPENCIL':
        # name of the active object (Type Gpencil Object)
        name_active = bpy.context.view_layer.objects.active.name
    else:
        name_active = bpy.context.scene.gp_active

    if (name_active in (gp_pen.name for gp_pen in bpy.data.grease_pencil)):
        gp_pen = bpy.data.grease_pencil[name_active]
        if gp_pen.layers.active:
            if gp_pen.layers.active.active_frame.strokes:
                for stroke in gp_pen.layers.active.active_frame.strokes:
                    for point in stroke.points:
                        if point.select:
                            selected_points.append(point.co)

    print('add_workplane_3p: selected_points:')
    print(selected_points)
    if len(selected_points) == 0:
        print('no point selected')
    elif len(selected_points) == 1:
        print('1 point selected - creating horizontal plane')
        select_p1 = selected_points[-1]
        plane_array(select_p1, (0, 0, 0), '1p')
        gpencil_paint_mode()

    elif len(selected_points) == 2:
        print('2 points selected - creating plane through 2 points')
        select_p1 = selected_points[-1]
        select_p2 = selected_points[-2]
        plane_array(select_p1, select_p2, '3d')
        gpencil_paint_mode()

    elif len(selected_points) >= 3:
        print('3 or more points selected - creating plane through 3 points')
        select_p1 = selected_points[-1]
        select_p2 = selected_points[-2]
        select_p3 = selected_points[-3]
        v1 = select_p2 - select_p1
        # print(v1)
        v2 = select_p3 - select_p1
        # print(v2)
        v_normal = Vector((cross(v1, v2)))
        # print(v_normal)
        p_normal = select_p1 + v_normal
        plane_array(select_p1, p_normal, '3p')
        gpencil_paint_mode()

    return {'FINISHED'}


def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    angle = np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
    return angle


def angle_between_3d(z_dif, v_xparallel):
    """ Returns the angle in radians between vectors 'v1' and 'v2'
    v2 mostly used as vector parallel to x-y-plane for calculating x rotation
    """
    mag = np.sqrt(v_xparallel.dot(v_xparallel))
    angle_rad = atan(z_dif / mag)
    return angle_rad


def angle_between_z(v1, v2):
    """ returns the angle in radians between vectors 'v1' and 'v2' for z
    """
    v1_2d_z = Vector((v1[0], v1[1]))
    v2_2d_z = Vector((v2[0], v2[1]))
    angle_z = angle_between(v1_2d_z, v2_2d_z)
    return angle_z


def calc_location_2p(point_a, point_b):
    """ calculates midpoint of line between two input points
    """
    loc = []
    loc.append((point_a[0] + point_b[0]) / 2)
    loc.append((point_a[1] + point_b[1]) / 2)
    loc.append((point_a[2] + point_b[2]) / 2)
    return loc


def calc_rotation_2p_zh(point_a, point_b):
    """ returns rotation vector for a horizontal plane by 2 points
    """
    if point_a[0] > point_b[0]:
        v_2p = point_b - point_a
    else:
        v_2p = point_a - point_b

    v_y = Vector((0, 1, 0))
    z = angle_between_z(v_y, v_2p)

    return ((0, 0, z))


def calc_rotation_2p_zv(point_a, point_b):
    """ returns rotation vector of a Plane by 2 points
    first: set y rotation to 90°
    then: rotation in z
    """
    if point_a[0] > point_b[0]:
        v_2p = point_b - point_a
    else:
        v_2p = point_a - point_b

    v_y = Vector((0, 1, 0))
    y = 90 * math.pi / 180
    z = angle_between_z(v_y, v_2p)

    return ((0, y, z))


def calc_rotation_2p_3d(point_a, point_b):
    """returns rotation vector for plane by 2 Points
    first: rotation in z
    then: roration in x by z difference and projected distance of points"""
    if point_a[0] > point_b[0]:
        v_2p = point_b - point_a
        z_dif = point_b[2] - point_a[2]
    else:
        v_2p = point_a - point_b
        z_dif = point_a[2] - point_b[2]

    v_y = Vector((0, 1, 0))
    v_xparallel = v_2p
    v_xparallel[2] = 0
    x = angle_between_3d(z_dif, v_xparallel)
    z = angle_between_z(v_y, v_2p)

    return ((x, 0, z))


def calc_rotation_3p(point_a, point_b):
    """returns rotation vector for plane by 3 Points
    first: rotation in z
    then: rotation in x with the normal-vector of plane
    adding 90° to rotation for final plane
    """
    if point_a[0] > point_b[0]:
        v_2p = point_b - point_a
        z_dif = point_b[2] - point_a[2]
    else:
        v_2p = point_a - point_b
        z_dif = point_a[2] - point_b[2]

    v_y = Vector((0, 1, 0))
    v_xparallel = v_2p
    v_xparallel[2] = 0

    # adding 90 degrees to the x rotation because it is the normal vector
    ortho = 90 * math.pi / 180
    x = ortho + angle_between_3d(z_dif, v_xparallel)
    # print(x)
    z = angle_between_z(v_y, v_2p)
    # print(z)

    return ((x, 0, z))


def deselect_all():
    """deselects every object
    """
    if not bpy.context.mode == 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')


def deselect_all_gp():
    """deselects all gp vertices / strokes
    """
    if not bpy.context.mode == 'EDIT_GPENCIL':
        bpy.ops.object.mode_set(mode='EDIT_GPENCIL')
    bpy.ops.gpencil.select_all(action='DESELECT')


def find_3dview_space():
    """returns 3D_View and its screen space
    """
    area = None

    for a in bpy.data.window_managers[0].windows[0].screen.areas:
        if a.type == 'VIEW_3D':
            area = a
            break
    if area:
        space = area.spaces[0]
    else:
        space = bpy.context.space_data

    return space


def gpencil_obj_name():
    """Generates Name for new GP object based on existing GP objects
    """
    # for o in bpy.data.objects:
    #    if o.type == 'GPENCIL':
    #        num = num + 1

    # list all existing GP objects
    namelist = [gp_obj.name for gp_obj in bpy.data.objects if gp_obj.type == 'GPENCIL']

    num = 1
    name = 'Drawing ' + str(num)
    # as long as name+num is allready taken, count up num
    while name in namelist:
        num = num + 1
        name = 'Drawing ' + str(num)

    return name


def gpencil_paint_mode():
    """Gpencil has to be selected! activates DRAW mode / GPENCIL_PAINT mode, unless it's already active
    """
    if not bpy.context.mode == 'PAINT_GPENCIL':
        bpy.ops.object.mode_set(mode='PAINT_GPENCIL')
    return {'FINISHED'}


def laststroke():
    """returns last stroke of active Greasepencil object
    returns 'No GP object active' when no GP Obj is active
    returns 'Names not equal' if data.objects GP name + data.grease_pencil object Name of active GP Object are not equal
    """
    if bpy.context.view_layer.objects.active.type == 'GPENCIL':
        # name of the active object (Type Gpencil Object)
        name_active = bpy.context.view_layer.objects.active.name

        if (name_active in (gp_pen.name for gp_pen in bpy.data.grease_pencil)):
            gp_pen = bpy.data.grease_pencil[name_active]
            if gp_pen.layers.active:
                if gp_pen.layers.active.active_frame.strokes:
                    ls = gp_pen.layers.active.active_frame.strokes[-1]
                    return ls
                else:
                    print('laststroke: active GP Obj has no strokes')
                    return {'No Strokes'}
            else:
                print('laststroke: active GP Obj has no strokes')
                return {'No Strokes'}
        else:
            print('laststroke: Names of active GP object and its bpy.data.grease_pencil equivalent must be equal')
            return {'Names not equal'}
    else:
        print('No GP object active')
        return {'GP obj inactive'}


# def offset_plane():
#
#    cube = bpy.data.objects["Cube"]
#    # one blender unit in x-direction
#    vec = mathutils.Vector((1.0, 0.0, 0.0))
#    inv = cube.rotation_euler.to_matrix()
#    # vec aligned to local axis
#    vec_rot = vec * inv
#    cube.location = cube.location + vec_rot


def plane_array(p1, p2, rotation):
    """adds an array of 1m by 1m planes at given location, parameter rotation defines way to calculate angle
    """
    # define standard scale / count
    save_active_gp()
    # delete last workplane
    if bpy.data.objects:
        deselect_all()
        # select last temporary workplane
        for o in bpy.data.objects:
            if o.name == 'workplane_TEMPORARY':
                o.select_set(state=True)
                # save settings of last workplane
                save_grid_settings()
                break
        # delete last workplane
        bpy.ops.object.delete()
        bpy.context.scene.plane_offset = 0.0
    if rotation == '1p':
        p_loc = calc_location_2p(p1, p1)
        p_rot = ((0, 0, 0))
    elif rotation == '3p':
        p_loc = calc_location_2p(p1, p1)
    else:
        p_loc = calc_location_2p(p1, p2)

    if rotation == 'v':
        p_rot = calc_rotation_2p_zv(p1, p2)
    elif rotation in ('h', 'bp'):
        p_rot = calc_rotation_2p_zh(p1, p2)
    elif rotation == '3d':
        p_rot = calc_rotation_2p_3d(p1, p2)
    elif rotation == '3p':
        p_rot = calc_rotation_3p(p1, p2)

    bpy.context.scene.plane_location = p_loc
    bpy.ops.mesh.primitive_plane_add(size=1, location=p_loc, rotation=p_rot)

    baseplane = bpy.context.active_object
    baseplane.name = 'workplane_TEMPORARY'
    add4arrays()
    baseplane.scale = bpy.context.scene.grid_scale

    # set material of plane
    # mat = bpy.data.materials['Mat_Transparent_White']
    # baseplane.active_material = mat
    baseplane.show_wire = True
    deselect_all()
    activate_gp()
    if rotation not in ('3p', 'bp'):
        if bpy.context.scene.del_stroke:
            bpy.ops.dt.delete_last_stroke()
    return {'FINISHED'}


def save_active_gp():
    """save active gp obj in global variable
    """
    if bpy.context.view_layer.objects.active:
        if (bpy.context.view_layer.objects.active.type == 'GPENCIL'):
            # name of the active object (Type Gpencil Object)
            name_active = bpy.context.view_layer.objects.active.name
            if (name_active in (gp_pen.name for gp_pen in bpy.data.grease_pencil)):
                # select data.grease_pencil object to select its strokes
                bpy.context.scene.gp_active = name_active
            else:
                bpy.context.scene.gp_active = 'empty'
        else:
            bpy.context.scene.gp_active = 'empty'
    else:
        bpy.context.scene.gp_active = 'empty'


def save_grid_settings():
    """Stores Grid settings of workplane to global Property of scene
    """
    bpy.context.scene.grid_scale = bpy.data.objects['workplane_TEMPORARY'].scale
    bpy.context.scene.grid_count = (
        bpy.data.objects['workplane_TEMPORARY'].modifiers[0].count,
        bpy.data.objects['workplane_TEMPORARY'].modifiers[1].count, 0)


def unit_vector(vector):
    """ Returns the unit vector of the input vector.
    """
    return vector / np.linalg.norm(vector)


class SetupDrawchitecture(bpy.types.Operator):  # standard plane
    """initializes the setup: colors & viewsettings
    """
    bl_idname = 'dt.setup'
    bl_label = 'SetupDrawchitecture View'

    def execute(self, context):
        # Viewport shader mode set to 'WIREFRAME' for transparent objects
        find_3dview_space().shading.type = 'WIREFRAME'
        find_3dview_space().shading.show_xray_wireframe = True

        # Disable Floor Grid + Cursor in active View3D, make Vertices in editmode visible
        find_3dview_space().overlay.show_floor = False
        find_3dview_space().overlay.show_cursor = False
        find_3dview_space().overlay.show_object_origins = False
        find_3dview_space().overlay.vertex_opacity = 1

        # Set 3d View Background color to white and Wire color to grey
        bpy.context.preferences.themes[0].view_3d.space.gradients.high_gradient = (0.8, 0.8, 0.8)
        bpy.context.preferences.themes[0].view_3d.wire = (0.5, 0.5, 0.5)

        # Set Stroke Placement in active Scene to 'Surface'
        bpy.context.window.scene.tool_settings.gpencil_stroke_placement_view3d = 'SURFACE'

        # plane_array(Vector((0, 0.5, 0)), Vector((1, 0.5, 0)), 'h')  # default workplane at 0,0,0

        # create GP object or activate last GP object
        activate_gp()
        # switch to DRAW mode
        gpencil_paint_mode()

        return {'FINISHED'}


class InitializeDrawchitecture(bpy.types.Operator):  # standard plane
    """initializes the setup: default workplane at start, activates GP mode
    """
    bl_idname = 'dt.initialize'
    bl_label = 'Create Baseplane (+ GP Object if there is none)'

    def execute(self, context):
        # default workplane at 0,0,0
        plane_array(Vector((0, 0.5, 0)), Vector((1, 0.5, 0)), 'bp')

        # create GP object if there is none
        # if not [obj for obj in bpy.data.objects if obj.type == 'GPENCIL']:
        # add_GP()
        activate_gp()
        # switch to DRAW mode
        gpencil_paint_mode()

        return {'FINISHED'}


class AddGPObject(bpy.types.Operator):
    """Adds new GP Object to Scene, locked at 0.0.0
    """
    bl_idname = 'dt.add_gp_object'
    bl_label = 'adds gp object, locked at 0.0.0'

    def execute(self, context):
        add_GP()
        gpencil_paint_mode()
        return {'FINISHED'}


class AddRotation(bpy.types.Operator):
    """Adds given rotation to the rotation vector of workplane_TEMPORARY, property sets +/- and Achsis
    only shown when workplane_Temporary exists
    """
    bl_idname = 'dt.add_rotation'
    bl_label = 'add rotation'
    axis: bpy.props.StringProperty()
    rotation: bpy.props.FloatProperty()

    # axis_index = bpy.props.IntProperty()

    def execute(self, context):
        wp = bpy.data.objects['workplane_TEMPORARY']
        rotation_old = wp.rotation_euler
        rotation_add = self.rotation * math.pi / 180

        if self.axis == 'x':
            axis_index = 0
        elif self.axis == 'y':
            axis_index = 1
        elif self.axis == 'z':
            axis_index = 2
        else:
            print('error: axis must be x / y / z')
            return {'CANCELLED'}

        bpy.data.objects['workplane_TEMPORARY'].rotation_euler[axis_index] = rotation_old[axis_index] + rotation_add
        return {'FINISHED'}


class ClearPlaneAndGP(bpy.types.Operator):
    """ Deletes the Temporary Workplane and all GP Objects
    """
    bl_idname = 'dt.clear_all_objects'
    bl_label = 'clears all Temporary Workplane + gp objects in project'

    def execute(self, context):
        if not bpy.context.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # delete all objects
        if bpy.data.objects:
            for o in bpy.data.objects:
                if o.name == 'workplane_TEMPORARY':
                    o.select_set(state=True)
                if o.type == 'GPENCIL':
                    o.select_set(state=True)
            bpy.ops.object.delete()

            if bpy.data.grease_pencil:
                for gp in bpy.data.grease_pencil:
                    bpy.data.grease_pencil.remove(gp)
            bpy.context.scene.gp_active = 'empty'
            bpy.context.scene.plane_offset = 0.0
            bpy.ops.dt.initialize()
            return {'FINISHED'}
        else:
            bpy.context.scene.gp_active = 'empty'
            bpy.ops.dt.initialize()
            return {'FINISHED'}


class DeleteLastStroke(bpy.types.Operator):
    """For V/H/3D: deletes last drawn stroke of active GP Object
    """
    bl_idname = 'dt.delete_last_stroke'
    bl_label = 'deletes last stroke of active GP object'

    def execute(self, context):
        save_active_gp()
        activate_gp()
        gpencil_paint_mode()

        active_name = bpy.context.scene.gp_active
        if bpy.data.grease_pencil[active_name].layers.active:
            if bpy.data.grease_pencil[active_name].layers.active.active_frame.strokes:
                # deselect gp to only delete latest stroke
                deselect_all_gp()
                bpy.data.grease_pencil[active_name].layers.active.active_frame.strokes[-1].select = True
                bpy.ops.gpencil.delete(type='STROKES')
            else:
                print('DeleteLastStroke: Active Grease Pencil has no strokes to be deleted')
        else:
            print('DeleteLastStroke: Active Grease Pencil has no strokes to be deleted')

        gpencil_paint_mode()
        return {'FINISHED'}


class RemoveGPObject(bpy.types.Operator):
    """Removes the active GP Object
    """
    bl_idname = 'dt.remove_gp_object'
    bl_label = 'removes active GP Object'

    def execute(self, context):
        # make sure no other object is selected
        deselect_all()
        # activate last gp or write gp name in global variable
        activate_gp()

        # object mode must be activated to delete an object
        if not bpy.context.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        name_active = bpy.context.scene.gp_active
        # if there is an object with the same name as the saved GP, delete it
        if (name_active in (gp_obj.name for gp_obj in bpy.data.objects)):
            bpy.data.objects[name_active].select_set(state=True)
            bpy.ops.object.delete()
            # clear saved GP name to activate any other GP or create new if no GP left
            bpy.context.scene.gp_active = 'empty'

        activate_gp()
        gpencil_paint_mode()
        return {'FINISHED'}


class ResetScale(bpy.types.Operator):
    """Reset X and Y scale + count of workplane
    """
    bl_idname = 'dt.reset_scale'
    bl_label = 'reset scale + count'

    def execute(self, context):
        scale_default = (1.0, 1.0, 0)

        wp = bpy.data.objects['workplane_TEMPORARY']

        wp.scale = scale_default
        wp.modifiers[0].count = 100
        wp.modifiers[1].count = 100

        save_grid_settings()
        return {'FINISHED'}


class SelectGPobject(bpy.types.Operator):
    """Shows buttons with all GP Objects and selects them
    (Problems with hidden GP Objects)
    """
    bl_idname = 'dt.select_gp_object'
    bl_label = 'Activates Greasepencil Object by Name on Button'
    gp: bpy.props.StringProperty(default='', options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        deselect_all()
        gp = context.scene.objects.get(self.gp)
        bpy.context.view_layer.objects.active = gp
        context.scene.grease_pencil = gp.grease_pencil
        save_active_gp()
        gpencil_paint_mode()
        return {'FINISHED'}


class SwitchScaleAndCount(bpy.types.Operator):
    """Switches X and Y scale + count of workplane
    """
    bl_idname = 'dt.switch_scale_and_count'
    bl_label = 'switch x/y'

    def execute(self, context):
        scale = bpy.data.objects['workplane_TEMPORARY'].scale
        scale_switched = (scale[1], scale[0], scale[2])

        wp = bpy.data.objects['workplane_TEMPORARY']

        wp.scale = scale_switched

        count_x = wp.modifiers[0].count
        wp.modifiers[0].count = wp.modifiers[1].count
        wp.modifiers[1].count = count_x

        save_grid_settings()
        return {'FINISHED'}


class WPstrokeV(bpy.types.Operator):  # First+ Last Point of last Stroke create vertical plane
    """adds VERTICAL workplane at last grease pencil stroke by start + endpoint of stroke
    ! GP Object must be selected first
    ! GP Object and Grease_Pencil object need equal Names
    """
    bl_idname = 'dt.work_plane_on_stroke_2p'
    bl_label = 'add vertical workplane by stroke start end'

    def execute(self, context):
        # last greasepencil stroke
        # gp_laststroke = bpy.data.grease_pencil[-1].layers.active.active_frame.strokes[-1]
        ls = laststroke()
        if ls == {'GP obj inactive'}:
            return {'CANCELLED'}
        elif ls == {'Names not equal'}:
            return {'CANCELLED'}
        elif ls == {'No Strokes'}:
            return {'CANCELLED'}
        else:
            p1 = ls.points[0].co
            p2 = ls.points[-1].co
            plane_array(p1, p2, "v")
            # DELETE LAST GP STROKE
            # if not bpy.context.mode == 'EDIT':
            #    bpy.ops.object.mode_set(mode='EDIT')
            # gp_laststroke
            # bpy.ops.gpencil.delete(type='STROKES')
            gpencil_paint_mode()
            return {'FINISHED'}


class WPStrokeH(bpy.types.Operator):  # First+ Last Point of last Stroke create horizontal plane
    """adds HORIZONTAL workplane at last grease pencil stroke by start + endpoint of stroke
    ! GP Object must be selected first
    ! GP Object and Grease_Pencil object need equal Names
    """
    bl_idname = 'dt.work_plane_on_stroke_2p_horizontal'
    bl_label = 'add horizontal workplane by stroke start end'

    def execute(self, context):
        # last greasepencil stroke
        # gp_laststroke = bpy.data.grease_pencil[-1].layers.active.active_frame.strokes[-1]
        ls = laststroke()
        if ls == {'GP obj inactive'}:
            return {'CANCELLED'}
        elif ls == {'Names not equal'}:
            return {'CANCELLED'}
        elif ls == {'No Strokes'}:
            return {'CANCELLED'}
        else:
            p1 = ls.points[0].co
            p2 = ls.points[-1].co
            plane_array(p1, p2, "h")
            gpencil_paint_mode()
            return {'FINISHED'}


class WPstroke3D(bpy.types.Operator):  # First+ Last Point of last Stroke create horizontal plane
    """adds tilted Plane to any Stroke by Start + Endpoint of Stroke
    ! GP Object must be selected first -
    ! GP Object and Grease_Pencil object need equal Names
    """
    bl_idname = 'dt.work_plane_on_stroke_2p_3d'
    bl_label = 'align workplane to tilted 3d-strokes by start end'

    def execute(self, context):
        ls = laststroke()
        if ls == {'GP obj inactive'}:
            return {'CANCELLED'}
        elif ls == {'Names not equal'}:
            return {'CANCELLED'}
        elif ls == {'No Strokes'}:
            return {'CANCELLED'}
        else:
            p1 = ls.points[0].co
            p2 = ls.points[-1].co
            plane_array(p1, p2, '3d')
            gpencil_paint_mode()
            return {'FINISHED'}


class WPselect3P(bpy.types.Operator):  # Plane from 1/2/3 Points in Selection
    """First click: enter Stroke-Edit mode, select up to 3 points (hold SHIFT)
    Second Click: create Plane through Points
    1point: horizontal plane
    2points: 3D Plane through 2 Points
    3points: 3D Plane through 3 Points
    """
    bl_idname = 'dt.work_plane_points_3d'
    bl_label = 'Enters Editmode, or converts up to 3 Selected GP_Points to a Plane'

    def execute(self, context):
        # save gp here?
        save_active_gp()
        activate_gp()
        if not bpy.context.mode == 'EDIT_GPENCIL':
            bpy.ops.object.mode_set(mode='EDIT_GPENCIL')
            bpy.context.scene.tool_settings.gpencil_selectmode = 'POINT'
        else:
            # prevent this mode from deleting last stroke
            if bpy.context.scene.del_stroke:
                bpy.context.scene.del_stroke = False
                add_workplane_3p()
                bpy.context.scene.del_stroke = True
            else:
                add_workplane_3p()

            # reactivate gp here
            gpencil_paint_mode()
        return {'FINISHED'}


class View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Drawchitecture'


class AddPanel(View3DPanel, Panel):
    """Interface
    """
    bl_label = 'Drawchitecture'

    # bl_context = 'objectmode' # without context works for all contexts
    # bl_category = 'Drawchitecture'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        system_box = layout.box()
        system_box_title = system_box.row(align=True)
        system_box_title.label(text='System Tools', icon='SETTINGS')
        system_box_title_sub = system_box_title.row()
        system_box_title_sub.prop(bpy.context.scene, 'expand_system', text='', icon='THREE_DOTS', emboss=False)
        if bpy.context.scene.expand_system:
            system_box_col1 = system_box.column(align=True)
            system_box_col1.operator('dt.setup', text='Setup View', icon='PLAY')
            system_box_col1.operator('dt.clear_all_objects', text='Clear All Objects', icon='LIBRARY_DATA_BROKEN')

            bg_color = bpy.context.preferences.themes[0].view_3d.space.gradients
            color_col1 = system_box.column(align=True)
            color_col1.label(icon='COLOR', text='Colors')
            color_col1.prop(bg_color, 'high_gradient', text='background')

            wire_color = bpy.context.preferences.themes[0].view_3d
            color_col1.prop(wire_color, 'wire', text='wire lines')

        # box with Create WP options
        workplane_box = layout.box()
        workplane_box_title = workplane_box.row(align=True)
        workplane_box_title.label(text='Workplanes', icon='MESH_GRID')
        workplane_box_title.prop(bpy.context.scene, "del_stroke", text="delete Stroke")
        # Buttons
        workplane_box_row1 = workplane_box.row()
        workplane_box_row1.operator('dt.delete_last_stroke', text='Delete Last Stroke', icon='STROKE')
        workplane_box_col1 = workplane_box.column(align=True)
        workplane_box_col1.operator('dt.initialize', text='horizontal base plane', icon='AXIS_TOP')
        workplane_box_row2 = workplane_box_col1.row(align=True)
        if bpy.context.scene.del_stroke:
            workplane_box_row2.alert = True
        workplane_box_row2.operator('dt.work_plane_on_stroke_2p', text='V', icon='AXIS_FRONT')
        workplane_box_row2.operator('dt.work_plane_on_stroke_2p_horizontal', text='H', icon='AXIS_TOP')
        workplane_box_row2.operator('dt.work_plane_on_stroke_2p_3d', text='3D', icon='MOD_LATTICE')
        workplane_box_row3 = workplane_box_col1.row(align=True)
        if bpy.context.mode == 'EDIT_GPENCIL':
            workplane_box_row3.alert = True
        workplane_box_row3.operator('dt.work_plane_points_3d', text='select 1 / 2 / 3 points', icon='MOD_DATA_TRANSFER')

        if [obj for obj in bpy.data.objects if obj.name == 'workplane_TEMPORARY']:
            workplane_rotation_box = layout.box()
            workplane_rotation_box_title = workplane_rotation_box.row(align=True)
            workplane_rotation_box_title.label(text='Workplane Rotation', icon='FILE_REFRESH')
            wp_rot_box_row1 = workplane_rotation_box.row(align=True)
            wp_rot_box_row1_sub1 = wp_rot_box_row1.row()

            wp_rot_box_row1_sub1.prop(bpy.data.objects['workplane_TEMPORARY'], 'rotation_euler', text=' ')

            wp_rot_box_row1_sub2 = wp_rot_box_row1.column(align=True)
            minus_x = wp_rot_box_row1_sub2.operator('dt.add_rotation', text='- 45°')
            minus_x.axis = 'x'
            minus_x.rotation = -45
            minus_y = wp_rot_box_row1_sub2.operator('dt.add_rotation', text='- 45°')
            minus_y.axis = 'y'
            minus_y.rotation = -45
            minus_z = wp_rot_box_row1_sub2.operator('dt.add_rotation', text='- 45°')
            minus_z.axis = 'z'
            minus_z.rotation = -45

            wp_rot_box_row1_sub3 = wp_rot_box_row1.column(align=True)
            plus_x = wp_rot_box_row1_sub3.operator('dt.add_rotation', text='+ 45°')
            plus_x.axis = 'x'
            plus_x.rotation = 45
            plus_y = wp_rot_box_row1_sub3.operator('dt.add_rotation', text='+ 45°')
            plus_y.axis = 'y'
            plus_y.rotation = 45
            plus_z = wp_rot_box_row1_sub3.operator('dt.add_rotation', text='+ 45°')
            plus_z.axis = 'z'
            plus_z.rotation = 45

            wp_rot_box_row2 = workplane_rotation_box.row(align=True)
            wp_rot_box_row2.prop(bpy.context.scene, 'plane_offset')

        workplane_grid_box = layout.box()
        workplane_grid_box_title = workplane_grid_box.row(align=True)
        workplane_grid_box_title.label(text='Grid Size', icon='GRID')
        workplane_grid_box_title.prop(bpy.context.scene, 'expand_grid', text='', icon='THREE_DOTS', icon_only=True,
                                      emboss=False)
        if bpy.context.scene.expand_grid:
            if [obj for obj in bpy.data.objects if obj.name == 'workplane_TEMPORARY']:
                workplane_grid_box_row1 = workplane_grid_box.row(align=True)

                workplane_grid_box_row1_col1 = workplane_grid_box_row1.column(align=True)
                workplane_grid_box_row1_col1.label(text='scale')
                workplane_grid_box_row1_col1.prop(bpy.data.objects['workplane_TEMPORARY'], 'scale', index=0,
                                                  icon_only=True)
                workplane_grid_box_row1_col1.prop(bpy.data.objects['workplane_TEMPORARY'], 'scale', index=1,
                                                  icon_only=True)

                workplane_grid_box_row1_col2 = workplane_grid_box_row1.column(align=True)
                workplane_grid_box_row1_col2.label(text='count')
                workplane_grid_box_row1_col2.prop(bpy.data.objects['workplane_TEMPORARY'].modifiers[0], 'count',
                                                  icon_only=True)
                workplane_grid_box_row1_col2.prop(bpy.data.objects['workplane_TEMPORARY'].modifiers[1], 'count',
                                                  icon_only=True)

        workplane_grid_box_row2 = workplane_grid_box.row(align=True)
        workplane_grid_box_row2.operator('dt.switch_scale_and_count', icon='ARROW_LEFTRIGHT', text='switch')
        workplane_grid_box_row2.operator('dt.reset_scale', icon='LOOP_BACK', text='reset')

        box_gp = layout.box()
        # Show which GP Obj is active
        box_gp.label(text='Grease Pencil Objects: ' + bpy.context.scene.gp_active, icon='GREASEPENCIL')
        box_gp_row1 = box_gp.row(align=True)
        box_gp_row1.operator('dt.add_gp_object', icon='ADD', text='add new')
        box_gp_row1.operator('dt.remove_gp_object', icon='REMOVE', text='del active')

        greasepencils = [gp for gp in context.scene.objects if gp.type == 'GPENCIL']
        box_gp_col1 = box_gp.column(align=True)
        for gp in greasepencils:
            op = box_gp_col1.row()
            if gp.name == bpy.context.scene.gp_active:
                op.alert = True
            opo = op.operator('dt.select_gp_object', text=gp.name)
            opo.gp = gp.name
            # op.alert = True


# tuple of all used classes
classes = (
    SetupDrawchitecture, InitializeDrawchitecture, AddGPObject, AddRotation, ClearPlaneAndGP, DeleteLastStroke,
    RemoveGPObject, ResetScale, SelectGPobject, SwitchScaleAndCount, WPstrokeV, WPStrokeH, WPstroke3D, WPselect3P,
    AddPanel)


# registering/unregistering classes
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
