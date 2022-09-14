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
        print(total_atoms_perc_displayed, len(ABGlobals.all_data), context.scene.atom_blend_addon_settings.vertex_percentage)

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
        print('UPDATE POINT SIZE DISPLAY SETTINGS')

        for elem_name in ABGlobals.all_elements_by_name:
            num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']
            point_size = bpy.context.scene.color_settings[elem_name].point_size
            ABGlobals.point_size_list.append([point_size] * num_displayed)
            print(elem_name, point_size, num_displayed, len(ABGlobals.point_size_list))

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if len(ABGlobals.point_size_list) > 0 and isinstance(ABGlobals.point_size_list[0], list):
            ABGlobals.point_size_list = [x for xs in ABGlobals.point_size_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

    name: bpy.props.StringProperty(name="Test Property", default="Unknown")
    color: bpy.props.FloatVectorProperty(name="", subtype='COLOR', min=0.0, max=1.0, size=4, default=(0.4, 0.4, 0.4, 1.0), update=atom_color_update)
    display: bpy.props.BoolProperty(name="", default=True, update=atom_coords_update)
    perc_displayed: bpy.props.FloatProperty(name="", default=1.0, min=0.0, soft_min=0.0, soft_max=1.0, step=0.01, precision=4, update=atom_coords_update)
    point_size: bpy.props.FloatProperty(name="", default=5.0, min=0.0, soft_min=0.0, step=0.5, precision=2, update=update_point_size)

# --- properties used for all elements ---
class AB_properties(bpy.types.PropertyGroup):
    # update functions
    def update_point_size(self, context):
        print('UPDATE POINT SIZE AB PROP')
        general_point_size = context.scene.atom_blend_addon_settings.point_size

        for elem_name in ABGlobals.all_elements_by_name:
            bpy.context.scene.color_settings[elem_name].point_size = general_point_size

    def update_camera_distance(self, context):
        dist = self.camera_distance
        bpy.data.objects['Camera path'].scale = (dist, dist, dist)

    def update_camera_elevation(self, context):
        angle = self.camera_elevation
        bpy.data.objects['Camera path'].location[2] = angle

    def update_camera_rotation(self, context):
        offset = self.camera_rotation
        bpy.data.objects["Camera"].constraints["Follow Path"].offset = offset

    def update_frame_rot_amount(self, context):
        # set frame amount in path settings
        bpy.context.view_layer.objects.active = bpy.data.objects['Camera path']
        bpy.data.curves['BezierCircle'].path_duration = int(self.frame_amount / self.rotation_amount)

        # animate path
        # bpy.context.view_layer.objects.active = bpy.data.objects['Camera']
        # bpy.ops.constraint.followpath_path_animate(constraint='Follow Path')

        # set total amount of frames
        bpy.data.scenes["Scene"].frame_end = self.frame_amount

    def update_animation_mode(self, context):
        if self.animation_mode == 'Circle around tip':
            # clear the keyframes in the first and last frame
            cam_path = bpy.data.objects['Camera path']
            cam_path.keyframe_delete(data_path='location', index=2, frame=1)
            cam_path.keyframe_delete(data_path='location', index=2, frame=self.frame_amount)

        elif self.animation_mode == 'Spiral around tip':
            cam_path = bpy.data.objects['Camera path']
            # set keyframe for frame 1
            cam_path.location[2] = 50
            cam_path.keyframe_insert(data_path="location", index=2, frame=1)

            # set keyframe for last frame
            frame_amount = self.frame_amount
            cam_path.location[2] = -50
            cam_path.keyframe_insert(data_path="location", index=2, frame=frame_amount)

    def update_background_color(self, context):
        # if context.space_data.region_3d.view_perspective == 'CAMERA':
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = self.background_color


    # properties
    e_pos_filepath: bpy.props.StringProperty(name='', default='', description='')
    rrng_filepath: bpy.props.StringProperty(name='', default='', description='')
    vertex_percentage: bpy.props.FloatProperty(name="Total displayed", default=0.001, min=0.000001, max=1.0, soft_min=1, step=0.01, description="Percentage of displayed atoms", precision=4, update=DisplaySettings.total_atom_coords_update)
    point_size: bpy.props.FloatProperty(name='Point size', default=5.0, min=0.0, max=100.0, step=0.5, description='Point size of the atoms', update=update_point_size)
    display_all_elements: bpy.props.BoolProperty(name='', default=True, description='Display or hide all elements', update=DisplaySettings.update_display_all_elements)
    background_color: bpy.props.FloatVectorProperty(name='Background color', subtype='COLOR', description='Background color for rendering', min=0.0, max=1.0, size=4, default=[1.0, 1.0, 1.0, 1.0], update=update_background_color)
    camera_distance: bpy.props.FloatProperty(name='Camera distance', min=0.0, default=3.0, description='Edit the camera distance to the tip', update=update_camera_distance)
    camera_rotation: bpy.props.FloatProperty(name='Camera rotation', default=0.0, description='Rotate the camera around the tip', update=update_camera_rotation)
    camera_elevation: bpy.props.FloatProperty(name='Camera elevation', default=0.0, description='Edit the camera elevation', update=update_camera_elevation)
    frame_amount: bpy.props.IntProperty(name='Frames', default=5, description='Amount of frames', update=update_frame_rot_amount)
    rotation_amount: bpy.props.IntProperty(name='Number of rotations', default=1, description='Number of rotations', update=update_frame_rot_amount)
    animation_mode: bpy.props.EnumProperty(
        name='Animation mode',
        items=[('Circle around tip', 'Circle around tip', 'Circle around tip'),
               ('Spiral around tip', 'Spiral around tip', 'Spiral around tip')
               ],
        default='Circle around tip',
        update=update_animation_mode
    )

    # for developing purposes
    dev_automatic_file_loading: bpy.props.BoolProperty(name='Automatic file loading', default=True)
    dev_dataset_selection: bpy.props.EnumProperty(
        name='Dataset Selection',
        items=[('T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01', 'Eisenkorngrenze', 'Eisenkorngrenze'),
               ('T:\Heller\AtomBlendII\Data for iso-surface\R56_02476-v03', 'IsoSurface', 'IsoSurface')
        ],
        default='T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01',
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
    bl_parent_id = "ATOMBLEND_PT_panel_general"

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
        col.operator('atom_blend_viewer.load_file', icon='FILE_FOLDER')

        # .rrng file
        load_rrng_file_row = layout.row(align=True)
        col = load_rrng_file_row.split(factor=0.3)
        col.label(text='.rrng file:')
        col = col.split(factor=1.0)
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'rrng_filepath')
        col.enabled = False
        col = load_rrng_file_row.column(align=True)
        col.operator('atom_blend_viewer.load_rrng_file', icon="FILE_FOLDER")

# --- display settings ---
class ATOMBLEND_PT_shader_display_settings(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_shader_display_settings"  # unique identifier for buttons and menu items to reference.
    bl_label = "Display settings"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = "ATOMBLEND_PT_panel_general"


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
        split = layout.split(factor=0.1)
        display_col = split.column(align=True)
        split = split.split(factor=0.05 / 0.9)
        name_col = split.column(align=True)
        split = split.split(factor=0.05 / 0.85)
        charge_col = split.column(align=True)
        split = split.split(factor=0.1 / 0.8)
        color_col = split.column(align=True)
        split = split.split(factor=0.2 / 0.6)
        point_size_col = split.column(align=True)
        split = split.split(factor=0.2 / 0.4)
        displayed_col = split.column(align=True)
        split = split.split(factor=0.2 / 0.2)
        amount_col = split.column(align=True)
        # split = split.split(factor=0.0)

        # label row
        prop = context.scene.atom_blend_addon_settings
        display_col.prop(prop, 'display_all_elements', icon_only=True, icon='HIDE_OFF' if prop.display_all_elements else 'HIDE_ON')
        # display_col.label(text='')
        name_col.label(text='Name')
        charge_col.label(text='Charge')
        color_col.label(text='Color')
        point_size_col.label(text='Point size')
        displayed_col.label(text='% Displayed')
        amount_col.label(text='# Displayed')

        display_all_elements = bpy.context.scene.atom_blend_addon_settings.display_all_elements

        for prop in bpy.context.scene.color_settings:
            if prop.name == ABGlobals.unknown_label:  # add unknown atoms in the last row
                continue

            elem_name_charge = prop.name
            elem_name = elem_name_charge.split('_')[0]
            elem_charge = elem_name_charge.split('_')[1]
            display_col.prop(prop, 'display', icon_only=True, icon='HIDE_OFF' if prop.display else 'HIDE_ON')
            name_col.label(text=elem_name)
            charge_col.label(text=elem_charge)
            color_col.prop(prop, 'color')
            point_size_col.prop(prop, 'point_size')
            displayed_col.prop(prop, 'perc_displayed')
            atom_amount_shown = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_displayed'])  # add comma after every thousand place
            atom_amount_available = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_of_atoms'])  # add comma after every thousand place
            amount_col.label(text=str(atom_amount_shown) + '/' + str(atom_amount_available))

        # display unknown atoms in last row
        prop = bpy.context.scene.color_settings[ABGlobals.unknown_label]
        elem_name_charge = prop.name
        elem_name = elem_name_charge.split('_')[0]
        elem_charge = elem_name_charge.split('_')[1]
        display_col.prop(prop, 'display', icon_only=True, icon='HIDE_OFF' if prop.display else 'HIDE_ON')
        name_col.label(text=elem_name)
        charge_col.label(text=elem_charge)
        color_col.prop(prop, 'color')
        point_size_col.prop(prop, 'point_size')
        displayed_col.prop(prop, 'perc_displayed')
        atom_amount_shown = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_displayed'])  # add comma after every thousand place
        atom_amount_available = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_of_atoms'])  # add comma after every thousand place
        amount_col.label(text=str(atom_amount_shown) + '/' + str(atom_amount_available))

# --- development extras ---
class ATOMBLEND_PT_panel_dev(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_dev"  # unique identifier for buttons and menu items to reference.
    bl_label = "Development Extras"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = "ATOMBLEND_PT_panel_general"
    bl_options = {'DEFAULT_CLOSED'}

    # @classmethod
    # def poll(cls, context):
    #     return True  # context.object is not None

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'dev_dataset_selection')
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'dev_automatic_file_loading')


# --- render settings ---
class ATOMBLEND_PT_rendering(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_rendering"
    bl_label = "Rendering"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = "ATOMBLEND_PT_panel_general"
    bl_options = {'DEFAULT_CLOSED'}

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

        # camera location
        col.label(text='Camera settings:')
        col.prop(context.scene.atom_blend_addon_settings, 'camera_distance')
        col.prop(context.scene.atom_blend_addon_settings, 'camera_rotation')
        col.prop(context.scene.atom_blend_addon_settings, 'camera_elevation')

        # background color
        background_color = layout.row(align=True)
        background_color.prop(context.scene.atom_blend_addon_settings, 'background_color')

        if not ABGlobals.render_frame:
            col = layout.column(align=True)
            # frame amount
            frame_amount = col.row(align=True)
            seconds = str('%.1f' % (context.scene.atom_blend_addon_settings.frame_amount / 24))
            frame_amount.prop(context.scene.atom_blend_addon_settings, 'frame_amount', text='Frames (approx.' + str(seconds) + ' seconds)')

            # rotation amount
            rot_amount = col.row(align=True)
            rot_amount.prop(context.scene.atom_blend_addon_settings, 'rotation_amount')

            # animation mode
            anim_mode = layout.row(align=True)
            anim_mode.prop(bpy.context.scene.atom_blend_addon_settings, 'animation_mode')

        # file path selection
        file_path_row = layout.row(align=True)
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


# --- file loading ---
class ATOMBLEND_OT_load_file(bpy.types.Operator):
    bl_idname = "atom_blend_viewer.load_file"
    bl_label = ""
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
        path = context.scene.atom_blend_addon_settings.dev_dataset_selection + '.epos'
        if context.scene.atom_blend_addon_settings.dev_automatic_file_loading and os.path.isfile(path):
            self.filepath = context.scene.atom_blend_addon_settings.dev_dataset_selection + '.epos'
            return self.execute(context)
        else:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

class ATOMBLEND_OT_load_rrng_file(bpy.types.Operator):
    bl_idname = "atom_blend_viewer.load_rrng_file"
    bl_label = ""
    bl_description = "Load a file of the following types:\n.rrng"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(
        default='*.rrng',
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        ABGlobals.path_rrng = self.filepath

        if ABGlobals.path_rrng.lower().endswith('.rrng'):
            AtomBlendAddon.load_rrng_file(self, context)

        ABGlobals.FileLoaded_rrng = True
        print(f"Object Loaded: {ABGlobals.FileLoaded_rrng}")

        # set filepath to property
        bpy.context.scene.atom_blend_addon_settings.rrng_filepath = self.filepath

        # https://docs.blender.org/api/current/bpy.types.Operator.html#calling-a-file-selector
        return {'FINISHED'}

    def invoke(self, context, event):
        path = context.scene.atom_blend_addon_settings.dev_dataset_selection + '.epos'
        if context.scene.atom_blend_addon_settings.dev_automatic_file_loading and os.path.isfile(path):
            self.filepath = context.scene.atom_blend_addon_settings.dev_dataset_selection + '.rrng'
            return self.execute(context)
        else:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}


# --- buttons for switching between rendering a picture and video ---
# (maybe there is a better solution for this...)
class ATOMBLEND_OT_render_frame(bpy.types.Operator):
    bl_idname = "atom_blend.render_frame"
    bl_label = "Picture"
    bl_description = "Select if you want to render a picture"

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
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
        ABGlobals.render_frame = False
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

            print('Starting animation rendering...', context.scene.atom_blend_addon_settings.frame_amount)
            for i in range(1, context.scene.atom_blend_addon_settings.frame_amount+1):
                bpy.context.scene.frame_set(i)
                # write file
                ABManagement.save_image(self, context, cur_frame=i)

                # add frame to video editor
                img_name = ABGlobals.dataset_name + '_frame_' + str(i)
                img_path = out_path + '\\' + ABGlobals.dataset_name + '_frame_' + str(i) + '.png'
                bpy.context.scene.sequence_editor.sequences.new_image(name=img_name, filepath=img_path, channel=1, frame_start=i)
                print('Rendered frame ' + str(i) + ' / ' + str(context.scene.atom_blend_addon_settings.frame_amount))

            print('Wrote all frames. Creating the video now...')
            # render and save video
            bpy.data.scenes["Scene"].render.image_settings.file_format = 'AVI_JPEG'
            bpy.context.scene.render.filepath = out_path + '\\' + ABGlobals.dataset_name + '.avi'
            bpy.ops.render.render(animation=True)

            # delete all the written frames
            for i in range(1, context.scene.atom_blend_addon_settings.frame_amount+1):
                os.remove(path=out_path + '\\' + ABGlobals.dataset_name + '_frame_' + str(i) + '.png')

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
        # todo?: doesnt work when pressing numpad+0
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