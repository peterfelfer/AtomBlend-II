import math

import bpy

from .read_data import *
from .render import *

# ------------------- EXTERNAL MODULES -------------------
import sys
from math import *

import bpy
from bpy.props import StringProperty
from bpy.types import PropertyGroup

import numpy as np

from .globals import ABGlobals

# append the add-on's path to Blender's python PATH
sys.path.insert(0, ABGlobals.addon_path)

# --- properties that each element has ---
# e.g. each element has its own name, charge, point size, ...
class DisplaySettings(bpy.types.PropertyGroup):
    def total_atom_coords_update(self, context):
        total_atoms_perc_displayed = context.scene.atom_blend_addon_settings.vertex_percentage
        total_atoms_perc_displayed = total_atoms_perc_displayed #/ len(ABGlobals.all_data)
        # print(total_atoms_perc_displayed, len(ABGlobals.all_data), context.scene.atom_blend_addon_settings.vertex_percentage)

        # update function atom_coords_update gets called as we're editing perc_displayed
        for elem_name in ABGlobals.all_elements_by_name:
            bpy.context.scene.color_settings[elem_name].perc_displayed = total_atoms_perc_displayed

        # update other lists
        DisplaySettings.atom_color_update(self, context)
        DisplaySettings.update_point_size(self, context)

    def atom_coords_update(self, context):
        # reset coords list
        ABGlobals.atom_coords = []
        for elem_name in ABGlobals.all_elements_by_name:
            elem_amount = ABGlobals.all_elements_by_name[elem_name]['num_of_atoms']
            perc_displayed = bpy.context.scene.color_settings[elem_name].perc_displayed

            if not bpy.context.scene.color_settings[elem_name].display:
                perc_displayed = 0.0

            # if perc_displayed > 1.0 the input is not a percentage but an amount -> we calculate the percentage
            if perc_displayed > 1.0:
                num_displayed = int(perc_displayed)
                if num_displayed > elem_amount:
                    num_displayed = elem_amount
                perc_displayed = num_displayed / elem_amount
                bpy.context.scene.color_settings[elem_name].perc_displayed = perc_displayed
                return
            else:
                num_displayed = int(math.ceil(elem_amount * perc_displayed))

            ABGlobals.all_elements_by_name[elem_name]['num_displayed'] = num_displayed

            # build coord list for shader according to the new shown percentage
            this_elem_coords = ABGlobals.all_elements_by_name[elem_name]['coordinates'][:num_displayed]
            ABGlobals.atom_coords.append(this_elem_coords)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if len(ABGlobals.atom_coords) > 0 and isinstance(ABGlobals.atom_coords[0], list):
            ABGlobals.atom_coords = [x for xs in ABGlobals.atom_coords for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

        # update other lists
        DisplaySettings.atom_color_update(self, context)
        DisplaySettings.update_point_size(self, context)

    def update_display_all_elements(self, context):
        for elem_name in ABGlobals.all_elements_by_name:
            if bpy.context.scene.atom_blend_addon_settings.display_all_elements:
                bpy.context.scene.color_settings[elem_name].display = True
            else:
                bpy.context.scene.color_settings[elem_name].display = False
                # perc_displayed = 0.0

    def atom_color_update(self, context):
        # reset color list
        ABGlobals.atom_color_list = []

        for elem_name in ABGlobals.all_elements_by_name:
            num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']

            col_struct = bpy.context.scene.color_settings[elem_name].color
            col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            ABGlobals.atom_color_list.append([col] * num_displayed)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if len(ABGlobals.atom_color_list) > 0 and isinstance(ABGlobals.atom_color_list[0], list):
            ABGlobals.atom_color_list = [x for xs in ABGlobals.atom_color_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

    def update_point_size(self, context):
        ABGlobals.point_size_list = []

        for elem_name in ABGlobals.all_elements_by_name:
            num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']
            point_size = bpy.context.scene.color_settings[elem_name].point_size
            ABGlobals.point_size_list.append([point_size] * num_displayed)
            # print(elem_name, point_size, num_displayed, len(ABGlobals.point_size_list))

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if len(ABGlobals.point_size_list) > 0 and isinstance(ABGlobals.point_size_list[0], list):
            ABGlobals.point_size_list = [x for xs in ABGlobals.point_size_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

    def export_update(self, context):
        elem_coords = ABGlobals.all_elements_by_name[self.name]['coordinates']

        # create mesh
        elem_mesh = bpy.data.meshes.new(self.name)
        elem_mesh.from_pydata(elem_coords, [], [])
        elem_mesh.update()

        # create object
        elem_object = bpy.data.objects.new(self.name, elem_mesh)
        bpy.context.collection.objects.link(elem_object)

        # transform point cloud to the rest of the atom tip
        bpy.data.objects[self.name].rotation_euler[0] = math.pi
        bpy.data.objects[self.name].location[2] = bpy.data.objects['Top'].location[2]

        # transform object to point cloud
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.context.scene.objects[self.name]
        obj = bpy.data.objects[self.name]
        obj.select_set(True)
        bpy.ops.object.convert(target='POINTCLOUD')

        # add material to the point cloud
        mat = bpy.data.materials.new(name=self.name)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = bpy.context.scene.color_settings[self.name].color
        obj.data.materials.append(mat)

        # --- add geometry node stuff ---
        modifier = obj.modifiers.new(self.name, 'NODES')
        node_group = bpy.data.node_groups.new(type='GeometryNodeTree', name=self.name)
        modifier.node_group = node_group

        # input node
        group_inputs = node_group.nodes.new('NodeGroupInput')

        # set point radius node
        set_point_radius = node_group.nodes.new('GeometryNodeSetPointRadius')
        set_point_radius.location = (400, 0)
        set_point_radius.inputs[2].default_value = bpy.context.scene.color_settings[self.name].point_size / 16

        # output node
        group_outputs = node_group.nodes.new('NodeGroupOutput')
        group_outputs.location = (800, 0)

        # link nodes
        node_group.links.new(group_inputs.outputs[0], set_point_radius.inputs[0])
        node_group.links.new(set_point_radius.outputs[0], group_outputs.inputs[0])

        # deselect object
        bpy.data.objects[self.name].select_set(False)

    name: bpy.props.StringProperty(name="name", default="Unknown")
    display_name: bpy.props.StringProperty(name="name", default="Unknown")
    color: bpy.props.FloatVectorProperty(name="", subtype='COLOR', min=0.0, max=1.0, size=4, default=(0.4, 0.4, 0.4, 1.0), update=atom_color_update)
    display: bpy.props.BoolProperty(name="", default=True, update=atom_coords_update)
    perc_displayed: bpy.props.FloatProperty(name="", default=1.0, min=0.0, soft_min=0.0, soft_max=1.0, step=0.01, precision=4, update=atom_coords_update)
    point_size: bpy.props.FloatProperty(name="", default=5.0, min=0.0, soft_min=0.0, step=0.5, precision=2, update=update_point_size)
    export: bpy.props.BoolProperty(name='', description='Export this element as an own object. Only available in 3.5.0+ Alpha.', default=False, update=export_update)

# --- properties used for all elements ---
class AB_properties(bpy.types.PropertyGroup):
    # update functions
    def update_point_size(self, context):
        general_point_size = context.scene.atom_blend_addon_settings.point_size

        for elem_name in ABGlobals.all_elements_by_name:
            bpy.context.scene.color_settings[elem_name].point_size = general_point_size

    def update_camera_distance(self, context):
        bpy.data.objects['Camera'].location[1] = self.camera_distance

    def update_camera_elevation(self, context):
        center_loc = bpy.data.objects['Center'].location
        bpy.data.objects['Camera'].location[2] = center_loc[2] + self.camera_elevation

    def update_camera_rotation(self, context):
        bpy.data.objects['Top'].rotation_euler[2] = self.camera_rotation

    def update_camera_track_to_center(self, context):
        center_x = (ABGlobals.max_x + ABGlobals.min_x) / 2
        center_y = (ABGlobals.max_y + ABGlobals.min_y) / 2
        center_z = (ABGlobals.max_z + ABGlobals.min_z) / 2
        if self.camera_track_to_center:
            bpy.data.objects['Camera Tracker'].location = (center_x, center_y, center_z)
        else:
            bpy.data.objects['Camera Tracker'].location = (self.camera_pos_x, center_y, self.camera_pos_z)

    def update_camera_pos_x(self, context):
        if not self.camera_track_to_center or True:
            # the camera should be parallel to the tip. otherwise the x and y axis would not be parallel anymore
            bpy.data.objects['Camera Tracker'].location[0] = self.camera_pos_x
            bpy.data.objects['Camera'].location[0] = self.camera_pos_x

    def update_camera_pos_z(self, context):
        if not self.camera_track_to_center or True:
            # the camera should be parallel to the tip. otherwise the x and y axis would not be parallel anymore
            bpy.data.objects['Camera Tracker'].location[2] = self.camera_pos_z
            bpy.data.objects['Camera'].location[2] = self.camera_pos_z

    def update_frame_amount(self, context):
        # delete old keyframes
        bpy.data.objects['Top'].animation_data_clear()
        bpy.data.objects['Camera'].animation_data_clear()
        bpy.data.objects['Scaling Cube'].animation_data_clear()

        # set total amount of frames
        bpy.data.scenes["Scene"].frame_end = self.frames

        # set keyframes according to frames and rotation amount
        context.scene.objects['Top'].rotation_euler[2] = 0
        context.scene.objects['Scaling Cube'].rotation_euler[2] = 0
        for i in range(0, self.frames+1, self.frames // self.rotation_amount):
            context.scene.objects['Top'].keyframe_insert(data_path="rotation_euler", index=2, frame=i)
            context.scene.objects['Top'].rotation_euler[2] += 2 * math.pi

            if context.scene.atom_blend_addon_settings.scaling_cube_rotate_with_tip:
                context.scene.objects['Scaling Cube'].keyframe_insert(data_path="rotation_euler", index=2, frame=i)
                context.scene.objects['Scaling Cube'].rotation_euler[2] += 2 * math.pi

        if self.animation_mode == 'Spiral around tip':
            center_loc = context.scene.objects['Center'].location

            # set keyframe for frame 1
            context.scene.objects['Camera'].location[2] = center_loc[2] + 50
            context.scene.objects['Camera'].keyframe_insert(data_path="location", index=2, frame=1)

            # set keyframe for last frame
            context.scene.objects['Camera'].location[2] = center_loc[2] - 50
            context.scene.objects['Camera'].keyframe_insert(data_path="location", index=2, frame=self.frames)

        # make keyframes interpolation linear
        bpy.data.objects['Top'].animation_data.action.fcurves[0].keyframe_points[0].interpolation = 'LINEAR'
        bpy.data.objects['Top'].animation_data.action.fcurves[0].keyframe_points[1].interpolation = 'LINEAR'
        # keyframe.interpolation = 'LINEAR'

        # set duration value of property
        duration = self.frames / 24
        if float("{:.2f}".format(duration)) != float("{:.2f}".format(context.scene.atom_blend_addon_settings.duration)): # permit endless loop between frames and duration
            context.scene.atom_blend_addon_settings.duration = float("{:.2f}".format(duration))

    def update_duration(self, context):
        # set frame value of property
        frames = self.duration * 24
        if ceil(frames) != context.scene.atom_blend_addon_settings.frames:  # permit endless loop between frames and duration
            context.scene.atom_blend_addon_settings.frames = int(frames)

    def update_animation_mode(self, context):
        # delete camera keyframes
        bpy.data.objects['Camera'].animation_data_clear()

        if self.animation_mode == 'Spiral around tip':
            center_loc = context.scene.objects['Center'].location

            # set keyframe for frame 1
            context.scene.objects['Camera'].location[2] = center_loc[2] + 50
            context.scene.objects['Camera'].keyframe_insert(data_path="location", index=2, frame=1)

            # set keyframe for last frame
            context.scene.objects['Camera'].location[2] = center_loc[2] - 50
            context.scene.objects['Camera'].keyframe_insert(data_path="location", index=2, frame=self.frames)

    def update_background_color(self, context):
        # if context.space_data.region_3d.view_perspective == 'CAMERA':
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = self.background_color

    def update_file_format(self, context):
        # if render mode is image, change the displayed file path to the new file ending
        if ABGlobals.render_frame:
            file_path = bpy.data.scenes["Scene"].render.filepath
            file_format = context.scene.atom_blend_addon_settings.file_format.lower()

            bpy.data.scenes["Scene"].render.filepath = os.path.splitext(file_path)[0] + '.' + file_format

        if self.file_format == 'JPEG':
            context.scene.atom_blend_addon_settings.transparent_background = False

    def update_transparent_background(self, context):
        if self.file_format != 'JPEG':
            bpy.data.scenes["Scene"].render.film_transparent = not bpy.data.scenes["Scene"].render.film_transparent
        else:
            bpy.data.scenes["Scene"].render.film_transparent = False

        if not ABGlobals.render_frame:
            bpy.data.scenes["Scene"].render.film_transparent = False

        # show the transparent color in ui background color panel
        if self.transparent_background:
            bc = self.background_color
            context.scene.atom_blend_addon_settings.background_color = [bc[0], bc[1], bc[2], 0.0]
        else:
            bc = self.background_color
            context.scene.atom_blend_addon_settings.background_color = [bc[0], bc[1], bc[2], 1.0]

    def update_legend_scale(self, context):
        print('update legend scale')
        scale = context.scene.atom_blend_addon_settings.legend_scale
        default_line_spacing = 50
        default_column_spacing = 20
        default_point_size = 50
        default_font_size = 30
        context.scene.atom_blend_addon_settings.legend_line_spacing = int(default_line_spacing * scale)
        context.scene.atom_blend_addon_settings.legend_column_spacing = int(default_column_spacing * scale)
        context.scene.atom_blend_addon_settings.legend_point_size = int(default_point_size * scale)
        context.scene.atom_blend_addon_settings.legend_font_size = int(default_font_size * scale)

    def update_scaling_cube_track_to_center(self, context):
        if self.scaling_cube_track_to_center:
            bpy.data.objects['Scaling Cube'].location = (0, 0, 0)
        else:
            bpy.data.objects['Scaling Cube'].location = (self.scaling_cube_pos_x, self.scaling_cube_pos_y, self.scaling_cube_pos_z)

    def update_scaling_cube_pos_x(self, context):
        if not self.scaling_cube_track_to_center:
            bpy.data.objects['Scaling Cube'].location[0] = self.scaling_cube_pos_x

    def update_scaling_cube_pos_y(self, context):
        if not self.scaling_cube_track_to_center:
            bpy.data.objects['Scaling Cube'].location[1] = self.scaling_cube_pos_y

    def update_scaling_cube_pos_z(self, context):
        if not self.scaling_cube_track_to_center:
            # top_z = (ABGlobals.max_z + ABGlobals.min_z) / 2
            # bpy.data.objects['Scaling Cube'].location[2] = top_z + self.scaling_cube_pos_z
            bpy.data.objects['Scaling Cube'].location[2] = self.scaling_cube_pos_z

    # only accept values that are in a acceptable range
    def set_legend_position_x(self, value):
        if 0 <= value <= bpy.data.scenes["Scene"].render.resolution_x:
            self['legend_position_x'] = value

    def get_legend_position_x(self):
        return self.get('legend_position_x', 50) # if key is not found, return 50 (default)

    # only accept values that are in a acceptable range
    def set_legend_position_y(self, value):
        if 0 <= value <= bpy.data.scenes["Scene"].render.resolution_y:
            self['legend_position_y'] = value

    def get_legend_position_y(self):
        return self.get('legend_position_y', 50) # if key is not found, return 50 (default)


    # properties
    e_pos_filepath: bpy.props.StringProperty(name='', default='', description='')
    rrng_filepath: bpy.props.StringProperty(name='', default='', description='')
    vertex_percentage: bpy.props.FloatProperty(name="Total displayed (%)", default=0.001, min=0.000001, max=1.0, soft_min=1, step=0.01, description="Percentage of displayed atoms", precision=4, update=DisplaySettings.total_atom_coords_update)
    point_size: bpy.props.FloatProperty(name='Point size', default=5.0, min=0.0, max=100.0, step=0.5, description='Changes the point size of all the atoms', update=update_point_size)
    display_all_elements: bpy.props.BoolProperty(name='', default=True, description='Display or hide all elements', update=DisplaySettings.update_display_all_elements)
    background_color: bpy.props.FloatVectorProperty(name='Background color', subtype='COLOR', description='Background color for rendering', min=0.0, max=1.0, size=4, default=[1.0, 1.0, 1.0, 1.0], update=update_background_color)

    transparent_background: bpy.props.BoolProperty(name='Transparent Background', description='Only available for .png and .tiff file format and image rendering', default=False, update=update_transparent_background)
    camera_distance: bpy.props.FloatProperty(name='Camera distance', min=0.0, default=300.0, description='Edit the camera distance to the tip', update=update_camera_distance)
    camera_elevation: bpy.props.FloatProperty(name='Camera elevation', default=0.0, step=50, description='Edit the camera elevation', update=update_camera_elevation)
    camera_rotation: bpy.props.FloatProperty(name='Atom tip rotation', default=0.0, subtype='ANGLE', step=50.0, description='Rotate the atom tip', update=update_camera_rotation)
    camera_track_to_center: bpy.props.BoolProperty(name='Track camera to center of atom tip', description='If enabled, the camera is always tracked to the center of the atom tip', default=True, update=update_camera_track_to_center)
    camera_pos_x: bpy.props.FloatProperty(name='x-position', description='If the camera is not tracked to the atom tip\s center, the camera position can be edited', default=3.0, update=update_camera_pos_x)
    camera_pos_z: bpy.props.FloatProperty(name='z-position', description='If the camera is not tracked to the atom tip\s center, the camera position can be edited', default=3.0, update=update_camera_pos_z)

    frames: bpy.props.IntProperty(name='Frames', default=50, description='Duration of video', update=update_frame_amount, step=5)
    duration: bpy.props.FloatProperty(name='Duration (seconds)', precision=2, description='Duration of the video', min=0.0, soft_min=0.0, step=0.5, update=update_duration)
    rotation_amount: bpy.props.IntProperty(name='Number of rotations', default=1, description='Number of rotations', update=update_frame_amount)
    scaling_cube: bpy.props.BoolProperty(name='Scaling bar', default=True, description='Display the scaling bar')
    scaling_cube_mode: bpy.props.EnumProperty(
        name='',
        items=[('RGB', 'RGB', 'RGB'),
               ('Uniform Color', 'Uniform Color', 'Uniform Color')],
        default='RGB',
    )
    scaling_cube_uniform_color: bpy.props.FloatVectorProperty(name='', subtype='COLOR', description='Uniform color for scaling bar', min=0.0, max=1.0, size=4, default=[0.0, 0.0, 0.0, 1.0])
    scaling_cube_line_width: bpy.props.IntProperty(name='Line width', default=1, step=1, min=1, soft_min=1, description='Line width of the scaling cube')
    scaling_cube_font_size: bpy.props.IntProperty(name='Font size', default=30, min=0, soft_min=0, description='Font size of metric')
    scaling_cube_rotate_font: bpy.props.BoolProperty(name='Align font to axis', default=True, description='Rotate the font to align the axes')
    scaling_cube_track_to_center: bpy.props.BoolProperty(name='Track scaling cube to center of atom tip', description='If enabled, the scaling box is tracked to the center of the atom tip', default=True, update=update_scaling_cube_track_to_center)
    scaling_cube_pos_x: bpy.props.FloatProperty(name='x-position', description='If the scaling cube is not tracked to the atom tip\s center, the scaling cube position can be edited', default=0.0, update=update_scaling_cube_pos_x)
    scaling_cube_pos_y: bpy.props.FloatProperty(name='y-position', description='If the scaling cube is not tracked to the atom tip\s center, the scaling cube position can be edited', default=0.0, update=update_scaling_cube_pos_y)
    scaling_cube_pos_z: bpy.props.FloatProperty(name='z-position', description='If the scaling cube is not tracked to the atom tip\s center, the scaling cube position can be edited', default=0.0, update=update_scaling_cube_pos_z)
    scaling_cube_round: bpy.props.BoolProperty(name='Round', default=True, description='If activated, the size of the atom tip is rounded by the specified number of digits')
    scaling_cube_round_digits: bpy.props.IntProperty(name='Digits', default=0, soft_min=-4, soft_max=10, description='The number of digits that should be rounded')
    scaling_cube_scale: bpy.props.FloatVectorProperty(name='Scale', description='Scale the scaling cube', min=0.0, size=3, default=[1.0, 1.0, 1.0])
    scaling_cube_rotate_with_tip: bpy.props.BoolProperty(name='Rotate scaling cube', default=False, description='If activated, the scaling cube is rotated with the atom tip', update=update_frame_amount)

    legend: bpy.props.BoolProperty(name='Legend', default=True, description='Display the legend')
    legend_scale: bpy.props.FloatProperty(name='Scale', default=1.0, min=0.0, soft_min=0.0, description='Scale of legend', update=update_legend_scale)
    legend_font_color: bpy.props.FloatVectorProperty(name='Font color', subtype='COLOR', description='Color of the legend font', min=0.0, max=1.0, size=4, default=[0.0, 0.0, 0.0, 1.0])
    legend_position_x: bpy.props.IntProperty(name='x-position', description='Lower left corner x-position of the legend', min=0, default=50, set=set_legend_position_x, get=get_legend_position_x)
    legend_position_y: bpy.props.IntProperty(name='y-position', description='Lower left corner y-position of the legend', min=0, default=50, set=set_legend_position_y, get=get_legend_position_y)
    legend_line_spacing: bpy.props.IntProperty(name='Line spacing', description='Line spacing between elements', min=0, default=50)
    legend_column_spacing: bpy.props.IntProperty(name='Column spacing', description='Column spacing between the colored circle and element name', min=0, default=20)
    legend_point_size: bpy.props.IntProperty(name='Point size', description='Point size of the colored circle', min=0, default=50)
    legend_font_size: bpy.props.IntProperty(name='Font size', description='Font size of the element names', min=0, default=30)
    legend_hide_hidden_elements: bpy.props.BoolProperty(name='Hide hidden elements in legend', default=True, description='Hides elements that were hidden in display settings also in legend')

    animation_mode: bpy.props.EnumProperty(
        name='Animation mode',
        items=[('Circle around tip', 'Circle around tip', 'Circle around tip'),
               ('Spiral around tip', 'Spiral around tip', 'Spiral around tip')
               ],
        default='Circle around tip',
        update=update_animation_mode
    )
    file_format: bpy.props.EnumProperty(
        name='File format',
        items=[('PNG', 'PNG', 'PNG'),
               ('JPEG', 'JPEG', 'JPEG'),
               ('TIFF', 'TIFF', 'TIFF')],
        default='PNG',
        update=update_file_format
    )

    # for developing purposes
    dev_mode: bpy.props.BoolProperty(name='Dev mode', default=False)
    dev_automatic_file_loading: bpy.props.BoolProperty(name='Automatic file loading', default=True)
    dev_dataset_selection: bpy.props.EnumProperty(
        name='Dataset Selection',
        items=[('T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v05.epos?T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01.RRNG', 'Eisenkorngrenze', 'Eisenkorngrenze'),
               ('T:\Heller\AtomBlendII\EisenKorngrenze\FeGB_small.pos?T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01.RRNG', 'Eisenkorngrenze-small', 'Eisenkorngrenze-small'),
               ('T:\Heller\AtomBlendII\Data for iso-surface\R56_02476-v03', 'IsoSurface', 'IsoSurface')
        ],
        default='T:\Heller\AtomBlendII\EisenKorngrenze\FeGB_small.pos?T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01.RRNG',
        # default='T:\Heller\AtomBlendII\Data for iso-surface\R56_02476-v03',
    )

class ATOMBLEND_PT_panel_general(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_general"  # unique identifier for buttons and menu items to reference.
    bl_label = "AtomBlend-II"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"

    def draw(self, context):
        layout = self.layout

# --- file loading ---
class ATOMBLEND_PT_panel_file(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_file"  # unique identifier for buttons and menu items to reference.
    bl_label = "File loading"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    #bl_parent_id = "ATOMBLEND_PT_panel_general"

    # define own poll method to be able to hide / show the panel on demand
    @classmethod
    def poll(cls, context):
        # the panel should always be drawn
        return True

    def draw(self, context):
        layout = self.layout

        # .pos/.epos file
        col = layout.column(align=True)
        load_e_pos_file_row = col.row(align=True)
        col = load_e_pos_file_row.split(factor=0.3)
        col.label(text='.pos/.epos file:')
        col = col.split(factor=1.0)
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'e_pos_filepath')
        col.enabled = False
        col = load_e_pos_file_row.column(align=True)
        col.operator('atom_blend_viewer.load_file', icon='FILE_FOLDER', text='')

        # .rrng file
        load_rrng_file_row = layout.row(align=True)
        col = load_rrng_file_row.split(factor=0.3)
        col.label(text='.rng/.rrng file:')
        col = col.split(factor=1.0)
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'rrng_filepath')
        col.enabled = False
        col = load_rrng_file_row.column(align=True)
        col.operator('atom_blend_viewer.load_rrng_file', icon="FILE_FOLDER", text='')

        # unload files button
        if ABGlobals.FileLoaded_e_pos or ABGlobals.FileLoaded_rrng:
            unload_files_row = layout.row(align=True)
            unload_files_row.operator('atom_blend_viewer.unload_files')

# --- display settings ---
class ATOMBLEND_PT_shader_display_settings(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_shader_display_settings"  # unique identifier for buttons and menu items to reference.
    bl_label = "Display settings"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    #bl_parent_id = "ATOMBLEND_PT_panel_general"

    @classmethod
    def poll(cls, context):
        # draw panel as soon as e_pos file is loaded
        return ABGlobals.FileLoaded_e_pos

    def draw(self, context):
        layout = self.layout

        # point size settings
        row = layout.row()
        point_size_col = row.column(align=True)
        point_size_col.prop(context.scene.atom_blend_addon_settings, 'point_size')

        # total atoms shown in percentage
        vertex_percentage_row = layout.row()
        vertex_percentage_col = vertex_percentage_row.column(align=True)
        vertex_percentage_col.prop(context.scene.atom_blend_addon_settings, "vertex_percentage")

        # color settings
        # col = layout.column()
        # display_col = row.column()
        # displayed, name, charge, color, point size, % displayed, # displayed, export
        f = [0.07, 0.1, 0.1, 0.2, 0.2, 0.23, 0.1]
        perc_left = 1.0
        split = layout.split(factor=f[0] / perc_left)
        display_col = split.column(align=True)
        perc_left -= f[0]
        split = split.split(factor=f[1] / perc_left)
        display_name_col = split.column(align=True)
        perc_left -= f[1]
        # split = split.split(factor=f[2] / perc_left)
        # charge_col = split.column(align=True)
        # perc_left -= f[2]
        split = split.split(factor=f[2] / perc_left)
        color_col = split.column(align=True)
        perc_left -= f[2]
        split = split.split(factor=f[3] / perc_left)
        point_size_col = split.column(align=True)
        perc_left -= f[3]
        split = split.split(factor=f[4] / perc_left)
        displayed_col = split.column(align=True)
        perc_left -= f[4]
        split = split.split(factor=f[5] / perc_left)
        amount_col = split.column(align=True)
        perc_left -= f[5]
        split = split.split(factor=f[6] / perc_left)
        export_col = split.column(align=True)
        perc_left -= f[6]

        # label row
        prop = context.scene.atom_blend_addon_settings
        display_col.prop(prop, 'display_all_elements', icon_only=True, icon='HIDE_OFF' if prop.display_all_elements else 'HIDE_ON')
        # display_col.label(text='')
        display_name_col.label(text='Name')
        color_col.label(text='Color')
        point_size_col.label(text='Point size')
        displayed_col.label(text='% Displayed')
        amount_col.label(text='# Displayed')
        export_col.label(text='Export')

        # export feature is only available if (currently) version 3.6 alpha is used
        if bpy.app.version < (3, 6, 0):
            export_col.enabled = False

        display_all_elements = bpy.context.scene.atom_blend_addon_settings.display_all_elements

        for prop in bpy.context.scene.color_settings:
            if prop.name == ABGlobals.unknown_label:  # add unknown atoms in the last row
                continue
            elem_name_charge = prop.display_name
            print(elem_name_charge)
            elem_name = elem_name_charge.split('_')[0]
            display_col.prop(prop, 'display', icon_only=True, icon='HIDE_OFF' if prop.display else 'HIDE_ON')
            # name_col.label(text=elem_name)
            display_name_col.prop(prop, 'display_name', text='')
            color_col.prop(prop, 'color')
            point_size_col.prop(prop, 'point_size')
            displayed_col.prop(prop, 'perc_displayed')
            atom_amount_shown = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_displayed'])  # add comma after every thousand place
            atom_amount_available = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_of_atoms'])  # add comma after every thousand place
            amount_col.label(text=str(atom_amount_shown) + '/' + str(atom_amount_available))
            export_col.prop(prop, 'export', icon='EXPORT')

        # display unknown atoms in last row
        prop = bpy.context.scene.color_settings[ABGlobals.unknown_label]
        elem_name_charge = prop.name
        elem_name = elem_name_charge.split('_')[0]
        display_col.prop(prop, 'display', icon_only=True, icon='HIDE_OFF' if prop.display else 'HIDE_ON')
        display_name_col.prop(prop, 'display_name', text='')
        color_col.prop(prop, 'color')
        point_size_col.prop(prop, 'point_size')
        displayed_col.prop(prop, 'perc_displayed')
        atom_amount_shown = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_displayed'])  # add comma after every thousand place
        atom_amount_available = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_of_atoms'])  # add comma after every thousand place
        amount_col.label(text=str(atom_amount_shown) + '/' + str(atom_amount_available))
        export_col.prop(prop, 'export', icon='EXPORT')

# --- development extras ---
class ATOMBLEND_PT_panel_dev(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_dev"  # unique identifier for buttons and menu items to reference.
    bl_label = "Development Extras"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    #bl_parent_id = "ATOMBLEND_PT_panel_general"
    bl_options = {'DEFAULT_CLOSED'}

    # @classmethod
    # def poll(cls, context):
    #     return True  # context.object is not None

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'dev_dataset_selection')
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'dev_automatic_file_loading')


# --- legend ---
class ATOMBLEND_PT_legend_basic(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_legend_basic"
    bl_label = "Legend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # draw panel as soon as e_pos file is loaded
        return ABGlobals.FileLoaded_e_pos

    def draw_header(self, context):
        self.layout.prop(context.scene.atom_blend_addon_settings, 'legend', text="")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        row = col.row()
        row.active = context.scene.atom_blend_addon_settings.legend
        row.prop(context.scene.atom_blend_addon_settings, 'legend_scale')

class ATOMBLEND_PT_legend_advanced_settings(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_legend_advanced_settings"
    bl_label = "Advanced settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = 'ATOMBLEND_PT_legend_basic'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # draw panel as soon as e_pos file is loaded
        return ABGlobals.FileLoaded_e_pos

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.active = context.scene.atom_blend_addon_settings.legend
        x_pos = row.column(align=True)
        x_pos.prop(context.scene.atom_blend_addon_settings, 'legend_position_x')
        y_pos = row.column(align=True)
        y_pos.prop(context.scene.atom_blend_addon_settings, 'legend_position_y')

        row = col.row(align=True)
        row.active = context.scene.atom_blend_addon_settings.legend
        row.prop(context.scene.atom_blend_addon_settings, 'legend_line_spacing')
        row.prop(context.scene.atom_blend_addon_settings, 'legend_column_spacing')

        col = layout.column(align=True)
        row = col.row(align=True)
        row.active = context.scene.atom_blend_addon_settings.legend
        row.prop(context.scene.atom_blend_addon_settings, 'legend_point_size')

        row = col.row(align=True)
        row.active = context.scene.atom_blend_addon_settings.legend
        row.prop(context.scene.atom_blend_addon_settings, 'legend_font_size')

        col = layout.column(align=True)
        row = col.row()
        row.active = context.scene.atom_blend_addon_settings.legend
        split = row.split(factor=0.3)
        split.label(text='Font color:')
        split = split.split(factor=1.0)
        split.prop(context.scene.atom_blend_addon_settings, 'legend_font_color', text='')

        col = layout.column(align=True)
        row = col.row()
        row.active = context.scene.atom_blend_addon_settings.legend
        row.prop(context.scene.atom_blend_addon_settings, 'legend_hide_hidden_elements')


# --- scaling bar ---
class ATOMBLEND_PT_scaling_cube(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_scaling_cube"
    bl_label = "Scaling cube"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # draw panel as soon as e_pos file is loaded
        return ABGlobals.FileLoaded_e_pos

    def draw_header(self, context):
        self.layout.prop(context.scene.atom_blend_addon_settings, 'scaling_cube', text="")

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        row = col.row(align=True)
        row.active = context.scene.atom_blend_addon_settings.scaling_cube
        perc_left = 1.0

        row.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_mode')
        if context.scene.atom_blend_addon_settings.scaling_cube_mode == 'Uniform Color':
            f = [0.5, 0.5]
            split = row.split(factor=f[0] - perc_left)
            perc_left -= f[0]

            split = split.split(factor=f[1] / perc_left)
            split.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_uniform_color')

        row = col.row(align=True)
        row.active = context.scene.atom_blend_addon_settings.scaling_cube
        row.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_line_width')

        col = layout.column(align=True)
        row = col.row()
        row.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_scale')

        col = layout.column(align=True)
        row = col.row()
        row.active = context.scene.atom_blend_addon_settings.scaling_cube
        row.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_font_size')

        row = col.row()
        row.active = context.scene.atom_blend_addon_settings.scaling_cube
        row.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_rotate_font')

        row = col.row()
        row.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_round')
        row.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_round_digits')


class ATOMBLEND_PT_scaling_cube_track_to_center(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_scaling_cube_track_to_center"
    bl_label = "Track scaling cube to center of atom tip"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = 'ATOMBLEND_PT_scaling_cube'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # draw panel as soon as e_pos file is loaded
        return ABGlobals.FileLoaded_e_pos

    def draw_header(self, context):
        self.layout.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_track_to_center', text='')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row()
        row.active = not context.scene.atom_blend_addon_settings.scaling_cube_track_to_center
        row.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_pos_x')
        row.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_pos_y')
        row.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_pos_z')

# --- render settings ---
class ATOMBLEND_PT_rendering(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_rendering"
    bl_label = "Rendering"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    #bl_parent_id = "ATOMBLEND_PT_panel_general"
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # draw panel as soon as e_pos file is loaded
        return ABGlobals.FileLoaded_e_pos

    def draw(self, context):
        layout = self.layout

        # camera settings
        col = layout.column(align=True)
        render_mode_row = col.row(align=True)
        render_mode_row.operator('atom_blend.render_frame', depress=ABGlobals.render_frame)
        render_mode_row.operator('atom_blend.render_video', depress=not ABGlobals.render_frame)

        # background color
        box = layout.box()
        col = box.column()
        if ABGlobals.render_frame:
            f = [0.3, 0.3, 0.4]
        else:
            f = [0.3, 0.7]

        perc_left = 1.0
        split = col.split(factor=f[0] / perc_left)
        text = split.column(align=True)
        text.label(text='Background Color')
        perc_left -= f[0]

        split = split.split(factor=f[1] / perc_left)
        background_color = split.column(align=True)
        background_color.prop(context.scene.atom_blend_addon_settings, 'background_color', text='')
        perc_left -= f[1]

        # transparent background
        if ABGlobals.render_frame:
            split = split.split(factor=f[2] / perc_left)
            transparent_background = split.column(align=True)
            transparent_background.prop(context.scene.atom_blend_addon_settings, 'transparent_background')
            perc_left -= f[2]

            if context.scene.atom_blend_addon_settings.file_format == 'JPEG':
                transparent_background.enabled = False

        if not ABGlobals.render_frame:
            # layout.row().separator(factor=0.01)
            box = layout.box()
            col = box.column()
            # frame amount
            frame_duration_amount = col.row(align=True)
            seconds = str('%.1f' % (context.scene.atom_blend_addon_settings.frames / 24))
            frame_duration_amount.prop(context.scene.atom_blend_addon_settings, 'duration')
            frame_duration_amount.prop(context.scene.atom_blend_addon_settings, 'frames')
            # frame_duration_amount.prop(context.scene.atom_blend_addon_settings, 'frames', text='Frames (approx.' + str(seconds) + ' seconds)')

            # rotation amount
            rot_amount = col.row(align=True)
            rot_amount.prop(context.scene.atom_blend_addon_settings, 'rotation_amount')

            # animation mode
            anim_mode = col.row(align=True)
            anim_mode.prop(bpy.context.scene.atom_blend_addon_settings, 'animation_mode')

        # layout.row().separator(factor=0.01)

        # output image resolution
        # resolution_label = layout.row(align=True)
        box = layout.box()
        col = box.column()
        f = [0.23, 0.385, 0.385]
        perc_left = 1.0
        split = col.split(factor=f[0] / perc_left, align=True)
        resolution_xy = split.column(align=True)
        resolution_xy.label(text='Resolution:')
        perc_left -= f[0]

        split = split.split(factor=f[1] / perc_left, align=True)
        resolution_xy = split.column(align=True)
        resolution_xy.prop(bpy.data.scenes["Scene"].render, 'resolution_x', text='Width')
        perc_left -= f[1]

        split = split.split(factor=f[2] / perc_left, align=True)
        resolution_xy = split.column(align=True)
        resolution_xy.prop(bpy.data.scenes["Scene"].render, 'resolution_y', text='Height')

        # file format
        # file_format_col = layout.row(align=True)
        file_format_col = col
        file_format_col.prop(context.scene.atom_blend_addon_settings, 'file_format')

        # file path selection
        # file_path_row = layout.row(align=True)
        file_path_row = col
        file_path_row.prop(bpy.data.scenes["Scene"].render, 'filepath')

        # render
        row = layout.row()
        # preview_col = row.column(align=True)
        # render_col = row.column(align=True)

        # prev_split = preview_col.split(factor=0.8)
        # preview_button_col = prev_split.column(align=True)
        #
        # preview_split = prev_split.split(factor=1.0)
        # start_stop_col = preview_split.column(align=True)

        preview_col = row.split()
        preview_col = preview_col.split(align=True, factor=1.0 if ABGlobals.render_frame else 0.9)

        if context.space_data.region_3d.view_perspective == 'PERSP' or context.space_data.region_3d.view_perspective == 'ORTHO':  # view mode
            preview_col.operator('atom_blend.preview', icon='SEQ_PREVIEW')
        elif context.space_data.region_3d.view_perspective == 'CAMERA':  # preview
            preview_col.operator('atom_blend.preview', icon='SEQ_PREVIEW', depress=True)

        if not ABGlobals.render_frame:
            start_stop_col = preview_col.split(align=True)
            start_stop_col.operator('atom_blend.start_stop', icon='PAUSE' if ABGlobals.animation_playing else 'PLAY')

        render_col = row.split()
        render_col.operator('atom_blend.render', icon='RENDER_STILL')

class ATOMBLEND_PT_placement_settings(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_placement_settings"
    bl_label = "Placement settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # draw panel as soon as e_pos file is loaded
        return ABGlobals.FileLoaded_e_pos

    def draw(self, context):
        # camera location
        layout = self.layout
        col = layout.column(align=True)
        col.prop(context.scene.atom_blend_addon_settings, 'camera_distance')
        col.prop(context.scene.atom_blend_addon_settings, 'camera_elevation')
        col.separator()
        col.prop(context.scene.atom_blend_addon_settings, 'camera_rotation')
        col.prop(context.scene.atom_blend_addon_settings, 'scaling_cube_rotate_with_tip')

class ATOMBLEND_PT_camera_settings_track_to_center(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_camera_settings_track_to_center"
    bl_label = "Track camera to center of atom tip"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = 'ATOMBLEND_PT_placement_settings'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # draw panel as soon as e_pos file is loaded
        return ABGlobals.FileLoaded_e_pos

    def draw_header(self, context):
        self.layout.prop(context.scene.atom_blend_addon_settings, 'camera_track_to_center', text='')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row()
        row.active = not context.scene.atom_blend_addon_settings.camera_track_to_center
        row.prop(context.scene.atom_blend_addon_settings, 'camera_pos_x')
        row.prop(context.scene.atom_blend_addon_settings, 'camera_pos_z')


# --- file loading ---
class ATOMBLEND_OT_load_file(bpy.types.Operator):
    bl_idname = "atom_blend_viewer.load_file"
    bl_label = "Load .pos/.epos file"
    bl_description = "Load a file of the following types:\n.epos, .pos"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(
        default='*.epos;*.pos',
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        ABGlobals.path = self.filepath

        # if there's already an object loaded we want to delete it so we can load another object
        if ABGlobals.FileLoaded_e_pos:
            obj_to_delete = bpy.data.objects['Top']
            bpy.data.objects.remove(obj_to_delete, do_unlink=True)

        if ABGlobals.path.lower().endswith('.epos'):
            AtomBlendAddon.load_epos_file(self, context)
        elif ABGlobals.path.lower().endswith('.pos'):
            AtomBlendAddon.load_pos_file(self, context)

        ABGlobals.FileLoaded_e_pos = True
        print(f"Object Loaded: {ABGlobals.FileLoaded_e_pos}")

        # set filepath to property
        bpy.context.scene.atom_blend_addon_settings.e_pos_filepath = self.filepath

        return {'FINISHED'}

    def invoke(self, context, event):
        path = context.scene.atom_blend_addon_settings.dev_dataset_selection.split('?')[0]
        if context.scene.atom_blend_addon_settings.dev_automatic_file_loading and os.path.isfile(path):
            self.filepath = path
            return self.execute(context)
        else:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

class ATOMBLEND_OT_load_rrng_file(bpy.types.Operator):
    bl_idname = "atom_blend_viewer.load_rrng_file"
    bl_label = "Load .rng/.rrng file"
    bl_description = "Load a file of the following types:\n.rrng"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(
        default='*.rng;*.rrng',
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        ABGlobals.path_rrng = self.filepath

        if ABGlobals.path_rrng.lower().endswith('.rrng'):
            AtomBlendAddon.load_rrng_file(self, context)
        elif ABGlobals.path_rrng.lower().endswith('.rng'):
            AtomBlendAddon.load_rng_file(self, context)

        ABGlobals.FileLoaded_rrng = True
        print(f"Object Loaded: {ABGlobals.FileLoaded_rrng}")

        # set filepath to property
        bpy.context.scene.atom_blend_addon_settings.rrng_filepath = self.filepath

        # https://docs.blender.org/api/current/bpy.types.Operator.html#calling-a-file-selector
        return {'FINISHED'}

    def invoke(self, context, event):
        path = context.scene.atom_blend_addon_settings.dev_dataset_selection.split('?')[1]
        if context.scene.atom_blend_addon_settings.dev_automatic_file_loading and os.path.isfile(path):
            self.filepath = path
            return self.execute(context)
        else:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

# unload file
class ATOMBLEND_OT_unload_files(bpy.types.Operator):
    bl_idname = "atom_blend_viewer.unload_files"
    bl_label = "Unload .pos/.epos and .rng/.rrng file"
    bl_description = "Unload the currently loaded files"

    # filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    # filter_glob: bpy.props.StringProperty(
    #     default='*.epos;*.pos',
    #     options={'HIDDEN'}
    # )

    @classmethod
    def poll(cls, context):
        return ABGlobals.FileLoaded_e_pos or ABGlobals.FileLoaded_rrng

    def execute(self, context):
        # clear all data storages
        ABGlobals.all_elements.clear()
        ABGlobals.all_elements_by_name.clear()
        ABGlobals.all_data = []
        ABGlobals.element_count.clear()
        ABGlobals.atom_coords.clear()
        ABGlobals.atom_color_list.clear()
        ABGlobals.point_size_list.clear()

        # files are not loaded anymore
        ABGlobals.FileLoaded_e_pos = False
        ABGlobals.FileLoaded_rrng = False

        # reset file paths
        bpy.context.scene.atom_blend_addon_settings.e_pos_filepath = ''
        bpy.context.scene.atom_blend_addon_settings.rrng_filepath = ''

        # delete objects
        obj = bpy.data.objects['Camera']
        bpy.data.objects.remove(obj, do_unlink=True)

        obj = bpy.data.objects['Center']
        bpy.data.objects.remove(obj, do_unlink=True)

        obj = bpy.data.objects['Origin']
        bpy.data.objects.remove(obj, do_unlink=True)

        obj = bpy.data.objects['Top']
        bpy.data.objects.remove(obj, do_unlink=True)

        return {'FINISHED'}

    # def invoke(self, context, event):
    #     path = context.scene.atom_blend_addon_settings.dev_dataset_selection + '.epos'
    #     if context.scene.atom_blend_addon_settings.dev_automatic_file_loading and os.path.isfile(path):
    #         self.filepath = context.scene.atom_blend_addon_settings.dev_dataset_selection + '.epos'
    #         return self.execute(context)
    #     else:
    #         context.window_manager.fileselect_add(self)
    #         return {'RUNNING_MODAL'}


# --- buttons for switching between rendering a picture and video ---
# (maybe there is a better solution for this...)
class ATOMBLEND_OT_render_frame(bpy.types.Operator):
    bl_idname = "atom_blend.render_frame"
    bl_label = "Picture"
    bl_description = "Select if you want to render a picture"

    @classmethod
    def poll(cls, context):
        return ABGlobals.FileLoaded_e_pos # context.object is not None

    def execute(self, context):
        # set file format from avi to png/jpg/tiff
        file_path = bpy.data.scenes["Scene"].render.filepath
        file_format = context.scene.atom_blend_addon_settings.file_format.lower()
        if os.path.splitext(file_path)[1].lower() == '.avi':
            bpy.data.scenes["Scene"].render.filepath = os.path.splitext(file_path)[0] + '.' + file_format

        ABGlobals.render_frame = True
        if ABGlobals.animation_playing:  # if going to frame render mode and animation is still playing, stop it
            bpy.ops.screen.animation_play()
            ABGlobals.animation_playing = not ABGlobals.animation_playing
        return {'FINISHED'}


class ATOMBLEND_OT_render_video(bpy.types.Operator):
    bl_idname = "atom_blend.render_video"
    bl_label = "Video"
    bl_description = "Select if you want to render a video"

    @classmethod
    def poll(cls, context):
        return ABGlobals.FileLoaded_e_pos
        # return True  # context.object is not None

    def execute(self, context):
        # set file format from png/jpg/tiff to avi
        file_path = bpy.data.scenes["Scene"].render.filepath
        if os.path.splitext(file_path)[1].lower() in ['.png', '.jpg', '.jpeg', '.tiff']:
            bpy.data.scenes["Scene"].render.filepath = os.path.splitext(file_path)[0] + '.avi'

        ABGlobals.render_frame = False
        context.scene.atom_blend_addon_settings.transparent_background = False

        return {'FINISHED'}


# --- render button ---
class ATOMBLEND_OT_render(bpy.types.Operator):
    bl_idname = "atom_blend.render"
    bl_label = "Render"
    bl_description = "Render the scene"

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        if ABGlobals.render_frame:
            ABManagement.save_image(self, context)
        else:
            out_path = os.path.dirname(bpy.data.scenes['Scene'].render.filepath)
            # clear existing frames in video edit before rendering
            bpy.ops.sequencer.select_all(action='SELECT')
            bpy.ops.sequencer.delete()

            print('Starting animation rendering...')

            for i in range(1, context.scene.atom_blend_addon_settings.frames+1):
                bpy.context.scene.frame_set(i)

                # write file
                img_path = ABManagement.save_image(self, context, cur_frame=i)

                # add frame to video editor
                img_name = os.path.split(img_path)[1]
                # img_path = out_path + '\\' + ABGlobals.dataset_name + '_frame_' + str(i) + '.png'
                # img_path = r'%s' %img_path

                bpy.context.scene.sequence_editor.sequences.new_image(name=img_name, filepath=img_path, channel=1, frame_start=i)
                print('Rendered frame ' + str(i) + ' / ' + str(context.scene.atom_blend_addon_settings.frames))

            print('Wrote all frames. Creating the video now...')
            # render and save video
            bpy.data.scenes["Scene"].render.image_settings.file_format = 'AVI_JPEG'
            bpy.context.scene.render.filepath = out_path + '\\' + ABGlobals.dataset_name + '.avi'
            bpy.ops.render.render(animation=True)

            # delete all the written frames
            # file_format = context.scene.atom_blend_addon_settings.file_format.lower()
            # for i in range(1, context.scene.atom_blend_addon_settings.frames+1):
            #     os.remove(path=out_path + '\\' + ABGlobals.dataset_name + '_frame_' + str(i) + '.' + file_format)

            print('Animation rendering done. Saved video to ' + str(out_path) + '\\' + ABGlobals.dataset_name + '.avi')

        return {'FINISHED'}


# --- preview the render ---
class ATOMBLEND_OT_preview(bpy.types.Operator):
    bl_idname = "atom_blend.preview"
    bl_label = "Preview"
    bl_description = "Preview the render"

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        # toggle (normal) perspective view and camera view
        if context.space_data.region_3d.view_perspective == 'PERSP' or context.space_data.region_3d.view_perspective == 'ORTHO':
            context.space_data.region_3d.view_perspective = 'CAMERA'
            # background_color = bpy.context.scene.atom_blend_addon_settings.background_color
            # bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = background_color

        elif context.space_data.region_3d.view_perspective == 'CAMERA':
            context.space_data.region_3d.view_perspective = 'PERSP'
            # bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.051, 0.051, 0.051, 1)
            if ABGlobals.animation_playing and not ABGlobals.render_frame:  # if leaving preview mode and animation is still playing, stop it
                bpy.ops.screen.animation_play()
                ABGlobals.animation_playing = not ABGlobals.animation_playing

        return {'FINISHED'}


# --- preview start/stop button ---
class ATOMBLEND_OT_start_stop(bpy.types.Operator):
    bl_idname = "atom_blend.start_stop"
    bl_label = ""
    bl_description = "Start or stop the animation"

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        bpy.ops.screen.animation_play()
        ABGlobals.animation_playing = not ABGlobals.animation_playing
        return {'FINISHED'}